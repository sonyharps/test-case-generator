# PRD: Patient Appointment Booking System

**Document ID:** PRD-HLT-2024-003
**Version:** 2.0
**Status:** Approved
**Domain:** Healthcare

---

## 1. Overview

### 1.1 Purpose
Sistem booking janji temu pasien untuk klinik/rumah sakit. Mencakup pencarian dokter, jadwal, booking, reschedule, cancel, reminder, dan integrasi pembayaran konsultasi.

### 1.2 Scope
- Doctor search & filter (spesialisasi, lokasi, rating, jadwal)
- Slot availability real-time
- Booking & confirmation
- Reschedule & cancellation (dengan policy)
- Automated reminders (email/SMS/WhatsApp)
- Payment integration (BPJS/mandiri/asuransi)
- Telemedicine option (video call)

---

## 2. Functional Requirements

**FR-AP-01: Doctor Search**
Pasien dapat cari dokter berdasarkan: nama, spesialisasi (kategori), lokasi klinik, jadwal tersedia, rating minimum. Filter dapat dikombinasikan. Pagination 10 hasil per page.

**FR-AP-02: Slot Availability**
Tampilkan slot tersedia untuk dokter di tanggal terpilih. Slot 30 menit (09:00-09:30, dst). Real-time sync dengan kalender dokter. Slot booked hilang dari list.

**FR-AP-03: Booking Flow**
1. Pilih dokter + tanggal + slot
2. Pilih tipe konsultasi (offline/telemedicine)
3. Isi keluhan utama (opsional, maks 500 karakter)
4. Pilih payment (BPJS/Mandiri/Asuransi partner)
5. Konfirmasi → generate booking ID (format: BK-YYYYMMDD-XXXX)

**FR-AP-04: Booking Confirmation**
Setelah sukses:
- Status: CONFIRMED
- Email + SMS + WhatsApp notif (instantial)
- Add ke kalender pasien (.ics attachment)
- Booking ID + QR code untuk check-in

**FR-AP-05: Reschedule**
Pasien dapat reschedule maksimum H-2 sebelum janji. Alasan wajib (dropdown). Slot baru harus tersedia. Notifikasi ke dokter & pasien. Maksimum 2x reschedule per booking.

**FR-AP-06: Cancellation**
Pasien dapat cancel dengan policy:
- H-3 atau lebih: full refund
- H-2 sampai H-1: 50% refund
- Hari-H atau no-show: no refund
Notif ke dokter, slot dibebaskan kembali.

**FR-AP-07: Automated Reminders**
- H-1: email + SMS reminder
- H-2 jam: WhatsApp reminder
- H-30 menit: telemedicine link (jika video consult)
Pasien dapat opt-out reminder di settings.

**FR-AP-08: Check-in**
Pasien datang → scan QR di klinik (self-service kiosk) atau check-in manual di receptionist. Status → CHECKED_IN. Jika telat >15 menit, status → LATE (dokter dapat skip atau reschedule).

**FR-AP-09: Telemedicine**
Untuk video consult:
- Generate link (Zoom/Google Meet) 15 menit sebelum jadwal
- Pasien join via app/web
- Recording opsional (dengan consent pasien + dokter)
- Auto-end di akhir slot (30 menit) + 5 menit grace

**FR-AP-10: Payment**
- BPJS: verifikasi nomor kartu + quota tersisa (cek via API BPJS)
- Mandiri: payment gateway (VA/e-wallet/credit card)
- Asuransi: verifikasi policy + pre-authorization
- Refund otomatis sesuai cancellation policy

---

## 3. Business Rules

**BR-01: Booking Limit**
Pasien maksimum 3 active booking (CONFIRMED) di waktu bersamaan. Booking lewat → tolang dengan pesan "Selesaikan appointment aktif dulu".

**BR-02: No-Show Penalty**
3x no-show dalam 90 hari → akun suspended 30 hari. Counter reset setelah periode.

**BR-03: Doctor Cancellation**
Jika dokter cancel < H-1: pasien dapat reschedule gratis (priority slot) + voucher kompensasi Rp 50.000.

**BR-04: BPJS Quota**
BPJS cek via API real-time. Jika quota habis → tawarkan opsi mandiri. Limit 1 booking BPJS per pasien per hari.

**BR-05: Double Booking Prevention**
Sistem cek (patient_id + doctor_id + slot_datetime). Jika duplicate → reject dengan pesan spesifik.

**BR-06: Telemedicine Eligibility**
Tidak semua spesialisasi support telemedicine (mis. bedah, radiologi wajib offline). Validasi di booking step.

---

## 4. Non-Functional Requirements

### 4.1 Privacy & Security (HIPAA-like)
- Patient data encrypted at rest (AES-256)
- PII masking di log (nama → [PATIENT], NIK → [NIK])
- Audit log semua akses patient record
- Role-based access (pasien lihat own data, dokter lihat assigned patients)

### 4.2 Performance
- Search doctor: < 2 detik P95
- Booking confirmation: < 3 detik P95
- Slot sync: real-time (WebSocket)

### 4.3 Availability
- Uptime 99.9% (emergency room fallback via phone)
- BPJS/insurance API downtime → graceful degradation (offline verification)

---

## 5. Edge Cases

- **EC-01**: Dokter sakit mendadak → notif semua pasien hari itu, auto-reschedule atau cancel + voucher
- **EC-02**: Pasien checkout telemedicine saat konsultasi → dokter dapat end session, notif admin
- **EC-03**: Slot double-booked akibat race condition → first-wins, second dapat error + alternatif slot
- **EC-04**: BPJS API down saat booking → allow booking dengan catatan "verifikasi BPJS pending", deadline H-1
- **EC-05**: Pasien edit keluhan setelah confirm → hanya sampai H-1, setelah itu lock

---

## 6. Acceptance Criteria

| ID | Scenario | Expected |
|----|----------|----------|
| AC-01 | Search dokter by spesialisasi | Hasil relevan < 2s |
| AC-02 | Booking slot tersedia | Booking ID terbit, slot hilang |
| AC-03 | Reschedule H-1 | Ditolak, tampilkan policy |
| AC-04 | Cancel H-3 | Full refund otomatis |
| AC-05 | 3x no-show | Akun suspended 30 hari |
| AC-06 | BPJS quota habis | Tawarkan opsi mandiri |
| AC-07 | Double booking attempt | Reject + pesan spesifik |
| AC-08 | Telemedicine ineligible spec | Opsi telemedicine disabled |

---

*End of PRD*
