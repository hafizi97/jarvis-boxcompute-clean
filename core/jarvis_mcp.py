#!/usr/bin/env python3
"""
JARVIS AI MCP Server for OpenCode & Autonomous Agents
Connects OpenCode CLI directly to JARVIS Mark LVII on Chromebook:
- Live HUD communication log (/tmp/jarvis_ipc.sock)
- Voice synthesis & desktop notifications
- Real-time hardware telemetry (CPU, RAM, GPU Radeon R4, Temp, Battery)
- Desktop vision: instant screenshots (/tmp/jarvis_screenshot.png)
- Multimedia & volume controls (pactl / playerctl)
- Application launcher (Brave, Kodi, Thunar, Htop, Terminal)
- Telegram bot instant reporting & media/file delivery
- Shared persistent memory (jarvis_memory.json)
- Dynamic action caller (weather, prayer times, system settings)
- Background service manager (9router, jarvis-telegram, cloudflared)
- 1080p Video generation & TV HDMI playback
"""

import sys
import json
import os
import socket
import subprocess
import importlib
from pathlib import Path

# Paths
JARVIS_DIR = Path("/home/faiz/Jarvis")
MEMORY_PATH = JARVIS_DIR / "memory" / "jarvis_memory.json"
IPC_SOCK = "/tmp/jarvis_ipc.sock"

# ─── Helper Functions ────────────────────────────────────────────────────────

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

def _notify_desktop(title: str, text: str) -> None:
    try:
        env = os.environ.copy()
        env["DISPLAY"] = env.get("DISPLAY", ":0")
        subprocess.run(
            ["notify-send", "-a", "JARVIS AI", "-i", "/home/faiz/Jarvis/face.png", title, text],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=3, env=env
        )
    except Exception:
        pass

def _speak(text: str) -> None:
    try:
        if subprocess.run(["which", "spd-say"], capture_output=True).returncode == 0:
            subprocess.Popen(["spd-say", "-t", "female3", "-r", "10", text], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        elif subprocess.run(["which", "espeak"], capture_output=True).returncode == 0:
            subprocess.Popen(["espeak", "-v", "ms", text], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception:
        pass

def get_system_telemetry() -> dict:
    telemetry = {}
    try:
        # GPU
        gpu_path = "/sys/class/drm/card0/device/gpu_busy_percent"
        if os.path.exists(gpu_path):
            with open(gpu_path) as f:
                telemetry["gpu_percent"] = f.read().strip() + "%"
        else:
            telemetry["gpu_percent"] = "N/A"
            
        # Battery
        bat_cap = "/sys/class/power_supply/BAT0/capacity"
        bat_stat = "/sys/class/power_supply/BAT0/status"
        if os.path.exists(bat_cap):
            with open(bat_cap) as f:
                c = f.read().strip()
            with open(bat_stat) as f:
                s = f.read().strip()
            telemetry["battery"] = f"{c}% ({s})"

        # RAM
        with open("/proc/meminfo") as f:
            lines = f.readlines()
        mem = {}
        for l in lines[:5]:
            parts = l.split(":")
            if len(parts) == 2:
                mem[parts[0].strip()] = int(parts[1].replace("kB", "").strip())
        total = mem.get("MemTotal", 1)
        avail = mem.get("MemAvailable", 0)
        used_pct = round((total - avail) / total * 100, 1)
        telemetry["ram_usage"] = f"{used_pct}% ({round((total-avail)/1024/1024, 2)} GB / {round(total/1024/1024, 2)} GB)"

        # Temp
        temp_path = "/sys/class/thermal/thermal_zone0/temp"
        if os.path.exists(temp_path):
            with open(temp_path) as f:
                t = int(f.read().strip()) / 1000.0
                telemetry["cpu_temp"] = f"{round(t, 1)}°C"

        telemetry["platform"] = "Chromebook Treeya (AMD A4-9120C, Radeon R4, Debian 13 Trixie)"
    except Exception as e:
        telemetry["error"] = str(e)
    return telemetry

# ─── Tool Definitions ────────────────────────────────────────────────────────

TOOLS = [
    {
        "name": "jarvis_notify",
        "description": "Hantar mesej log atau kemas kini kemajuan OpenCode secara langsung ke paparan HUD JARVIS di desktop Chromebook dan notifikasi XFCE.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "message": {
                    "type": "string",
                    "description": "Mesej kemas kini atau makluman yang ingin dipaparkan pada skrin JARVIS."
                }
            },
            "required": ["message"]
        }
    },
    {
        "name": "jarvis_speak",
        "description": "Arahkan JARVIS untuk bersuara dan bercakap dengan Tuan Faiz melalui pembesar suara Chromebook.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "text": {
                    "type": "string",
                    "description": "Ayat atau teks yang ingin disebut secara lantang oleh JARVIS."
                }
            },
            "required": ["text"]
        }
    },
    {
        "name": "jarvis_system_status",
        "description": "Dapatkan metrik perkakasan Chromebook terkini: penggunaan RAM, beban GPU Radeon R4, suhu CPU, dan peratusan bateri.",
        "inputSchema": {
            "type": "object",
            "properties": {}
        }
    },
    {
        "name": "jarvis_take_screenshot",
        "description": "Ambil tangkapan skrin desktop Chromebook terkini (DISPLAY=:0) untuk analisis visual UI atau semakan skrin. Pilihan untuk hantar terus ke Telegram.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "filename": {
                    "type": "string",
                    "description": "Laluan fail simpanan gambar (lalai: '/tmp/jarvis_screenshot.png')."
                },
                "send_telegram": {
                    "type": "boolean",
                    "description": "Set true untuk hantar gambar skrin terus ke Telegram Tuan Faiz."
                }
            }
        }
    },
    {
        "name": "jarvis_telegram_send",
        "description": "Hantar mesej laporan teks ringkas terus ke akaun Telegram Tuan Faiz.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "message": {"type": "string", "description": "Teks mesej laporan untuk dihantar ke Telegram."}
            },
            "required": ["message"]
        }
    },
    {
        "name": "jarvis_telegram_send_file",
        "description": "Hantar fail dokumen, gambar, kod, atau arkib log secara langsung ke Telegram Tuan Faiz.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "file_path": {"type": "string", "description": "Laluan fail penuh di Chromebook (contohnya: '/tmp/screen.png' atau '/home/faiz/report.md')."},
                "caption": {"type": "string", "description": "Kapsyen atau penerangan ringkas mengenai fail yang dihantar."}
            },
            "required": ["file_path"]
        }
    },
    {
        "name": "jarvis_media_control",
        "description": "Kawal kelantangan audio sistem Chromebook (volume) dan kawalan main/jeda pemain media.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "description": "Tindakan audio: 'volume_up', 'volume_down', 'volume_set', 'mute', 'unmute', 'play_pause', 'next', 'prev'.",
                    "enum": ["volume_up", "volume_down", "volume_set", "mute", "unmute", "play_pause", "next", "prev"]
                },
                "level": {
                    "type": "integer",
                    "description": "Peratus aras suara (0 hingga 100) jika menggunakan action 'volume_set'."
                }
            },
            "required": ["action"]
        }
    },
    {
        "name": "jarvis_app_launch",
        "description": "Lancar atau buka aplikasi desktop pada skrin Chromebook secara selamat (contoh: Brave Browser, fail manager Thunar, Kodi, Htop, terminal).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "app": {
                    "type": "string",
                    "description": "Nama aplikasi: 'brave', 'thunar', 'kodi', 'htop', 'terminal', atau arahan lain."
                },
                "args": {
                    "type": "string",
                    "description": "Argumen tambahan (contoh URL untuk Brave atau folder untuk Thunar)."
                }
            },
            "required": ["app"]
        }
    },
    {
        "name": "jarvis_action_call",
        "description": "Panggil modul tindakan rasmi JARVIS (contohnya: waktu_solat, weather_report, system_monitor, tv_controller).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "action_name": {
                    "type": "string",
                    "description": "Nama fail modul tindakan dalam JARVIS/actions/ (contoh: 'waktu_solat', 'weather_report', 'system_monitor')."
                },
                "parameters": {
                    "type": "object",
                    "description": "Parameter kamus untuk tindakan tersebut."
                }
            },
            "required": ["action_name"]
        }
    },
    {
        "name": "jarvis_service_control",
        "description": "Semak status atau mulakan semula perkhidmatan latar belakang sistem (contoh: '9router', 'jarvis-telegram', 'cloudflared').",
        "inputSchema": {
            "type": "object",
            "properties": {
                "service": {
                    "type": "string",
                    "description": "Nama perkhidmatan: '9router', 'jarvis-telegram', 'cloudflared'."
                },
                "action": {
                    "type": "string",
                    "description": "Tindakan: 'status', 'restart', 'start', 'stop'.",
                    "enum": ["status", "restart", "start", "stop"]
                }
            },
            "required": ["service", "action"]
        }
    },
    {
        "name": "jarvis_memory_save",
        "description": "Simpan maklumat atau hasil keputusan penting ke dalam pangkalan memori kekal JARVIS.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "key": {"type": "string", "description": "Kunci atau tajuk topik memori (contohnya: 'projek/backend_update')."},
                "content": {"type": "string", "description": "Kandungan fakta atau nota yang ingin disimpan."}
            },
            "required": ["key", "content"]
        }
    },
    {
        "name": "jarvis_memory_search",
        "description": "Cari maklumat atau sejarah tugasan terdahulu di dalam pangkalan ingatan JARVIS.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Kata kunci carian memori."}
            },
            "required": ["query"]
        }
    },
    {
        "name": "jarvis_play_video_tv",
        "description": "Jana video animasi 1080p Full HD menggunakan enjin JARVIS dan mainkannya terus ke paparan TV HDMI.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "prompt": {"type": "string", "description": "Tajuk atau topik video."},
                "subtitle": {"type": "string", "description": "Sari kata atau penerangan ringkas video."}
            },
            "required": ["prompt"]
        }
    }
]

# ─── Tool Execution ──────────────────────────────────────────────────────────

def call_tool(name: str, arguments: dict) -> str:
    if name == "jarvis_notify":
        msg = arguments.get("message", "")
        formatted = f"🧠 [OpenCode AI]: {msg}"
        _send_ipc("LOG", formatted)
        _notify_desktop("OpenCode • JARVIS", msg)
        return f"Mesej berjaya dihantar ke HUD JARVIS: '{msg}'"

    elif name == "jarvis_speak":
        txt = arguments.get("text", "")
        _send_ipc("LOG", f"🔊 [Suara]: {txt}")
        _speak(txt)
        return f"JARVIS sedang menyebut: '{txt}'"

    elif name == "jarvis_system_status":
        telem = get_system_telemetry()
        return json.dumps(telem, indent=2)

    elif name == "jarvis_take_screenshot":
        filename = arguments.get("filename", "/tmp/jarvis_screenshot.png")
        send_tg = arguments.get("send_telegram", False)
        try:
            env = os.environ.copy()
            env["DISPLAY"] = env.get("DISPLAY", ":0")
            env["XAUTHORITY"] = env.get("XAUTHORITY", "/home/faiz/.Xauthority")
            res = subprocess.run(["scrot", "-z", filename], capture_output=True, text=True, timeout=5, env=env)
            if res.returncode != 0:
                # Fallback to import or ffmpeg
                subprocess.run(f"DISPLAY=:0 scrot {filename}", shell=True, timeout=5)
            
            if not os.path.exists(filename):
                return "Gagal mengambil tangkapan skrin (fail tidak tercipta)."
                
            status_msg = f"Tangkapan skrin berjaya disimpan di: {filename}"
            if send_tg:
                sys.path.insert(0, "/home/faiz/Jarvis/telegram_bot")
                from bot import JarvisTelegramBot
                bot = JarvisTelegramBot()
                cf = bot.config
                chat_id = (cf.get("allowed_chat_ids") or cf.get("allowed_user_ids") or [None])[0]
                if chat_id:
                    bot.send_photo(chat_id, filename, caption="📸 Tangkapan Skrin Terkini Chromebook Faiz")
                    status_msg += f" dan dihantar ke Telegram (ID {chat_id})."
            _send_ipc("LOG", f"📸 [Screenshot]: {filename}")
            return status_msg
        except Exception as e:
            return f"Ralat mengambil tangkapan skrin: {e}"

    elif name == "jarvis_telegram_send":
        msg = arguments.get("message", "")
        try:
            sys.path.insert(0, "/home/faiz/Jarvis/telegram_bot")
            from bot import JarvisTelegramBot
            bot = JarvisTelegramBot()
            cf = bot.config
            chat_id = (cf.get("allowed_chat_ids") or cf.get("allowed_user_ids") or [None])[0]
            if chat_id:
                bot.send_message(chat_id, f"🤖 [OpenCode AI Report]:\n{msg}")
                return f"Laporan berjaya dihantar ke Telegram (ID {chat_id})."
            else:
                return "Tiada chat_id berdaftar ditemui dalam konfigurasi Telegram bot."
        except Exception as e:
            return f"Ralat menghantar ke Telegram: {e}"

    elif name == "jarvis_telegram_send_file":
        fpath = arguments.get("file_path", "")
        cap = arguments.get("caption", "Fail daripada OpenCode AI")
        if not os.path.exists(fpath):
            return f"Ralat: Fail '{fpath}' tidak wujud."
        try:
            sys.path.insert(0, "/home/faiz/Jarvis/telegram_bot")
            from bot import JarvisTelegramBot
            bot = JarvisTelegramBot()
            cf = bot.config
            chat_id = (cf.get("allowed_chat_ids") or cf.get("allowed_user_ids") or [None])[0]
            if not chat_id:
                return "Tiada chat_id berdaftar ditemui."
            ext = os.path.splitext(fpath)[1].lower()
            if ext in [".png", ".jpg", ".jpeg", ".webp"]:
                bot.send_photo(chat_id, fpath, caption=cap)
            else:
                bot.send_document(chat_id, fpath, caption=cap)
            return f"Fail '{fpath}' berjaya dihantar ke Telegram Tuan Faiz."
        except Exception as e:
            return f"Ralat menghantar fail ke Telegram: {e}"

    elif name == "jarvis_media_control":
        action = arguments.get("action")
        level = arguments.get("level", 50)
        try:
            if action == "volume_up":
                subprocess.run(["pactl", "set-sink-volume", "@DEFAULT_SINK@", "+10%"], timeout=3)
                return "Kelantangan audio dinaikkan sebanyak 10%."
            elif action == "volume_down":
                subprocess.run(["pactl", "set-sink-volume", "@DEFAULT_SINK@", "-10%"], timeout=3)
                return "Kelantangan audio diturunkan sebanyak 10%."
            elif action == "volume_set":
                lvl = max(0, min(100, int(level)))
                subprocess.run(["pactl", "set-sink-volume", "@DEFAULT_SINK@", f"{lvl}%"], timeout=3)
                return f"Kelantangan audio ditetapkan ke {lvl}%."
            elif action == "mute":
                subprocess.run(["pactl", "set-sink-mute", "@DEFAULT_SINK@", "1"], timeout=3)
                return "Audio telah dibisukan (muted)."
            elif action == "unmute":
                subprocess.run(["pactl", "set-sink-mute", "@DEFAULT_SINK@", "0"], timeout=3)
                return "Audio telah dinyahbisu (unmuted)."
            elif action == "play_pause":
                subprocess.run(["playerctl", "play-pause"], timeout=3)
                return "Tindakan Main/Jeda dihantar ke pemain media."
            elif action == "next":
                subprocess.run(["playerctl", "next"], timeout=3)
                return "Lagu/media seterusnya."
            elif action == "prev":
                subprocess.run(["playerctl", "previous"], timeout=3)
                return "Lagu/media sebelumnya."
            return f"Tindakan media '{action}' tidak sah."
        except Exception as e:
            return f"Ralat kawalan media: {e}"

    elif name == "jarvis_app_launch":
        app = arguments.get("app", "").lower().strip()
        extra_args = arguments.get("args", "").strip()
        cmd = None
        env = os.environ.copy()
        env["DISPLAY"] = env.get("DISPLAY", ":0")
        env["XAUTHORITY"] = env.get("XAUTHORITY", "/home/faiz/.Xauthority")

        if app in ["brave", "browser"]:
            target_url = extra_args if extra_args else "http://localhost:20128"
            cmd = ["brave-browser", target_url]
        elif app in ["thunar", "files", "explorer"]:
            target_dir = extra_args if extra_args else "/home/faiz"
            cmd = ["thunar", target_dir]
        elif app in ["kodi"]:
            cmd = ["kodi"]
        elif app in ["htop"]:
            cmd = ["xfce4-terminal", "--title=htop", "-e", "htop"]
        elif app in ["terminal", "shell"]:
            cmd = ["xfce4-terminal"]
        else:
            cmd = [app] + (extra_args.split() if extra_args else [])

        try:
            subprocess.Popen(cmd, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            _send_ipc("LOG", f"🚀 [Buka Aplikasi]: {' '.join(cmd)}")
            return f"Aplikasi '{app}' berjaya dilancarkan pada skrin desktop."
        except Exception as e:
            return f"Ralat melancarkan aplikasi '{app}': {e}"

    elif name == "jarvis_action_call":
        act_name = arguments.get("action_name", "").strip()
        params = arguments.get("parameters", {})
        try:
            if "/home/faiz/Jarvis" not in sys.path:
                sys.path.insert(0, "/home/faiz/Jarvis")
            mod = importlib.import_module(f"actions.{act_name}")
            tool = getattr(mod, "TOOL", None)
            if not tool or "handler" not in tool:
                return f"Modul actions.{act_name} tidak mengandungi fungsi TOOL handler yang sah."
            res = tool["handler"](parameters=params)
            return str(res)
        except Exception as e:
            return f"Ralat memanggil tindakan JARVIS '{act_name}': {e}"

    elif name == "jarvis_service_control":
        svc = arguments.get("service", "").strip()
        action = arguments.get("action", "status").strip()
        allowed_svcs = ["9router", "jarvis-telegram", "cloudflared", "cron", "bluetooth"]
        if svc not in allowed_svcs:
            return f"Perkhidmatan '{svc}' tidak dibenarkan. Pilihan sah: {', '.join(allowed_svcs)}"
        try:
            if action == "status":
                p = subprocess.run(["systemctl", "status", svc], capture_output=True, text=True, timeout=5)
                lines = [l.strip() for l in p.stdout.split("\n") if l.strip()]
                return "\n".join(lines[:8]) if lines else "Tiada maklumat status."
            elif action in ["restart", "start", "stop"]:
                subprocess.run(["sudo", "systemctl", action, svc], timeout=10)
                return f"Perkhidmatan '{svc}' telah diarahkan untuk '{action}'."
        except Exception as e:
            return f"Ralat kawalan perkhidmatan: {e}"

    elif name == "jarvis_memory_save":
        k = arguments.get("key", "").strip()
        c = arguments.get("content", "").strip()
        try:
            mem = {}
            if MEMORY_PATH.exists():
                with open(MEMORY_PATH, "r", encoding="utf-8") as f:
                    mem = json.load(f)
            mem[k] = c
            with open(MEMORY_PATH, "w", encoding="utf-8") as f:
                json.dump(mem, f, indent=2, ensure_ascii=False)
            _send_ipc("LOG", f"📝 [Memori Disimpan]: {k}")
            return f"Memori '{k}' berjaya disimpan ke sistem JARVIS."
        except Exception as e:
            return f"Ralat menyimpan memori: {e}"

    elif name == "jarvis_memory_search":
        q = arguments.get("query", "").strip().lower()
        try:
            if not MEMORY_PATH.exists():
                return "Pangkalan memori kosong."
            with open(MEMORY_PATH, "r", encoding="utf-8") as f:
                mem = json.load(f)
            matched = {k: v for k, v in mem.items() if q in k.lower() or q in str(v).lower()}
            if not matched:
                return f"Tiada memori ditemui untuk carian '{q}'."
            return json.dumps(matched, indent=2, ensure_ascii=False)
        except Exception as e:
            return f"Ralat mencari memori: {e}"

    elif name == "jarvis_play_video_tv":
        p = arguments.get("prompt", "")
        sub = arguments.get("subtitle", "Dihasilkan Secara Pintar oleh JARVIS")
        try:
            sys.path.insert(0, "/home/faiz")
            from Jarvis.core.video_engine import generate_motion_video, play_video_on_tv
            res = generate_motion_video(p, sub)
            if res.get("ok"):
                vpath = res["video_path"]
                play_video_on_tv(vpath)
                return f"Video 1080p berjaya dijana ({vpath}) dan sedang dimainkan di TV HDMI."
            return f"Gagal menjana video: {res.get('error')}"
        except Exception as e:
            return f"Ralat enjin video: {e}"

    return f"Alat '{name}' tidak dikenali."

# ─── JSON-RPC 2.0 MCP Protocol Loop ──────────────────────────────────────────

def main():
    while True:
        try:
            line = sys.stdin.readline()
            if not line:
                break
            line = line.strip()
            if not line:
                continue

            req = json.loads(line)
            req_id = req.get("id")
            method = req.get("method")
            params = req.get("params", {})

            if method == "initialize":
                resp = {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": {
                        "protocolVersion": "2024-11-05",
                        "capabilities": {
                            "tools": {}
                        },
                        "serverInfo": {
                            "name": "jarvis-mcp",
                            "version": "1.1.0"
                        }
                    }
                }
                sys.stdout.write(json.dumps(resp) + "\n")
                sys.stdout.flush()

            elif method == "notifications/initialized":
                pass

            elif method == "ping":
                resp = {"jsonrpc": "2.0", "id": req_id, "result": {}}
                sys.stdout.write(json.dumps(resp) + "\n")
                sys.stdout.flush()

            elif method == "tools/list":
                resp = {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": {
                        "tools": TOOLS
                    }
                }
                sys.stdout.write(json.dumps(resp) + "\n")
                sys.stdout.flush()

            elif method == "tools/call":
                tool_name = params.get("name")
                tool_args = params.get("arguments", {})
                tool_res = call_tool(tool_name, tool_args)

                resp = {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": {
                        "content": [
                            {
                                "type": "text",
                                "text": tool_res
                            }
                        ]
                    }
                }
                sys.stdout.write(json.dumps(resp) + "\n")
                sys.stdout.flush()

            else:
                if req_id is not None:
                    resp = {
                        "jsonrpc": "2.0",
                        "id": req_id,
                        "error": {
                            "code": -32601,
                            "message": f"Method '{method}' not found"
                        }
                    }
                    sys.stdout.write(json.dumps(resp) + "\n")
                    sys.stdout.flush()

        except Exception as e:
            pass

if __name__ == "__main__":
    main()
