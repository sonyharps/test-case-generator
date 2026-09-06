# Setting Akses Google Drive — QA Test Case Generator

Aplikasi mengupload hasil export Excel ke Google **Shared Drive** atas nama
akun teknis (service account) — bukan akun Gmail siapa pun. Aksesnya
permanen, teraudit, dan tidak tergantung pada individu.

## Tiga lapis setting

### Lapis 1 — Keanggotaan di Shared Drive (disetel sekali oleh manusia)
- Service account: `tcg-drive@bridgtl-qas-d-prj-quality.iam.gserviceaccount.com`
- Di-add sebagai **member Shared Drive** dengan role **Content Manager**
  (boleh upload/edit/menata file; tidak bisa kelola anggota atau hapus drive)
- Satu-satunya langkah yang membutuhkan akun manusia ber-peran Manager

### Lapis 2 — Identitas di server (GCP, sudah aktif)
- SA di-attach ke VM `bridgtl-qa-cin-qa-generator` (zone asia-southeast2-b)
  dengan access scope `https://www.googleapis.com/auth/drive`
- Token diambil otomatis dari GCE metadata server — **tidak ada API key /
  file JSON credential di server** (tidak perlu rotate, tidak bisa bocor
  lewat backup/repo)
- Drive API di-enable di project `bridgtl-qas-d-prj-quality`

### Lapis 3 — Konfigurasi aplikasi (`.env` di VM)
```
DRIVE_FOLDER_ID=19zEixDpsov0Yonuzjzfil3M_gxuB48KY   # folder "Test Cases"
```
Nama file otomatis: `TC_<judul-requirement>_<tanggal>_<jumlah>TC.xlsx`.
Link file (webViewLink) disimpan ke kolom `orchestrator_sessions.drive_file_link`
dan tampil di halaman Riwayat → detail session.

## Alur upload
```
Browser → Backend (VM) → token dari metadata GCE
        → Drive API files.create (supportsAllDrives=true)
        → file muncul di folder tujuan → link disimpan ke DB → tampil di UI
```

## Cheat-sheet operasional

| Kebutuhan | Cara | Butuh akses |
|---|---|---|
| Ganti folder tujuan | Ubah `DRIVE_FOLDER_ID` di `.env` VM + restart backend (`docker compose -f docker-compose.prod.yml up -d backend`) | Akses VM |
| Cabut akses upload total | Hapus member `tcg-drive@…` dari Shared Drive | Manager shared drive |
| Cek siapa punya akses | Shared Drive → Manage members | Manager shared drive |
| Audit upload | Cloud Audit Logs (Drive API, identitas SA) + kolom `drive_file_link` per session | Admin GCP |
| Pindah/scoping ulang SA | `gcloud compute instances set-service-account …` (VM harus stop/start) | Compute admin |

## Poin keamanan
1. **Zero credential at rest** — autentikasi via VM identity (metadata), bukan key file
2. **Least privilege** — SA hanya berlaku di shared drive tempatnya jadi member; scope Drive eksplisit (bukan `cloud-platform` yang luas)
3. **Bukan akun personal** — resign/rotasi orang tidak mempengaruhi; file dimiliki organisasi via shared drive
4. **Terlacak** — setiap upload tercatat di audit log GCP (identitas SA) dan di aplikasi (user pemilik session)

## Ide lanjutan (belum diimplementasi)
- Subfolder per squad (`Digital-Lending/`, `Payment/`, …) — SA Content Manager
  sudah bisa membuat subfolder; tinggal pemetaan squad → folder di aplikasi
- Auto-save ke Drive setiap generate (toggle per user)
