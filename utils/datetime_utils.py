from datetime import datetime
from dateutil.relativedelta import relativedelta


# Generate the last n months im the specified format including the current month
def get_latest_months(num=3, format='%Y-%m'):
  current_date = datetime.today()
  return [(current_date - relativedelta(months=i)).strftime(format) for i in range(num)]
