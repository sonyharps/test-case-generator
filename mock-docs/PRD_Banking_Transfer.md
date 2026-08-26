# PRD: Interbank Fund Transfer System

**Document ID:** PRD-BNK-2024-002
**Version:** 1.5
**Status:** Approved
**Domain:** Banking / Fintech

---

## 1. Overview

### 1.1 Purpose
Modul transfer antar bank (LLG / RTGS / BI-FAST) yang memungkinkan nasabah mengirim dana ke rekening bank lain secara real-time atau scheduled.

### 1.2 Scope
- Single & batch transfer
- Beneficiary management (daftar favorit)
- Transfer scheduling (one-time & recurring)
- Fee calculation per channel
- Limit validation (daily/transaction)
- Fraud detection (velocity, blacklist)

---

## 2. Functional Requirements

**FR-TF-01: Single Transfer**
Nasabah input: bank tujuan (pilih dari list/autocomplete), nomor rekening, nama penerima (auto-fetch via inquiry), nominal, berita, jenis transfer (BI-FAST/LLG/RTGS). Validasi: rekening tujuan valid, saldo cukup, limit harian tersisa.

**FR-TF-02: BI-FAST Transfer**
Real-time transfer 24/7. Maksimum Rp 250.000.000 per transaksi. Fee flat Rp 2.500. Settle dalam 60 detik.

**FR-TF-03: LLG Transfer**
Transfer kliring non-real-time. Cut-off 15:00 WIB (diproses hari kerja berikutnya jika lewat). Fee Rp 3.500. Tidak ada limit maksimum (sesuai limit harian nasabah).

**FR-TF-04: RTGS Transfer**
Real-time gross settlement. Minimum Rp 100.000.000. Fee Rp 6.500. Cut-off 16:00 WIB. Settle dalam 30 menit.

**FR-TF-05: Beneficiary Inquiry**
Sistem query ke core banking untuk fetch nama pemilik rekening tujuan. Response time < 3 detik. Jika rekening tidak ditemukan, tampilkan error "Nomor rekening tidak valid".

**FR-TF-06: Scheduled Transfer**
Nasabah dapat jadwalkan transfer:
- One-time: pilih tanggal & jam spesifik
- Recurring: harian/mingguan/bulanan, dengan end date atau "sampai dimatikan"
Maksimum 20 schedule aktif per nasabah.

**FR-TF-07: Batch Transfer**
Upload CSV/Excel untuk multiple transfer sekaligus (maks 100 baris). Validasi per baris. Eksekusi sequential. Report hasil (sukses/gagal per baris).

**FR-TF-08: Transfer Receipt**
Setelah sukses, generate receipt PDF berisi: ID transaksi, timestamp, pengirim, penerima, nominal, fee, channel, reference number.

**FR-TF-09: Cancel Transfer**
Transfer BI-FAST tidak dapat dibatalkan (real-time). LLG/RTGS dapat dibatalkan jika status masih "pending" (sebelum cut-off). Refund full dalam 1x24 jam.

**FR-TF-10: Notification**
Push notification + email + SMS ke nasabah saat:
- Transfer sukses (dengan receipt link)
- Transfer gagal (dengan alasan)
- Schedule trigger (5 menit sebelum eksekusi)
- Limit harian hampir habis (80% terpakai)

---

## 3. Business Rules

**BR-01: Daily Limit**
Limit harian default Rp 50.000.000 (Silver), Rp 250.000.000 (Gold), Rp 1.000.000.000 (Platinum). Dapat diatur nasabah via settings (maksimum sesuai tier).

**BR-02: Transaction Limit**
Maksimum per transaksi = minimum(limit harian tersisa, limit channel). Minimum Rp 10.000.

**BR-03: Fraud Detection — Velocity**
Jika >5 transfer ke beneficiary berbeda dalam 10 menit → flag review manual (hold 30 menit untuk analisis).

**BR-04: Fraud Detection — Blacklist**
Beneficiary di daftar hitam Dukcapil/PPATK → transaksi ditolak otomatis dengan alasan "Hubungi cabang".

**BR-05: Off-Hours Handling**
BI-FAST 24/7. LLG/RTGS hanya business hours (08:00-15:00 LLG, 08:00-16:00 RTGS) di hari kerja. Di luar jam → otomatis schedule next business day.

**BR-06: Saldo Hold**
Saat konfirmasi transfer, saldo di-hold (reserved) selama 5 menit. Jika user tidak konfirmasi dalam 5 menit → hold dilepas, transaksi batal.

**BR-07: Double Transfer Prevention**
Idempotency key berdasarkan (source_account + beneficiary_account + nominal + timestamp_window_60s). Jika duplicate dalam 60 detik → reject.

---

## 4. Non-Functional Requirements

### 4.1 Security
- OTP/2FA wajib untuk transfer > Rp 5.000.000
- Device binding + geolocation check
- Encryption AES-256 untuk data rekening
- Audit log immutable (append-only)

### 4.2 Performance
- Beneficiary inquiry: < 3 detik P95
- Transfer execution (BI-FAST): < 60 detik P95
- Receipt generation: < 5 detik

### 4.3 Availability
- Uptime 99.95% (core banking dependency)
- Maintenance window: Minggu 00:00-04:00 WIB

---

## 5. Edge Cases

- **EC-01**: Beneficiary bank maintenance → tampilkan pesan "Bank tujuan sedang maintenance, coba lagi nanti", jangan hold saldo
- **EC-02**: Saldo berubah saat hold (transaksi lain masuk) → validasi ulang saldo saat konfirmasi
- **EC-03**: Network timeout saat eksekusi → status "unknown", reconcile via callback dari core (maks 5 menit)
- **EC-04**: Nasabah blokir akun saat transfer pending → hold transfer, notif cabang
- **EC-05**: Rekursi schedule konflik (recurring + manual di tanggal sama) → eksekusi keduanya, flag untuk review

---

## 6. Acceptance Criteria

| ID | Scenario | Expected |
|----|----------|----------|
| AC-01 | BI-FAST transfer valid | Settle < 60s, receipt terbit |
| AC-02 | LLG di atas cut-off | Schedule next business day |
| AC-03 | Transfer ke rekening blacklist | Reject + alasan |
| AC-04 | Velocity >5 transfer | Hold 30 menit review |
| AC-05 | Saldo tidak cukup | Reject + saldo tidak hold |
| AC-06 | Batch CSV 100 baris | Eksekusi sequential, report per baris |
| AC-07 | Cancel RTGS pending | Refund 1x24 jam |
| AC-08 | OTP timeout | Transfer batal, notif nasabah |

---

*End of PRD*
