import { expect, test } from "@playwright/test";
import {
  createReservationFixture,
  dateFromOffset,
  findBookableRoom,
  formatCurrency,
  formatDisplayDate,
  newApiContext,
  prepareBookingReview,
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

test("creating a reservation clears form state, normalizes URL, and blocks returning to middle steps", async ({ page }) => {
  const api = await newApiContext();
  const { quote } = await prepareBookingReview(page, api, {
    customerName: "官網建立測試",
    notes: "需要安靜房間",
    requireExtraBed: true,
  });

  await page.getByRole("button", { name: "建立新訂單" }).click();

  const completeSummary = page.locator(".booking-complete");
  await expect(completeSummary).toContainText("訂房完成");
  await expect(completeSummary).toContainText("官網建立測試");
  await expect(completeSummary).toContainText("0912345678");
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

  await page.goto("/#booking");
  await page.getByRole("button", { name: "查詢/取消" }).click();
  await page.getByPlaceholder("例如 1024").fill(String(reservation.bookingId));
  await page.getByPlaceholder("訂房電話").fill("0922222222");
  await page.getByRole("button", { name: "查詢訂單" }).click();

  const manageSummary = page.locator(".booking-summary");
  await expect(manageSummary).toContainText("官網查詢測試");
  await expect(manageSummary).toContainText("0922222222");
  await expect(manageSummary).toContainText(reservation.checkIn);
  await expect(manageSummary).toContainText("官網優惠");
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
