import { expect, request, type APIRequestContext, type Page } from "@playwright/test";

export const apiBaseURL = process.env.E2E_API_BASE_URL || "http://127.0.0.1:5001";
const siteIntroducedRoomIds = new Set(["稻", "森", "藍", "紅", "太", "月"]);

export type AvailabilityRoom = {
  roomId: string;
  name: string;
  roomTypeLabel: string;
  available: boolean;
  extraBedNumber: number;
};

export type AvailabilityResponse = {
  rooms: AvailabilityRoom[];
  availableRoomIds: string[];
};

export type QuoteResponse = {
  originalTotalPrice: number;
  websiteDiscountAmount: number;
  totalPrice: number;
  suggestedPrepayment: number;
};

export type HolidayRateDatesResponse = {
  dates: string[];
};

export type ReservationResponse = {
  reservation: {
    bookingId: number;
    customerName: string;
    phoneNumber: string;
    checkIn: string;
    checkOut: string;
    nights: number;
    roomIds: string[];
    extraBedCounts: Record<string, number>;
    rooms?: AvailabilityRoom[];
    originalTotalPrice: number;
    websiteDiscountAmount: number;
    totalPrice: number;
    prepayment: number;
    prepaymentStatus: string;
    notes: string;
    status: string;
  };
};

export function toDateInputValue(date: Date) {
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, "0");
  const day = String(date.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
}

export function dateFromOffset(offsetDays: number) {
  const date = new Date();
  date.setDate(date.getDate() + offsetDays);
  return toDateInputValue(date);
}

export function formatCurrency(value: number) {
  return `NT$${value.toLocaleString("zh-TW")}`;
}

export function formatDisplayDate(dateValue: string) {
  const date = new Date(`${dateValue}T00:00:00`);
  return date.toLocaleDateString("zh-TW", {
    year: "numeric",
    month: "long",
    day: "numeric",
  });
}

function getMonthDifference(fromDateValue: string, toDateValue: string) {
  const fromDate = new Date(`${fromDateValue}T00:00:00`);
  const toDate = new Date(`${toDateValue}T00:00:00`);
  return (toDate.getFullYear() - fromDate.getFullYear()) * 12 + toDate.getMonth() - fromDate.getMonth();
}

export async function openBookingDateCalendar(page: Page, fieldLabel: "入住日期" | "退房日期", dateValue: string) {
  const trigger = page.getByRole("button", { name: `選擇${fieldLabel}` });
  const currentDateText = await trigger.textContent();
  const currentDateValue = currentDateText
    ? toDateInputValue(new Date(currentDateText.replace("年", "-").replace("月", "-").replace("日", "")))
    : dateValue;
  const monthDifference = getMonthDifference(currentDateValue, dateValue);

  await trigger.click();

  const calendar = page.locator(".booking-calendar");
  const navigationButtonName = monthDifference >= 0 ? "下一個月" : "上一個月";
  for (let index = 0; index < Math.abs(monthDifference); index += 1) {
    await calendar.getByRole("button", { name: navigationButtonName }).click();
  }

  return calendar;
}

export async function selectBookingDate(page: Page, fieldLabel: "入住日期" | "退房日期", dateValue: string) {
  const calendar = await openBookingDateCalendar(page, fieldLabel, dateValue);
  await calendar.getByRole("button", { name: formatDisplayDate(dateValue) }).click();
}

export async function newApiContext() {
  const api = await request.newContext({ baseURL: apiBaseURL });
  const healthResponse = await api.get("/health");
  expect(healthResponse.ok(), `Real backend is required at ${apiBaseURL}`).toBe(true);
  return api;
}

export async function findBookableRoom(
  api: APIRequestContext,
  options: { minOffset?: number; maxOffset?: number; requireExtraBed?: boolean } = {},
) {
  const minOffset = options.minOffset ?? 14;
  const maxOffset = options.maxOffset ?? 180;

  for (let offset = minOffset; offset < maxOffset; offset += 1) {
    const checkIn = dateFromOffset(offset);
    const checkOut = dateFromOffset(offset + 1);
    const availabilityResponse = await api.get("/api/public/availability", {
      params: { checkIn, checkOut },
    });
    if (!availabilityResponse.ok()) {
      continue;
    }

    const availability = (await availabilityResponse.json()) as AvailabilityResponse;
    const room = availability.rooms.find((candidate) => (
      siteIntroducedRoomIds.has(candidate.roomId)
      && candidate.available
      && (!options.requireExtraBed || candidate.extraBedNumber > 0)
    ));
    if (room) {
      return {
        checkIn,
        checkOut,
        roomId: room.roomId,
        roomName: room.name,
        roomTypeLabel: room.roomTypeLabel,
        extraBedNumber: room.extraBedNumber,
      };
    }
  }

  throw new Error(`No available room found between ${minOffset} and ${maxOffset} days from today.`);
}

export async function createReservationFixture(
  api: APIRequestContext,
  options: {
    minOffset?: number;
    customerName?: string;
    phoneNumber?: string;
    notes?: string;
  } = {},
) {
  const room = await findBookableRoom(api, { minOffset: options.minOffset ?? 21 });
  const payload = {
    customerName: options.customerName ?? "官網測試",
    phoneNumber: options.phoneNumber ?? "0912345678",
    checkIn: room.checkIn,
    checkOut: room.checkOut,
    roomIds: [room.roomId],
    extraBedCounts: { [room.roomId]: 0 },
    notes: options.notes ?? "E2E fixture",
  };
  const response = await api.post("/api/public/reservations", { data: payload });
  expect(response.ok()).toBe(true);
  return (await response.json()) as ReservationResponse;
}

export async function prepareBookingReview(
  page: Page,
  api: APIRequestContext,
  options: {
    customerName?: string;
    phoneInput?: string;
    notes?: string;
    requireExtraBed?: boolean;
  } = {},
) {
  const room = await findBookableRoom(api, { requireExtraBed: options.requireExtraBed });
  const extraBedCounts = options.requireExtraBed ? { [room.roomId]: 1 } : { [room.roomId]: 0 };
  const quoteResponse = await api.post("/api/public/quote", {
    data: {
      checkIn: room.checkIn,
      checkOut: room.checkOut,
      roomIds: [room.roomId],
      extraBedCounts,
    },
  });
  expect(quoteResponse.ok()).toBe(true);
  const quote = (await quoteResponse.json()) as QuoteResponse;

  await page.goto(`/#booking?roomIds=${encodeURIComponent(room.roomId)}`);
  await selectBookingDate(page, "入住日期", room.checkIn);
  await selectBookingDate(page, "退房日期", room.checkOut);
  await page.getByRole("button", { name: "查詢空房" }).click();

  if (options.requireExtraBed) {
    const oneExtraBedButton = page.locator(".booking-room-card.is-selected .extra-bed-options button").filter({ hasText: "1" });
    await expect(oneExtraBedButton).toHaveCount(1);
    await oneExtraBedButton.click();
  }

  await expect(page.getByRole("button", { name: "下一步" })).toBeEnabled();
  await page.getByRole("button", { name: "下一步" }).click();

  await page.getByPlaceholder("訂房人姓名").fill(options.customerName ?? "官網測試");
  await page.getByPlaceholder("0912345678").fill(options.phoneInput ?? "0912345678");
  if (options.notes) {
    await page.getByPlaceholder("抵達時間、特殊需求等").fill(options.notes);
  }
  await page.getByRole("button", { name: "下一步" }).click();

  return { room, quote };
}
