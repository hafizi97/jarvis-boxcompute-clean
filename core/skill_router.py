#!/usr/bin/env python3
"""
JARVIS Skill Router & Orchestrator
Automatically analyzes user intent and routes prompts to specialized skills:
  - UI/UX and Frontend: impeccable, frontend-design, taste-skill, ui-ux-pro-max
  - Debug and TDD: systematic-debugging, karpathy-guidelines, test-driven-development
  - Security and Audit: hackers-hate-this, security-audit, tresor-scanner
  - Video and Media: remotion-create, hyperframes, ffmpeg, video-toolkit
  - Architecture: gsd-plan-phase, cto-toolkit
  - Default: karpathy-guidelines (surgical edits, simplicity, verify assumptions)
Also manages synchronization of Claude Code sessions with Jarvis Conversational Memory.
"""

import os
import re
import json
import datetime
from pathlib import Path
from typing import Tuple, List, Dict, Any, Optional

SESSIONS_FILE = Path("/home/faiz/Jarvis/memory/opencode_sessions.json")
LEGACY_SESSIONS_FILE = Path("/home/faiz/Jarvis/memory/claude_sessions.json")
SESSIONS_FILE.parent.mkdir(parents=True, exist_ok=True)

# Domain intent keywords and corresponding skills
INTENT_RULES = [
    {
        "category": "🎨 UI/UX & Frontend Craft",
        "key": "ui",
        "keywords": [
            "ui", "ux", "frontend", "front-end", "design", "css", "html", "tailwind",
            "react", "tampilan", "butang", "warna", "cantik", "kemas", "dashboard",
            "landing page", "komponen", "component", "typography", "font", "responsif",
            "dark mode", "theme", "layout", "nav", "modal", "animation"
        ],
        "skills": ["impeccable", "frontend-design", "taste-skill", "ui-ux-pro-max"],
        "instruction": (
            "Apply world-class frontend design and craft guidelines from `impeccable`, "
            "`frontend-design`, and `taste-skill`: ensure distinctive visual hierarchy, "
            "polished spacing, intentional typography, and high aesthetic refinement."
        )
    },
    {
        "category": "⚡ Systematic Debugging & TDD",
        "key": "debug",
        "keywords": [
            "bug", "error", "ralat", "fail", "baiki", "fix", "debug", "crash",
            "test", "tdd", "refactor", "masalah", "rosak", "exception", "broken",
            "stacktrace", "panik", "freeze", "hang"
        ],
        "skills": ["systematic-debugging", "karpathy-guidelines", "test-driven-development"],
        "instruction": (
            "Follow systematic debugging principles from `superpowers` and `karpathy-guidelines`: "
            "first reproduce and trace root cause with verifiable evidence before modifying code, "
            "make minimal surgical changes, and verify with tests without breaking existing functions."
        )
    },
    {
        "category": "🛡 Keselamatan & AppSec Audit",
        "key": "security",
        "keywords": [
            "security", "audit", "keselamatan", "vulnerability", "hack", "pentest",
            "harden", "injection", "xss", "csrf", "auth", "jwt", "token", "leak",
            "tresor", "secret", "permission", "cors", "dos", "sanitize"
        ],
        "skills": ["hackers-hate-this", "security-audit", "tresor-scanner"],
        "instruction": (
            "Apply rigorous security audit standards from `hackers-hate-this` and `security-audit`: "
            "thoroughly check input validation, authentication, authorization, secret exposure, "
            "sanitization, and patch potential vulnerabilities."
        )
    },
    {
        "category": "🎬 Video & Motion Media",
        "key": "video",
        "keywords": [
            "video", "remotion", "animasi", "motion", "klip", "movie", "render",
            "hyperframes", "ffmpeg", "subtitle", "caption", "timeline", "audio",
            "transcode", "codec", "mp4"
        ],
        "skills": ["remotion-create", "hyperframes", "ffmpeg", "video-toolkit"],
        "instruction": (
            "Use Remotion and video production skills (`remotion-create`, `ffmpeg`, `hyperframes`): "
            "author modular React compositions with smooth animations, clear typography, and optimal rendering."
        )
    },
    {
        "category": "🏛️ Senibina & Perancangan (CTO/GSD)",
        "key": "architecture",
        "keywords": [
            "plan", "rancang", "senibina", "arsitektur", "architecture", "cto",
            "scaling", "roadmap", "gsd", "fasa", "phase", "spec", "milestone",
            "tech debt", "system design"
        ],
        "skills": ["gsd-plan-phase", "cto-toolkit"],
        "instruction": (
            "Follow architecture and execution guidelines from `gsd-plan-phase` and `cto-toolkit`: "
            "plan modular phases, analyze trade-offs, manage tech debt, and define explicit milestones."
        )
    },
    {
        "category": "☁️ Cloud & Infrastruktur",
        "key": "cloud",
        "keywords": [
            "cloud", "terraform", "packer", "docker", "infra", "server", "deploy",
            "container", "kubernetes", "k8s", "aws", "gcp", "azure"
        ],
        "skills": ["terraform", "packer", "context7"],
        "instruction": (
            "Follow Infrastructure as Code (IaC) and cloud architecture best practices "
            "from `terraform` and `packer`: maintain clean declarative configurations."
        )
    }
]

DEFAULT_INSTRUCTION = (
    "Think before coding, minimize unnecessary complexity, make surgical focused changes, "
    "and verify all assumptions before concluding."
)

SKILL_ROOTS = (
    Path("/home/faiz/.config/opencode/skills"),
    Path("/home/faiz/Jarvis/skills"),
)


def _skill_installed(name: str) -> bool:
    name = name.strip()
    if not name:
        return False
    for root in SKILL_ROOTS:
        if (root / name / "SKILL.md").exists() or (root / name).exists() or (root / (name + ".md")).exists():
            return True
    return False


def _sanitize_instruction(text: str, available) -> str:
    names = set(available)

    def repl(match):
        return match.group(0) if match.group(1) in names else ""

    cleaned = re.sub(r"`([^`]+)`", repl, text)
    cleaned = re.sub(r"\s*,\s*,", ",", cleaned)
    cleaned = re.sub(r",\s+and\b", " and", cleaned)
    cleaned = re.sub(r"\bfrom\s+and\b", "from the available skills", cleaned)
    cleaned = re.sub(r"\s+([,.:])", r"\1", cleaned)
    return re.sub(r"\s{2,}", " ", cleaned).strip()


def route_intent(prompt: str) -> Dict[str, Any]:
    """Keluarkan hanya kemahiran yang benar-benar dipasang pada mesin ini."""
    intent = _route_intent_raw(prompt)
    all_skills = intent.get("skills", [])
    available = [name for name in all_skills if _skill_installed(name)]
    intent["skills"] = available
    intent["skills_missing"] = [name for name in all_skills if name not in available]
    intent["instruction"] = (
        _sanitize_instruction(intent.get("instruction", ""), available) if available else ""
    )
    return intent


def _route_intent_raw(prompt: str) -> Dict[str, Any]:
    """Menilai intent teks dan memilih kategori kemahiran yang paling relevan."""
    prompt_lower = prompt.lower()
    
    # Check explicit skill mentions (e.g. "guna skill impeccable")
    if "impeccable" in prompt_lower or "taste" in prompt_lower or "uipro" in prompt_lower:
        rule = INTENT_RULES[0]
        return {"category": rule["category"], "key": rule["key"], "skills": rule["skills"], "instruction": rule["instruction"]}
    if "debug" in prompt_lower or "karpathy" in prompt_lower or "tdd" in prompt_lower:
        rule = INTENT_RULES[1]
        return {"category": rule["category"], "key": rule["key"], "skills": rule["skills"], "instruction": rule["instruction"]}
    if "security" in prompt_lower or "hackers" in prompt_lower or "tresor" in prompt_lower:
        rule = INTENT_RULES[2]
        return {"category": rule["category"], "key": rule["key"], "skills": rule["skills"], "instruction": rule["instruction"]}
    if "remotion" in prompt_lower or "hyperframes" in prompt_lower or "video" in prompt_lower:
        rule = INTENT_RULES[3]
        return {"category": rule["category"], "key": rule["key"], "skills": rule["skills"], "instruction": rule["instruction"]}
    if "gsd" in prompt_lower or "cto" in prompt_lower or "plan" in prompt_lower:
        rule = INTENT_RULES[4]
        return {"category": rule["category"], "key": rule["key"], "skills": rule["skills"], "instruction": rule["instruction"]}

    # Score each category based on keyword matches
    best_rule = None
    max_score = 0
    for rule in INTENT_RULES:
        score = sum(1 for kw in rule["keywords"] if kw in prompt_lower)
        if score > max_score:
            max_score = score
            best_rule = rule
            
    if best_rule and max_score >= 1:
        return {
            "category": best_rule["category"],
            "key": best_rule["key"],
            "skills": best_rule["skills"],
            "instruction": best_rule["instruction"]
        }
        
    return {
        "category": "🧠 Karpathy Surgical Engineering",
        "key": "general",
        "skills": ["karpathy-guidelines"],
        "instruction": DEFAULT_INSTRUCTION
    }

def enhance_prompt(prompt: str) -> Tuple[str, Dict[str, Any]]:
    """Kekalkan arahan asal Tuan Faiz dan tambah panduan kemahiran yang benar-benar ada."""
    intent = route_intent(prompt)
    base = prompt.strip()
    guidance = intent.get("instruction", "")
    enhanced = base + f"\n\n[Skill Guidance — guna jika relevan]: {guidance}" if guidance else base
    return enhanced, intent

def record_session(prompt: str, intent_info: Dict[str, Any], result_summary: str, status: str = "success") -> None:
    """Menyimpan ringkasan sesi Claude Code ke memori jangka masa panjang JARVIS."""
    try:
        sessions = []
        if SESSIONS_FILE.exists():
            try:
                with open(SESSIONS_FILE, "r", encoding="utf-8") as f:
                    sessions = json.load(f)
            except Exception:
                sessions = []
                
        # Clean preview
        clean_res = result_summary.strip()
        lines = [l for l in clean_res.split("\n") if l.strip()]
        preview = " ".join(lines[:3])[:250] if lines else "Tugasan selesai."
        
        entry = {
            "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "prompt": prompt[:200],
            "category": intent_info.get("category", "General"),
            "skills_used": intent_info.get("skills", []),
            "summary": preview,
            "status": status
        }
        
        sessions.append(entry)
        # Keep last 25 sessions
        if len(sessions) > 25:
            sessions = sessions[-25:]
            
        with open(SESSIONS_FILE, "w", encoding="utf-8") as f:
            json.dump(sessions, f, indent=2, ensure_ascii=False)
        with open(LEGACY_SESSIONS_FILE, "w", encoding="utf-8") as f:
            json.dump(sessions, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"[SkillRouter] Gagal mencatat memori sesi: {e}", flush=True)

def get_recent_sessions_context(limit: int = 3) -> str:
    """Menjana teks konteks memori aktiviti Claude Code terkini untuk disuntik ke ask_ai."""
    if not SESSIONS_FILE.exists():
        return ""
    try:
        with open(SESSIONS_FILE, "r", encoding="utf-8") as f:
            sessions = json.load(f)
        if not sessions:
            return ""
            
        recent = sessions[-limit:]
        lines = ["\n[Aktiviti OpenCode AI Terkini di Chromebook Faiz]:"]
        for s in recent:
            ts = s.get("timestamp", "").split(" ")[-1]
            cat = s.get("category", "")
            pr = s.get("prompt", "")
            sum_txt = s.get("summary", "")
            lines.append(f"- ({ts}) [{cat}] Tugasan: '{pr}' -> Ringkasan: {sum_txt}")
        return "\n".join(lines)
    except Exception:
        return ""

if __name__ == "__main__":
    test_prompts = [
        "Tolong buatkan butang navigasi yang cantik dan modern untuk landing page",
        "Kenapa program ini keluar error NullPointerException bila submit form?",
        "Tolong semak kod ini kalau ada lubang sekuriti atau sql injection",
        "Buatkan video ucapan selamat ulang tahun guna remotion",
        "Rancang fasa senibina untuk aplikasi e-commerce berskala tinggi",
        "Tolong tulis skrip ringkas untuk senaraikan fail"
    ]
    for tp in test_prompts:
        enh, it = enhance_prompt(tp)
        print(f"Prompt: {tp}")
        print(f"  -> Routed: {it['category']} (Skills: {', '.join(it['skills'])})")
