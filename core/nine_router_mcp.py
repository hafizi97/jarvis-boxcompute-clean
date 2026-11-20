#!/usr/bin/env python3
"""
9Router AI MCP Server for OpenCode
Exposes 9Router AI & Web capabilities directly to OpenCode:
- Real-time Web Search (Web & News)
- Web Fetch & Scraper (URL to Markdown extraction)
- Image Generation (Gemini Imagen, FLUX, DALL-E)
- Video Generation (xAI Grok Imagine)
- Active Models Discovery
"""

import sys
import json
import os
import urllib.request
import urllib.parse
import subprocess
import time
import re
from pathlib import Path

ROUTER_URL = os.environ.get("NINEROUTER_URL", "http://127.0.0.1:20128")
ROUTER_KEY = os.environ.get("NINEROUTER_KEY", "sk-eba49bed4ad933fe-3ux51u-e90d2ed3")
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


# ─── Helper Functions ────────────────────────────────────────────────────────

def _http_request(endpoint: str, data: dict = None, method: str = "GET", timeout: int = 30) -> dict:
    url = f"{ROUTER_URL.rstrip('/')}{endpoint}"
    headers = {
        "Authorization": f"Bearer {ROUTER_KEY}",
        "Content-Type": "application/json"
    }
    body = json.dumps(data).encode("utf-8") if data is not None else None
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        content = resp.read().decode("utf-8", errors="replace")
        try:
            return json.loads(content)
        except Exception:
            return {"raw": content}

def _search_web(query: str, max_results: int = 5) -> list:
    """Fallback search using DuckDuckGo Search library."""
    results = []
    try:
        from duckduckgo_search import DDGS
        with DDGS() as ddgs:
            for r in ddgs.text(query, max_results=max_results):
                results.append({
                    "title": r.get("title", ""),
                    "snippet": r.get("body", ""),
                    "url": r.get("href", "")
                })
    except Exception as e:
        # Simple HTML fallback
        try:
            url = f"https://html.duckduckgo.com/html/?q={urllib.parse.quote(query)}"
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=10) as resp:
                html = resp.read().decode("utf-8", errors="replace")
                matches = re.findall(r'<a class="result__snippet[^>]*href="([^"]+)"[^>]*>(.*?)</a>', html)
                for href, snip in matches[:max_results]:
                    clean_snip = re.sub(r'<[^>]+>', '', snip)
                    results.append({"title": clean_snip[:60], "snippet": clean_snip, "url": href})
        except Exception:
            pass
    return results

def _fetch_url_markdown(url: str, max_chars: int = 8000) -> str:
    """Ekstrak teks bersih daripada mana-mana pautan web."""
    # First attempt 9Router web fetch
    try:
        res = _http_request("/v1/web/fetch", data={"model": "ollama", "url": url, "format": "markdown"}, method="POST", timeout=20)
        if isinstance(res, dict) and "content" in res:
            c = res["content"]
            txt = c.get("text", "") if isinstance(c, dict) else str(c)
            if txt:
                return txt[:max_chars]
    except Exception:
        pass

    # Direct fallback via curl / lynx / urllib
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            html = resp.read().decode("utf-8", errors="replace")
            # Strip script and style
            html = re.sub(r'<script.*?</script>', '', html, flags=re.DOTALL | re.IGNORECASE)
            html = re.sub(r'<style.*?</style>', '', html, flags=re.DOTALL | re.IGNORECASE)
            text = re.sub(r'<[^>]+>', ' ', html)
            lines = [l.strip() for l in text.split("\n") if l.strip()]
            clean_text = "\n".join(lines)
            return clean_text[:max_chars]
    except Exception as e:
        return f"Gagal mengekstrak kandungan URL: {e}"

# ─── Tool Definitions ────────────────────────────────────────────────────────

TOOLS = [
    {
        "name": "9router_web_search",
        "description": "Lakukan carian web masa nyata untuk mendapatkan fakta, dokumentasi, berita terkini, atau rujukan teknikal.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Kata kunci carian maklumat di internet."
                },
                "max_results": {
                    "type": "integer",
                    "description": "Bilangan hasil carian maksimum (lalai: 5)."
                }
            },
            "required": ["query"]
        }
    },
    {
        "name": "9router_web_fetch",
        "description": "Ambil dan ekstrak kandungan penuh sesuatu laman web (URL) ke dalam format teks/Markdown bersih.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "url": {
                    "type": "string",
                    "description": "Pautan URL laman web atau dokumentasi yang ingin dibaca."
                },
                "max_characters": {
                    "type": "integer",
                    "description": "Had maksimum aksara kandungan (lalai: 8000)."
                }
            },
            "required": ["url"]
        }
    },
    {
        "name": "9router_generate_image",
        "description": "Jana imej berkualiti tinggi menggunakan model Imagen / FLUX / DALL-E melalui 9Router AI dan simpan ke fail tempatan.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "prompt": {
                    "type": "string",
                    "description": "Penerangan deskriptif imej yang ingin dijana."
                },
                "model": {
                    "type": "string",
                    "description": "Nama model imej (contoh: 'ag/gemini-3.1-flash-image' atau 'gemini/gemini-3-pro-image-preview')."
                },
                "output_path": {
                    "type": "string",
                    "description": "Laluan fail gambar simpanan (lalai: '/tmp/generated_image.png')."
                }
            },
            "required": ["prompt"]
        }
    },
    {
        "name": "9router_list_models",
        "description": "Dapatkan senarai model AI aktif yang tersedia pada gerbang 9Router tempatan (Chat, Imej, Suara, Video).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "kind": {
                    "type": "string",
                    "description": "Kategori model: 'all', 'chat', 'image', 'tts', 'web', 'video'.",
                    "enum": ["all", "chat", "image", "tts", "web", "video"]
                }
            }
        }
    }
]

# ─── Tool Execution ──────────────────────────────────────────────────────────

def call_tool(name: str, arguments: dict) -> str:
    _send_ipc("LOG", f"⚙️ [9Router MCP]: Melaksanakan '{name}'...")
    if name == "9router_web_search":
        q = arguments.get("query", "").strip()
        n = int(arguments.get("max_results", 5))
        if not q:
            return "Sila masukkan kata kunci carian."
        results = _search_web(q, max_results=n)
        if not results:
            return f"Tiada hasil carian ditemui untuk: '{q}'."
        out = [f"Hasil carian web untuk: '{q}':\n"]
        for idx, r in enumerate(results, 1):
            out.append(f"{idx}. {r['title']}\n   Pautan: {r['url']}\n   Ringkasan: {r['snippet']}\n")
        return "\n".join(out)

    elif name == "9router_web_fetch":
        url = arguments.get("url", "").strip()
        limit = int(arguments.get("max_characters", 8000))
        if not url:
            return "Sila masukkan pautan URL."
        return _fetch_url_markdown(url, max_chars=limit)

    elif name == "9router_generate_image":
        prompt = arguments.get("prompt", "").strip()
        model = arguments.get("model", "ag/gemini-3.1-flash-image")
        out_path = arguments.get("output_path", "/tmp/generated_image.png")
        if not prompt:
            return "Sila masukkan penerangan prompt imej."
        try:
            req_data = {
                "model": model,
                "prompt": prompt,
                "size": "1024x1024",
                "response_format": "url"
            }
            res = _http_request("/v1/images/generations", data=req_data, method="POST", timeout=60)
            if "data" in res and len(res["data"]) > 0:
                img_url = res["data"][0].get("url")
                if img_url:
                    urllib.request.urlretrieve(img_url, out_path)
                    return f"Imej berjaya dijana dan disimpan ke '{out_path}' (Model: {model})."
                b64 = res["data"][0].get("b64_json")
                if b64:
                    import base64
                    with open(out_path, "wb") as f:
                        f.write(base64.b64decode(b64))
                    return f"Imej berjaya dijana dan disimpan ke '{out_path}'."
            return f"9Router membalas tanpa fail imej: {res}"
        except Exception as e:
            return f"Ralat menjana imej 9Router: {e}"

    elif name == "9router_list_models":
        k = arguments.get("kind", "all")
        endpoints = {
            "chat": "/v1/models",
            "image": "/v1/models/image",
            "tts": "/v1/models/tts",
            "web": "/v1/models/web",
            "video": "/v1/models/video"
        }
        res_summary = {}
        targets = [k] if k != "all" else list(endpoints.keys())
        for t in targets:
            ep = endpoints.get(t)
            if ep:
                try:
                    res = _http_request(ep)
                    if "data" in res:
                        res_summary[t] = [m.get("id") for m in res["data"] if "id" in m]
                except Exception:
                    pass
        return json.dumps(res_summary, indent=2)

    return f"Alat '{name}' tidak dikenali."

# ─── JSON-RPC 2.0 Loop ───────────────────────────────────────────────────────

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
                        "serverInfo": {"name": "9router-mcp", "version": "1.0.0"}
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
