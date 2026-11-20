# Mini BoxCompute Local Sandbox

Sistem pengurusan API Sandbox & Ejen AI terpencil (berfungsi seperti BoxCompute) telah berjaya dipasang dan diuji secara tempatan.

## 📂 Lokasi Fail Projek
- Direktori Utama: `/home/faiz/Jarvis/boxcompute_local`
- Kod Utama API: `/home/faiz/Jarvis/boxcompute_local/main.py`
- Direktori Workspace Ejen: `/home/faiz/Jarvis/boxcompute_local/workspaces`
- Fail Konfigurasi Docker: `/home/faiz/Jarvis/boxcompute_local/docker-compose.yml`

## 🚀 Cara Menjalankan Pelayan API
1. Masuk ke folder projek:
   ```bash
   cd /home/faiz/Jarvis/boxcompute_local
   ```
2. Jalankan pelayan Uvicorn secara manual:
   ```bash
   ./venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000
   ```
   Atau gunakan Docker Compose:
   ```bash
   docker compose up -d
   ```

## 🛠️ Cara Menguji (API Endpoints)
- **Cipta / Mula Sandbox:**
  ```bash
  curl -X POST "http://127.0.0.1:8000/sandbox/start/namasandbox"
  ```
- **Jalankan Arahan (Command Execution):**
  ```bash
  curl -X POST "http://127.0.0.1:8000/sandbox/exec/namasandbox?command=ls%20-la"
  ```
- **Hentikan & Buang Sandbox:**
  ```bash
  curl -X DELETE "http://127.0.0.1:8000/sandbox/stop/namasandbox"
  ```
