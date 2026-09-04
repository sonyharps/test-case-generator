#!/bin/bash
# ============================================================
#  QA Test Case Generator — akses via IAP tunnel (macOS)
#  Dobel-klik file ini → tunggu ±15 detik → browser kebuka.
#  Pertama kali: akan minta login akun Google KANTOR (sekali saja).
# ============================================================

PORT="${QA_TUNNEL_PORT:-8080}"
VM="bridgtl-qa-cin-qa-generator"
ZONE="asia-southeast2-b"
PROJECT="bridgtl-qas-d-prj-quality"
URL="http://localhost:$PORT"

cd "$(dirname "$0")"

# gcloud belum terinstall?
if ! command -v gcloud >/dev/null 2>&1; then
  echo ""
  echo "❌ gcloud belum terinstall."
  echo "   Install dulu: https://cloud.google.com/sdk/docs/install"
  echo "   (atau lewat Homebrew: brew install google-cloud-cli)"
  echo ""
  echo "Setelah terinstall, dobel-klik file ini lagi."
  read -r -p "Tekan Enter untuk tutup..." _
  exit 1
fi

# Tunnel sudah hidup? langsung buka browser.
if curl -s -m 3 -o /dev/null "$URL/"; then
  open "$URL"
  exit 0
fi

# Belum login Google? (hanya pertama kali)
ACTIVE=$(gcloud config list --format="value(core.account)" 2>/dev/null)
if [ -z "$ACTIVE" ]; then
  echo ""
  echo "=============================================="
  echo "  LOGIN PAKAI AKUN GOOGLE KANTOR"
  echo "  (misal: nama@bankraya.co.id)"
  echo "=============================================="
  echo ""
  gcloud auth login --project="$PROJECT" </dev/tty >/dev/tty || {
    echo "❌ Login gagal."; read -r -p "Tekan Enter untuk tutup..." _; exit 1; }
fi

# Nyalakan tunnel di background
echo "Menyalakan tunnel ke server QA... (±15 detik)"
nohup gcloud compute start-iap-tunnel "$VM" 80 \
  --zone "$ZONE" --project "$PROJECT" \
  --local-host-port="localhost:$PORT" \
  > /tmp/qa-tunnel.log 2>&1 &

# Tunggu maksimal 60 detik sampai web kebuka
for _ in $(seq 1 20); do
  sleep 3
  if curl -s -m 3 -o /dev/null "$URL/"; then
    echo "✅ Terhubung! Membuka browser..."
    open "$URL"
    exit 0
  fi
done

echo ""
echo "❌ Tunnel belum nyala setelah 60 detik."
echo "   Log: /tmp/qa-tunnel.log"
echo "   Kemungkinan: belum dapat akses IAP — hubungi tim QA/platform."
read -r -p "Tekan Enter untuk tutup..." _
exit 1
