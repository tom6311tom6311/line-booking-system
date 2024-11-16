import yaml
import logging
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
from jobs.import_historical_bookings import import_historical_bookings
from jobs.sync_bookings_to_google_calendar import sync_bookings_to_google_calendar
from jobs.sync_bookings_with_notion import sync_bookings_with_notion

JOBS_CONFIG_PATH = 'jobs_config.yaml'

JOB_TYPE_STARTUP = 'startup'
JOB_TYPE_CRON = 'cron'

def load_config(file_path=JOBS_CONFIG_PATH):
  logging.info("Loading job config")
  with open(file_path, 'r') as file:
    config = yaml.safe_load(file)
  return config


JOB_FUNCTIONS = {
  'import_historical_bookings': import_historical_bookings,
  'sync_bookings_to_google_calendar': sync_bookings_to_google_calendar,
  'sync_bookings_with_notion': sync_bookings_with_notion
}

# Scheduler setup
def schedule_jobs(config):
  logging.info("Scheduling jobs")
  scheduler = BlockingScheduler()
  for job_name, job_details in config['jobs'].items():
    enabled = job_details['enabled'] == 'True'
    job_function = JOB_FUNCTIONS[job_details['job_function']]
    job_type = job_details['type']

    if (not enabled):
      logging.info(f"Job {job_name} disabled.")
      continue

    if job_type == JOB_TYPE_STARTUP:
      logging.info(f"Trigger startup job: {job_name}")
      job_function()
    elif job_type == JOB_TYPE_CRON:
      cron_expr = job_details['cron'].split()
      trigger = CronTrigger(
        minute=cron_expr[0], hour=cron_expr[1], day=cron_expr[2],
        month=cron_expr[3], day_of_week=cron_expr[4]
      )
      scheduler.add_job(job_function, trigger, id=job_name)
      logging.info(f"Scheduled job: {job_name} with cron: {job_details['cron']}")

  return scheduler

if __name__ == "__main__":
  logging.basicConfig(level=logging.INFO)

  config = load_config()
  scheduler = schedule_jobs(config)

  scheduler.start()
