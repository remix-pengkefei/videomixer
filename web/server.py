"""VideoMixer Web Server - FastAPI backend."""

import asyncio
import json
import os
import shutil
import subprocess as sp
import sys
import time
import uuid
from contextlib import asynccontextmanager
from dataclasses import dataclass, field, asdict
from enum import Enum
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel

# Add project root to path so we can import src modules
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

DATA_DIR = PROJECT_ROOT / "data"
DATA_DIR.mkdir(exist_ok=True)
CONFIG_FILE = DATA_DIR / "config.json"
HISTORY_FILE = DATA_DIR / "history.json"

DEFAULT_STRATEGY_CONFIGS = {
    "handwriting": {
        "sticker_count": 14, "sparkle_count": 5, "sparkle_style": "gold",
        "color_scheme": "random", "enable_particles": True,
        "enable_decorations": True, "enable_border": True,
        "enable_color_preset": True, "enable_audio_fx": True,
    },
    "emotional": {
        "sticker_count": 20, "sparkle_count": 5, "sparkle_style": "pink",
        "color_scheme": "random", "enable_particles": True,
        "enable_decorations": True, "enable_border": True,
        "enable_color_preset": True, "enable_audio_fx": True,
    },
    "health": {
        "sticker_count": 20, "sparkle_count": 5, "sparkle_style": "warm",
        "color_scheme": "random", "enable_particles": True,
        "enable_decorations": True, "enable_border": True,
        "enable_color_preset": True, "enable_audio_fx": True,
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
    cancel_requested: bool = False

    def to_dict(self):
        d = asdict(self)
        d["status"] = self.status.value
        return d


# ---------------------------------------------------------------------------
# In-memory store
# ---------------------------------------------------------------------------

tasks: dict[str, TaskState] = {}
ws_connections: dict[str, list[WebSocket]] = {}  # task_id -> list of ws
RUN_PROCESSOR = str(Path(__file__).parent / "run_processor.py")


# ---------------------------------------------------------------------------
# FastAPI app
# ---------------------------------------------------------------------------

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

class CategoryInput(BaseModel):
    folder: str
    strategy: str
    config: Optional[dict] = None


class CreateTaskBody(BaseModel):
    input_dir: str
    output_dir: str
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
        strategy = "handwriting"  # default
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
            strategy = "handwriting"
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
    """Check remote origin for new commits via git fetch."""
    try:
        # git fetch origin (silent, timeout 15s)
        fetch_proc = await asyncio.create_subprocess_exec(
            "git", "fetch", "origin",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=str(PROJECT_ROOT),
        )
        await asyncio.wait_for(fetch_proc.communicate(), timeout=15)

        # Get local HEAD
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

        # Get current branch
        proc2 = await asyncio.create_subprocess_exec(
            "git", "rev-parse", "--abbrev-ref", "HEAD",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=str(PROJECT_ROOT),
        )
        stdout2, _ = await proc2.communicate()
        branch = stdout2.decode().strip() or "main"

        # Check commits between local and origin
        proc3 = await asyncio.create_subprocess_exec(
            "git", "log", f"HEAD..origin/{branch}", "--oneline", "--no-decorate",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=str(PROJECT_ROOT),
        )
        stdout3, stderr3 = await proc3.communicate()
        lines = [l.strip() for l in stdout3.decode().strip().split("\n") if l.strip()]

        if not lines:
            return {"has_update": False, "local_sha": local_sha[:7]}

        commits = []
        for line in lines[:5]:
            parts = line.split(" ", 1)
            commits.append({
                "sha": parts[0],
                "message": parts[1] if len(parts) > 1 else "",
            })

        return {
            "has_update": True,
            "ahead": len(lines),
            "local_sha": local_sha[:7],
            "commits": commits,
        }
    except asyncio.TimeoutError:
        return {"has_update": False, "error": "fetch timeout"}
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
        config = cat.get("config")

        # Create output sub-directory
        out_sub = Path(task.output_dir) / folder
        out_sub.mkdir(parents=True, exist_ok=True)

        for fname in cat["files"]:
            if task.cancel_requested:
                task.status = TaskStatus.CANCELLED
                task.finished_at = time.time()
                await _broadcast(task.id, {"type": "cancelled", "status": "cancelled"})
                return

            input_path = str(Path(task.input_dir) / folder / fname)
            output_path = str(out_sub / fname)
            display_name = f"{folder}/{fname}"

            task.current_file = display_name
            await _broadcast(task.id, {
                "type": "file_start",
                "filename": display_name,
                "completed": task.completed_count,
                "failed": task.failed_count,
                "total": task.total_count,
            })

            t0 = time.time()
            try:
                cmd = [sys.executable, RUN_PROCESSOR, strategy, input_path, output_path, str(video_index)]
                if config:
                    cmd.append(json.dumps(config))

                proc = await asyncio.create_subprocess_exec(
                    *cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.STDOUT,
                    cwd=str(PROJECT_ROOT),
                )

                async for raw_line in proc.stdout:
                    line = raw_line.decode("utf-8", errors="replace").rstrip()
                    if line:
                        await _broadcast(task.id, {
                            "type": "file_log",
                            "filename": display_name,
                            "line": line,
                        })

                returncode = await proc.wait()
                elapsed_s = round(time.time() - t0, 1)
                success = returncode == 0
                error = "" if success else f"exit code {returncode}"
            except Exception as e:
                elapsed_s = round(time.time() - t0, 1)
                success = False
                error = str(e)

            video_index += 1

            fr = {
                "filename": display_name,
                "status": "done" if success else "failed",
                "elapsed": elapsed_s,
                "error": error,
            }
            task.file_results.append(fr)

            if success:
                task.completed_count += 1
            else:
                task.failed_count += 1

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
        from datetime import datetime
        _append_history({
            "id": task.id,
            "timestamp": datetime.now().isoformat(timespec="seconds"),
            "input_dir": task.input_dir,
            "output_dir": task.output_dir,
            "categories": [
                {"folder": c["folder"], "strategy": c["strategy"], "count": len(c["files"])}
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
