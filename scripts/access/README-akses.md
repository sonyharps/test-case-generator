# Akses QA Test Case Generator (via IAP Tunnel)

Aplikasi QA generator berjalan di VM GCP **tanpa IP publik** — aksesnya lewat
IAP (Identity-Aware Proxy) tunnel: koneksi diizinkan hanya untuk akun Google
yang di-grant IAM, semua akses tercatat di Cloud Audit Logs, dan bisa dicabut
kapan saja. Tidak perlu VPN.

## Untuk user (bos / QA) — 3 langkah

1. **Install gcloud sekali**: https://cloud.google.com/sdk/docs/install
2. Kirim file ke user:
   - macOS → `qa-generator-mac.command`
   - Windows → `qa-generator-windows.bat`
3. User **dobel-klik file tersebut**:
   - Pertama kali: muncul prompt login → login pakai **akun Google kantor**
   - Setelah itu: tunggu ±15 detik, browser otomatis kebuka `http://localhost:8080`
   - Login aplikasi pakai username/password QA (bukan Google)

Catatan macOS: kalau file ditolak karena "unidentified developer" (hasil
download), buka **System Settings → Privacy & Security → Open Anyway**.
Terminal harus punya izin menjalankan file — klik kanan → Open juga bisa.

## Untuk admin (grant akses sekali per user)

Ganti `EMAIL@bankraya.co.id` lalu jalankan (butuh punya hak kelola IAM project):

```bash
gcloud projects add-iam-policy-binding bridgtl-qas-d-prj-quality \
  --member="user:EMAIL@bankraya.co.id" \
  --role="roles/iap.tunnelResourceAccessor"

gcloud projects add-iam-policy-binding bridgtl-qas-d-prj-quality \
  --member="user:EMAIL@bankraya.co.id" \
  --role="roles/compute.networkUser"
```

Cabut akses: jalankan `remove-iam-policy-binding` dengan role yang sama.

## Detail teknis

| Item | Nilai |
|---|---|
| VM | `bridgtl-qa-cin-qa-generator` (asia-southeast2-b, IP internal 10.99.1.12) |
| Project | `bridgtl-qas-d-prj-quality` |
| Port lokal | 8080 (bisa di-override: `QA_TUNNEL_PORT=8081 ./qa-generator-mac.command`) |
| Log tunnel (mac) | `/tmp/qa-tunnel.log` |
| Log tunnel (win) | `%TEMP%\qa-tunnel.log` |

Tunnel mati kalau laptop restart — tinggal dobel-klik lagi.
