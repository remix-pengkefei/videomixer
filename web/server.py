"""VideoMixer Web Server - FastAPI backend."""

import asyncio
import json
import os
import shutil
import zipfile
import subprocess as sp
import sys
import time
import uuid
from contextlib import asynccontextmanager
from dataclasses import dataclass, field, asdict
from enum import Enum
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel

# Add project root to path so we can import src modules
if getattr(sys, 'frozen', False):
    # PyInstaller: executable is in bin/, project root is parent
    PROJECT_ROOT = Path(sys.executable).parent.parent
else:
    PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.sticker_pool import generate_video_id

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

DATA_DIR = PROJECT_ROOT / "data"
DATA_DIR.mkdir(exist_ok=True)
CONFIG_FILE = DATA_DIR / "config.json"
HISTORY_FILE = DATA_DIR / "history.json"

WORKSPACE_DIR = PROJECT_ROOT / "workspace"
UPLOADS_DIR = WORKSPACE_DIR / "uploads"
OUTPUTS_DIR = WORKSPACE_DIR / "outputs"
LOGS_DIR = WORKSPACE_DIR / "logs"
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
LOGS_DIR.mkdir(parents=True, exist_ok=True)

DEFAULT_STRATEGY_CONFIGS = {
    "handwriting": {
        "sticker_count": 14, "sparkle_count": 5, "sparkle_style": "gold",
        "color_scheme": "random", "enable_particles": True,
        "enable_decorations": True, "enable_border": True,
        "enable_color_preset": True, "enable_audio_fx": True,
        "enable_lut": True, "enable_speed_ramp": True,
        "enable_lens_effect": True, "enable_glitch": True,
    },
    "emotional": {
        "sticker_count": 20, "sparkle_count": 5, "sparkle_style": "pink",
        "color_scheme": "random", "enable_particles": True,
        "enable_decorations": True, "enable_border": True,
        "enable_color_preset": True, "enable_audio_fx": True,
        "enable_lut": True, "enable_speed_ramp": True,
        "enable_lens_effect": True, "enable_glitch": True,
    },
    "health": {
        "sticker_count": 20, "sparkle_count": 5, "sparkle_style": "warm",
        "color_scheme": "random", "enable_particles": True,
        "enable_decorations": True, "enable_border": True,
        "enable_color_preset": True, "enable_audio_fx": True,
        "enable_lut": True, "enable_speed_ramp": True,
        "enable_lens_effect": True, "enable_glitch": True,
    },
}


def _load_config() -> dict:
    if CONFIG_FILE.exists():
        try:
            return json.loads(CONFIG_FILE.read_text("utf-8"))
        except Exception:
            pass
    return {
        "last_input_dir": "",
        "last_output_dir": "",
        "strategies": DEFAULT_STRATEGY_CONFIGS,
    }


def _save_config(cfg: dict):
    CONFIG_FILE.write_text(json.dumps(cfg, ensure_ascii=False, indent=2), "utf-8")


def _load_history() -> dict:
    if HISTORY_FILE.exists():
        try:
            return json.loads(HISTORY_FILE.read_text("utf-8"))
        except Exception:
            pass
    return {"tasks": []}


def _save_history(history: dict):
    HISTORY_FILE.write_text(json.dumps(history, ensure_ascii=False, indent=2), "utf-8")


def _append_history(entry: dict):
    history = _load_history()
    history["tasks"].insert(0, entry)
    # Keep last 100 records
    history["tasks"] = history["tasks"][:100]
    _save_history(history)


VIDEO_EXTENSIONS = frozenset({
    '.mp4', '.mov', '.m4v', '.avi', '.mkv', '.webm', '.flv', '.wmv'
})

STRATEGY_MAP = {
    "手写": "handwriting", "文案": "handwriting", "handwriting": "handwriting",
    "情感": "emotional", "励志": "emotional", "emotional": "emotional",
    "养生": "health", "健康": "health", "health": "health",
}

STRATEGIES = [
    {
        "id": "handwriting", "name": "手写混剪",
        "description": "手写/文案类视频，金色配色，14个贴纸",
        "defaults": {"sticker_count": 14, "sparkle_count": 5, "sparkle_style": "gold"},
    },
    {
        "id": "emotional", "name": "情感混剪",
        "description": "情感/励志类视频，粉紫配色，20个贴纸",
        "defaults": {"sticker_count": 20, "sparkle_count": 5, "sparkle_style": "pink"},
    },
    {
        "id": "health", "name": "养生混剪",
        "description": "养生/健康类视频，暖色配色，20个贴纸",
        "defaults": {"sticker_count": 20, "sparkle_count": 5, "sparkle_style": "warm"},
    },
]

# 5种策略预设 (A-E)
STRATEGY_PRESETS = [
    {"id": "D", "name": "D-智能避让", "description": "智能检测内容区域，自动避让主体，推荐默认"},
    {"id": "A", "name": "A-极简隐形", "description": "最少装饰，几乎不可见的修改"},
    {"id": "B", "name": "B-边框画框", "description": "边框为主，画框式装饰"},
    {"id": "C", "name": "C-角落点缀", "description": "角落放置贴纸和闪光，不遮挡中心"},
    {"id": "E", "name": "E-动感变换", "description": "最丰富的效果，动感十足"},
]

# 混剪模式
MIXING_MODES = [
    {"id": "standard", "name": "传统混剪", "description": "标准贴纸+闪光+边框效果"},
    {"id": "blur_center", "name": "背景模糊居中", "description": "模糊背景+居中内容，类似Apple Music风格"},
    {"id": "fake_player", "name": "假播放器", "description": "假音乐播放器UI覆盖，伪装为音乐App"},
    {"id": "sandwich", "name": "三层夹心", "description": "上下层填充视频+中间层内容，三层拼接"},
    {"id": "concat", "name": "多段串联", "description": "将视频重复拼接延长至目标时长"},
]

SPARKLE_STYLES = ["gold", "pink", "warm", "cool", "mixed"]
COLOR_SCHEME_OPTIONS = [
    "random", "金色暖调", "冷色优雅", "莫兰迪", "粉紫甜美",
    "自然绿意", "赛博朋克", "复古怀旧", "海洋蓝调",
]

# ---------------------------------------------------------------------------
# Task model
# ---------------------------------------------------------------------------

class TaskStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class FileProgress:
    filename: str
    status: str = "pending"  # pending / running / done / failed
    elapsed: float = 0.0
    error: str = ""


@dataclass
class TaskState:
    id: str
    input_dir: str
    output_dir: str
    categories: list  # [{folder, strategy, files: [...]}]
    status: TaskStatus = TaskStatus.PENDING
    created_at: float = 0.0
    started_at: float = 0.0
    finished_at: float = 0.0
    current_file: str = ""
    completed_count: int = 0
    failed_count: int = 0
    total_count: int = 0
    file_results: list = field(default_factory=list)
    source_name: str = ""
    cancel_requested: bool = False
    _current_proc: object = field(default=None, repr=False)

    def to_dict(self):
        d = asdict(self)
        d["status"] = self.status.value
        return d


# ---------------------------------------------------------------------------
# In-memory store
# ---------------------------------------------------------------------------

tasks: dict[str, TaskState] = {}
ws_connections: dict[str, list[WebSocket]] = {}  # task_id -> list of ws
if getattr(sys, 'frozen', False):
    RUN_PROCESSOR = str(Path(sys.executable).parent / "videomixer-processor")
else:
    RUN_PROCESSOR = str(Path(__file__).parent / "run_processor.py")


# ---------------------------------------------------------------------------
# FastAPI app
# ---------------------------------------------------------------------------

if getattr(sys, 'frozen', False):
    FRONTEND_DIST = PROJECT_ROOT / "web" / "frontend" / "dist"
else:
    FRONTEND_DIST = Path(__file__).parent / "frontend" / "dist"


@asynccontextmanager
async def lifespan(app: FastAPI):
    if FRONTEND_DIST.exists():
        app.mount("/assets", StaticFiles(directory=str(FRONTEND_DIST / "assets")), name="static-assets")
    yield


app = FastAPI(title="VideoMixer Web", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------

class OutputConfig(BaseModel):
    mode: str = "standard"
    strategy_preset: str = "D"


class FileConfig(BaseModel):
    filename: str
    outputs: list[OutputConfig] = [OutputConfig()]


class CategoryInput(BaseModel):
    folder: str
    strategy: str
    config: Optional[dict] = None
    files: list[FileConfig] = []


class CreateTaskBody(BaseModel):
    input_dir: str
    output_dir: str
    categories: list[CategoryInput]


class UploadTaskBody(BaseModel):
    session_id: str
    source_name: str = ""
    categories: list[CategoryInput]


# ---------------------------------------------------------------------------
# REST endpoints
# ---------------------------------------------------------------------------

@app.get("/api/folders")
async def list_folders(path: str = "~"):
    """Browse directories. Returns dirs and video files."""
    target = Path(path).expanduser().resolve()
    if not target.exists():
        raise HTTPException(404, f"Path not found: {target}")
    if not target.is_dir():
        raise HTTPException(400, f"Not a directory: {target}")

    dirs = []
    files = []
    try:
        for entry in sorted(target.iterdir()):
            if entry.name.startswith('.'):
                continue
            if entry.is_dir():
                dirs.append({"name": entry.name, "path": str(entry)})
            elif entry.suffix.lower() in VIDEO_EXTENSIONS:
                files.append({"name": entry.name, "path": str(entry)})
    except PermissionError:
        raise HTTPException(403, f"Permission denied: {target}")

    return {
        "path": str(target),
        "parent": str(target.parent) if target != target.parent else None,
        "dirs": dirs,
        "files": files,
    }


@app.get("/api/scan")
async def scan_input(path: str):
    """Scan input directory for sub-folders with videos. Returns categories."""
    target = Path(path).expanduser().resolve()
    if not target.is_dir():
        raise HTTPException(400, f"Not a directory: {target}")

    categories = []
    for sub in sorted(target.iterdir()):
        if sub.name.startswith('.') or not sub.is_dir():
            continue
        video_files = [f.name for f in sorted(sub.iterdir())
                       if f.suffix.lower() in VIDEO_EXTENSIONS and not f.name.startswith('.')]
        if not video_files:
            continue

        # Auto-detect strategy from folder name
        folder_lower = sub.name.lower()
        strategy = "none"
        for key, val in STRATEGY_MAP.items():
            if key in folder_lower:
                strategy = val
                break

        categories.append({
            "folder": sub.name,
            "path": str(sub),
            "video_count": len(video_files),
            "files": video_files,
            "strategy": strategy,
        })

    # Fallback: if no subdirectory categories found, check for videos directly in the folder
    if not categories:
        root_videos = [f.name for f in sorted(target.iterdir())
                       if f.is_file() and f.suffix.lower() in VIDEO_EXTENSIONS and not f.name.startswith('.')]
        if root_videos:
            folder_lower = target.name.lower()
            strategy = "none"
            for key, val in STRATEGY_MAP.items():
                if key in folder_lower:
                    strategy = val
                    break
            categories.append({
                "folder": ".",
                "path": str(target),
                "display_name": target.name,
                "video_count": len(root_videos),
                "files": root_videos,
                "strategy": strategy,
            })

    return {"path": str(target), "categories": categories}


@app.get("/api/strategies")
async def get_strategies():
    return {
        "strategies": STRATEGIES,
        "strategy_presets": STRATEGY_PRESETS,
        "mixing_modes": MIXING_MODES,
        "sparkle_styles": SPARKLE_STYLES,
        "color_schemes": COLOR_SCHEME_OPTIONS,
    }


@app.get("/api/assets/overview")
async def get_assets_overview():
    """Return detailed asset counts and metadata."""
    from src.sticker_pool import ALL_STICKER_GROUPS, SPARKLE_STYLE_DIRS, COLOR_SCHEMES

    assets_root = PROJECT_ROOT / "assets"

    # Sticker breakdown by category
    sticker_dir = assets_root / "stickers"
    sticker_categories = {}
    total_stickers = 0
    if sticker_dir.is_dir():
        for category, folders in ALL_STICKER_GROUPS.items():
            count = 0
            for folder_name in folders:
                folder_path = sticker_dir / folder_name
                if folder_path.exists():
                    count += sum(1 for _ in folder_path.glob("*.png"))
            sticker_categories[category] = count
            total_stickers += count

    # Sparkle breakdown by style
    sparkle_dir = assets_root / "sparkles" / "png"
    sparkle_styles_data = {}
    if sparkle_dir.is_dir():
        for style, subdirs in SPARKLE_STYLE_DIRS.items():
            count = sum(1 for _ in sparkle_dir.glob("*.png"))
            for subdir_name in subdirs:
                subdir = sparkle_dir / subdir_name
                if subdir.exists():
                    count += sum(1 for _ in subdir.glob("*.png"))
            sparkle_styles_data[style] = count

    total_sparkles = sum(1 for _ in sparkle_dir.rglob("*.png")) if sparkle_dir.is_dir() else 0

    return {
        "stickers": {"total": total_stickers, "categories": sticker_categories},
        "sparkles": {"total": total_sparkles, "styles": sparkle_styles_data},
        "effects": {
            "color_schemes": len(COLOR_SCHEMES),
            "mask_styles": 5,
            "particle_styles": 6,
            "decoration_styles": 5,
            "border_styles": 6,
            "text_styles": 6,
            "audio_effects": 5,
            "color_presets": 8,
            "lut_presets": 10,
            "speed_ramps": 7,
            "lens_effects": 9,
            "glitch_effects": 8,
        }
    }


@app.get("/api/env-check")
async def env_check():
    """Check runtime environment: ffmpeg, ffprobe, assets."""
    # ffmpeg
    ffmpeg_info = {"installed": False, "path": None, "version": None}
    for p in ["/opt/homebrew/bin/ffmpeg", "/usr/local/bin/ffmpeg", "ffmpeg"]:
        resolved = shutil.which(p)
        if resolved:
            ffmpeg_info["installed"] = True
            ffmpeg_info["path"] = resolved
            try:
                result = sp.run([resolved, "-version"], capture_output=True, text=True, timeout=5)
                first_line = result.stdout.split('\n')[0]
                ffmpeg_info["version"] = first_line.split('version')[1].strip().split()[0] if 'version' in first_line else "unknown"
            except Exception:
                ffmpeg_info["version"] = "unknown"
            break

    # ffprobe
    ffprobe_info = {"installed": False, "path": None}
    for p in ["/opt/homebrew/bin/ffprobe", "/usr/local/bin/ffprobe", "ffprobe"]:
        resolved = shutil.which(p)
        if resolved:
            ffprobe_info["installed"] = True
            ffprobe_info["path"] = resolved
            break

    # Assets
    assets_root = PROJECT_ROOT / "assets"
    sticker_dir = assets_root / "stickers"
    sticker_count = sum(1 for _ in sticker_dir.rglob("*.png")) if sticker_dir.is_dir() else 0
    sparkle_dir = assets_root / "sparkles" / "png"
    sparkle_count = sum(1 for _ in sparkle_dir.rglob("*.png")) if sparkle_dir.is_dir() else 0

    return {
        "ffmpeg": ffmpeg_info,
        "ffprobe": ffprobe_info,
        "assets": {
            "stickers": {"exists": sticker_dir.is_dir(), "count": sticker_count},
            "sparkles": {"exists": sparkle_dir.is_dir(), "count": sparkle_count},
        }
    }


@app.get("/api/check-update")
async def check_update():
    """Check GitHub for new commits via REST API (no credentials needed)."""
    import re
    import urllib.request
    import urllib.error

    try:
        # Get local HEAD (local only, no network)
        proc = await asyncio.create_subprocess_exec(
            "git", "rev-parse", "HEAD",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=str(PROJECT_ROOT),
        )
        stdout, _ = await proc.communicate()
        local_sha = stdout.decode().strip()
        if not local_sha:
            return {"has_update": False, "error": "Not a git repo"}

        # Get current branch (local only)
        proc2 = await asyncio.create_subprocess_exec(
            "git", "rev-parse", "--abbrev-ref", "HEAD",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=str(PROJECT_ROOT),
        )
        stdout2, _ = await proc2.communicate()
        branch = stdout2.decode().strip() or "main"

        # Get GitHub owner/repo from git remote URL
        proc3 = await asyncio.create_subprocess_exec(
            "git", "remote", "get-url", "origin",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=str(PROJECT_ROOT),
        )
        stdout3, _ = await proc3.communicate()
        remote_url = stdout3.decode().strip()

        # Parse owner/repo from HTTPS or SSH URL
        m = re.search(r'github\.com[:/](.+?)(?:\.git)?$', remote_url)
        if not m:
            return {"has_update": False, "error": "Not a GitHub repo"}
        repo_path = m.group(1)

        # Call GitHub REST API (no auth needed for public repos)
        api_url = f"https://api.github.com/repos/{repo_path}/commits?sha={branch}&per_page=20"
        req = urllib.request.Request(api_url, headers={
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "VideoMixer-UpdateChecker",
        })

        def _fetch_api():
            try:
                with urllib.request.urlopen(req, timeout=10) as resp:
                    return json.loads(resp.read())
            except urllib.error.HTTPError as e:
                if e.code == 404:
                    return {"_error": "private_repo"}
                raise

        remote_commits = await asyncio.to_thread(_fetch_api)

        # Handle private repo (GitHub API returns 404)
        if isinstance(remote_commits, dict) and remote_commits.get("_error") == "private_repo":
            return {
                "has_update": False,
                "local_sha": local_sha[:7],
                "error": "仓库为私有，请在 GitHub 设置中将仓库改为 Public",
            }

        if not remote_commits:
            return {"has_update": False, "local_sha": local_sha[:7]}

        # Find commits ahead of local HEAD
        ahead_commits = []
        found_local = False
        for c in remote_commits:
            if c["sha"] == local_sha:
                found_local = True
                break
            ahead_commits.append({
                "sha": c["sha"][:7],
                "message": c["commit"]["message"].split("\n")[0],
            })

        # If local HEAD not found in remote list, local is likely ahead — no update
        if not found_local or not ahead_commits:
            return {"has_update": False, "local_sha": local_sha[:7]}

        return {
            "has_update": True,
            "ahead": len(ahead_commits),
            "local_sha": local_sha[:7],
            "commits": ahead_commits[:5],
        }
    except urllib.error.URLError as e:
        return {"has_update": False, "error": f"网络请求失败: {getattr(e, 'reason', str(e))}"}
    except Exception as e:
        return {"has_update": False, "error": str(e)}


@app.get("/api/config")
async def get_config():
    """Read persisted config."""
    return _load_config()


@app.put("/api/config")
async def put_config(body: dict):
    """Write persisted config (deep-merge strategies)."""
    cfg = _load_config()
    # Deep merge strategies
    if "strategies" in body and isinstance(body["strategies"], dict):
        if "strategies" not in cfg:
            cfg["strategies"] = {}
        for sid, sval in body["strategies"].items():
            if isinstance(sval, dict):
                cfg["strategies"].setdefault(sid, {}).update(sval)
            else:
                cfg["strategies"][sid] = sval
        body_rest = {k: v for k, v in body.items() if k != "strategies"}
        cfg.update(body_rest)
    else:
        cfg.update(body)
    _save_config(cfg)
    return {"ok": True}


@app.get("/api/history")
async def get_history():
    """Read task history."""
    return _load_history()


@app.delete("/api/history")
async def clear_history():
    """Clear all task history."""
    _save_history({"tasks": []})
    return {"ok": True}


STATS_FILE = DATA_DIR / "video_stats.json"

def _load_stats():
    if STATS_FILE.exists():
        return json.loads(STATS_FILE.read_text("utf-8"))
    return {"videos": []}

def _save_stats(data):
    STATS_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), "utf-8")


@app.get("/api/video-stats")
async def get_video_stats():
    """Read all video stats."""
    return _load_stats()


class VideoStatUpdate(BaseModel):
    id: str
    stats: dict

@app.put("/api/video-stats")
async def update_video_stat(body: VideoStatUpdate):
    """Update stats for a single video entry."""
    data = _load_stats()
    for v in data["videos"]:
        if v["id"] == body.id:
            v["stats"].update(body.stats)
            _save_stats(data)
            return {"ok": True}
    raise HTTPException(status_code=404, detail="Video not found")


class VideoStatCreate(BaseModel):
    videos: list

@app.post("/api/video-stats/batch")
async def batch_create_video_stats(body: VideoStatCreate):
    """Add new video entries (from completed task) without duplicates."""
    data = _load_stats()
    existing_ids = {v["id"] for v in data["videos"]}
    for v in body.videos:
        if v["id"] not in existing_ids:
            data["videos"].append(v)
    _save_stats(data)
    return {"ok": True}


class OpenFolderBody(BaseModel):
    path: str

@app.post("/api/open-folder")
async def open_folder(body: OpenFolderBody):
    """Open a folder in Finder (macOS)."""
    folder = Path(body.path).expanduser().resolve()
    if not folder.is_dir():
        raise HTTPException(status_code=400, detail="目录不存在")
    proc = await asyncio.create_subprocess_exec("open", str(folder))
    await proc.wait()
    return {"ok": True}


# ---------------------------------------------------------------------------
# Upload / Download endpoints
# ---------------------------------------------------------------------------

@app.post("/api/upload")
async def upload_files(
    session_id: str = Form(...),
    category: str = Form(...),
    files: list[UploadFile] = File(...),
):
    """Upload video files into a session/category directory."""
    safe_category = category.replace("/", "_").replace("\\", "_").strip()
    if not safe_category:
        raise HTTPException(400, "Invalid category name")

    target_dir = UPLOADS_DIR / session_id / safe_category
    target_dir.mkdir(parents=True, exist_ok=True)

    uploaded = []
    for f in files:
        # Use basename only (webkitdirectory may include path prefix)
        safe_name = Path(f.filename).name
        ext = Path(safe_name).suffix.lower()
        if ext not in VIDEO_EXTENSIONS:
            continue
        dest = target_dir / safe_name
        with open(dest, "wb") as out:
            while True:
                chunk = await f.read(1024 * 1024)
                if not chunk:
                    break
                out.write(chunk)
        uploaded.append(safe_name)

    return {"uploaded": uploaded, "count": len(uploaded)}


@app.get("/api/upload/{session_id}/scan")
async def scan_uploads(session_id: str):
    """Scan uploaded files for a session. Returns categories like /api/scan."""
    session_dir = UPLOADS_DIR / session_id
    if not session_dir.is_dir():
        return {"path": str(session_dir), "categories": []}

    categories = []
    for sub in sorted(session_dir.iterdir()):
        if sub.name.startswith('.') or not sub.is_dir():
            continue
        video_files = [f.name for f in sorted(sub.iterdir())
                       if f.suffix.lower() in VIDEO_EXTENSIONS and not f.name.startswith('.')]
        if not video_files:
            continue

        folder_lower = sub.name.lower()
        strategy = "none"
        for key, val in STRATEGY_MAP.items():
            if key in folder_lower:
                strategy = val
                break

        categories.append({
            "folder": sub.name,
            "path": str(sub),
            "video_count": len(video_files),
            "files": video_files,
            "strategy": strategy,
        })

    return {"path": str(session_dir), "categories": categories}


@app.delete("/api/upload/{session_id}/{category}/{filename}")
async def delete_uploaded_file(session_id: str, category: str, filename: str):
    """Delete a single uploaded file."""
    target = UPLOADS_DIR / session_id / category / filename
    if target.is_file():
        target.unlink()
        return {"ok": True}
    raise HTTPException(404, "File not found")


@app.delete("/api/upload/{session_id}/{category}")
async def delete_uploaded_category(session_id: str, category: str):
    """Delete an entire uploaded category."""
    target = UPLOADS_DIR / session_id / category
    if target.is_dir():
        shutil.rmtree(target)
        return {"ok": True}
    raise HTTPException(404, "Category not found")


@app.post("/api/tasks/upload")
async def create_task_from_upload(body: UploadTaskBody):
    """Create a mixing task from uploaded files."""
    session_dir = UPLOADS_DIR / body.session_id
    if not session_dir.is_dir():
        raise HTTPException(400, "No uploads found for this session")

    task_id = str(uuid.uuid4())[:8]
    output_dir = OUTPUTS_DIR / task_id

    cat_list = []
    total = 0
    for cat in body.categories:
        folder_path = session_dir / cat.folder
        if not folder_path.is_dir():
            continue

        # Build per-file configs from cat.files
        file_configs = []
        for fc in cat.files:
            if not (folder_path / fc.filename).is_file():
                continue
            outputs = [{"mode": o.mode, "strategy_preset": o.strategy_preset} for o in fc.outputs]
            if not outputs:
                outputs = [{"mode": "standard", "strategy_preset": "D"}]
            outputs = outputs[:10]
            file_configs.append({"filename": fc.filename, "outputs": outputs})
            total += len(outputs)

        # Fallback: scan folder if frontend didn't send file list
        if not file_configs:
            video_files = [f.name for f in sorted(folder_path.iterdir())
                           if f.suffix.lower() in VIDEO_EXTENSIONS and not f.name.startswith('.')]
            for vf in video_files:
                file_configs.append({
                    "filename": vf,
                    "outputs": [{"mode": "standard", "strategy_preset": "D"}],
                })
                total += 1

        if file_configs:
            cat_list.append({
                "folder": cat.folder,
                "strategy": cat.strategy,
                "config": cat.config,
                "files": file_configs,
            })

    if total == 0:
        raise HTTPException(400, "No video files found in uploaded categories")

    task = TaskState(
        id=task_id,
        input_dir=str(session_dir),
        output_dir=str(output_dir),
        categories=cat_list,
        total_count=total,
        created_at=time.time(),
        source_name=body.source_name,
    )
    tasks[task_id] = task
    asyncio.get_event_loop().create_task(_run_task(task))

    return {"task_id": task_id, "total": total}


def _resolve_task_output(task_id: str) -> Path:
    """Find the output directory for a task (workspace or history)."""
    # First try workspace
    wp = OUTPUTS_DIR / task_id
    if wp.is_dir():
        return wp
    # Fallback: check history for old output_dir
    history = _load_history()
    for t in history.get("tasks", []):
        if t.get("id") == task_id:
            p = Path(t.get("output_dir", ""))
            if p.is_dir():
                return p
            break
    return wp  # return default even if missing (caller checks)


@app.get("/api/download/{task_id}/list")
async def list_downloads(task_id: str):
    """List downloadable output files for a task."""
    task_output = _resolve_task_output(task_id)
    if not task_output.is_dir():
        return {"task_id": task_id, "files": []}

    files = []
    for cat_dir in sorted(task_output.iterdir()):
        if not cat_dir.is_dir():
            continue
        for video_file in sorted(cat_dir.iterdir()):
            if video_file.suffix.lower() in VIDEO_EXTENSIONS:
                size_mb = round(video_file.stat().st_size / (1024 * 1024), 1)
                files.append({
                    "category": cat_dir.name,
                    "filename": video_file.name,
                    "size_mb": size_mb,
                    "url": f"/api/download/{task_id}/{cat_dir.name}/{video_file.name}",
                })
    return {"task_id": task_id, "files": files}


@app.get("/api/download/{task_id}/{category}/{filename}")
async def download_file(task_id: str, category: str, filename: str):
    """Download a single processed file."""
    task_output = _resolve_task_output(task_id)
    file_path = task_output / category / filename
    if not file_path.is_file():
        raise HTTPException(404, "File not found")
    return FileResponse(
        str(file_path),
        filename=filename,
        media_type="application/octet-stream",
    )


@app.get("/api/download/{task_id}/all")
async def download_all(task_id: str):
    """Download all processed files as ZIP."""
    task_output = _resolve_task_output(task_id)
    if not task_output.is_dir():
        raise HTTPException(404, "Task output not found")

    task = tasks.get(task_id)
    if task and task.source_name:
        root_folder = f"{task.source_name}_已处理"
    else:
        root_folder = f"videomixer_{task_id}"
    zip_name = f"{root_folder}.zip"

    zip_path = task_output / zip_name
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_STORED) as zf:
        for cat_dir in sorted(task_output.iterdir()):
            if not cat_dir.is_dir():
                continue
            for video_file in sorted(cat_dir.iterdir()):
                if video_file.suffix.lower() in VIDEO_EXTENSIONS:
                    zf.write(video_file, f"{root_folder}/{cat_dir.name}/{video_file.name}")

    return FileResponse(
        str(zip_path),
        filename=zip_name,
        media_type="application/zip",
    )


@app.websocket("/ws/env-install")
async def ws_env_install(ws: WebSocket):
    """Stream brew install ffmpeg output."""
    await ws.accept()
    try:
        process = await asyncio.create_subprocess_exec(
            "brew", "install", "ffmpeg",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
        )
        async for line in process.stdout:
            text = line.decode("utf-8", errors="replace").rstrip()
            await ws.send_json({"type": "output", "line": text})
        returncode = await process.wait()
        await ws.send_json({"type": "done", "success": returncode == 0,
                            "error": "" if returncode == 0 else f"exit code {returncode}"})
    except FileNotFoundError:
        await ws.send_json({"type": "done", "success": False,
                            "error": "未找到 Homebrew，请先安装: /bin/bash -c \"$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\""})
    except Exception as e:
        await ws.send_json({"type": "done", "success": False, "error": str(e)})
    finally:
        try:
            await ws.close()
        except Exception:
            pass


@app.websocket("/ws/git-pull")
async def ws_git_pull(ws: WebSocket):
    """Stream git pull output for manual updates."""
    await ws.accept()
    # Suppress ALL credential prompts (macOS keychain, terminal, etc.)
    git_env = {
        **os.environ,
        "GIT_TERMINAL_PROMPT": "0",
        "GIT_ASKPASS": "/usr/bin/true",
        "GIT_CONFIG_NOSYSTEM": "1",
        "SSH_ASKPASS": "",
    }
    try:
        process = await asyncio.create_subprocess_exec(
            "git", "-c", "credential.helper=",
            "-c", "credential.interactive=false",
            "pull", "--ff-only",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
            env=git_env,
            cwd=str(PROJECT_ROOT),
        )
        async for line in process.stdout:
            text = line.decode("utf-8", errors="replace").rstrip()
            await ws.send_json({"type": "output", "line": text})
        returncode = await process.wait()
        await ws.send_json({
            "type": "done",
            "success": returncode == 0,
            "error": "" if returncode == 0 else f"exit code {returncode}",
        })
    except FileNotFoundError:
        await ws.send_json({"type": "done", "success": False,
                            "error": "未找到 git 命令"})
    except Exception as e:
        await ws.send_json({"type": "done", "success": False, "error": str(e)})
    finally:
        try:
            await ws.close()
        except Exception:
            pass


@app.post("/api/tasks")
async def create_task(body: CreateTaskBody):
    """Create a new mixing task."""
    input_dir = Path(body.input_dir).expanduser().resolve()
    output_dir = Path(body.output_dir).expanduser().resolve()

    if not input_dir.is_dir():
        raise HTTPException(400, f"Input directory not found: {input_dir}")

    # Create output dir if needed
    output_dir.mkdir(parents=True, exist_ok=True)

    # Build file list for each category
    cat_list = []
    total = 0
    for cat in body.categories:
        folder_path = input_dir / cat.folder
        if not folder_path.is_dir():
            continue
        video_files = [f.name for f in sorted(folder_path.iterdir())
                       if f.suffix.lower() in VIDEO_EXTENSIONS and not f.name.startswith('.')]
        cat_list.append({
            "folder": cat.folder,
            "strategy": cat.strategy,
            "files": video_files,
            "config": cat.config,
            "mode": cat.mode,
            "strategy_preset": cat.strategy_preset,
        })
        total += len(video_files)

    if total == 0:
        raise HTTPException(400, "No video files found in selected categories")

    task_id = str(uuid.uuid4())[:8]
    task = TaskState(
        id=task_id,
        input_dir=str(input_dir),
        output_dir=str(output_dir),
        categories=cat_list,
        total_count=total,
        created_at=time.time(),
    )
    tasks[task_id] = task

    # Start processing in background
    asyncio.get_event_loop().create_task(_run_task(task))

    return {"task_id": task_id, "total": total}


@app.get("/api/tasks")
async def list_tasks():
    return [t.to_dict() for t in tasks.values()]


@app.get("/api/tasks/{task_id}")
async def get_task(task_id: str):
    task = tasks.get(task_id)
    if not task:
        raise HTTPException(404, "Task not found")
    return task.to_dict()


@app.post("/api/tasks/{task_id}/cancel")
async def cancel_task(task_id: str):
    task = tasks.get(task_id)
    if not task:
        raise HTTPException(404, "Task not found")
    task.cancel_requested = True
    # Kill running subprocess immediately
    if task._current_proc and task._current_proc.returncode is None:
        try:
            task._current_proc.kill()
        except Exception:
            pass
    return {"ok": True}


# ---------------------------------------------------------------------------
# WebSocket
# ---------------------------------------------------------------------------

@app.websocket("/ws/progress/{task_id}")
async def ws_progress(ws: WebSocket, task_id: str):
    await ws.accept()
    if task_id not in ws_connections:
        ws_connections[task_id] = []
    ws_connections[task_id].append(ws)

    # Send current state immediately
    task = tasks.get(task_id)
    if task:
        await ws.send_json({
            "type": "state",
            "status": task.status.value,
            "completed": task.completed_count,
            "failed": task.failed_count,
            "total": task.total_count,
            "current_file": task.current_file,
            "file_results": task.file_results,
        })

    try:
        while True:
            await ws.receive_text()  # keep alive
    except WebSocketDisconnect:
        ws_connections.get(task_id, []).remove(ws) if ws in ws_connections.get(task_id, []) else None


async def _broadcast(task_id: str, msg: dict):
    conns = ws_connections.get(task_id, [])
    dead = []
    for ws in conns:
        try:
            await ws.send_json(msg)
        except Exception:
            dead.append(ws)
    for ws in dead:
        conns.remove(ws)


# ---------------------------------------------------------------------------
# Task runner
# ---------------------------------------------------------------------------

async def _run_task(task: TaskState):
    """Execute a task: process videos via asyncio subprocess with real-time output."""
    task.status = TaskStatus.RUNNING
    task.started_at = time.time()

    # Open task log file
    from datetime import datetime
    log_file = LOGS_DIR / f"task_{task.id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    task_log = open(log_file, "w", encoding="utf-8")

    def _log(line: str):
        task_log.write(line + "\n")
        task_log.flush()

    _log(f"[TASK] id={task.id} started at {datetime.now().isoformat()}")
    _log(f"[TASK] input={task.input_dir} output={task.output_dir} total={task.total_count}")
    _log(f"[TASK] categories={json.dumps(task.categories, ensure_ascii=False)}")

    # Save last I/O dirs
    try:
        cfg = _load_config()
        cfg["last_input_dir"] = task.input_dir
        cfg["last_output_dir"] = task.output_dir
        _save_config(cfg)
    except Exception:
        pass

    await _broadcast(task.id, {
        "type": "started",
        "status": "running",
        "total": task.total_count,
    })

    video_index = 0
    for cat in task.categories:
        strategy = cat["strategy"]
        folder = cat["folder"]
        config = cat.get("config") or {}

        # Create output sub-directory
        out_sub = Path(task.output_dir) / folder
        out_sub.mkdir(parents=True, exist_ok=True)

        for file_cfg in cat["files"]:
            fname = file_cfg["filename"]
            outputs = file_cfg.get("outputs", [{"mode": "standard", "strategy_preset": "D"}])

            for out_idx, out_cfg in enumerate(outputs):
                mode = out_cfg.get("mode", "standard")
                strategy_preset = out_cfg.get("strategy_preset", "D")

                # Check cancel
                if task.cancel_requested:
                    task.status = TaskStatus.CANCELLED
                    task.finished_at = time.time()
                    _log(f"[TASK] stopped by user")
                    task_log.close()
                    await _broadcast(task.id, {"type": "cancelled", "status": "cancelled"})
                    return

                input_path = str(Path(task.input_dir) / folder / fname)
                video_id = generate_video_id(category=strategy, strategy=strategy_preset or "D")
                ext = Path(fname).suffix or ".mp4"
                output_fname = f"{video_id}{ext}"
                output_path = str(out_sub / output_fname)
                display_name = f"{folder}/{fname}" + (f" #{out_idx+1}" if len(outputs) > 1 else "")

                # For concat mode, collect all files in this category
                if mode == "concat":
                    all_paths = [str(Path(task.input_dir) / folder / fc["filename"]) for fc in cat["files"]]

                task.current_file = display_name
                _log(f"\n[FILE] {display_name} | strategy={strategy} mode={mode} preset={strategy_preset}")
                _log(f"[FILE] input={input_path}")
                _log(f"[FILE] output={output_path}")
                await _broadcast(task.id, {
                    "type": "file_start",
                    "filename": display_name,
                    "completed": task.completed_count,
                    "failed": task.failed_count,
                    "total": task.total_count,
                })

                t0 = time.time()
                try:
                    run_config = {**config, "_mode": mode, "_strategy_preset": strategy_preset}
                    if mode == "concat":
                        run_config["_input_paths"] = all_paths

                    if getattr(sys, 'frozen', False):
                        cmd = [RUN_PROCESSOR, strategy, input_path, output_path, str(video_index)]
                    else:
                        cmd = [sys.executable, RUN_PROCESSOR, strategy, input_path, output_path, str(video_index)]
                    cmd.append(json.dumps(run_config))
                    _log(f"[CMD] {' '.join(cmd)}")

                    proc = await asyncio.create_subprocess_exec(
                        *cmd,
                        stdout=asyncio.subprocess.PIPE,
                        stderr=asyncio.subprocess.STDOUT,
                        cwd=str(PROJECT_ROOT),
                    )
                    task._current_proc = proc

                    async for raw_line in proc.stdout:
                        line = raw_line.decode("utf-8", errors="replace").rstrip()
                        if line:
                            _log(line)
                            await _broadcast(task.id, {
                                "type": "file_log",
                                "filename": display_name,
                                "line": line,
                            })

                    returncode = await proc.wait()
                    task._current_proc = None
                    elapsed_s = round(time.time() - t0, 1)

                    # If killed by cancel, stop immediately
                    if task.cancel_requested:
                        task.status = TaskStatus.CANCELLED
                        task.finished_at = time.time()
                        _log(f"[TASK] stopped by user (killed subprocess)")
                        task_log.close()
                        await _broadcast(task.id, {"type": "cancelled", "status": "cancelled"})
                        return

                    success = returncode == 0
                    error = "" if success else f"exit code {returncode}"
                except Exception as e:
                    elapsed_s = round(time.time() - t0, 1)
                    task._current_proc = None
                    success = False
                    error = str(e)

                video_index += 1

                fr = {
                    "filename": display_name,
                    "video_id": video_id,
                    "output_file": output_fname,
                    "folder": folder,
                    "strategy": strategy,
                    "mode": mode,
                    "strategy_preset": strategy_preset,
                    "status": "done" if success else "failed",
                    "elapsed": elapsed_s,
                    "error": error,
                }
                task.file_results.append(fr)

                if success:
                    task.completed_count += 1
                    _log(f"[RESULT] {display_name} -> OK ({elapsed_s}s)")
                else:
                    task.failed_count += 1
                    _log(f"[RESULT] {display_name} -> FAILED ({elapsed_s}s) {error}")

                await _broadcast(task.id, {
                    "type": "file_done",
                    "filename": display_name,
                    "result": fr,
                    "completed": task.completed_count,
                    "failed": task.failed_count,
                    "total": task.total_count,
                })

    task.status = TaskStatus.COMPLETED if task.failed_count == 0 else TaskStatus.FAILED
    task.finished_at = time.time()
    task.current_file = ""

    elapsed_total = round(task.finished_at - task.started_at, 1)

    _log(f"\n[TASK] finished status={task.status.value} completed={task.completed_count} failed={task.failed_count} elapsed={elapsed_total}s")
    task_log.close()

    await _broadcast(task.id, {
        "type": "finished",
        "status": task.status.value,
        "completed": task.completed_count,
        "failed": task.failed_count,
        "total": task.total_count,
        "elapsed": elapsed_total,
    })

    # Save to history
    try:
        _append_history({
            "id": task.id,
            "timestamp": datetime.now().isoformat(timespec="seconds"),
            "input_dir": task.input_dir,
            "output_dir": task.output_dir,
            "categories": [
                {"folder": c["folder"], "strategy": c["strategy"],
                 "files": c.get("files", []),
                 "count": sum(len(fc.get("outputs", [1])) for fc in c.get("files", []))}
                for c in task.categories
            ],
            "total": task.total_count,
            "completed": task.completed_count,
            "failed": task.failed_count,
            "elapsed": elapsed_total,
            "status": task.status.value,
            "file_results": task.file_results,
        })
    except Exception:
        pass


# ---------------------------------------------------------------------------
# Static files (serve built frontend)
# ---------------------------------------------------------------------------

@app.get("/{full_path:path}")
async def serve_spa(full_path: str):
    """Serve the SPA index.html for all non-API routes."""
    if FRONTEND_DIST.exists():
        file_path = FRONTEND_DIST / full_path
        if file_path.is_file():
            return FileResponse(str(file_path))
        return FileResponse(str(FRONTEND_DIST / "index.html"))
    return {"message": "Frontend not built. Run: cd frontend && npm run build"}


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=True)
