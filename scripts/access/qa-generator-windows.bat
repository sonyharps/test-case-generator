@echo off
chcp 65001 >nul
title QA Test Case Generator - IAP Tunnel
REM ============================================================
REM  QA Test Case Generator — akses via IAP tunnel (Windows)
REM  Dobel-klik file ini -> tunggu +-15 detik -> browser kebuka.
REM  Pertama kali: akan minta login akun Google KANTOR (sekali saja).
REM ============================================================

set PORT=8080
set VM=bridgtl-qa-cin-qa-generator
set ZONE=asia-southeast2-b
set PROJECT=bridgtl-qas-d-prj-quality
set URL=http://localhost:%PORT%

where gcloud >nul 2>&1
if errorlevel 1 (
  echo.
  echo [X] gcloud belum terinstall.
  echo     Install dulu: https://cloud.google.com/sdk/docs/install
  echo.
  pause
  exit /b 1
)

REM Tunnel sudah hidup? langsung buka browser.
curl -s -m 3 -o nul %URL%/
if not errorlevel 1 (
  start "" %URL%
  exit /b 0
)

REM Belum login Google? (hanya pertama kali)
for /f "delims=" %%i in ('gcloud config list --format^=value^(core.account^) 2^>nul') do set ACC=%%i
if "%ACC%"=="" (
  echo.
  echo ==============================================
  echo   LOGIN PAKAI AKUN GOOGLE KANTOR
  echo   ^(misal: nama@bankraya.co.id^)
  echo ==============================================
  echo.
  gcloud auth login --project=%PROJECT%
  if errorlevel 1 (
    echo [X] Login gagal.
    pause
    exit /b 1
  )
)

echo Menyalakan tunnel ke server QA... ^(+-15 detik^)
start /b "" gcloud compute start-iap-tunnel %VM% 80 --zone %ZONE% --project %PROJECT% --local-host-port=localhost:%PORT% > "%TEMP%\qa-tunnel.log" 2>&1

set /a TRIES=0
:wait
timeout /t 3 /nobreak >nul
curl -s -m 3 -o nul %URL%/
if not errorlevel 1 (
  echo [OK] Terhubung! Membuka browser...
  start "" %URL%
  exit /b 0
)
set /a TRIES+=1
if %TRIES% lss 20 goto wait

echo.
echo [X] Tunnel belum nyala setelah 60 detik.
echo     Log: %%TEMP%%\qa-tunnel.log
echo     Kemungkinan: belum dapat akses IAP — hubungi tim QA/platform.
pause
exit /b 1
