# Panduan Konfigurasi VirtualBox untuk BoxCompute Local

Panduan ini menerangkan cara menyediakan VirtualBox agar ia bertindak sebagai pelayan sandboxed BoxCompute yang boleh diakses dari komputer fizikal anda.

## Langkah 1: Sediakan VM Ubuntu di VirtualBox
1. Muat turun fail ISO **Ubuntu Server**.
2. Di VirtualBox, klik **New**, beri nama (cth: `BoxCompute-VM`), dan pilih Ubuntu ISO.
3. Berikan spesifikasi minimum:
   - **RAM:** 4096 MB (4GB)
   - **CPU:** 2 Cores
   - **Disk:** 20 GB – 30 GB
4. Mulakan VM dan lengkapkan pemasangan Ubuntu.

## Langkah 2: Konfigurasi Port Forwarding (Supaya Hos Boleh Capai API)
1. Di paparan utama VirtualBox, klik kanan pada VM anda dan pilih **Settings**.
2. Pergi ke tab **Network** -> **Adapter 1**.
3. Pastikan **Attached to:** ditetapkan kepada **NAT**.
4. Klik butang **Advanced** -> **Port Forwarding**.
5. Tambah aturan baharu (Rule):
   - **Name:** `BoxCompute-API`
   - **Protocol:** `TCP`
   - **Host IP:** `127.0.0.1`
   - **Host Port:** `8000`
   - **Guest IP:** (Biarkan kosong atau isi IP dalaman VM)
   - **Guest Port:** `8000`
6. Klik **OK**.

## Langkah 3: Jalankan Skrip Automasi di dalam VM Ubuntu
Masuk ke terminal VM Ubuntu anda, kemudian salin dan jalankan skrip persediaan ini:

```bash
# 1. Kemas kini & pasang Docker
sudo apt update && sudo apt upgrade -y
sudo apt install -y docker.io docker-compose git curl
sudo usermod -aG docker $USER
newgrp docker

# 2. Muat turun / Cipta struktur BoxCompute Local
mkdir -p ~/boxcompute_local/workspaces
cd ~/boxcompute_local

# 3. Cipta main.py (API Controller)
cat << 'EOF' > main.py
from fastapi import FastAPI, HTTPException
import subprocess
import os

app = FastAPI(title="VirtualBox BoxCompute API")
WORKSPACE_DIR = "/home/faiz/boxcompute_local/workspaces"
os.makedirs(WORKSPACE_DIR, exist_ok=True)

@app.post("/sandbox/start/{agent_id}")
def start_sandbox(agent_id: str):
    container_name = f"agent_box_{agent_id}"
    workspace_path = os.path.join(WORKSPACE_DIR, agent_id)
    os.makedirs(workspace_path, exist_ok=True)
    
    check = subprocess.run(f"docker ps -a -q -f name=^/{container_name}$", shell=True, capture_output=True, text=True)
    if check.stdout.strip():
        subprocess.run(f"docker start {container_name}", shell=True)
        return {"status": "resumed", "container": container_name}
    
    cmd = f"docker run -d --name {container_name} -v {workspace_path}:/workspace ubuntu:latest tail -f /dev/null"
    res = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if res.returncode != 0:
        raise HTTPException(status_code=500, detail=res.stderr)
    return {"status": "created", "container": container_name, "path": workspace_path}

@app.post("/sandbox/exec/{agent_id}")
def exec_command(agent_id: str, command: str):
    container_name = f"agent_box_{agent_id}"
    cmd = f"docker exec {container_name} bash -c '{command}'"
    res = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    return {"exit_code": res.returncode, "stdout": res.stdout, "stderr": res.stderr}

@app.delete("/sandbox/stop/{agent_id}")
def stop_sandbox(agent_id: str):
    container_name = f"agent_box_{agent_id}"
    subprocess.run(f"docker stop {container_name} && docker rm {container_name}", shell=True)
    return {"status": "stopped and removed", "container": container_name}
EOF

# 4. Cipta keperluan Python & jalankan API
cat << 'EOF' > requirements.txt
fastapi
uvicorn
pydantic
requests
EOF

python3 -m venv venv
./venv/bin/pip install -r requirements.txt

# 5. Jalankan pelayan API di latar belakang
nohup ./venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000 &
```

## Langkah 4: Uji Dari Komputer Fizikal (Hos)
Selepas skrip di atas berjalan di dalam VM, buka terminal di komputer fizikal anda dan uji sambungan:
---
title: BoxCompute VirtualBox Setup Guide
---
