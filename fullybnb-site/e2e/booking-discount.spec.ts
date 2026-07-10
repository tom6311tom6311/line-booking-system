import { expect, test } from "@playwright/test";
import { findBookableRoom, formatCurrency, newApiContext, selectBookingDate, type QuoteResponse } from "./booking-test-utils";

test("booking summary shows the site-only discount from the real backend", async ({ page }) => {
  const api = await newApiContext();
  const { checkIn, checkOut, roomId } = await findBookableRoom(api);
  const quoteResponse = await api.post("/api/public/quote", {
    data: {
      checkIn,
      checkOut,
      roomIds: [roomId],
      extraBedCounts: { [roomId]: 0 },
    },
  });
  expect(quoteResponse.ok()).toBe(true);

  const quote = (await quoteResponse.json()) as QuoteResponse;
  expect(quote.websiteDiscountAmount).toBeGreaterThan(0);
  expect(quote.originalTotalPrice - quote.websiteDiscountAmount).toBe(quote.totalPrice);

  await page.goto(`/#booking?roomIds=${encodeURIComponent(roomId)}`);
  await selectBookingDate(page, "入住日期", checkIn);
  await selectBookingDate(page, "退房日期", checkOut);
  await page.getByRole("button", { name: "查詢空房" }).click();

  await expect(page.getByRole("button", { name: "下一步" })).toBeEnabled();
  await page.getByRole("button", { name: "下一步" }).click();

  await page.getByPlaceholder("訂房人姓名").fill("官網測試");
  await page.getByPlaceholder("0912345678").fill("0912345678");
  await page.getByRole("button", { name: "下一步" }).click();

  const summary = page.locator(".booking-summary").first();
  await expect(summary).toContainText("原價");
  await expect(summary).toContainText("官網限定優惠");
  await expect(summary).toContainText(formatCurrency(quote.originalTotalPrice));
  await expect(summary).toContainText(`-${formatCurrency(quote.websiteDiscountAmount)}`);
  await expect(summary).toContainText(formatCurrency(quote.totalPrice));

  await api.dispose();
});
