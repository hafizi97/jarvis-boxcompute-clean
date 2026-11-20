#!/usr/bin/env python3
"""
Git Version Control MCP Server for OpenCode
Provides structured, safe Git repository operations:
- git_status (Branch, staged, unstaged, untracked)
- git_diff (Unified diff with line truncation protection)
- git_commit (Safe staging & commit with message)
- git_log (Recent commit history)
- git_branch (List, create, or switch branches)
- git_checkpoint (Create safety snapshot before making changes)
- git_rollback (Instantly restore codebase to last checkpoint)
"""

import sys
import json
import os
import subprocess
from pathlib import Path

DEFAULT_REPO = "/home/faiz/Jarvis"
IPC_SOCK = "/tmp/jarvis_ipc.sock"

def _send_ipc(prefix: str, text: str) -> bool:
    try:
        if os.path.exists(IPC_SOCK):
            import socket
            with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as s:
                s.settimeout(1.0)
                s.connect(IPC_SOCK)
                s.sendall(f"{prefix}:{text}\n".encode("utf-8"))
            return True
    except Exception:
        pass
    return False


def _run_git(args: list, cwd: str = None) -> tuple:
    work_dir = cwd if cwd and os.path.exists(cwd) else DEFAULT_REPO
    try:
        p = subprocess.run(
            ["git"] + args,
            cwd=work_dir,
            capture_output=True,
            text=True,
            timeout=15
        )
        return p.returncode, p.stdout.strip(), p.stderr.strip()
    except Exception as e:
        return 1, "", str(e)

TOOLS = [
    {
        "name": "git_status",
        "description": "Dapatkan status repositori Git terkini (cawangan semasa, fail diubah suai, fail staged, dan fail baharu).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "repo_path": {
                    "type": "string",
                    "description": "Laluan direktori repositori Git (lalai: '/home/faiz/Jarvis')."
                }
            }
        }
    },
    {
        "name": "git_diff",
        "description": "Dapatkan perbezaan kod (diff) bagi perubahan fail yang belum atau sudah di-stage.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "repo_path": {
                    "type": "string",
                    "description": "Laluan direktori repositori Git."
                },
                "staged": {
                    "type": "boolean",
                    "description": "Set true untuk melihat perubahan yang sudah di-stage (--cached)."
                },
                "file_path": {
                    "type": "string",
                    "description": "Laluan fail khusus jika hanya ingin melihat diff bagi satu fail tertentu."
                },
                "max_lines": {
                    "type": "integer",
                    "description": "Had baris maksimum output diff untuk mengelakkan teks terlalu panjang (lalai: 150)."
                }
            }
        }
    },
    {
        "name": "git_checkpoint",
        "description": "Cipta titik pemulihan keselamatan (checkpoint) sebelum membuat sebarang pindaan kod besar.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "label": {
                    "type": "string",
                    "description": "Label penerangan checkpoint (contoh: 'sebelum refactor bot')."
                },
                "repo_path": {
                    "type": "string",
                    "description": "Laluan direktori repositori Git."
                }
            }
        }
    },
    {
        "name": "git_rollback",
        "description": "Pulihkan (rollback) seluruh kod projek kembali ke titik keselamatan (checkpoint) terakhir secara selamat.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "repo_path": {
                    "type": "string",
                    "description": "Laluan direktori repositori Git."
                }
            }
        }
    },
    {
        "name": "git_commit",
        "description": "Stage fail terpilih dan cipta commit baharu dengan mesej yang jelas.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "message": {
                    "type": "string",
                    "description": "Mesej commit (cth: 'feat: naik taraf mcp server')."
                },
                "files": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Senarai fail untuk di-stage. Biarkan kosong untuk 'git add -u' (semua fail diubah suai)."
                },
                "repo_path": {
                    "type": "string",
                    "description": "Laluan direktori repositori Git."
                }
            },
            "required": ["message"]
        }
    },
    {
        "name": "git_log",
        "description": "Lihat senarai sejarah commit terdahulu dalam format ringkas.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "count": {
                    "type": "integer",
                    "description": "Bilangan commit untuk dipaparkan (lalai: 5)."
                },
                "repo_path": {
                    "type": "string",
                    "description": "Laluan direktori repositori Git."
                }
            }
        }
    },
    {
        "name": "git_branch",
        "description": "Senaraikan cawangan (branches) Git atau cipta cawangan baharu.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "create": {
                    "type": "string",
                    "description": "Nama cawangan baharu untuk dicipta."
                },
                "checkout": {
                    "type": "string",
                    "description": "Nama cawangan untuk ditukar (checkout)."
                },
                "repo_path": {
                    "type": "string",
                    "description": "Laluan direktori repositori Git."
                }
            }
        }
    }
]

def call_tool(name: str, arguments: dict) -> str:
    _send_ipc("LOG", f"⚙️ [Git MCP]: Melaksanakan '{name}'...")
    repo = arguments.get("repo_path", DEFAULT_REPO)

    if name == "git_status":
        code, out, err = _run_git(["status", "-s", "-b"], cwd=repo)
        if code != 0:
            return f"Ralat git status: {err}"
        return f"Status Git ({repo}):\n{out}" if out else "Repositori bersih (tiada perubahan)."

    elif name == "git_diff":
        staged = arguments.get("staged", False)
        fpath = arguments.get("file_path")
        max_l = int(arguments.get("max_lines", 150))
        cmd = ["diff"]
        if staged:
            cmd.append("--cached")
        if fpath:
            cmd.extend(["--", fpath])
        code, out, err = _run_git(cmd, cwd=repo)
        if code != 0:
            return f"Ralat git diff: {err}"
        if not out:
            return "Tiada perbezaan dikesan."
        lines = out.split("\n")
        if len(lines) > max_l:
            return "\n".join(lines[:max_l]) + f"\n\n... (Dipotong: {len(lines) - max_l} lagi baris)"
        return out

    elif name == "git_checkpoint":
        label = arguments.get("label", "pre-opencode")
        # Check if there are changes to commit
        _run_git(["add", "-A"], cwd=repo)
        c, out, err = _run_git(["commit", "-m", f"checkpoint: {label}"], cwd=repo)
        _run_git(["tag", "-f", "opencode-checkpoint-latest"], cwd=repo)
        return f"Titik keselamatan '{label}' berjaya disimpan. Tag 'opencode-checkpoint-latest' dikemas kini."

    elif name == "git_rollback":
        c, out, err = _run_git(["rev-parse", "--verify", "opencode-checkpoint-latest"], cwd=repo)
        if c != 0:
            return "Tiada titik keselamatan (opencode-checkpoint-latest) ditemui untuk dipulihkan."
        c2, out2, err2 = _run_git(["reset", "--hard", "opencode-checkpoint-latest"], cwd=repo)
        if c2 != 0:
            return f"Ralat semasa rollback: {err2}"
        return "Kod projek berjaya dipulihkan kembali ke titik keselamatan terakhir (Rollback Selesai)."

    elif name == "git_commit":
        msg = arguments.get("message", "").strip()
        files = arguments.get("files", [])
        if not msg:
            return "Sila sertakan mesej commit."
        if files:
            for f in files:
                c, _, e = _run_git(["add", f], cwd=repo)
                if c != 0:
                    return f"Gagal add fail '{f}': {e}"
        else:
            _run_git(["add", "-u"], cwd=repo)
        code, out, err = _run_git(["commit", "-m", msg], cwd=repo)
        if code != 0:
            return f"Gagal commit: {err}"
        return f"Commit berjaya dicipta:\n{out}"

    elif name == "git_log":
        n = int(arguments.get("count", 5))
        code, out, err = _run_git(["log", f"-n{n}", "--oneline", "--graph"], cwd=repo)
        if code != 0:
            return f"Ralat git log: {err}"
        return f"Sejarah Commit ({repo}):\n{out}" if out else "Tiada rekod commit."

    elif name == "git_branch":
        create = arguments.get("create")
        checkout = arguments.get("checkout")
        if create:
            code, out, err = _run_git(["branch", create], cwd=repo)
            if code != 0:
                return f"Gagal mencipta branch: {err}"
            return f"Branch '{create}' berjaya dicipta."
        elif checkout:
            code, out, err = _run_git(["checkout", checkout], cwd=repo)
            if code != 0:
                return f"Gagal checkout: {err}"
            return f"Berjaya bertukar ke branch '{checkout}'."
        else:
            code, out, err = _run_git(["branch", "-a"], cwd=repo)
            if code != 0:
                return f"Ralat menyenaraikan branch: {err}"
            return f"Senarai Branch ({repo}):\n{out}"

    return f"Alat '{name}' tidak dikenali."

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
                        "capabilities": {"tools": {}},
                        "serverInfo": {"name": "git-mcp", "version": "1.1.0"}
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
                    "result": {"tools": TOOLS}
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
                        "content": [{"type": "text", "text": tool_res}]
                    }
                }
                sys.stdout.write(json.dumps(resp) + "\n")
                sys.stdout.flush()

            else:
                if req_id is not None:
                    resp = {
                        "jsonrpc": "2.0",
                        "id": req_id,
                        "error": {"code": -32601, "message": f"Method '{method}' not found"}
                    }
                    sys.stdout.write(json.dumps(resp) + "\n")
                    sys.stdout.flush()

        except Exception as e:
            pass

if __name__ == "__main__":
    main()
