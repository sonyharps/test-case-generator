# Figma Flow Specification: E-Commerce Checkout User Journey

**Document ID:** FIGMA-ECO-2024-001
**Source:** Design Team (Figma export)
**Domain:** E-Commerce (matches PRD-ECO-2024-001, US-ECO-2024-001)
**Figma File:** `checkout-flow-v2.fig`

---

## Overview

This document describes the visual user flow for the e-commerce checkout journey, exported from Figma. Each screen is numbered with its route, key UI elements, and transition triggers. Use this alongside the PRD and User Stories to understand both the visual design and the interaction states.

---

## Screen 1: Product Detail Page (PDP)
**Route:** `/product/[id]`
**Purpose:** Display product info and allow add-to-cart.

**Key UI Elements:**
- Product image carousel (swipeable, max 6 images)
- Product title, price (strikethrough if discounted), rating stars
- Quantity selector stepper (default 1, min 1, max 99)
- "Add to Cart" button (primary, full-width)
- "Buy Now" button (secondary — skips cart, goes direct to checkout)
- Stock indicator: "Stok: 15 tersisa" (orange if < 10, red if 0)
- "Out of Stock" state: button disabled, greyed, tooltip

**Micro-interactions:**
- Add to Cart → toast "Ditambahkan ke keranjang" + cart badge increments with bounce animation
- Buy Now → loading spinner 1s → redirect to `/checkout`

---

## Screen 2: Shopping Cart
**Route:** `/cart`
**Purpose:** Review items, adjust quantities, proceed to checkout.

**Key UI Elements:**
- List of cart items (image, title, price, quantity stepper, line total)
- "Remove" button per item (icon, red, with confirmation modal)
- Subtotal, estimated shipping (calculated by default address), tax (PPN 11%)
- Promo code input field + "Apply" button (inline, shows success/error below)
- "Checkout" button (sticky bottom, disabled if cart empty or all items out of stock)
- Empty cart state: illustration + "Mulai belanja" CTA

**Micro-interactions:**
- Quantity change → subtotal animates (count-up), shipping recalculates if address changed
- Promo applied → discount line appears with strikethrough original price, green checkmark
- Promo rejected → red error message inline, input border red

---

## Screen 3: Checkout — Address Step
**Route:** `/checkout/address`
**Purpose:** Select or input shipping address.

**Key UI Elements:**
- Saved addresses list (radio cards, max 5, with label "Rumah/Kantor")
- "Tambah alamat baru" button (opens modal form)
- Address form fields: nama penerima, telepon (+62/08), alamat, kota, provinsi, kode pos (5 digit)
- "Use this address" button (saves if new, selects if existing)
- Coverage check indicator: loading spinner while validating postal code

**Validation States (inline):**
- Phone invalid: red border, "Format: 08xxx atau +62xxx"
- Postal code not covered: red banner "Maaf, area Anda belum terjangkau"
- Form incomplete: submit disabled, fields with errors highlighted

---

## Screen 4: Checkout — Shipping Step
**Route:** `/checkout/shipping`
**Purpose:** Choose shipping method.

**Key UI Elements:**
- Shipping options (radio cards): Regular, Express, Same Day, Instant
- Each card: method name, ETA, price, icon (truck/lightning/clock)
- "Same Day" / "Instant" greyed out if address outside metro coverage (with tooltip)
- Free shipping badge if subtotal ≥ Rp 500.000 (Regular only)
- Weight summary: "Total berat: 2.3 kg (dibulatkan ke 3 kg)"

**Transitions:**
- Select shipping → ETA + price updates in order summary (right sidebar)
- Shipping cost recalculates if user goes back to change address

---

## Screen 5: Checkout — Payment Step
**Route:** `/checkout/payment`
**Purpose:** Choose payment method and complete transaction.

**Key UI Elements:**
- Payment method tabs/cards: Virtual Account, Credit Card, E-Wallet, QRIS, COD
- **VA panel:** bank logo grid (BCA/Mandiri/BNI/BRI), generates VA number on select
- **Card panel:** card number input (auto-format spaces), expiry MM/YY, CVV (3 digit), "Pay" button
- **E-Wallet panel:** provider logos (GoPay/OVO/DANA/ShopeePay), redirect notice
- **QRIS panel:** QR code display (static, 15-min countdown), "I've paid" button
- **COD panel:** eligibility notice, "Confirm COD" button (disabled if > Rp 2.000.000)
- Order summary sidebar: items, subtotal, discount, shipping, tax, total
- "Pay Now" / "Confirm Order" button (sticky bottom)

**Critical States:**
- 3D Secure redirect: full-screen overlay "Redirecting to bank..." with cancel option (5 min)
- Payment processing: modal with spinner "Memproses pembayaran..." (locks UI, 3-5 sec)
- Payment success: confetti animation, "Pembayaran Berhasil!" → auto-redirect to confirmation
- Payment failure: error modal with reason + "Coba lagi" / "Ganti metode" buttons

---

## Screen 6: Order Confirmation
**Route:** `/order/[id]/confirmation`
**Purpose:** Show success state and receipt.

**Key UI Elements:**
- Success hero: checkmark icon, "Pesanan Diterima!" heading, order ID
- Order details card: items, prices, discount, shipping, tax, total, payment method
- "Download Receipt (PDF)" button
- "Lacak Pesanan" button (active once status = Shipped)
- "Kembali ke Beranda" button
- Delivery ETA estimate

**Next steps banner:**
- Email confirmation sent indicator (green check or red "gagal kirim, hubungi CS")
- WhatsApp opt-in prompt (if not yet opted in)

---

## Cross-Screen Elements

### Order Summary Sidebar (Screens 3, 4, 5)
**Position:** Right sidebar (desktop) / collapsible bottom sheet (mobile)
**Contents:**
- Item count + thumbnails
- Subtotal, discount (if promo), shipping (if address selected), tax (PPN 11%), **Total**
- Sticky position, updates in real-time as user progresses through steps

### Progress Indicator (Screens 3, 4, 5)
- Stepper at top: "1. Alamat → 2. Pengiriman → 3. Pembayaran"
- Current step highlighted, completed steps have checkmark
- Clickable to navigate back (with confirmation if data will be lost)

### Error & Empty States (all screens)
- Network error: full-screen illustration "Koneksi bermasalah" + retry button
- Session expired: modal "Sesi berakhir" → redirect to login → resume checkout after re-auth
- Generic error: red toast notification (top, auto-dismiss 5s)

---

## Edge Case Visual States

- **Concurrent checkout lock:** modal "Keranjang sedang diproses di perangkat lain" with "Batalkan proses lain" option
- **Price changed mid-checkout:** yellow banner "Harga berubah" with old vs new price, "Lanjutkan" / "Batalkan" buttons
- **Stock depleted mid-checkout:** item row red-highlighted "Stok habis", "Hapus item" button, checkout disabled until resolved
- **Payment gateway down:** affected payment method card greyed with tooltip "Metode ini sedang tidak tersedia"

---

*End of Figma Flow Specification*
