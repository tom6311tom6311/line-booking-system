import { expect, test } from "@playwright/test";
import {
  type AvailabilityResponse,
  createReservationFixture,
  dateFromOffset,
  findBookablePeriodForAllIntroducedRooms,
  findBookableRoom,
  formatCurrency,
  formatDisplayDate,
  openBookingDateCalendar,
  type HolidayRateDatesResponse,
  newApiContext,
  prepareBookingReview,
  type ReservationResponse,
  selectBookingDate,
} from "./booking-test-utils";

test("empty manage tab does not show an empty booking summary", async ({ page }) => {
  await page.goto("/#booking");
  await page.getByRole("button", { name: "查詢/取消" }).click();

  await expect(page.getByRole("heading", { name: "查詢訂單" })).toBeVisible();
  await expect(page.locator(".booking-manage-note")).toContainText("如需修改入住日期、房型、加床、備註或其他訂房內容，請直接來電聯絡民宿");
  await expect(page.getByRole("heading", { name: "訂單內容" })).toHaveCount(0);
});

test("invalid date period cannot be searched", async ({ page }) => {
  const api = await newApiContext();
  await page.goto("/#booking");
  const room = await findBookableRoom(api);

  await selectBookingDate(page, "入住日期", room.checkIn);
  await expect(page.getByRole("button", { name: "選擇退房日期" })).toContainText(formatDisplayDate(room.checkOut));

  await page.getByRole("button", { name: "選擇退房日期" }).click();
  await expect(page.locator(".booking-calendar").getByRole("button", { name: formatDisplayDate(room.checkIn) })).toBeDisabled();

  await api.dispose();
});

test("calendar blocks past dates and auto-selects the next checkout date", async ({ page }) => {
  await page.goto("/#booking");

  const tomorrow = dateFromOffset(1);
  const dayAfterTomorrow = dateFromOffset(2);
  const yesterday = dateFromOffset(-1);

  await page.getByRole("button", { name: "選擇入住日期" }).click();
  await expect(page.locator(".booking-calendar").getByRole("button", { name: formatDisplayDate(yesterday) })).toBeDisabled();
  await page.locator(".booking-calendar").getByRole("button", { name: formatDisplayDate(tomorrow) }).click();

  await expect(page.getByRole("button", { name: "選擇入住日期" })).toContainText(formatDisplayDate(tomorrow));
  await expect(page.getByRole("button", { name: "選擇退房日期" })).toContainText(formatDisplayDate(dayAfterTomorrow));
  await expect(page.getByRole("button", { name: "查詢空房" })).toBeEnabled();
});

test("calendar highlights holiday-rate dates", async ({ page }) => {
  const api = await newApiContext();
  const response = await api.get("/api/public/holiday-rate-dates", {
    params: {
      start: dateFromOffset(1),
      end: dateFromOffset(180),
    },
  });
  expect(response.ok()).toBe(true);
  const holidayRates = (await response.json()) as HolidayRateDatesResponse;
  expect(holidayRates.dates.length).toBeGreaterThan(0);
  const holidayRateDate = holidayRates.dates[0];

  await page.goto("/#booking");
  const calendar = await openBookingDateCalendar(page, "入住日期", holidayRateDate);
  const holidayRateButton = calendar.getByRole("button", { name: `${formatDisplayDate(holidayRateDate)}，假日價` });
  await expect(holidayRateButton).toHaveClass(/is-holiday-rate/);

  await api.dispose();
});

test("calendar closes when clicking outside", async ({ page }) => {
  await page.goto("/#booking");

  await page.getByRole("button", { name: "選擇入住日期" }).click();
  await expect(page.locator(".booking-calendar")).toBeVisible();

  await page.getByRole("button", { name: "查詢空房" }).click();
  await expect(page.locator(".booking-calendar")).toHaveCount(0);
});

test("public booking API rejects past check-in dates with a localized error", async () => {
  const api = await newApiContext();
  const response = await api.get("/api/public/availability", {
    params: {
      checkIn: dateFromOffset(-1),
      checkOut: dateFromOffset(1),
    },
  });

  expect(response.ok()).toBe(false);
  const payload = await response.json();
  expect(payload.error).toContain("入住日期不能早於今天");
  expect(payload.error).not.toMatch(/[A-Za-z]{3,}/);

  const invalidDateResponse = await api.get("/api/public/availability", {
    params: {
      checkIn: "bad-date",
      checkOut: dateFromOffset(2),
    },
  });
  expect(invalidDateResponse.ok()).toBe(false);
  const invalidDatePayload = await invalidDateResponse.json();
  expect(invalidDatePayload.error).toContain("日期格式不正確");
  expect(invalidDatePayload.error).not.toMatch(/[A-Za-z]{3,}/);

  const invalidPhoneResponse = await api.get("/api/public/reservations/999999", {
    params: {
      phoneNumber: "123",
    },
  });
  expect(invalidPhoneResponse.ok()).toBe(false);
  const invalidPhonePayload = await invalidPhoneResponse.json();
  expect(invalidPhonePayload.error).toContain("電話格式不正確");
  expect(invalidPhonePayload.error).not.toMatch(/[A-Za-z]{3,}/);

  const invalidRoomResponse = await api.post("/api/public/quote", {
    data: {
      checkIn: dateFromOffset(20),
      checkOut: dateFromOffset(21),
      roomIds: ["不存在"],
      extraBedCounts: { "不存在": 0 },
    },
  });
  expect(invalidRoomResponse.ok()).toBe(false);
  const invalidRoomPayload = await invalidRoomResponse.json();
  expect(invalidRoomPayload.error).toContain("選擇的房間不存在");
  expect(invalidRoomPayload.error).not.toMatch(/[A-Za-z]{3,}/);

  const invalidExtraBedResponse = await api.post("/api/public/quote", {
    data: {
      checkIn: dateFromOffset(20),
      checkOut: dateFromOffset(21),
      roomIds: ["稻"],
      extraBedCounts: { "稻": "many" },
    },
  });
  expect(invalidExtraBedResponse.ok()).toBe(false);
  const invalidExtraBedPayload = await invalidExtraBedResponse.json();
  expect(invalidExtraBedPayload.error).toContain("加床數需為整數");
  expect(invalidExtraBedPayload.error).not.toMatch(/[A-Za-z]{3,}/);

  await api.dispose();
});

test("phone fields accept only normalized 09 mobile numbers", async ({ page }) => {
  const api = await newApiContext();
  const room = await findBookableRoom(api);

  await page.goto(`/#booking?roomIds=${encodeURIComponent(room.roomId)}`);
  await selectBookingDate(page, "入住日期", room.checkIn);
  await selectBookingDate(page, "退房日期", room.checkOut);
  await page.getByRole("button", { name: "查詢空房" }).click();
  await expect(page.getByRole("button", { name: "下一步" })).toBeEnabled();
  await page.getByRole("button", { name: "下一步" }).click();

  const phoneInput = page.getByPlaceholder("0912345678");
  await page.getByPlaceholder("訂房人姓名").fill("官網電話測試");
  await phoneInput.fill("09ab123456789");
  await expect(phoneInput).toHaveValue("0912345678");
  await page.getByRole("button", { name: "下一步" }).click();
  await expect(page.locator(".booking-summary")).toContainText("0912345678");

  await api.dispose();
});

test("availability search shows a note when no rooms are available", async ({ page }) => {
  const api = await newApiContext();
  const period = await findBookablePeriodForAllIntroducedRooms(api);
  const createResponse = await api.post("/api/public/reservations", {
    data: {
      customerName: "滿房提示測試",
      phoneNumber: "0955555555",
      checkIn: period.checkIn,
      checkOut: period.checkOut,
      roomIds: period.roomIds,
      extraBedCounts: Object.fromEntries(period.roomIds.map((roomId) => [roomId, 0])),
      notes: "占用所有官網房型",
    },
  });
  expect(createResponse.ok()).toBe(true);

  await page.goto("/#booking");
  await selectBookingDate(page, "入住日期", period.checkIn);
  await selectBookingDate(page, "退房日期", period.checkOut);
  await page.getByRole("button", { name: "查詢空房" }).click();

  await expect(page.locator(".booking-result")).toContainText("此日期目前沒有可線上預訂的空房");
  await expect(page.getByRole("button", { name: "選擇房間" })).toBeDisabled();
  await expect(page.locator(".booking-room-card")).toHaveCount(0);

  await api.dispose();
});

test("creating a reservation clears form state, normalizes URL, and blocks returning to middle steps", async ({ page }) => {
  const api = await newApiContext();
  const { room, quote } = await prepareBookingReview(page, api, {
    customerName: "官網建立測試",
    notes: "需要安靜房間",
    requireExtraBed: true,
  });

  await expect(page.locator(".booking-summary")).toContainText(`${room.roomTypeLabel} ${room.roomName}`);

  const createReservationResponsePromise = page.waitForResponse((response) => (
    response.url().includes("/api/public/reservations")
    && response.request().method() === "POST"
  ));
  await page.getByRole("button", { name: "立即預訂" }).click();
  const createReservationResponse = await createReservationResponsePromise;
  expect(createReservationResponse.ok()).toBe(true);
  const { reservation } = (await createReservationResponse.json()) as ReservationResponse;

  const completeSummary = page.locator(".booking-complete");
  await expect(completeSummary).toContainText("訂房完成");
  await expect(completeSummary).toContainText("官網建立測試");
  await expect(completeSummary).toContainText("0912345678");
  await expect(completeSummary).toContainText(`${room.roomTypeLabel} ${room.roomName}`);
  await expect(completeSummary).toContainText("需要安靜房間");
  await expect(completeSummary).toContainText("加1床");
  await expect(completeSummary).toContainText(formatCurrency(quote.totalPrice));
  await expect(completeSummary).toContainText("未付");
  await expect(page).toHaveURL(/#booking$/);

  await expect(page.getByRole("button", { name: "選擇房間" })).toBeDisabled();
  await expect(page.getByRole("button", { name: "填寫資料" })).toBeDisabled();
  await expect(page.getByRole("button", { name: "確認送出" })).toBeDisabled();

  await page.getByRole("button", { name: "查詢日期" }).click();
  await expect(page.getByPlaceholder("訂房人姓名")).toHaveCount(0);

  const availabilityResponse = await api.get("/api/public/availability", {
    params: {
      checkIn: room.checkIn,
      checkOut: room.checkOut,
    },
  });
  expect(availabilityResponse.ok()).toBe(true);
  const availability = (await availabilityResponse.json()) as AvailabilityResponse;
  expect(availability.availableRoomIds).not.toContain(room.roomId);

  await selectBookingDate(page, "入住日期", room.checkIn);
  await selectBookingDate(page, "退房日期", room.checkOut);
  await page.getByRole("button", { name: "查詢空房" }).click();
  await expect(page.locator(".booking-panel .booking-room-card").filter({ hasText: room.roomName })).toHaveCount(0);

  await page.getByRole("button", { name: "查詢/取消" }).click();
  await page.getByPlaceholder("例如 1024").fill(String(reservation.bookingId));
  await page.getByPlaceholder("訂房電話").fill("0912345678");
  await page.getByRole("button", { name: "查詢訂單" }).click();

  const createdBookingLookupSummary = page.locator(".booking-summary");
  await expect(createdBookingLookupSummary).toContainText("官網建立測試");
  await expect(createdBookingLookupSummary).toContainText("0912345678");
  await expect(createdBookingLookupSummary).toContainText(`${room.roomTypeLabel} ${room.roomName}`);
  await expect(createdBookingLookupSummary).toContainText("需要安靜房間");
  await expect(createdBookingLookupSummary).not.toContainText(`#${reservation.bookingId}`);

  await api.dispose();
});

test("manage lookup shows reservation financial details and can cancel eligible bookings", async ({ page }) => {
  const api = await newApiContext();
  const { reservation } = await createReservationFixture(api, {
    minOffset: 30,
    customerName: "官網查詢測試",
    phoneNumber: "0922222222",
    notes: "查詢備註",
  });

  expect(reservation.rooms?.[0]?.roomTypeLabel).toBeTruthy();
  expect(reservation.rooms?.[0]?.name).toBeTruthy();

  await page.goto("/#booking");
  await page.getByRole("button", { name: "查詢/取消" }).click();
  await page.getByPlaceholder("例如 1024").fill(String(reservation.bookingId));
  await page.getByPlaceholder("訂房電話").fill("0922222222");
  await page.getByRole("button", { name: "查詢訂單" }).click();

  const manageSummary = page.locator(".booking-summary");
  await expect(manageSummary).toContainText("官網查詢測試");
  await expect(manageSummary).toContainText("0922222222");
  await expect(manageSummary).toContainText(reservation.checkIn);
  await expect(manageSummary).toContainText(`${reservation.rooms?.[0]?.roomTypeLabel} ${reservation.rooms?.[0]?.name}`);
  await expect(manageSummary).toContainText("官網限定優惠");
  await expect(manageSummary).toContainText(formatCurrency(reservation.totalPrice));
  await expect(manageSummary).toContainText("查詢備註");
  await expect(manageSummary).not.toContainText(`#${reservation.bookingId}`);

  await expect(page.getByRole("button", { name: "取消訂單" })).toBeEnabled();
  await page.getByRole("button", { name: "取消訂單" }).click();
  await expect(manageSummary).toContainText("已取消");
  await expect(page.getByRole("button", { name: "取消訂單" })).toHaveCount(0);

  await api.dispose();
});

test("manage lookup prevents online cancellation within 7 days of check-in", async ({ page }) => {
  const api = await newApiContext();
  const room = await findBookableRoom(api, { minOffset: 2, maxOffset: 7 });
  const createResponse = await api.post("/api/public/reservations", {
    data: {
      customerName: "七日內測試",
      phoneNumber: "0933333333",
      checkIn: room.checkIn,
      checkOut: room.checkOut,
      roomIds: [room.roomId],
      extraBedCounts: { [room.roomId]: 0 },
      notes: "不可取消",
    },
  });
  expect(createResponse.ok()).toBe(true);
  const { reservation } = await createResponse.json();

  await page.goto("/#booking");
  await page.getByRole("button", { name: "查詢/取消" }).click();
  await page.getByPlaceholder("例如 1024").fill(String(reservation.bookingId));
  await page.getByPlaceholder("訂房電話").fill("0933333333");
  await page.getByRole("button", { name: "查詢訂單" }).click();

  await expect(page.locator(".booking-summary")).toContainText("入住日前 7 天內不可取消訂房");
  await expect(page.getByRole("button", { name: "取消訂單" })).toBeDisabled();

  await api.dispose();
});
