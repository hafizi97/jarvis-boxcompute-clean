from fastapi import FastAPI, HTTPException, Security, BackgroundTasks
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import subprocess
import os
import requests
import time
import threading

app = FastAPI(title="BoxCompute Local Runner & JARVIS Bridge Pro", version="1.2.0")

SECRET_TOKEN = os.getenv("BOXCOMPUTE_RUNNER_TOKEN", "jarvis-secret-token-2026")
security = HTTPBearer()

def verify_token(credentials: HTTPAuthorizationCredentials = Security(security)):
    if credentials.credentials != SECRET_TOKEN:
        raise HTTPException(status_code=401, detail="Invalid Authentication Token")
    return credentials.credentials

BASE_WORKSPACES = "/home/faiz/Jarvis/boxcompute_local/workspaces"
os.makedirs(BASE_WORKSPACES, exist_ok=True)

# Penambahbaikan 4: Auto-Prune & Idle Monitor (Hentikan sandbox melahu > 30 minit)
IDLE_TIMEOUT_SECONDS = 1800
active_sandboxes = {} # {agent_id: last_active_timestamp}

def background_idle_cleaner():
    while True:
        time.sleep(60)
        now = time.time()
        for agent_id, last_active in list(active_sandboxes.items()):
            if now - last_active > IDLE_TIMEOUT_SECONDS:
                container_name = f"agent_box_{agent_id}"
                subprocess.run(f"docker rm -f {container_name}", shell=True, capture_output=True)
                active_sandboxes.pop(agent_id, None)

cleaner_thread = threading.Thread(target=background_idle_cleaner, daemon=True)
cleaner_thread.start()

@app.post("/sandbox/start/{agent_id}")
def start_sandbox(agent_id: str, token: str = Security(verify_token)):
    workspace_dir = os.path.join(BASE_WORKSPACES, agent_id)
    os.makedirs(workspace_dir, exist_ok=True)
    container_name = f"agent_box_{agent_id}"
    
    subprocess.run(f"docker rm -f {container_name}", shell=True, capture_output=True)
    
    cmd = (
        f"docker run -d --name {container_name} "
        f"--memory='512m' --cpus='1.0' "
        f"--label com.boxcompute.sandbox=true "
        f"-v {workspace_dir}:/workspace -w /workspace "
        f"debian:trixie-slim sleep infinity"
    )
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if result.returncode != 0:
        raise HTTPException(status_code=500, detail=result.stderr.strip())
        
    active_sandboxes[agent_id] = time.time()
    return {"status": "created", "container": container_name, "path": workspace_dir}

@app.post("/sandbox/exec/{agent_id}")
def exec_sandbox(agent_id: str, command: str, token: str = Security(verify_token)):
    if agent_id in active_sandboxes:
        active_sandboxes[agent_id] = time.time()
        
    container_name = f"agent_box_{agent_id}"
    cmd = f"docker exec {container_name} bash -c {repr(command)}"
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    return {"exit_code": result.returncode, "stdout": result.stdout, "stderr": result.stderr}

@app.delete("/sandbox/stop/{agent_id}")
def stop_sandbox(agent_id: str, token: str = Security(verify_token)):
    container_name = f"agent_box_{agent_id}"
    result = subprocess.run(f"docker rm -f {container_name}", shell=True, capture_output=True, text=True)
    active_sandboxes.pop(agent_id, None)
    return {"status": "stopped", "container": container_name}

@app.post("/ai/complete")
def ai_complete(prompt: str, token: str = Security(verify_token)):
    nine_router_url = "http://127.0.0.1:20128/v1/chat/completions"
    headers = {"Authorization": "Bearer 9router"}
    payload = {
        "model": "recommended",
        "messages": [{"role": "user", "content": prompt}]
    }
    try:
        resp = requests.post(nine_router_url, json=payload, headers=headers, timeout=30)
        return resp.json()
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Gagal berhubung dengan 9Router: {str(e)}")
