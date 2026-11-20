#!/usr/bin/env python3
import json
import os
from pathlib import Path

JARVIS_HOME = Path("/home/faiz/Jarvis")
CONFIG_DIR = JARVIS_HOME / "core" / "config"
CONFIG_DIR.mkdir(parents=True, exist_ok=True)

mcp_config_path = CONFIG_DIR / "mcp_servers.json"

mcp_servers = {
    "mcpServers": {
        "filesystem": {
            "command": "npx",
            "args": ["-y", "@modelcontextprotocol/server-filesystem", str(JARVIS_HOME)]
        },
        "git": {
            "command": "npx",
            "args": ["-y", "@modelcontextprotocol/server-git", str(JARVIS_HOME)]
        },
        "sqlite": {
            "command": "npx",
            "args": ["-y", "@modelcontextprotocol/server-sqlite", str(JARVIS_HOME / "core" / "memory" / "jarvis.db")]
        },
        "puppeteer": {
            "command": "npx",
            "args": ["-y", "@modelcontextprotocol/server-puppeteer"]
        },
        "docker": {
            "command": "docker",
            "args": ["run", "-i", "--rm", "-v", "/var/run/docker.sock:/var/run/docker.sock", "mcp/docker"]
        }
    }
}

def main():
    print(f"[*] Menulis konfigurasi MCP ke {mcp_config_path}...")
    with open(mcp_config_path, "w") as f:
        json.dump(mcp_servers, f, indent=4)
    
    print("[✓] Konfigurasi MCP Berjaya Direkodkan!")
    print("[*] Seterusnya, pastikan Node.js & Docker aktif pada Debian 13 untuk jalankan server ini.")

if __name__ == "__main__":
    main()
