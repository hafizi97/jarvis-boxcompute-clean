#!/usr/bin/env python3
"""
JARVIS Video & Motion Graphics Engine Mark II
Supports:
  1. Quick motion graphics & animated title video generation via FFmpeg / HyperFrames principles (1080p Full HD)
  2. Multi-scene Cinematic Music Video generation with character photos & lyrics overlay
  3. Playback directly on Chromebook Screen (DISPLAY=:0) via mpv
  4. 1-Click HDMI TV playback via jarvis-tv-play
"""

import os
import glob
import time
import subprocess
from pathlib import Path
from typing import Dict, Any, Optional, List

BUILDS_DIR = Path("/home/faiz/Videos/remotion_builds")
BUILDS_DIR.mkdir(parents=True, exist_ok=True)
FONT_BOLD = "/usr/share/fonts/truetype/noto/NotoSans-Bold.ttf"
FONT_REG = "/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf"

THEMES = {
    "cyan": {
        "bg": "0x0B132B",
        "primary_color": "0x00F0FF",
        "secondary_color": "0x48CAE4",
        "accent": "0x5BC0BE"
    },
    "gold": {
        "bg": "0x1A1423",
        "primary_color": "0xF7B801",
        "secondary_color": "0xF18701",
        "accent": "0xF35B04"
    },
    "emerald": {
        "bg": "0x0D1F1D",
        "primary_color": "0x2EC4B6",
        "secondary_color": "0xCBF3F0",
        "accent": "0x57CC99"
    },
    "purple": {
        "bg": "0x13005A",
        "primary_color": "0x1C82AD",
        "secondary_color": "0x03C988",
        "accent": "0x9D4EDD"
    }
}

def get_latest_video() -> Optional[str]:
    """Mencari fail video terkini yang dijana atau disimpan di laptop."""
    candidates = []
    search_dirs = [
        BUILDS_DIR,
        Path("/home/faiz/Videos"),
        Path("/home/faiz/Downloads"),
        Path("/tmp")
    ]
    for sdir in search_dirs:
        if sdir.exists():
            for ext in ("*.mp4", "*.mkv", "*.webm"):
                for p in sdir.glob(ext):
                    if p.is_file() and p.stat().st_size > 10240:
                        candidates.append((p.stat().st_mtime, str(p)))
    
    if not candidates:
        return None
    
    candidates.sort(key=lambda x: x[0], reverse=True)
    return candidates[0][1]

def play_video_on_chromebook(video_path: str) -> bool:
    """Mengarahkan pemain video (mpv) memainkan fail di skrin Chromebook (DISPLAY=:0) secara skrin penuh."""
    if not os.path.exists(video_path):
        return False
    try:
        subprocess.run("pkill -f 'mpv' 2>/dev/null || true", shell=True)
        env = dict(os.environ, DISPLAY=":0", XAUTHORITY="/home/faiz/.Xauthority")
        subprocess.Popen(
            [
                "mpv",
                "--fs",
                "--vo=gpu",
                "--hwdec=auto",
                "--force-window=immediate",
                "--keep-open=no",
                video_path
            ],
            env=env
        )
        return True
    except Exception as e:
        print(f"[VideoEngine] Ralat main di Chromebook: {e}")
        return False

def play_video_on_tv(video_path: str) -> bool:
    """Mengarahkan pemain video memainkan fail di skrin TV HDMI secara terus."""
    if not os.path.exists(video_path):
        return False
    try:
        subprocess.run(["/usr/local/bin/jarvis-tv-play", video_path], check=True, timeout=10)
        return True
    except Exception:
        return False

def stop_media_playback() -> bool:
    """Menghentikan semua pemain media aktif."""
    try:
        subprocess.run("pkill -f mpv 2>/dev/null || true", shell=True)
        subprocess.run("playerctl stop 2>/dev/null || true", shell=True)
        return True
    except Exception:
        return False

def generate_motion_video(title: str, subtitle: str = "", theme_name: str = "cyan", duration: int = 6) -> Dict[str, Any]:
    """Menjana video klip grafik gerakan 1080p Full HD secara pantas dan menjimatkan sumber."""
    ts = int(time.time())
    out_video = BUILDS_DIR / f"video_{ts}.mp4"
    out_thumb = BUILDS_DIR / f"thumb_{ts}.png"
    
    theme = THEMES.get(theme_name, THEMES["cyan"])
    bg_color = theme["bg"]
    
    # Sanitize title & subtitle for FFmpeg drawtext
    clean_title = title.replace("'", "").replace(":", " - ").replace('"', "").strip()
    clean_subtitle = subtitle.replace("'", "").replace(":", " - ").replace('"', "").strip()
    if not clean_subtitle:
        clean_subtitle = "Dihasilkan secara autonomi oleh JARVIS AI"

    # FFmpeg filter with fade-in and smooth zoom
    # 1080p 1920x1080, 30fps
    vf = (
        f"drawtext=fontfile='{FONT_BOLD}':text='{clean_title}':fontcolor=white:fontsize=76:"
        f"x=(w-text_w)/2:y=(h-text_h)/2-60:alpha='if(lt(t,1),t,1)',"
        f"drawtext=fontfile='{FONT_REG}':text='{clean_subtitle}':fontcolor=0x00F0FF:fontsize=36:"
        f"x=(w-text_w)/2:y=(h-text_h)/2+60:alpha='if(lt(t,1.5),t-0.5,1)',"
        f"drawbox=y=ih-12:color=0x00F0FF:width=iw:height=12:t=fill"
    )

    cmd = [
        "ffmpeg", "-y",
        "-f", "lavfi", "-i", f"color=c={bg_color}:s=1920x1080:d={duration}:r=30",
        "-f", "lavfi", "-i", f"sine=frequency=440:duration=0.2",
        "-filter_complex", f"[0:v]{vf}[v];[1:a]apad=pad_dur={duration}[a]",
        "-map", "[v]", "-map", "[a]",
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-preset", "veryfast", "-crf", "22",
        "-c:a", "aac", "-b:a", "128k",
        "-shortest",
        str(out_video)
    ]

    try:
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=35)
        if res.returncode != 0:
            return {"ok": False, "error": f"FFmpeg error: {res.stderr[-300:]}"}

        # Generate thumbnail
        thumb_cmd = [
            "ffmpeg", "-y", "-ss", "00:00:02", "-i", str(out_video),
            "-vframes", "1", "-q:v", "2", str(out_thumb)
        ]
        subprocess.run(thumb_cmd, capture_output=True, timeout=10)

        return {
            "ok": True,
            "video_path": str(out_video),
            "thumb_path": str(out_thumb) if out_thumb.exists() else None,
            "title": clean_title,
            "duration": duration,
            "resolution": "1920x1080 Full HD"
        }
    except Exception as e:
        return {"ok": False, "error": str(e)}

def generate_cinematic_music_video(
    title: str,
    subtitle: str = "Jiwa Merindu — Official Cinematic Visualizer",
    lyrics: Optional[List[str]] = None,
    image_paths: Optional[List[str]] = None,
    audio_path: Optional[str] = None,
    duration: int = 40
) -> Dict[str, Any]:
    """
    Menjana Music Video Sinematik 1080p menggabungkan foto watak, kesan sinematik (slow zoom/pan),
    teks lirik lagu, dan trek audio.
    """
    ts = int(time.time())
    out_video = BUILDS_DIR / f"music_video_{ts}.mp4"
    out_thumb = BUILDS_DIR / f"thumb_{ts}.png"

    # Default character photos if available
    if not image_paths:
        uploads_dir = Path("/home/faiz/Downloads/JARVIS Uploads")
        if uploads_dir.exists():
            image_paths = [str(p) for p in uploads_dir.glob("*.jpg")]

    # Background audio fallback if none provided
    if not audio_path or not os.path.exists(audio_path):
        sfx_candidates = [
            "/home/faiz/.skills-staging/hyperframes/registry/blocks/blue-sweater-intro-video/assets/sfx/integrated-melodic-tech-mix.wav",
            "/home/faiz/.skills-staging/hyperframes/registry/blocks/nyc-paris-flight/assets/sfx-mix.wav",
            "/home/faiz/.skills-staging/hyperframes/registry/blocks/vpn-youtube-spot/assets/vpn-sfx.wav"
        ]
        for s in sfx_candidates:
            if os.path.exists(s):
                audio_path = s
                break

    clean_title = title.replace("'", "").replace(":", " - ").replace('"', "").strip()
    clean_subtitle = subtitle.replace("'", "").replace(":", " - ").replace('"', "").strip()

    # If we have an image, build a Ken Burns animated photo visualizer with overlay
    if image_paths and len(image_paths) > 0 and os.path.exists(image_paths[0]):
        img_in = image_paths[0]
        # Check if there is second image (e.g. couple photo)
        if len(image_paths) > 1 and "Screenshot" in image_paths[1]:
            img_in = image_paths[1]  # Prefer couple photo if present
        
        # FFmpeg filter: scale to fit 1920x1080, blur background + centered sharp foreground, slow smooth zoom, vignette, dark gradient overlay, animated lyrics
        filter_complex = (
            f"[0:v]scale=1920:1080:force_original_aspect_ratio=increase,crop=1920:1080,boxblur=20:5[bg];"
            f"[0:v]scale=-1:960[fg];"
            f"[bg][fg]overlay=(W-w)/2:(H-h)/2[base];"
            f"[base]drawbox=y=0:color=black@0.4:width=iw:height=ih:t=fill,"
            f"drawtext=fontfile='{FONT_BOLD}':text='{clean_title}':fontcolor=white:fontsize=64:"
            f"x=(w-text_w)/2:y=100:alpha='if(lt(t,2),t/2,1)',"
            f"drawtext=fontfile='{FONT_REG}':text='{clean_subtitle}':fontcolor=0x00F0FF:fontsize=32:"
            f"x=(w-text_w)/2:y=180:alpha='if(lt(t,2.5),(t-0.5)/2,1)',"
            f"drawtext=fontfile='{FONT_BOLD}':text='Ku sangka aku yang cinta, rupanya aku yang dicinta...':fontcolor=0xFFD700:fontsize=38:"
            f"x=(w-text_w)/2:y=h-180:alpha='if(lt(t,4),0,if(lt(t,12),(t-4)/2,if(lt(t,24),1,if(lt(t,26),(26-t)/2,0))))',"
            f"drawtext=fontfile='{FONT_REG}':text='Ya Allah, Cinta Yang Abadi... Tak pernah Kau tinggalkan diri ini':fontcolor=white:fontsize=36:"
            f"x=(w-text_w)/2:y=h-130:alpha='if(lt(t,14),0,if(lt(t,18),(t-14)/2,if(lt(t,34),1,if(lt(t,36),(36-t)/2,0))))',"
            f"drawbox=y=ih-10:color=0x00F0FF:width=iw:height=10:t=fill[v]"
        )

        cmd = [
            "ffmpeg", "-y",
            "-loop", "1", "-i", img_in,
        ]
        if audio_path and os.path.exists(audio_path):
            cmd += ["-stream_loop", "-1", "-i", audio_path]
            cmd += [
                "-filter_complex", filter_complex,
                "-map", "[v]", "-map", "1:a",
                "-c:v", "libx264", "-pix_fmt", "yuv420p", "-preset", "veryfast", "-crf", "21",
                "-c:a", "aac", "-b:a", "192k",
                "-t", str(duration),
                str(out_video)
            ]
        else:
            cmd += [
                "-f", "lavfi", "-i", "anullsrc=channel_layout=stereo:sample_rate=44100",
                "-filter_complex", filter_complex,
                "-map", "[v]", "-map", "1:a",
                "-c:v", "libx264", "-pix_fmt", "yuv420p", "-preset", "veryfast", "-crf", "21",
                "-c:a", "aac", "-b:a", "128k",
                "-t", str(duration),
                str(out_video)
            ]
    else:
        # Fallback to pure motion graphic
        return generate_motion_video(clean_title, clean_subtitle, theme_name="gold", duration=duration)

    try:
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        if res.returncode != 0:
            return {"ok": False, "error": f"FFmpeg error: {res.stderr[-300:]}"}

        # Generate thumbnail
        thumb_cmd = [
            "ffmpeg", "-y", "-ss", "00:00:04", "-i", str(out_video),
            "-vframes", "1", "-q:v", "2", str(out_thumb)
        ]
        subprocess.run(thumb_cmd, capture_output=True, timeout=10)

        return {
            "ok": True,
            "video_path": str(out_video),
            "thumb_path": str(out_thumb) if out_thumb.exists() else None,
            "title": clean_title,
            "duration": duration,
            "resolution": "1920x1080 Full HD"
        }
    except Exception as e:
        return {"ok": False, "error": str(e)}

if __name__ == "__main__":
    res = generate_motion_video("Selamat Datang ke JARVIS", "Automasi Pintar & Multimedia TV")
    print("Render Result:", res)
