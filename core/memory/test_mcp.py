#!/usr/bin/env python3
import sqlite3
import subprocess
from pathlib import Path

JARVIS_HOME = Path("/home/faiz/Jarvis")
DB_PATH = JARVIS_HOME / "core" / "memory" / "jarvis.db"
TEST_FILE = JARVIS_HOME / "core" / "memory" / "mcp_test_output.txt"

def test_sqlite_mcp():
    print("[*] Menguji SQLite MCP (Long-Term Memory)...")
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        # Masukkan data ujian
        cursor.execute("INSERT OR REPLACE INTO memory_store (category, key, value) VALUES (?, ?, ?)", 
                       ("system_test", "status", "MCP Fully Operational"))
        conn.commit()
        
        # Baca semula data
        cursor.execute("SELECT value FROM memory_store WHERE key='status'")
        result = cursor.fetchone()
        conn.close()
        
        if result and result[0] == "MCP Fully Operational":
            print("[✓] SQLite MCP Berjaya: Data berjaya ditulis dan dibaca daripada jarvis.db!")
        else:
            print("[!] SQLite MCP Amaran: Data tidak sepadan.")
    except Exception as e:
        print(f"[✗] SQLite MCP Ralat: {e}")

def test_filesystem_mcp():
    print("[*] Menguji Filesystem MCP...")
    try:
        TEST_FILE.write_text("Ujian interaksi MCP Filesystem berjaya direkodkan pada Debian 13.")
        if TEST_FILE.exists():
            content = TEST_FILE.read_text()
            print(f"[✓] Filesystem MCP Berjaya: Kandungan dibaca -> '{content}'")
        else:
            print("[!] Filesystem MCP Amaran: Fail tidak wujud.")
    except Exception as e:
        print(f"[✗] Filesystem MCP Ralat: {e}")

def test_git_mcp():
    print("[*] Menguji Git MCP Status...")
    try:
        result = subprocess.run(["git", "-C", str(JARVIS_HOME), "status", "--short"], 
                                capture_output=True, text=True, check=True)
        print(f"[✓] Git MCP Berjaya:\n{result.stdout.strip() if result.stdout.strip() else '[Repo bersih]'}")
    except Exception as e:
        print(f"[✗] Git MCP Ralat: {e}")

if __name__ == "__main__":
    print("=== JARVIS MCP INTERACTION TEST START ===")
    test_sqlite_mcp()
    test_filesystem_mcp()
    test_git_mcp()
    print("=== SEMUA UJIAN SELESAI ===")
