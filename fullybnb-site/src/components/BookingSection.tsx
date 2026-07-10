import { BedDouble, Check, ChevronLeft, ChevronRight, Search, Send, UserRound } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import {
  cancelReservation,
  createReservation,
  getAvailability,
  getHolidayRateDates,
  getReservation,
  quoteReservation,
  type PublicQuote,
  type PublicReservation,
  type PublicRoom,
  type NightlyRoomPrice,
} from "../api/publicBooking";
import { siteContent } from "../data/siteContent";
import {
  BookingDatePicker,
  addDaysToDateInputValue,
  isPastDate,
  isValidStayPeriod,
  parseDateInputValue,
  toDateInputValue,
} from "./BookingDatePicker";
import { ImageCarousel } from "./ImageCarousel";
import { SectionHeading } from "./SectionHeading";

type BookingMode = "new" | "manage";
type BookingStep = "search" | "rooms" | "contact" | "review" | "complete";
type BookingDateField = "checkIn" | "checkOut";
const minimumCancelDaysBeforeCheckIn = 7;
const websiteBookingSource = "官網";

function formatCurrency(value: number) {
  return `NT$${value.toLocaleString("zh-TW")}`;
}

function getDefaultDates() {
  const checkIn = new Date();
  checkIn.setDate(checkIn.getDate() + 7);
  const checkOut = new Date(checkIn);
  checkOut.setDate(checkOut.getDate() + 1);
  return {
    checkIn: toDateInputValue(checkIn),
    checkOut: toDateInputValue(checkOut),
  };
}

function getDaysUntilDate(dateValue: string) {
  const today = new Date();
  const todayDate = new Date(today.getFullYear(), today.getMonth(), today.getDate());
  const targetDate = new Date(`${dateValue}T00:00:00`);
  return Math.round((targetDate.getTime() - todayDate.getTime()) / 86400000);
}

function getUserFacingErrorMessage(error: unknown, fallbackMessage: string) {
  if (error instanceof Error && /[\u3400-\u9fff]/.test(error.message)) {
    return error.message;
  }

  return fallbackMessage;
}

function getPreselectedRoomIdsFromHash() {
  const [, hashQuery = ""] = window.location.hash.split("?");
  const roomIds = new URLSearchParams(hashQuery).get("roomIds");
  return roomIds?.split(",").map((roomId) => roomId.trim()).filter(Boolean) || [];
}

function normalizeBookingUrl() {
  window.history.replaceState(null, "", `${window.location.pathname}${window.location.search}#booking`);
}

function getRoomName(room: PublicRoom) {
  return room.name || room.roomId;
}

function getConfiguredRoomName(roomId: string) {
  const siteRoom = siteContent.rooms.find((room) => room.roomIds?.includes(roomId));
  if (!siteRoom) {
    return roomId;
  }

  const roomIndex = siteRoom.roomIds?.indexOf(roomId) ?? -1;
  const nameParts = siteRoom.name.split(" / ").map((name) => name.trim());
  if (roomIndex >= 0 && nameParts[roomIndex]) {
    return nameParts[roomIndex];
  }

  return siteRoom.name;
}

function formatPrepaymentStatus(status: string) {
  const statusLabels: Record<string, string> = {
    unpaid: "未付",
    paid: "已付",
  };

  return statusLabels[status] || status;
}

function normalizeExtraBedCounts(roomIds: string[], counts: Record<string, number>) {
  return Object.fromEntries(roomIds.map((roomId) => [roomId, counts[roomId] || 0]));
}

function normalizeMobilePhoneInput(value: string) {
  return value.replace(/\D/g, "").slice(0, 10);
}

function isValidMobilePhone(value: string) {
  return /^09\d{8}$/.test(value);
}

function isWebsiteReservation(reservation: PublicReservation) {
  return reservation.source === websiteBookingSource;
}

function getRoomTypeLabel(room: PublicRoom) {
  const labels: Record<string, string> = {
    standard_double_room: "雙人套房",
    standard_family_room: "四人套房",
    economic_family_room: "四人雅房",
    backpacker_bed: "背包客",
    washitsu: "和室",
    grass: "帳篷",
  };

  return labels[room.roomType] || room.roomType;
}

function getBookingStepIcon(step: BookingStep) {
  switch (step) {
    case "search":
      return <Search size={17} aria-hidden="true" />;
    case "rooms":
      return <BedDouble size={17} aria-hidden="true" />;
    case "contact":
      return <UserRound size={17} aria-hidden="true" />;
    case "review":
      return <Send size={17} aria-hidden="true" />;
    case "complete":
      return <Check size={17} aria-hidden="true" />;
  }
}

function getRoomImageGroup(room: PublicRoom) {
  return siteContent.rooms.find((siteRoom) => {
    if (siteRoom.roomIds?.includes(room.roomId)) {
      return true;
    }
    return siteRoom.name.split(" / ").some((namePart) => namePart === room.name);
  });
}

function isSiteIntroducedRoom(room: PublicRoom) {
  return Boolean(getRoomImageGroup(room));
}

function getRoomSpecialNotes(room: PublicRoom) {
  return getRoomImageGroup(room)?.specialNotes?.filter((note) => note.roomId === room.roomId) || [];
}

function getFallbackNightlyPrices(room: PublicRoom, checkIn: string, checkOut: string): NightlyRoomPrice[] {
  const prices: NightlyRoomPrice[] = [];
  const currentDate = new Date(`${checkIn}T00:00:00`);
  const lastDate = new Date(`${checkOut}T00:00:00`);

  while (currentDate < lastDate) {
    const isHoliday = currentDate.getDay() === 6;
    prices.push({
      date: toDateInputValue(currentDate),
      price: isHoliday ? room.holidayPricePerNight : room.weekdayPricePerNight,
      rateType: isHoliday ? "holiday" : "weekday",
    });
    currentDate.setDate(currentDate.getDate() + 1);
  }

  return prices;
}

export function BookingSection() {
  const { bookingSection, reservationPolicies } = siteContent;
  const defaultDates = useMemo(getDefaultDates, []);
  const todayDate = useMemo(() => toDateInputValue(new Date()), []);
  const [mode, setMode] = useState<BookingMode>("new");
  const [bookingStep, setBookingStep] = useState<BookingStep>("search");
  const [checkIn, setCheckIn] = useState(defaultDates.checkIn);
  const [checkOut, setCheckOut] = useState(defaultDates.checkOut);
  const [rooms, setRooms] = useState<PublicRoom[]>([]);
  const [roomSlideIndex, setRoomSlideIndex] = useState(0);
  const [nightlyRoomPrices, setNightlyRoomPrices] = useState<Record<string, NightlyRoomPrice[]>>({});
  const [selectedRoomIds, setSelectedRoomIds] = useState<string[]>([]);
  const [extraBedCounts, setExtraBedCounts] = useState<Record<string, number>>({});
  const [quote, setQuote] = useState<PublicQuote | null>(null);
  const [customerName, setCustomerName] = useState("");
  const [phoneNumber, setPhoneNumber] = useState("");
  const [notes, setNotes] = useState("");
  const [createdReservation, setCreatedReservation] = useState<PublicReservation | null>(null);
  const [lookupBookingId, setLookupBookingId] = useState("");
  const [lookupPhoneNumber, setLookupPhoneNumber] = useState("");
  const [lookupReservation, setLookupReservation] = useState<PublicReservation | null>(null);
  const [statusMessage, setStatusMessage] = useState("");
  const [errorMessage, setErrorMessage] = useState("");
  const [holidayRateDates, setHolidayRateDates] = useState<string[]>([]);
  const [isAvailabilityLoading, setIsAvailabilityLoading] = useState(false);
  const [isQuoteLoading, setIsQuoteLoading] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isLookupLoading, setIsLookupLoading] = useState(false);
  const [activeDatePicker, setActiveDatePicker] = useState<BookingDateField | null>(null);

  const roomById = Object.fromEntries(rooms.map((room) => [room.roomId, room]));
  const bookingSteps: BookingStep[] = ["search", "rooms", "contact", "review", "complete"];
  const activeStepIndex = bookingSteps.indexOf(bookingStep);
  const activeRoomIndex = rooms.length ? Math.min(Math.max(roomSlideIndex, 0), rooms.length - 1) : 0;
  const isStayPeriodValid = isValidStayPeriod(checkIn, checkOut);
  const isSearchPeriodValid = isStayPeriodValid && !isPastDate(checkIn) && !isPastDate(checkOut);
  const isRoomSelectionValid = Boolean(selectedRoomIds.length && quote && !isQuoteLoading);
  const isContactInfoValid = Boolean(customerName.trim() && isValidMobilePhone(phoneNumber));

  useEffect(() => {
    setQuote(null);
  }, [checkIn, checkOut, selectedRoomIds, extraBedCounts]);

  useEffect(() => {
    let isCurrent = true;
    const startDate = todayDate;
    const endDate = addDaysToDateInputValue(todayDate, 730);

    getHolidayRateDates(startDate, endDate)
      .then((result) => {
        if (isCurrent) {
          setHolidayRateDates(result.dates);
        }
      })
      .catch(() => {
        if (isCurrent) {
          setHolidayRateDates([]);
        }
      });

    return () => {
      isCurrent = false;
    };
  }, [todayDate]);

  useEffect(() => {
    function handleHashChange() {
      if (window.location.hash.startsWith("#booking?roomIds=")) {
        document.getElementById("booking")?.scrollIntoView();
        setMode("new");
        setBookingStep("search");
        setRooms([]);
        setNightlyRoomPrices({});
        setSelectedRoomIds([]);
        setExtraBedCounts({});
        setQuote(null);
        setStatusMessage("");
        setErrorMessage("");
      }
    }

    handleHashChange();
    window.addEventListener("hashchange", handleHashChange);
    return () => window.removeEventListener("hashchange", handleHashChange);
  }, []);

  useEffect(() => {
    if (!selectedRoomIds.length) {
      return;
    }

    let isCurrent = true;
    setIsQuoteLoading(true);
    quoteReservation({
      checkIn,
      checkOut,
      roomIds: selectedRoomIds,
      extraBedCounts: normalizeExtraBedCounts(selectedRoomIds, extraBedCounts),
    })
      .then((nextQuote) => {
        if (isCurrent) {
          setQuote(nextQuote);
        }
      })
      .catch((error: Error) => {
        if (isCurrent) {
          setQuote(null);
          setErrorMessage(getUserFacingErrorMessage(error, bookingSection.messages.quoteError));
        }
      })
      .finally(() => {
        if (isCurrent) {
          setIsQuoteLoading(false);
        }
      });

    return () => {
      isCurrent = false;
    };
  }, [checkIn, checkOut, selectedRoomIds, extraBedCounts]);

  function updateCheckIn(value: string) {
    const nextCheckIn = isPastDate(value) ? todayDate : value;

    if (nextCheckIn !== value) {
      setErrorMessage(bookingSection.messages.pastDateNotAllowed);
    } else {
      setErrorMessage("");
    }

    setCheckIn(nextCheckIn);
    setCheckOut(addDaysToDateInputValue(nextCheckIn, 1));
    setBookingStep("search");
    setCreatedReservation(null);
  }

  function updateCheckOut(value: string) {
    if (isPastDate(value)) {
      setCheckOut(addDaysToDateInputValue(checkIn, 1));
      setErrorMessage(bookingSection.messages.pastDateNotAllowed);
      setBookingStep("search");
      setCreatedReservation(null);
      return;
    }

    if (!isValidStayPeriod(checkIn, value)) {
      setCheckOut(addDaysToDateInputValue(checkIn, 1));
      setErrorMessage(bookingSection.messages.invalidStayPeriod);
      setBookingStep("search");
      setCreatedReservation(null);
      return;
    }

    setErrorMessage("");
    setCheckOut(value);
    setBookingStep("search");
    setCreatedReservation(null);
  }

  async function handleAvailabilitySearch() {
    setErrorMessage("");
    setStatusMessage("");
    setCreatedReservation(null);
    if (isPastDate(checkIn) || isPastDate(checkOut)) {
      setRooms([]);
      setNightlyRoomPrices({});
      setSelectedRoomIds([]);
      setExtraBedCounts({});
      setQuote(null);
      setBookingStep("search");
      setErrorMessage(bookingSection.messages.pastDateNotAllowed);
      return;
    }
    if (!isValidStayPeriod(checkIn, checkOut)) {
      setRooms([]);
      setNightlyRoomPrices({});
      setSelectedRoomIds([]);
      setExtraBedCounts({});
      setQuote(null);
      setBookingStep("search");
      setErrorMessage(bookingSection.messages.invalidStayPeriod);
      return;
    }
    setIsAvailabilityLoading(true);
    try {
      const availability = await getAvailability(checkIn, checkOut);
      const availableRooms = availability.rooms.filter((room) => room.available && isSiteIntroducedRoom(room));
      if (!availableRooms.length) {
        setRooms([]);
        setNightlyRoomPrices(availability.nightlyRoomPrices || {});
        setSelectedRoomIds([]);
        setExtraBedCounts({});
        setQuote(null);
        setRoomSlideIndex(0);
        setBookingStep("rooms");
        setStatusMessage(bookingSection.messages.noRoomsAvailable);
        return;
      }

      const [preselectedRoomId] = getPreselectedRoomIdsFromHash();
      const isPreselectedRoomAvailable = availableRooms.some((room) => room.roomId === preselectedRoomId);
      const preselectedRoomIds = isPreselectedRoomAvailable && preselectedRoomId ? [preselectedRoomId] : [];
      const preselectedRoomIndex = availableRooms.findIndex((room) => room.roomId === preselectedRoomId);
      setRooms(availableRooms);
      setNightlyRoomPrices(availability.nightlyRoomPrices || {});
      setSelectedRoomIds(preselectedRoomIds);
      setExtraBedCounts({});
      setRoomSlideIndex(Math.max(preselectedRoomIndex, 0));
      setBookingStep("rooms");
    } catch (error) {
      setRooms([]);
      setNightlyRoomPrices({});
      setErrorMessage(getUserFacingErrorMessage(error, bookingSection.messages.availabilityError));
    } finally {
      setIsAvailabilityLoading(false);
    }
  }

  function handleRoomsContinue() {
    setErrorMessage("");
    if (!selectedRoomIds.length || !quote) {
      setErrorMessage(bookingSection.messages.roomsRequired);
      return;
    }
    setBookingStep("contact");
  }

  function toggleRoom(roomId: string) {
    setErrorMessage("");
    setCreatedReservation(null);
    setSelectedRoomIds((current) => {
      if (current.includes(roomId)) {
        setExtraBedCounts((counts) => {
          const nextCounts = { ...counts };
          delete nextCounts[roomId];
          return nextCounts;
        });
        return current.filter((selectedRoomId) => selectedRoomId !== roomId);
      }
      return [...current, roomId];
    });
  }

  function updateExtraBedCount(roomId: string, count: number) {
    setCreatedReservation(null);
    setExtraBedCounts((current) => ({
      ...current,
      [roomId]: count,
    }));
  }

  function updatePhoneNumber(value: string) {
    setPhoneNumber(normalizeMobilePhoneInput(value));
    setCreatedReservation(null);
  }

  function resetNewBookingForm() {
    setCheckIn(defaultDates.checkIn);
    setCheckOut(defaultDates.checkOut);
    setRooms([]);
    setRoomSlideIndex(0);
    setNightlyRoomPrices({});
    setSelectedRoomIds([]);
    setExtraBedCounts({});
    setQuote(null);
    setCustomerName("");
    setPhoneNumber("");
    setNotes("");
  }

  function canNavigateToStep(step: BookingStep) {
    if (step === bookingStep) {
      return true;
    }

    if (createdReservation) {
      return step === "search" || step === "complete";
    }

    switch (step) {
      case "search":
        return true;
      case "rooms":
        return rooms.length > 0;
      case "contact":
        return isRoomSelectionValid;
      case "review":
        return isRoomSelectionValid && isContactInfoValid;
      case "complete":
        return Boolean(createdReservation);
    }
  }

  function navigateToStep(step: BookingStep) {
    if (canNavigateToStep(step)) {
      setErrorMessage("");
      setBookingStep(step);
    }
  }

  function showPreviousRoom() {
    setRoomSlideIndex((current) => Math.max(current - 1, 0));
  }

  function showNextRoom() {
    setRoomSlideIndex((current) => Math.min(current + 1, rooms.length - 1));
  }

  function showRoom(index: number) {
    setRoomSlideIndex(index);
  }

  function handleContactContinue() {
    setErrorMessage("");
    setStatusMessage("");

    if (!selectedRoomIds.length || !quote) {
      setErrorMessage(bookingSection.messages.roomsRequired);
      return;
    }
    if (!customerName.trim()) {
      setErrorMessage(bookingSection.messages.nameRequired);
      return;
    }
    if (!phoneNumber.trim()) {
      setErrorMessage(bookingSection.messages.bookingPhoneRequired);
      return;
    }
    if (!isValidMobilePhone(phoneNumber)) {
      setErrorMessage(bookingSection.messages.mobilePhoneInvalid);
      return;
    }
    setBookingStep("review");
  }

  async function handleSubmitReservation() {
    setErrorMessage("");
    setStatusMessage("");
    setCreatedReservation(null);

    if (!selectedRoomIds.length || !quote) {
      setErrorMessage(bookingSection.messages.roomsRequired);
      return;
    }
    if (!customerName.trim()) {
      setErrorMessage(bookingSection.messages.nameRequired);
      return;
    }
    if (!phoneNumber.trim()) {
      setErrorMessage(bookingSection.messages.bookingPhoneRequired);
      return;
    }
    if (!isValidMobilePhone(phoneNumber)) {
      setErrorMessage(bookingSection.messages.mobilePhoneInvalid);
      return;
    }

    setIsSubmitting(true);
    try {
      const result = await createReservation({
        customerName: customerName.trim(),
        phoneNumber,
        checkIn,
        checkOut,
        roomIds: selectedRoomIds,
        extraBedCounts: normalizeExtraBedCounts(selectedRoomIds, extraBedCounts),
        notes: notes.trim(),
      });
      setCreatedReservation(result.reservation);
      resetNewBookingForm();
      normalizeBookingUrl();
      setStatusMessage(`${bookingSection.messages.createSuccessPrefix} ${result.reservation.bookingId} ${bookingSection.messages.createSuccessSuffix}`);
      setBookingStep("complete");
    } catch (error) {
      setErrorMessage(getUserFacingErrorMessage(error, bookingSection.messages.createError));
    } finally {
      setIsSubmitting(false);
    }
  }

  async function handleLookupReservation() {
    setErrorMessage("");
    setStatusMessage("");
    setLookupReservation(null);

    const bookingId = Number(lookupBookingId);
    if (!Number.isInteger(bookingId) || bookingId <= 0) {
      setErrorMessage(bookingSection.messages.invalidBookingId);
      return;
    }
    if (!lookupPhoneNumber.trim()) {
      setErrorMessage(bookingSection.messages.lookupPhoneRequired);
      return;
    }
    if (!isValidMobilePhone(lookupPhoneNumber)) {
      setErrorMessage(bookingSection.messages.mobilePhoneInvalid);
      return;
    }

    setIsLookupLoading(true);
    try {
      const result = await getReservation(bookingId, lookupPhoneNumber);
      setLookupReservation(result.reservation);
    } catch (error) {
      setErrorMessage(getUserFacingErrorMessage(error, bookingSection.messages.lookupError));
    } finally {
      setIsLookupLoading(false);
    }
  }

  async function handleCancelReservation() {
    if (!lookupReservation) {
      return;
    }

    setErrorMessage("");
    setStatusMessage("");
    setIsLookupLoading(true);
    try {
      const result = await cancelReservation(lookupReservation.bookingId, lookupPhoneNumber);
      setLookupReservation(result.reservation);
      setStatusMessage(`${bookingSection.messages.cancelSuccessPrefix} ${result.reservation.bookingId} ${bookingSection.messages.cancelSuccessSuffix}`);
    } catch (error) {
      setErrorMessage(getUserFacingErrorMessage(error, bookingSection.messages.cancelError));
    } finally {
      setIsLookupLoading(false);
    }
  }

  function getRoomSummaryName(roomId: string, reservationRooms?: PublicRoom[]) {
    const reservationRoomById = Object.fromEntries((reservationRooms || []).map((room) => [room.roomId, room]));
    const room = reservationRoomById[roomId] || roomById[roomId];
    const roomName = room ? getRoomName(room) : getConfiguredRoomName(roomId);
    const roomTypeLabel = room?.roomTypeLabel || (room ? getRoomTypeLabel(room) : "");
    return roomTypeLabel ? `${roomTypeLabel} ${roomName}` : roomName;
  }

  function renderRoomDetails(roomIds: string[], extraBedCountsByRoom: Record<string, number>, reservationRooms?: PublicRoom[]) {
    return roomIds.map((roomId) => {
      const extraBedCount = extraBedCountsByRoom[roomId] || 0;
      const roomName = getRoomSummaryName(roomId, reservationRooms);
      return (
        <span className="booking-room-detail" key={roomId}>
          {roomName}
          {extraBedCount > 0 && `（${bookingSection.breakdown.extraBedPrefix}${extraBedCount}${bookingSection.breakdown.extraBedSuffix}）`}
        </span>
      );
    });
  }

  function renderReservationDiscountRows(reservation: PublicReservation) {
    const websiteDiscountAmount = reservation.websiteDiscountAmount ?? 0;
    if (websiteDiscountAmount <= 0) {
      return null;
    }

    const originalTotalPrice = reservation.originalTotalPrice ?? reservation.totalPrice + websiteDiscountAmount;
    return (
      <>
        <div>
          <dt>{bookingSection.summary.originalTotalPrice}</dt>
          <dd>{formatCurrency(originalTotalPrice)}</dd>
        </div>
        <div>
          <dt>{bookingSection.summary.websiteDiscount}</dt>
          <dd className="booking-discount-amount">-{formatCurrency(websiteDiscountAmount)}</dd>
        </div>
      </>
    );
  }

  const bookingSummaryContent = (
    <>
      <h3>{bookingSection.summary.title}</h3>
      {isQuoteLoading ? (
        <p>{bookingSection.summary.quoting}</p>
      ) : quote ? (
        <dl>
          <div>
            <dt>{bookingSection.summary.customerName}</dt>
            <dd>{customerName.trim() || "-"}</dd>
          </div>
          <div>
            <dt>{bookingSection.summary.phone}</dt>
            <dd>{phoneNumber || "-"}</dd>
          </div>
          <div>
            <dt>{bookingSection.dateFields.checkIn}</dt>
            <dd>{checkIn}</dd>
          </div>
          <div>
            <dt>{bookingSection.dateFields.checkOut}</dt>
            <dd>{checkOut}</dd>
          </div>
          <div>
            <dt>{bookingSection.summary.nights}</dt>
            <dd>{quote.nights}</dd>
          </div>
          <div>
            <dt>{bookingSection.manage.rooms}</dt>
            <dd>{renderRoomDetails(selectedRoomIds, normalizeExtraBedCounts(selectedRoomIds, extraBedCounts))}</dd>
          </div>
          {quote.websiteDiscountAmount > 0 && (
            <>
              <div>
                <dt>{bookingSection.summary.originalTotalPrice}</dt>
                <dd>{formatCurrency(quote.originalTotalPrice)}</dd>
              </div>
              <div>
                <dt>{bookingSection.summary.websiteDiscount}</dt>
                <dd className="booking-discount-amount">-{formatCurrency(quote.websiteDiscountAmount)}</dd>
              </div>
            </>
          )}
          <div>
            <dt>{bookingSection.summary.totalPrice}</dt>
            <dd>{formatCurrency(quote.totalPrice)}</dd>
          </div>
          <div>
            <dt>{bookingSection.summary.prepayment}</dt>
            <dd>{formatCurrency(quote.suggestedPrepayment)}</dd>
          </div>
          <div>
            <dt>{bookingSection.summary.notes}</dt>
            <dd>{notes.trim() || bookingSection.summary.noNotes}</dd>
          </div>
        </dl>
      ) : (
        <p>{bookingSection.summary.emptyQuote}</p>
      )}
    </>
  );

  return (
    <section className="section booking-section" id="booking">
      <SectionHeading eyebrow={bookingSection.eyebrow} title={bookingSection.title} />

      <div className="booking-discount-banner">
        <strong>{bookingSection.discountBanner.title}</strong>
        <span>{bookingSection.discountBanner.description}</span>
      </div>

      <div className="booking-policies">
        <h3>{reservationPolicies.title}</h3>
        <ul>
          {reservationPolicies.items.map((item) => (
            <li key={item}>{item}</li>
          ))}
        </ul>
      </div>

      <div className="booking-tabs" role="group" aria-label={bookingSection.messages.tabsAriaLabel}>
        <button type="button" className={mode === "new" ? "is-active" : ""} onClick={() => setMode("new")}>
          {bookingSection.tabs.booking}
        </button>
        <button type="button" className={mode === "manage" ? "is-active" : ""} onClick={() => setMode("manage")}>
          {bookingSection.tabs.manage}
        </button>
      </div>

      {mode === "new" ? (
        <div className="booking-panel">
          <ol className="booking-stepper" aria-label={bookingSection.steps.ariaLabel}>
            {bookingSteps.map((step, index) => {
              const isActive = index === activeStepIndex;
              const canNavigate = canNavigateToStep(step);
              return (
                <li
                  className={isActive ? "is-active" : index < activeStepIndex ? "is-complete" : ""}
                  key={step}
                >
                  <button
                    type="button"
                    disabled={!canNavigate}
                    onClick={() => navigateToStep(step)}
                    aria-current={isActive ? "step" : undefined}
                    aria-label={bookingSection.steps[step]}
                    title={bookingSection.steps[step]}
                  >
                    <span>{getBookingStepIcon(step)}</span>
                    {isActive && <strong>{bookingSection.steps[step]}</strong>}
                  </button>
                </li>
              );
            })}
          </ol>

          {bookingStep === "search" && (
            <div className="booking-date-row">
              <BookingDatePicker
                label={bookingSection.dateFields.checkIn}
                selectLabelPrefix={bookingSection.dateFields.selectPrefix}
                value={checkIn}
                minDate={todayDate}
                invalidDateMessage={bookingSection.messages.pastDateNotAllowed}
                holidayRateDates={holidayRateDates}
                holidayRateLabel={bookingSection.dateFields.holidayRate}
                isOpen={activeDatePicker === "checkIn"}
                onToggle={() => setActiveDatePicker((current) => (current === "checkIn" ? null : "checkIn"))}
                onClose={() => setActiveDatePicker(null)}
                onChange={updateCheckIn}
                onInvalidDate={setErrorMessage}
              />
              <BookingDatePicker
                label={bookingSection.dateFields.checkOut}
                selectLabelPrefix={bookingSection.dateFields.selectPrefix}
                value={checkOut}
                minDate={addDaysToDateInputValue(checkIn, 1)}
                invalidDateMessage={bookingSection.messages.invalidStayPeriod}
                holidayRateDates={holidayRateDates}
                holidayRateLabel={bookingSection.dateFields.holidayRate}
                isOpen={activeDatePicker === "checkOut"}
                onToggle={() => setActiveDatePicker((current) => (current === "checkOut" ? null : "checkOut"))}
                onClose={() => setActiveDatePicker(null)}
                onChange={updateCheckOut}
                onInvalidDate={setErrorMessage}
              />
              <button className="primary-button booking-search-button" type="button" onClick={handleAvailabilitySearch} disabled={isAvailabilityLoading || !isSearchPeriodValid}>
                <Search size={18} aria-hidden="true" />
                {isAvailabilityLoading ? bookingSection.dateFields.searching : bookingSection.dateFields.search}
              </button>
            </div>
          )}

          {bookingStep === "rooms" && rooms.length > 0 && (
            <>
              <div className={`booking-room-carousel ${rooms.length > 1 ? "has-controls" : ""}`} aria-label={bookingSection.roomCarousel.ariaLabel}>
                {rooms.length > 1 && (
                  <button
                    className="carousel-button carousel-button-previous booking-room-carousel-button"
                    type="button"
                    onClick={showPreviousRoom}
                    disabled={activeRoomIndex === 0}
                    aria-label={bookingSection.roomCarousel.previous}
                  >
                    <ChevronLeft size={22} aria-hidden="true" />
                  </button>
                )}
                <div className="booking-room-viewport">
                  <div
                    className="booking-room-track"
                    style={{ transform: `translateX(-${activeRoomIndex * 100}%)` }}
                  >
                {rooms.map((room) => {
                const isSelected = selectedRoomIds.includes(room.roomId);
                const roomImageGroup = getRoomImageGroup(room);
                const roomSpecialNotes = getRoomSpecialNotes(room);
                const roomNightlyPrices = nightlyRoomPrices[room.roomId] || getFallbackNightlyPrices(room, checkIn, checkOut);
                const roomStayTotal = roomNightlyPrices.reduce((total, nightlyPrice) => total + nightlyPrice.price, 0);
                return (
                  <article
                    className={`booking-room-card ${isSelected ? "is-selected" : ""}`}
                    key={room.roomId}
                    aria-hidden={room.roomId !== rooms[activeRoomIndex]?.roomId}
                  >
                    {roomImageGroup && (
                      <ImageCarousel images={roomImageGroup.images} label={`${getRoomName(room)}${room.description}`} />
                    )}
                    <div>
                      <p className="eyebrow">{getRoomTypeLabel(room)}</p>
                      <h3>{getRoomName(room)}</h3>
                      <ul className="tag-list booking-room-tags" aria-label={`${getRoomName(room)}特色`}>
                        {roomImageGroup?.highlights.map((highlight) => (
                          <li key={highlight}>{highlight}</li>
                        ))}
                        <li>{bookingSection.roomCard.extraBedPrefix}{room.extraBedNumber}{bookingSection.roomCard.extraBedSuffix}</li>
                      </ul>
                      {roomSpecialNotes.length > 0 && (
                        <ul className="room-special-notes booking-room-special-notes">
                          {roomSpecialNotes.map((note) => (
                            <li key={note.roomId}>{note.text}</li>
                          ))}
                        </ul>
                      )}
                      <div className="booking-nightly-prices">
                        {roomNightlyPrices.map((nightlyPrice) => (
                          <div key={`${room.roomId}-${nightlyPrice.date}`}>
                            <span>{nightlyPrice.date}</span>
                            <strong>{formatCurrency(nightlyPrice.price)}</strong>
                          </div>
                        ))}
                        <div className="booking-room-total">
                          <span>{bookingSection.roomCard.stayTotal}</span>
                          <strong>{formatCurrency(roomStayTotal)}</strong>
                        </div>
                      </div>
                    </div>
                    <button
                      type="button"
                      className={isSelected ? "secondary-action is-selected" : "secondary-action"}
                      onClick={() => toggleRoom(room.roomId)}
                    >
                      {isSelected ? bookingSection.roomCard.selected : bookingSection.roomCard.add}
                    </button>
                    <div className="extra-bed-control">
                      <span>{bookingSection.roomCard.extraBedLabel}</span>
                      <div className="extra-bed-options">
                        {isSelected && room.extraBedNumber > 0 ? (
                        Array.from({ length: room.extraBedNumber + 1 }, (_, count) => (
                          <button
                            key={count}
                            type="button"
                            className={(extraBedCounts[room.roomId] || 0) === count ? "is-selected" : ""}
                            onClick={() => updateExtraBedCount(room.roomId, count)}
                          >
                            {count}
                          </button>
                        ))
                        ) : (
                          <span className="extra-bed-placeholder">{bookingSection.roomCard.extraBedPlaceholder}</span>
                        )}
                      </div>
                    </div>
                  </article>
                );
              })}
                  </div>
                </div>
                {rooms.length > 1 && (
                  <button
                    className="carousel-button carousel-button-next booking-room-carousel-button"
                    type="button"
                    onClick={showNextRoom}
                    disabled={activeRoomIndex === rooms.length - 1}
                    aria-label={bookingSection.roomCarousel.next}
                  >
                    <ChevronRight size={22} aria-hidden="true" />
                  </button>
                )}
              </div>
              {rooms.length > 1 && (
                <div className="carousel-dots booking-room-carousel-dots" aria-label={bookingSection.roomCarousel.paginationAriaLabel}>
                  {rooms.map((room, index) => (
                    <button
                      key={room.roomId}
                      type="button"
                      className={index === activeRoomIndex ? "is-active" : ""}
                      onClick={() => showRoom(index)}
                      aria-label={`${bookingSection.roomCarousel.goToPrefix} ${index + 1} ${bookingSection.roomCarousel.goToSuffix}`}
                      aria-current={index === activeRoomIndex}
                    />
                  ))}
                </div>
              )}
              <div className="booking-step-actions">
                <button className="secondary-action" type="button" onClick={() => setBookingStep("search")}>
                  {bookingSection.actions.backToSearch}
                </button>
                <button className="primary-button" type="button" onClick={handleRoomsContinue} disabled={!selectedRoomIds.length || isQuoteLoading}>
                  {bookingSection.actions.next}
                </button>
              </div>
            </>
          )}

          {bookingStep === "rooms" && rooms.length === 0 && (
            <div className="booking-step-actions">
              <button className="secondary-action" type="button" onClick={() => setBookingStep("search")}>
                {bookingSection.actions.backToSearch}
              </button>
            </div>
          )}

          {bookingStep === "contact" && (
            <div className="booking-form">
              <h3>{bookingSection.form.title}</h3>
              <label>
                <span>{bookingSection.form.name}</span>
                <input value={customerName} onChange={(event) => setCustomerName(event.target.value)} placeholder={bookingSection.form.namePlaceholder} />
              </label>
              <label>
                <span>{bookingSection.form.phone}</span>
                <input
                  value={phoneNumber}
                  onChange={(event) => updatePhoneNumber(event.target.value)}
                  placeholder={bookingSection.form.phonePlaceholder}
                  inputMode="numeric"
                  pattern="09[0-9]{8}"
                  type="tel"
                />
              </label>
              <label>
                <span>{bookingSection.form.notes}</span>
                <textarea value={notes} onChange={(event) => setNotes(event.target.value)} placeholder={bookingSection.form.notesPlaceholder} />
              </label>
              <div className="booking-step-actions">
                <button className="secondary-action" type="button" onClick={() => setBookingStep("rooms")}>
                  {bookingSection.actions.back}
                </button>
                <button className="primary-button" type="button" onClick={handleContactContinue}>
                  {bookingSection.actions.next}
                </button>
              </div>
            </div>
          )}

          {bookingStep === "review" && (
            <aside className="booking-summary">
              {bookingSummaryContent}
              <div className="booking-action-row">
                <button className="secondary-action" type="button" onClick={() => setBookingStep("contact")}>
                  {bookingSection.actions.back}
                </button>
                <button className="primary-button" type="button" disabled={isSubmitting || !quote} onClick={handleSubmitReservation}>
                  {bookingSection.summary.create}
                </button>
              </div>
            </aside>
          )}

          {bookingStep === "complete" && createdReservation && (
            <aside className="booking-summary booking-complete">
              <h3>{bookingSection.complete.title}</h3>
              <p>
                <Check size={17} aria-hidden="true" />
                {bookingSection.messages.saveBookingId} {createdReservation.bookingId}，{bookingSection.messages.saveBookingIdSuffix}
              </p>
              <dl>
                <div>
                  <dt>{bookingSection.complete.bookingId}</dt>
                  <dd>{createdReservation.bookingId}</dd>
                </div>
                <div>
                  <dt>{bookingSection.summary.customerName}</dt>
                  <dd>{createdReservation.customerName}</dd>
                </div>
                <div>
                  <dt>{bookingSection.summary.phone}</dt>
                  <dd>{createdReservation.phoneNumber}</dd>
                </div>
                <div>
                  <dt>{bookingSection.dateFields.checkIn}</dt>
                  <dd>{createdReservation.checkIn}</dd>
                </div>
                <div>
                  <dt>{bookingSection.dateFields.checkOut}</dt>
                  <dd>{createdReservation.checkOut}</dd>
                </div>
                <div>
                  <dt>{bookingSection.summary.nights}</dt>
                  <dd>{createdReservation.nights}</dd>
                </div>
                <div>
                  <dt>{bookingSection.manage.rooms}</dt>
                  <dd>{renderRoomDetails(createdReservation.roomIds, createdReservation.extraBedCounts, createdReservation.rooms)}</dd>
                </div>
                {renderReservationDiscountRows(createdReservation)}
                <div>
                  <dt>{bookingSection.summary.totalPrice}</dt>
                  <dd>{formatCurrency(createdReservation.totalPrice)}</dd>
                </div>
                <div>
                  <dt>{bookingSection.summary.prepayment}</dt>
                  <dd>{formatCurrency(createdReservation.prepayment)}</dd>
                </div>
                <div>
                  <dt>{bookingSection.complete.prepaymentStatus}</dt>
                  <dd>{formatPrepaymentStatus(createdReservation.prepaymentStatus)}</dd>
                </div>
                {isWebsiteReservation(createdReservation) && (
                  <div>
                    <dt>{bookingSection.summary.notes}</dt>
                    <dd>{createdReservation.notes || bookingSection.summary.noNotes}</dd>
                  </div>
                )}
              </dl>
              <p className="booking-confirmation-note">{bookingSection.complete.prepaymentNotice}</p>
            </aside>
          )}

          {(errorMessage || (statusMessage && bookingStep !== "complete")) && (
            <div className={`booking-result ${errorMessage ? "is-error" : ""}`}>
              {errorMessage && <p>{errorMessage}</p>}
              {statusMessage && <p>{statusMessage}</p>}
            </div>
          )}
        </div>
      ) : (
        <div className="booking-panel booking-manage-panel">
          <div className="booking-form">
            <h3>{bookingSection.manage.formTitle}</h3>
            <p className="booking-manage-note">{bookingSection.manage.supportNote}</p>
            <label>
              <span>{bookingSection.manage.bookingId}</span>
              <input value={lookupBookingId} onChange={(event) => setLookupBookingId(event.target.value)} placeholder={bookingSection.manage.bookingIdPlaceholder} />
            </label>
            <label>
              <span>{bookingSection.manage.phone}</span>
              <input
                value={lookupPhoneNumber}
                onChange={(event) => setLookupPhoneNumber(normalizeMobilePhoneInput(event.target.value))}
                placeholder={bookingSection.manage.phonePlaceholder}
                inputMode="numeric"
                pattern="09[0-9]{8}"
                type="tel"
              />
            </label>
            <button className="primary-button" type="button" disabled={!lookupBookingId || !lookupPhoneNumber || isLookupLoading} onClick={handleLookupReservation}>
              <UserRound size={18} aria-hidden="true" />
              {isLookupLoading ? bookingSection.manage.searching : bookingSection.manage.search}
            </button>
          </div>
          {lookupReservation && (
            <div className="booking-summary">
              <h3>{bookingSection.manage.summaryTitle}</h3>
                <dl>
                  <div>
                    <dt>{bookingSection.complete.bookingId}</dt>
                    <dd>{lookupReservation.bookingId}</dd>
                  </div>
                  <div>
                    <dt>{bookingSection.manage.status}</dt>
                    <dd>{lookupReservation.status === "canceled" ? bookingSection.manage.canceledStatus : bookingSection.manage.activeStatus}</dd>
                  </div>
                  <div>
                    <dt>{bookingSection.summary.customerName}</dt>
                    <dd>{lookupReservation.customerName}</dd>
                  </div>
                  <div>
                    <dt>{bookingSection.summary.phone}</dt>
                    <dd>{lookupReservation.phoneNumber}</dd>
                  </div>
                  <div>
                    <dt>{bookingSection.dateFields.checkIn}</dt>
                    <dd>{lookupReservation.checkIn}</dd>
                  </div>
                  <div>
                    <dt>{bookingSection.dateFields.checkOut}</dt>
                    <dd>{lookupReservation.checkOut}</dd>
                  </div>
                  <div>
                    <dt>{bookingSection.summary.nights}</dt>
                    <dd>{lookupReservation.nights}</dd>
                  </div>
                  <div>
                    <dt>{bookingSection.manage.rooms}</dt>
                    <dd>{renderRoomDetails(lookupReservation.roomIds, lookupReservation.extraBedCounts, lookupReservation.rooms)}</dd>
                  </div>
                  {renderReservationDiscountRows(lookupReservation)}
                  <div>
                    <dt>{bookingSection.manage.totalPrice}</dt>
                    <dd>{formatCurrency(lookupReservation.totalPrice)}</dd>
                  </div>
                  <div>
                    <dt>{bookingSection.manage.prepayment}</dt>
                    <dd>{formatCurrency(lookupReservation.prepayment)}</dd>
                  </div>
                  <div>
                    <dt>{bookingSection.complete.prepaymentStatus}</dt>
                    <dd>{formatPrepaymentStatus(lookupReservation.prepaymentStatus)}</dd>
                  </div>
                  {isWebsiteReservation(lookupReservation) && (
                    <div>
                      <dt>{bookingSection.summary.notes}</dt>
                      <dd>{lookupReservation.notes || bookingSection.summary.noNotes}</dd>
                    </div>
                  )}
                </dl>
                {lookupReservation.status !== "canceled" && getDaysUntilDate(lookupReservation.checkIn) < minimumCancelDaysBeforeCheckIn && (
                  <p>{bookingSection.manage.cancelUnavailable}</p>
                )}
                {lookupReservation.status !== "canceled" && (
                  <button
                    className="secondary-action"
                    type="button"
                    disabled={isLookupLoading || getDaysUntilDate(lookupReservation.checkIn) < minimumCancelDaysBeforeCheckIn}
                    onClick={handleCancelReservation}
                  >
                    {bookingSection.manage.cancel}
                  </button>
                )}
            </div>
          )}
          {(errorMessage || statusMessage) && (
            <div className={`booking-result ${errorMessage ? "is-error" : ""}`}>
              {errorMessage && <p>{errorMessage}</p>}
              {statusMessage && <p>{statusMessage}</p>}
            </div>
          )}
        </div>
      )}
    </section>
  );
}
