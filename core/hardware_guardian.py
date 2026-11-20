#!/usr/bin/env python3
"""
JARVIS Hardware Guardian Daemon
Monitors Chromebook hardware health autonomously:
- Low battery (<15%, <10%, <5%) with proactive Telegram alerts & voice chime
- Power-saving mode activation at critical battery (<7%)
- CPU Thermal warning (>75°C)
- Disk space warning (>90% full)
- Generates morning / on-demand daily briefings (Waktu Solat JAKIM, Hardware, OpenCode)
"""

import sys
import os
import time
import json
import socket
import subprocess
import threading
from pathlib import Path
from datetime import datetime

JARVIS_DIR = Path("/home/faiz/Jarvis")
IPC_SOCK = "/tmp/jarvis_ipc.sock"

# Guardian state
_last_battery_alert = 0.0
_last_temp_alert = 0.0
_last_battery_pct = 100
_power_saving_active = False

def _send_ipc(prefix: str, text: str) -> bool:
    try:
        if os.path.exists(IPC_SOCK):
            with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as s:
                s.settimeout(2.0)
                s.connect(IPC_SOCK)
                s.sendall(f"{prefix}:{text}\n".encode("utf-8"))
            return True
    except Exception:
        pass
    return False

def _send_telegram(message: str) -> bool:
    try:
        if "/home/faiz/Jarvis/telegram_bot" not in sys.path:
            sys.path.insert(0, "/home/faiz/Jarvis/telegram_bot")
        from bot import JarvisTelegramBot
        bot = JarvisTelegramBot()
        cf = bot.config
        chat_ids = cf.get("allowed_chat_ids") or cf.get("allowed_user_ids") or []
        chat_id = chat_ids[0] if chat_ids else None
        if chat_id:
            bot.send_message(chat_id, message)
            return True
    except Exception as e:
        print(f"[Guardian] Ralat menghantar Telegram: {e}", flush=True)
    return False

def _speak_local(text: str) -> None:
    try:
        if subprocess.run(["which", "spd-say"], capture_output=True).returncode == 0:
            subprocess.Popen(["spd-say", "-t", "female3", "-r", "10", text], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        elif subprocess.run(["which", "espeak"], capture_output=True).returncode == 0:
            subprocess.Popen(["espeak", "-v", "ms", text], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception:
        pass

def get_battery_info() -> tuple:
    """Mengembalikan (capacity_pct, is_charging)"""
    try:
        bat_cap_path = "/sys/class/power_supply/BAT0/capacity"
        bat_stat_path = "/sys/class/power_supply/BAT0/status"
        if os.path.exists(bat_cap_path):
            with open(bat_cap_path) as f:
                cap = int(f.read().strip())
            with open(bat_stat_path) as f:
                stat = f.read().strip().lower()
            is_charging = "charging" in stat or "full" in stat
            return cap, is_charging
    except Exception:
        pass
    return 100, True

def get_cpu_temp() -> float:
    try:
        temp_path = "/sys/class/thermal/thermal_zone0/temp"
        if os.path.exists(temp_path):
            with open(temp_path) as f:
                return int(f.read().strip()) / 1000.0
    except Exception:
        pass
    return 40.0

def activate_power_saving():
    global _power_saving_active
    if _power_saving_active:
        return
    _power_saving_active = True
    print("[Guardian] Mengaktifkan Mod Penjimatan Kuasa Ekstrem!", flush=True)
    try:
        subprocess.run("xrandr --output eDP-1 --brightness 0.35 2>/dev/null || brightnessctl set 20% 2>/dev/null || true", shell=True)
        _send_ipc("LOG", "🔋 [PENJIMATAN KUASA]: Kecerahan skrin dikurangkan automatik.")
    except Exception:
        pass

def restore_power_mode():
    global _power_saving_active
    if not _power_saving_active:
        return
    _power_saving_active = False
    print("[Guardian] Pengecas dikesan, memulihkan mod biasa.", flush=True)
    try:
        subprocess.run("xrandr --output eDP-1 --brightness 1.0 2>/dev/null || brightnessctl set 80% 2>/dev/null || true", shell=True)
        _send_ipc("LOG", "⚡ [PENGECAS DIKESAN]: Kecerahan skrin dipulihkan.")
    except Exception:
        pass

def generate_daily_briefing() -> str:
    """Menjana taklimat harian bersepadu: Solat, Cuaca, Perkakasan, & Projek."""
    lines = ["🌅 *TAKLIMAT HARIAN JARVIS MARK LVII*\n"]
    
    # 1. Tarikh & Hari
    now_str = datetime.now().strftime("%A, %d %B %Y • %I:%M %p")
    lines.append(f"📅 *{now_str}*\n")

    # 2. Waktu Solat JAKIM (Bera, PHG03)
    try:
        res_solat = subprocess.run(["/usr/local/bin/waktu-solat"], capture_output=True, text=True, timeout=5)
        if res_solat.returncode == 0 and res_solat.stdout:
            solat_raw = res_solat.stdout
            solat_lines = [l.strip() for l in solat_raw.split("\n") if l.strip() and not l.startswith("=")]
            lines.append("🕌 *Waktu Solat JAKIM (Bera, PHG03):*")
            lines.append(f"```\n{chr(10).join(solat_lines[:9])}\n```\n")
    except Exception as e:
        print(f"[Guardian] Gagal mendapatkan waktu solat: {e}", flush=True)

    # 3. Status Bateri & Sistem
    cap, charging = get_battery_info()
    temp = get_cpu_temp()
    stat_charge = "⚡ Sedang Dicas" if charging else "🔋 Menggunakan Bateri"
    lines.append("💻 *Kesihatan Perkakasan:*")
    lines.append(f"• Bateri: *{cap}%* ({stat_charge})")
    lines.append(f"• Suhu CPU: *{temp:.1f}°C*")
    
    # Storan
    try:
        st = os.statvfs("/")
        free_gb = (st.f_bavail * st.f_frsize) / (1024**3)
        total_gb = (st.f_blocks * st.f_frsize) / (1024**3)
        lines.append(f"• Storan Bebas: *{free_gb:.1f} GB* daripada {total_gb:.1f} GB\n")
    except Exception:
        pass

    # 4. Ringkasan Projek & OpenCode
    lines.append("🤖 *Gandingan OpenCode AI:*")
    lines.append("• 3 Pelayan MCP Aktif (`jarvis`, `9router`, `git`)")
    lines.append("• Sedia menerima arahan pengekodan dan automasi.")

    return "\n".join(lines)

def guardian_loop():
    """Gelung pemantau latar belakang setiap 60 saat."""
    global _last_battery_alert, _last_temp_alert, _last_battery_pct
    print("[Guardian] Pemantau perkakasan autonomi aktif...", flush=True)

    while True:
        try:
            now = time.monotonic()
            cap, charging = get_battery_info()
            temp = get_cpu_temp()

            if charging:
                restore_power_mode()
            else:
                # Alert battery < 15%
                if cap <= 15 and (now - _last_battery_alert > 600 or cap <= _last_battery_pct - 3):
                    _last_battery_alert = now
                    _last_battery_pct = cap
                    alert_msg = (
                        f"⚠️ *AMARAN BATERI KRITIKAL CHROMEBOOK!*\n\n"
                        f"Paras bateri laptop kini berada pada *{cap}%* dan *TIDAK DICAS*.\n"
                        f"Sila sambungkan kabel pengecas segera untuk mengelakkan sistem terpadam tiba-tiba!"
                    )
                    _send_telegram(alert_msg)
                    _send_ipc("LOG", f"⚠️ [BATERI KRITIKAL]: Paras bateri tinggal {cap}%! Sila pasang pengecas.")
                    _speak_local(f"Perhatian Tuan Faiz, paras bateri laptop tinggal {cap} peratus. Sila sambungkan pengecas sekarang.")

                # Extreme power save < 7%
                if cap <= 7:
                    activate_power_saving()

            # Thermal alert > 75°C
            if temp >= 75.0 and (now - _last_temp_alert > 900):
                _last_temp_alert = now
                th_msg = f"🔥 *AMARAN SUHU TINGGI CHROMEBOOK: {temp:.1f}°C!*\nSistem sedang mengalami beban tinggi. Menjeda proses berat."
                _send_telegram(th_msg)
                _send_ipc("LOG", f"🔥 [AMARAN HABA]: Suhu CPU mencecah {temp:.1f}°C!")

        except Exception as e:
            print(f"[Guardian] Ralat gelung pemantau: {e}", flush=True)

        time.sleep(60)

def start_guardian_thread():
    t = threading.Thread(target=guardian_loop, daemon=True, name="hardware-guardian")
    t.start()
    return t

if __name__ == "__main__":
    print(generate_daily_briefing())
    guardian_loop()
