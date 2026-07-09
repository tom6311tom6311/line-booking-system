export type PublicRoom = {
  roomId: string;
  name: string;
  roomType: string;
  roomTypeLabel?: string;
  capacity: number;
  holidayPricePerNight: number;
  weekdayPricePerNight: number;
  extraBedNumber: number;
  extraBedPricePerNight: number;
  description: string;
  status: string;
  available?: boolean;
};

export type NightlyRoomPrice = {
  date: string;
  price: number;
  rateType: "weekday" | "holiday";
};

export type PublicReservation = {
  bookingId: number;
  status: string;
  customerName: string;
  phoneNumber: string;
  checkIn: string;
  checkOut: string;
  nights: number;
  roomIds: string[];
  extraBedCount: number;
  extraBedCounts: Record<string, number>;
  originalTotalPrice?: number;
  websiteDiscountAmount?: number;
  totalPrice: number;
  prepayment: number;
  prepaymentStatus: string;
  source: string;
  notes: string;
};

export type PublicQuote = {
  checkIn: string;
  checkOut: string;
  nights: number;
  roomIds: string[];
  extraBedCount: number;
  extraBedCounts: Record<string, number>;
  originalTotalPrice: number;
  websiteDiscountAmount: number;
  totalPrice: number;
  suggestedPrepayment: number;
};

export type ReservationPayload = {
  customerName: string;
  phoneNumber: string;
  checkIn: string;
  checkOut: string;
  roomIds: string[];
  extraBedCounts: Record<string, number>;
  notes: string;
};

const publicApiBasePath = "/api/public";

async function requestJson<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${publicApiBasePath}${path}`, {
    headers: {
      "Content-Type": "application/json",
      ...init?.headers,
    },
    ...init,
  });
  const payload = await response.json().catch(() => ({}));

  if (!response.ok) {
    throw new Error(payload.error || "系統暫時無法處理，請稍後再試。");
  }

  return payload as T;
}

export async function getAvailability(checkIn: string, checkOut: string) {
  const params = new URLSearchParams({ checkIn, checkOut });
  return requestJson<{
    checkIn: string;
    checkOut: string;
    nights: number;
    rooms: PublicRoom[];
    availableRoomIds: string[];
    nightlyRoomPrices?: Record<string, NightlyRoomPrice[]>;
  }>(`/availability?${params.toString()}`);
}

export async function quoteReservation(payload: Pick<ReservationPayload, "checkIn" | "checkOut" | "roomIds" | "extraBedCounts">) {
  return requestJson<PublicQuote>("/quote", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function createReservation(payload: ReservationPayload) {
  return requestJson<{ reservation: PublicReservation }>("/reservations", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function getReservation(bookingId: number, phoneNumber: string) {
  const params = new URLSearchParams({ phoneNumber });
  return requestJson<{ reservation: PublicReservation }>(`/reservations/${bookingId}?${params.toString()}`);
}

export async function getOverlappingReservations(phoneNumber: string, checkIn: string, checkOut: string) {
  const params = new URLSearchParams({ phoneNumber, checkIn, checkOut });
  return requestJson<{
    checkIn: string;
    checkOut: string;
    nights: number;
    reservations: PublicReservation[];
  }>(`/reservations/overlap?${params.toString()}`);
}

export async function updateReservation(bookingId: number, payload: ReservationPayload) {
  return requestJson<{ reservation: PublicReservation }>(`/reservations/${bookingId}`, {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
}

export async function cancelReservation(bookingId: number, phoneNumber: string) {
  return requestJson<{ reservation: PublicReservation }>(`/reservations/${bookingId}/cancel`, {
    method: "POST",
    body: JSON.stringify({ phoneNumber }),
  });
}
