import { ChevronLeft, ChevronRight } from "lucide-react";
import { useEffect, useRef, useState } from "react";

type BookingDatePickerProps = {
  label: string;
  selectLabelPrefix: string;
  value: string;
  minDate: string;
  maxDate?: string;
  invalidDateMessage: string;
  maxInvalidDateMessage?: string;
  holidayRateDates?: string[];
  holidayRateLabel?: string;
  isOpen: boolean;
  onToggle: () => void;
  onClose: () => void;
  onChange: (value: string) => void;
  onInvalidDate: (message: string) => void;
};

export function toDateInputValue(date: Date) {
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, "0");
  const day = String(date.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
}

export function parseDateInputValue(dateValue: string) {
  const date = new Date(`${dateValue}T00:00:00`);
  return Number.isNaN(date.getTime()) ? null : date;
}

export function addDaysToDateInputValue(dateValue: string, days: number) {
  const date = parseDateInputValue(dateValue);
  if (!date) {
    return "";
  }

  date.setDate(date.getDate() + days);
  return toDateInputValue(date);
}

export function isValidStayPeriod(checkIn: string, checkOut: string) {
  const checkInDate = parseDateInputValue(checkIn);
  const checkOutDate = parseDateInputValue(checkOut);
  return Boolean(checkInDate && checkOutDate && checkOutDate > checkInDate);
}

export function isPastDate(dateValue: string) {
  const date = parseDateInputValue(dateValue);
  if (!date) {
    return false;
  }

  const today = new Date();
  const todayDate = new Date(today.getFullYear(), today.getMonth(), today.getDate());
  return date < todayDate;
}

function getMonthStart(dateValue: string) {
  const date = parseDateInputValue(dateValue) || new Date();
  return new Date(date.getFullYear(), date.getMonth(), 1);
}

function addMonths(date: Date, months: number) {
  return new Date(date.getFullYear(), date.getMonth() + months, 1);
}

function getCalendarDates(monthDate: Date) {
  const firstDate = new Date(monthDate.getFullYear(), monthDate.getMonth(), 1);
  const lastDate = new Date(monthDate.getFullYear(), monthDate.getMonth() + 1, 0);
  const dates: Array<Date | null> = Array.from({ length: firstDate.getDay() }, () => null);

  for (let day = 1; day <= lastDate.getDate(); day += 1) {
    dates.push(new Date(monthDate.getFullYear(), monthDate.getMonth(), day));
  }

  return dates;
}

function formatDisplayDate(dateValue: string) {
  const date = parseDateInputValue(dateValue);
  if (!date) {
    return "";
  }

  return date.toLocaleDateString("zh-TW", {
    year: "numeric",
    month: "long",
    day: "numeric",
  });
}

function formatMonthTitle(date: Date) {
  return date.toLocaleDateString("zh-TW", {
    year: "numeric",
    month: "long",
  });
}

function isBeforeDateValue(date: Date, dateValue: string) {
  const targetDate = parseDateInputValue(dateValue);
  return Boolean(targetDate && date < targetDate);
}

function isAfterDateValue(date: Date, dateValue?: string) {
  if (!dateValue) {
    return false;
  }

  const targetDate = parseDateInputValue(dateValue);
  return Boolean(targetDate && date > targetDate);
}

export function BookingDatePicker({
  label,
  selectLabelPrefix,
  value,
  minDate,
  maxDate,
  invalidDateMessage,
  maxInvalidDateMessage,
  holidayRateDates = [],
  holidayRateLabel = "假日價",
  isOpen,
  onToggle,
  onClose,
  onChange,
  onInvalidDate,
}: BookingDatePickerProps) {
  const [calendarMonth, setCalendarMonth] = useState(() => getMonthStart(value));
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!isOpen) {
      return;
    }

    function handleOutsidePointerDown(event: PointerEvent) {
      if (!containerRef.current || !(event.target instanceof Node)) {
        return;
      }

      if (!containerRef.current.contains(event.target)) {
        onClose();
      }
    }

    document.addEventListener("pointerdown", handleOutsidePointerDown);
    return () => document.removeEventListener("pointerdown", handleOutsidePointerDown);
  }, [isOpen, onClose]);

  function openDatePicker() {
    setCalendarMonth(getMonthStart(value));
    onToggle();
  }

  function canShowPreviousCalendarMonth() {
    const previousMonth = addMonths(calendarMonth, -1);
    const minimumMonth = getMonthStart(minDate);
    return previousMonth >= minimumMonth;
  }

  function canShowNextCalendarMonth() {
    if (!maxDate) {
      return true;
    }

    const nextMonth = addMonths(calendarMonth, 1);
    const maximumMonth = getMonthStart(maxDate);
    return nextMonth <= maximumMonth;
  }

  function selectCalendarDate(date: Date) {
    if (isBeforeDateValue(date, minDate)) {
      onInvalidDate(invalidDateMessage);
      return;
    }
    if (isAfterDateValue(date, maxDate)) {
      onInvalidDate(maxInvalidDateMessage || invalidDateMessage);
      return;
    }

    onChange(toDateInputValue(date));
    onClose();
  }

  return (
    <div className="booking-date-field" ref={containerRef}>
      <span>{label}</span>
      <button
        className="booking-date-trigger"
        type="button"
        onClick={openDatePicker}
        aria-label={`${selectLabelPrefix}${label}`}
        aria-expanded={isOpen}
      >
        {formatDisplayDate(value)}
      </button>
      {isOpen && (
        <div className="booking-calendar" role="dialog" aria-label={label}>
          <div className="booking-calendar-header">
            <button
              type="button"
              onClick={() => setCalendarMonth((current) => addMonths(current, -1))}
              disabled={!canShowPreviousCalendarMonth()}
              aria-label="上一個月"
            >
              <ChevronLeft size={17} aria-hidden="true" />
            </button>
            <strong>{formatMonthTitle(calendarMonth)}</strong>
            <button
              type="button"
              onClick={() => setCalendarMonth((current) => addMonths(current, 1))}
              disabled={!canShowNextCalendarMonth()}
              aria-label="下一個月"
            >
              <ChevronRight size={17} aria-hidden="true" />
            </button>
          </div>
          <div className="booking-calendar-weekdays" aria-hidden="true">
            {["日", "一", "二", "三", "四", "五", "六"].map((weekday) => (
              <span key={weekday}>{weekday}</span>
            ))}
          </div>
          <div className="booking-calendar-grid">
            {getCalendarDates(calendarMonth).map((date, index) => {
              if (!date) {
                return <span className="booking-calendar-empty" key={`empty-${index}`} />;
              }

              const dateValue = toDateInputValue(date);
              const isSelected = dateValue === value;
              const isDisabled = isBeforeDateValue(date, minDate) || isAfterDateValue(date, maxDate);
              const isHolidayRate = holidayRateDates.includes(dateValue);
              const classNames = [
                isSelected ? "is-selected" : "",
                isHolidayRate ? "is-holiday-rate" : "",
              ].filter(Boolean).join(" ");
              return (
                <button
                  className={classNames}
                  type="button"
                  key={dateValue}
                  disabled={isDisabled}
                  onClick={() => selectCalendarDate(date)}
                  aria-label={isHolidayRate ? `${formatDisplayDate(dateValue)}，${holidayRateLabel}` : formatDisplayDate(dateValue)}
                  aria-pressed={isSelected}
                  title={isHolidayRate ? holidayRateLabel : undefined}
                >
                  {date.getDate()}
                </button>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}
