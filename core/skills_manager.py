import os
import json
from typing import Dict, List, Optional

SKILLS_ROOT = "/home/faiz/Jarvis/skills"
CATALOG_PATH = os.path.join(SKILLS_ROOT, "skills_catalog.json")

SUITE_INFO = {
    "superpowers": {
        "title": "⚡ Superpowers (Obra)",
        "cmd": "/skills superpowers",
        "desc": "TDD, systematic debugging, brainstorm, dev branch, plans",
        "aliases": ["superpower", "superpowers", "tdd", "debugging"]
    },
    "karpathy": {
        "title": "🧠 Karpathy Guidelines",
        "cmd": "/skills karpathy",
        "desc": "Surgical changes, think before coding, minimize complexity",
        "aliases": ["karpathy", "andrej", "guidelines"]
    },
    "anthropic": {
        "title": "🎨 Frontend Design & Anthropic",
        "cmd": "/skills frontend",
        "desc": "Distinctive typography, UI styling, artifacts, PDF, PPTX",
        "aliases": ["frontend", "anthropic", "design", "ui", "pdf", "pptx", "xlsx"]
    },
    "impeccable": {
        "title": "💎 Impeccable Craft (Paul Bakaus)",
        "cmd": "/skills impeccable",
        "desc": "World-class frontend craft, design systems, UI audit, polish",
        "aliases": ["impeccable", "craft", "bakaus", "polish"]
    },
    "taste-skill": {
        "title": "👁 Leon Taste Skill",
        "cmd": "/skills taste",
        "desc": "Aesthetic judgment, design critique, visual taste rules for AI",
        "aliases": ["taste", "taste-skill", "aesthetic"]
    },
    "ui-ux-pro-max": {
        "title": "✨ UI/UX Pro Max",
        "cmd": "/skills uipro",
        "desc": "Pro design systems, UI styling, banners, brand guidelines, slides",
        "aliases": ["uipro", "ui-ux-pro-max", "uimax", "design-system"]
    },
    "remotion": {
        "title": "🎬 Remotion Video Suite",
        "cmd": "/skills remotion",
        "desc": "Programmatic React video creation, rendering, captions, studio",
        "aliases": ["remotion", "react-video"]
    },
    "hyperframes": {
        "title": "🎞 HeyGen HyperFrames",
        "cmd": "/skills hyperframes",
        "desc": "Motion graphics, title cards, orbital animations, audio visuals",
        "aliases": ["hyperframes", "heygen", "motion", "frames"]
    },
    "video-toolkit": {
        "title": "📹 Video Production Toolkit",
        "cmd": "/skills video",
        "desc": "FFmpeg transcoding, Playwright screen record, ElevenLabs, Blender",
        "aliases": ["video", "video-toolkit", "ffmpeg", "elevenlabs", "blender"]
    },
    "mrjonesbot": {
        "title": "🎙 MrJones Episode & Production",
        "cmd": "/skills episode",
        "desc": "Produce-episode, rough-cut AI timeline, image optimization, SEO",
        "aliases": ["episode", "roughcut", "rough-cut", "mrjones", "mrjonesbot"]
    },
    "one-skill": {
        "title": "👑 One Skill to Rule Them All",
        "cmd": "/skills oneskill",
        "desc": "Task observer: turns user corrections into permanent skill improvements",
        "aliases": ["oneskill", "one-skill", "observer", "task-observer"]
    },
    "claude-mem": {
        "title": "🧠 OpenCode Persistent Memory",
        "cmd": "/skills mem",
        "desc": "Cross-session memory, timeline reports, codebase knowledge, digests",
        "aliases": ["mem", "claude-mem", "memory"]
    },
    "vercel-skills": {
        "title": "▲ Vercel Skills Ecosystem",
        "cmd": "/skills vercel",
        "desc": "Find-skills discovery engine, PR triage, Next.js agent workflows",
        "aliases": ["vercel", "vercel-skills", "findskills", "find-skills"]
    },
    "gsd": {
        "title": "📦 Get-Shit-Done (GSD)",
        "cmd": "/skills gsd",
        "desc": "Spec-driven autonomous coding, phase planner, forensics",
        "aliases": ["gsd", "get-shit-done"]
    },
    "mattpocock": {
        "title": "🛠 Matt Pocock Skills",
        "cmd": "/skills mattpocock",
        "desc": "Ask-Matt, TypeScript architecture, diagnosing bugs, grill-me",
        "aliases": ["matt", "mattpocock", "pocock", "typescript"]
    },
    "ponytail": {
        "title": "🎀 Ponytail Audit",
        "cmd": "/skills ponytail",
        "desc": "Code debt, audit, reviews, gain analysis",
        "aliases": ["ponytail", "debt"]
    },
    "security-audit": {
        "title": "🛡 Toshipon Security Audit",
        "cmd": "/skills sec-audit",
        "desc": "Automated security audits and vulnerability checks for OpenCode",
        "aliases": ["sec-audit", "security-audit", "toshipon"]
    },
    "hackers-hate-this": {
        "title": "🥷 Hackers Hate This (AppSec)",
        "cmd": "/skills hackers",
        "desc": "Backend hardening, pentest, SQL/NoSQL injection, JWT/RBAC audit",
        "aliases": ["hackers", "hackers-hate-this", "pentest", "harden", "injection"]
    },
    "hashicorp": {
        "title": "☁️ HashiCorp Agent Skills",
        "cmd": "/skills hashicorp",
        "desc": "Terraform modules/test/import, Packer image builders (AWS/Azure/Win)",
        "aliases": ["hashicorp", "terraform", "packer", "iac"]
    },
    "context7": {
        "title": "📑 Upstash Context7",
        "cmd": "/skills context7",
        "desc": "Context-aware docs retrieval, real-time library documentation search",
        "aliases": ["context7", "upstash", "docs"]
    },
    "graphify": {
        "title": "🕸 Graphify Knowledge Graph",
        "cmd": "/skills graphify",
        "desc": "Codebase relationship mapping, community detection, GraphRAG JSON",
        "aliases": ["graphify", "graph", "knowledge-graph", "codebase-map"]
    },
    "gstack": {
        "title": "🚀 Garry Tan Gstack",
        "cmd": "/skills gstack",
        "desc": "Full startup stack: browse, design, verify, ship, QA, review, retro",
        "aliases": ["gstack", "garrytan", "ship", "qa"]
    },
    "agent-browser": {
        "title": "🌐 Vercel Agent-Browser",
        "cmd": "/skills browser",
        "desc": "Browser automation, web MCP interaction, DOM inspection",
        "aliases": ["browser", "agent-browser", "vercel-browser", "web"]
    },
    "mcp-servers": {
        "title": "🔌 Model Context Protocol (MCP)",
        "cmd": "/skills mcp",
        "desc": "Official MCP servers: filesystem, git, github, postgres, sqlite",
        "aliases": ["mcp", "mcp-servers", "modelcontextprotocol"]
    },
    "wshobson-agents": {
        "title": "🤖 Wshobson Agents Suite",
        "cmd": "/skills agents",
        "desc": "180+ multi-agent workflows, code documentation, orchestration",
        "aliases": ["agents", "wshobson", "wshobson-agents", "workflows"]
    },
    "tresor": {
        "title": "🔐 OpenCode Trésor",
        "cmd": "/skills tresor",
        "desc": "Secret scanner, dependency auditor, security auditor, git helper",
        "aliases": ["tresor", "secrets", "scanner"]
    },
    "cto-toolkit": {
        "title": "👔 CTO Toolkit",
        "cmd": "/skills cto",
        "desc": "Architecture board, tech debt, team scaling, metrics, chaos eng, cost",
        "aliases": ["cto", "cto-toolkit", "architecture", "scaling"]
    },
    "claude-skills": {
        "title": "🏢 OpenCode Skills Suite",
        "cmd": "/skills opencode",
        "desc": "480+ skills in engineering, product, project management, marketing",
        "aliases": ["claude", "claude-skills", "marketing", "pm", "product"]
    }
}

def load_catalog() -> Dict[str, List[dict]]:
    if not os.path.exists(CATALOG_PATH):
        return {}
    try:
        with open(CATALOG_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}

def get_stats() -> dict:
    catalog = load_catalog()
    return {
        "total_suites": len(catalog),
        "total_skills": sum(len(skills) for skills in catalog.values()),
        "breakdown": {k: len(v) for k, v in catalog.items()}
    }

def search_skills(query: str, limit: int = 15) -> List[dict]:
    query = query.lower().strip()
    catalog = load_catalog()
    results = []
    
    for suite, skills in catalog.items():
        for s in skills:
            name = s.get("name", "").lower()
            desc = s.get("description", "").lower()
            if query in name or query in desc or query in suite.lower():
                item = s.copy()
                item["suite"] = suite
                results.append(item)
                if len(results) >= limit:
                    return results
    return results

def format_telegram_skills_response(query: Optional[str] = None) -> str:
    catalog = load_catalog()
    if not catalog:
        return "⚠️ Pangkalan data kemahiran (skills) JARVIS belum dimuatkan."
    
    if not query:
        total = sum(len(v) for v in catalog.values())
        msg = [
            "🧩 *JARVIS & OPENCODE AI KEMAHIRAN (SKILLS)* 🚀",
            f"Jumlah Kemahiran Aktif: *{total} Kemahiran* merentasi *{len(catalog)} Koleksi*.",
            "",
            "📚 *Senarai Koleksi Kemahiran Utama:*"
        ]
        
        idx = 1
        for suite_key, info in SUITE_INFO.items():
            count = len(catalog.get(suite_key, []))
            msg.append(f"{idx}. {info['title']} ({count}) - `{info['cmd']}`")
            msg.append(f"   _{info['desc']}_")
            idx += 1
            
        msg.extend([
            "",
            "💡 *Cara Menggunakan Kemahiran:*",
            "• Cari kemahiran: `/skills <kata_kunci>` (cth: `/skills impeccable`, `/skills mem`, `/skills oneskill`)",
            "• Jalankan tugasan dengan OpenCode: `/opencode guna skill <nama_skill> untuk <tindakan>`"
        ])
        return "\n".join(msg)
    
    # Pencarian mengikut suite atau kata kunci
    q = query.lower().strip()
    
    # Check suite alias match
    matched_suite = None
    for suite_key, info in SUITE_INFO.items():
        if q == suite_key or q in info["aliases"]:
            matched_suite = suite_key
            break
            
    if matched_suite and matched_suite in catalog:
        suite_skills = catalog[matched_suite]
        info = SUITE_INFO.get(matched_suite, {"title": matched_suite.upper()})
        msg = [
            f"📦 *KOLEKSI KEMAHIRAN: {info.get('title', matched_suite.upper())}* ({len(suite_skills)} kemahiran)",
            ""
        ]
        for idx, s in enumerate(suite_skills[:15], 1):
            desc = s.get("description", "")
            if desc:
                msg.append(f"{idx}. `/{s['name']}`\n   _{desc}_")
            else:
                msg.append(f"{idx}. `/{s['name']}`")
        if len(suite_skills) > 15:
            msg.append(f"\n... dan {len(suite_skills) - 15} lagi kemahiran dalam koleksi ini.")
        msg.append("\n💡 *Gunakan dalam arahan:* `/opencode [arahan anda]`")
        return "\n".join(msg)
    
    # Pencarian kata kunci umum
    matches = search_skills(q, limit=12)
    if not matches:
        return f"🔍 Tiada kemahiran ditemui untuk kata kunci: `{query}`.\nCuba cari perkataan lain seperti: `impeccable`, `memory`, `remotion`, `video`, `taste`, `design`, `security`."
    
    msg = [f"🔍 *HASIL CARIAN KEMAHIRAN UNTUK:* `{query}` ({len(matches)} ditemui)", ""]
    for idx, m in enumerate(matches, 1):
        msg.append(f"{idx}. *{m['name']}* [{m['suite']}]\n   _{m['description']}_")
    
    msg.append("\n💡 *Gunakan dalam arahan:* `/opencode [arahan anda]`")
    return "\n".join(msg)

if __name__ == "__main__":
    print(get_stats())
    print("\n--- Impeccable query ---")
    print(format_telegram_skills_response("impeccable"))
    print("\n--- Claude Mem query ---")
    print(format_telegram_skills_response("mem"))
    print("\n--- One-skill query ---")
    print(format_telegram_skills_response("oneskill"))
