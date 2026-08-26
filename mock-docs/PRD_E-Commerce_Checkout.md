# PRD: E-Commerce Checkout System v2.0

**Document ID:** PRD-ECO-2024-001
**Version:** 2.0
**Status:** Approved
**Owner:** Product Team
**Last Updated:** 2024-Q4

---

## 1. Overview

### 1.1 Purpose
Sistem checkout e-commerce yang memungkinkan pelanggan menyelesaikan pembelian produk digital dan fisik. Sistem mendukung multiple payment methods, address management, discount/voucher redemption, dan order tracking.

### 1.2 Scope
Modul checkout mencakup:
- Shopping cart management
- Address selection & input
- Shipping method selection
- Payment processing (multiple gateways)
- Voucher/discount application
- Order confirmation & receipt
- Order history & tracking

### 1.3 Target Users
- **Customer** (pelanggan terdaftar) — dapat checkout dengan saved address & payment
- **Guest** (tamu) — dapat checkout tanpa registrasi, wajib input data lengkap
- **Admin** — kelola order, refund, dan resolve payment disputes

---

## 2. Functional Requirements

### 2.1 Shopping Cart (FR-CART)

**FR-CART-01: Add to Cart**
Pengguna dapat menambahkan produk ke keranjang. Quantity default 1, maksimum 99 per produk. Jika produk sudah ada di cart, quantity ditambahkan.

**FR-CART-02: Cart Validation**
Sistem memvalidasi stok produk real-time sebelum checkout. Jika stok tidak cukup, tampilkan pesan "Stok tidak mencukupi" dan opsi untuk menyesuaikan quantity.

**FR-CART-03: Remove from Cart**
Pengguna dapat menghapus item dari keranjang. Konfirmasi modal muncul sebelum penghapusan permanen.

**FR-CART-04: Cart Expiry**
Keranjang disimpan selama 30 hari untuk user terdaftar. Untuk guest, cart hilang setelah session berakhir (browser closed).

### 2.2 Address Management (FR-ADDR)

**FR-ADDR-01: Saved Address**
Customer terdaftar dapat memilih dari daftar alamat tersimpan (rumah, kantor, dll). Maksimum 5 alamat per akun.

**FR-ADDR-02: New Address Input**
Form alamat baru wajib berisi:
- Nama penerima (3-50 karakter)
- Nomor telepon (format: +62 atau 08, 10-13 digit)
- Alamat lengkap (10-200 karakter)
- Kota, Provinsi, Kode Pos (5 digit)
- Label alamat (opsional)

**FR-ADDR-03: Address Validation**
Sistem memvalidasi kode pos terhadap database wilayah. Alamat di luar coverage area pengiriman ditolak dengan pesan spesifik.

**FR-ADDR-04: Guest Checkout**
Guest wajib input email & nomor telepon untuk tracking. Email dijadikan identifier sementara selama proses order.

### 2.3 Shipping Method (FR-SHIP)

**FR-SHIP-01: Shipping Options**
Sistem menampilkan opsi pengiriman berdasarkan alamat tujuan & berat paket:
- **Regular** (3-5 hari kerja) — Rp 15.000
- **Express** (1-2 hari kerja) — Rp 25.000
- **Same Day** (area metro tertentu, 6 jam) — Rp 45.000
- **Instant** (area metro, 2 jam) — Rp 35.000

**FR-SHIP-02: Shipping Cost Calculation**
Ongkir dihitung berdasarkan: berat paket (kg) × tarif per kg + flat fee per metode. Berat dibulatkan ke atas (contoh: 1.2kg → 2kg).

**FR-SHIP-03: Free Shipping Threshold**
Customer dapat klaim free shipping regular jika subtotal order ≥ Rp 500.000. Berlaku untuk customer terdaftar saja.

### 2.4 Payment Processing (FR-PAY)

**FR-PAY-01: Payment Methods**
Sistem mendukung:
- **Virtual Account** (BCA, Mandiri, BNI, BRI) — auto-generate VA number, expired dalam 24 jam
- **Credit Card** (Visa, Mastercard) — 3D Secure wajib
- **E-Wallet** (GoPay, OVO, DANA, ShopeePay) — redirect ke app/WebView
- **QRIS** — QR code static, expired dalam 15 menit
- **Cash on Delivery (COD)** — area terbatas, maksimum Rp 2.000.000

**FR-PAY-02: Payment Validation**
Sistem memvalidasi:
- Credit card: format 16 digit, expiry date, CVV 3 digit. Lakukan tokenisasi via gateway.
- VA: generate unique number, bind ke order ID
- E-wallet: cek saldo cukup via provider API

**FR-PAY-03: Payment Timeout**
Setiap metode punya timeout:
- VA & QRIS: expired dalam jam yang ditentukan, status order → CANCELLED
- Credit card: 5 menit untuk complete 3D Secure
- E-wallet: 10 menit untuk konfirmasi

**FR-PAY-04: Payment Failure Handling**
Jika pembayaran gagal, sistem:
1. Retry maksimum 3 kali untuk credit card
2. Tawarkan metode pembayaran alternatif
3. Simpan cart selama 24 jam untuk retry

**FR-PAY-05: Double Payment Prevention**
Sistem mencegah double charge:
- Idempotency key per payment attempt
- Lock order selama proses (3-5 detik)
- Webhook dari gateway untuk konfirmasi single source

### 2.5 Voucher & Discount (FR-VOUCHER)

**FR-VOUCHER-01: Voucher Application**
Customer dapat apply voucher di halaman checkout. Validasi:
- Kode valid & aktif
- Minimum spend terpenuhi
- Dalam periode berlaku
- Belum melebihi kuota penggunaan

**FR-VOUCHER-02: Discount Types**
- **Percentage** (5%-50%, maksimum diskon Rp 500.000)
- **Fixed amount** (Rp 10.000 - Rp 100.000)
- **Free shipping** (lihat FR-SHIP-03)
- **Bundle discount** (beli produk A+B, dapat X%)

**FR-VOUCHER-03: Voucher Stacking**
Maksimum 2 voucher per order: 1 product discount + 1 shipping discount. Tidak boleh stack 2 product discount.

### 2.6 Order Confirmation (FR-ORDER)

**FR-ORDER-01: Order Number Generation**
Format: `ORD-YYYYMMDD-XXXXX` (XXXXX = sequential 5 digit per hari). Unique constraint enforced.

**FR-ORDER-02: Confirmation Email/SMS**
Setelah order berhasil:
- Email konfirmasi (instantial, ≤ 1 menit)
- SMS dengan order ID & tracking link (instantial)
- WhatsApp notif (opsional, jika opt-in)

**FR-ORDER-03: Receipt Download**
Customer dapat download PDF receipt. Berisi: order ID, items, prices, discount, tax, total, payment method, shipping address.

---

## 3. Non-Functional Requirements

### 3.1 Performance
- Checkout flow completion: < 30 detik (P95)
- Payment gateway response: < 5 detik
- Page load (cart → payment): < 2 detik

### 3.2 Security
- PCI DSS compliance untuk credit card
- PII encryption at rest (AES-256) untuk alamat & nomor telepon
- Rate limit: 10 checkout attempts per menit per IP
- Anti-fraud: device fingerprinting, velocity check, blacklisted cards

### 3.3 Availability
- Uptime SLA: 99.9%
- Payment gateway failover: < 10 detik
- Graceful degradation: jika 1 payment gateway down, disable opsi itu & tampilkan alternatif

---

## 4. Business Rules

**BR-01: Minimum Order Value**
Minimum subtotal Rp 10.000 (sebelum ongkir & pajak). Di bawah ini, checkout ditolak.

**BR-02: Tax Calculation**
PPN 11% dihitung dari (subtotal - discount). Ditampilkan terpisah di receipt.

**BR-03: COD Eligibility**
COD hanya untuk: subtotal ≤ Rp 2.000.000, area coverage tier 1, customer dengan ≥ 3 order sukses sebelumnya.

**BR-04: Blacklisted Customer**
Customer dengan history chargeback > 2 kali dalam 6 bulan di-blacklist, checkout ditolak dengan pesan "Hubungi customer service".

**BR-05: Concurrent Checkout Lock**
Prevent race condition: 1 cart hanya bisa 1 active checkout process. Lock释放 setelah payment success/fail/timeout.

---

## 5. Edge Cases & Constraints

- **EC-01**: Produk dihapus dari catalog saat ada di cart → tampilkan "produk tidak tersedia", disable checkout item itu
- **EC-02**: Harga berubah saat checkout → pakai harga saat order dibuat (locked), kirim notif ke seller
- **EC-03**: User checkout di 2 device bersamaan → yang pertama process menang, kedua dapat error "cart sedang diproses"
- **EC-04**: Session expired di tengah checkout → cart disimpan, redirect ke login, resume setelah re-auth
- **EC-05**: Internet terputus saat payment → polling status selama 60 detik, sync dengan webhook gateway

---

## 6. Acceptance Criteria Summary

| ID | Scenario | Expected Result |
|----|----------|-----------------|
| AC-01 | Add item to cart | Item muncul, quantity correct |
| AC-02 | Checkout dengan 1 item | Order berhasil, receipt terdownload |
| AC-03 | Apply voucher invalid | Error message spesifik tampil |
| AC-04 | Payment timeout VA | Order status CANCELLED, cart dikembalikan |
| AC-05 | COD di atas limit | Opsi COD disabled, pesan informatif |
| AC-06 | Concurrent checkout | Hanya 1 yang sukses, lainnya blocked |
| AC-07 | Stok habis saat checkout | Stok real-time check, error + adjust qty |
| AC-08 | Guest checkout | Order berhasil, email konfirmasi terkirim |

---

## 7. Out of Scope (v2.0)

- Wishlist & save for later (v2.1)
- Subscription/recurring order (v2.2)
- International shipping (v3.0)
- Multi-currency (v3.0)

---

*End of PRD Document*
