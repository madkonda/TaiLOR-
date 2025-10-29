import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import List, Optional

from fastapi import FastAPI, File, Form, Request, UploadFile
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.templating import Jinja2Templates
try:
    from dotenv import load_dotenv  # type: ignore
    load_dotenv()
except Exception:
    pass
from sam2_runner import Sam2NotAvailable, run_sam2_on_points  # type: ignore


BASE_DIR = Path(__file__).resolve().parent
TEMPLATES_DIR = BASE_DIR / "templates"
STATIC_DIR = BASE_DIR / "static"

# Target video storage directory (as requested)
VIDEOS_DIR = Path("/home/morsestudio/sam2/videos")
FRAMES_SUFFIX = "_frames"


def ensure_directories() -> None:
    VIDEOS_DIR.mkdir(parents=True, exist_ok=True)
    (STATIC_DIR / "css").mkdir(parents=True, exist_ok=True)
    (STATIC_DIR / "js").mkdir(parents=True, exist_ok=True)


ensure_directories()

app = FastAPI(title="TaiLOR Video Frames")
cors_env = os.getenv("CORS_ORIGINS", "")
origins = [o.strip() for o in cors_env.split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins if origins else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static assets
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# Mount raw and generated media as static for easy access
app.mount("/videos", StaticFiles(directory=str(VIDEOS_DIR)), name="videos")

templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


def video_basename(file_name: str) -> str:
    name = Path(file_name).name
    return str(Path(name).with_suffix(""))


def frames_dir_for(video_path: Path) -> Path:
    base = video_basename(video_path.name)
    return VIDEOS_DIR / f"{base}{FRAMES_SUFFIX}"


def list_videos() -> List[str]:
    items: List[str] = []
    for p in VIDEOS_DIR.iterdir() if VIDEOS_DIR.exists() else []:
        if p.is_file() and p.suffix.lower() in {".mp4", ".mov", ".mkv", ".avi", ".webm"}:
            items.append(p.name)
    return sorted(items, key=str.lower)


def list_frames(video_stem: str) -> List[str]:
    frames_dir = VIDEOS_DIR / f"{video_stem}{FRAMES_SUFFIX}"
    if not frames_dir.exists():
        return []
    frames = [f"/videos/{frames_dir.name}/{p.name}" for p in sorted(frames_dir.iterdir()) if p.suffix.lower() in {".png", ".jpg", ".jpeg"}]
    return frames


def _resolve_ffmpeg_bin() -> str:
    # 1) Explicit env var
    ff = os.getenv("FFMPEG_BIN")
    if ff:
        return ff
    # 2) Current python's bin dir (conda envs)
    py_dir = Path(sys.executable).parent
    conda_ff = py_dir / "ffmpeg"
    if conda_ff.exists():
        return str(conda_ff)
    # 3) CONDA_PREFIX
    conda_prefix = os.getenv("CONDA_PREFIX")
    if conda_prefix:
        cp_ff = Path(conda_prefix) / "bin" / "ffmpeg"
        if cp_ff.exists():
            return str(cp_ff)
    # 4) Known env path for `sam2`
    known_sam2 = Path("/home/morsestudio/anaconda3/envs/sam2/bin/ffmpeg")
    if known_sam2.exists():
        return str(known_sam2)
    # 5) PATH
    which_ff = shutil.which("ffmpeg")
    if which_ff:
        return which_ff
    # Fallback literal (will likely fail, but keeps error consistent)
    return "ffmpeg"


def run_ffmpeg_extract_frames(src_video: Path, out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    # Extract every 10th frame of a 30fps video => 3 fps; start numbering at 000000; save as %06d.jpg
    cmd = [
        _resolve_ffmpeg_bin(),
        "-y",
        "-i",
        str(src_video),
        "-vf",
        "fps=3",
        "-start_number",
        "0",
        "-q:v",
        "2",
        str(out_dir / "%06d.jpg"),
    ]
    try:
        subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except FileNotFoundError as e:
        raise RuntimeError("ffmpeg not found on system PATH.") from e
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"ffmpeg failed: {e.stderr.decode(errors='ignore')}") from e


def _resolve_sam2_paths() -> tuple[Path, Path]:
    """Resolve SAM2 config and checkpoint from env or common locations.

    Env vars:
      - SAM2_CONFIG: absolute path to YAML
      - SAM2_CHECKPOINT: absolute path to .pt
    Fallbacks checked in order:
      - /home/morsestudio/sam2/configs/sam2.1/sam2.1_hiera_l.yaml
      - /home/morsestudio/sam2/checkpoints/sam2.1_hiera_large.pt
      - ../checkpoints/sam2.1_hiera_large.pt (relative to server dir)
      - configs/sam2.1/sam2.1_hiera_l.yaml (relative to server dir)
    """
    env_cfg = os.getenv("SAM2_CONFIG")
    env_ckpt = os.getenv("SAM2_CHECKPOINT")
    if env_cfg and env_ckpt:
        cfg_p = Path(env_cfg)
        ckpt_p = Path(env_ckpt)
        if cfg_p.exists() and ckpt_p.exists():
            return cfg_p, ckpt_p

    candidates_cfg = []
    candidates_ckpt = []

    # Prefer /home/morsestudio/sam2 tree, search recursively
    sam2_root = Path("/home/morsestudio/sam2")
    if sam2_root.exists():
        specific_cfg = sam2_root / "configs" / "sam2.1" / "sam2.1_hiera_l.yaml"
        if specific_cfg.exists():
            candidates_cfg.append(specific_cfg)
        candidates_cfg.extend(list(sam2_root.rglob("sam2.1_hiera_l.yaml")))

        specific_ckpt = sam2_root / "checkpoints" / "sam2.1_hiera_large.pt"
        if specific_ckpt.exists():
            candidates_ckpt.append(specific_ckpt)
        candidates_ckpt.extend(list(sam2_root.rglob("*.pt")))

    # Project local fallbacks
    candidates_cfg.append((BASE_DIR / "configs" / "sam2.1" / "sam2.1_hiera_l.yaml").resolve())
    candidates_ckpt.append((BASE_DIR / ".." / "checkpoints" / "sam2.1_hiera_large.pt").resolve())

    cfg_found = next((p for p in candidates_cfg if p.exists()), None)
    ckpt_found = next((p for p in candidates_ckpt if p.exists()), None)
    if cfg_found and ckpt_found:
        return cfg_found, ckpt_found

    raise FileNotFoundError(
        "SAM2 config/checkpoint not found. Set SAM2_CONFIG and SAM2_CHECKPOINT env vars to absolute paths."
    )


@app.get("/", response_class=HTMLResponse)
async def home(request: Request, tab: Optional[str] = None) -> HTMLResponse:
    active_tab = tab or "upload"
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "active_tab": active_tab,
            "videos": list_videos(),
        },
    )


@app.post("/upload")
async def upload_video(request: Request, file: UploadFile = File(...)):
    VIDEOS_DIR.mkdir(parents=True, exist_ok=True)

    target_path = VIDEOS_DIR / Path(file.filename).name

    with target_path.open("wb") as out_f:
        shutil.copyfileobj(file.file, out_f)

    frames_out = frames_dir_for(target_path)
    try:
        run_ffmpeg_extract_frames(target_path, frames_out)
    except RuntimeError as e:
        return templates.TemplateResponse(
            "index.html",
            {
                "request": request,
                "active_tab": "upload",
                "videos": list_videos(),
                "error": str(e),
            },
            status_code=500,
        )

    return RedirectResponse(url=f"/gallery?video={video_basename(target_path.name)}", status_code=303)


@app.get("/gallery", response_class=HTMLResponse)
async def gallery(request: Request, video: Optional[str] = None) -> HTMLResponse:
    chosen = video
    frames: List[str] = list_frames(chosen) if chosen else []
    return templates.TemplateResponse(
        "gallery.html",
        {
            "request": request,
            "videos": list_videos(),
            "selected": chosen,
            "frames": frames,
        },
    )


@app.get("/api/frames")
async def api_frames(video: str):
    return JSONResponse({"frames": list_frames(video)})


@app.get("/segment", response_class=HTMLResponse)
async def segment(request: Request, video: Optional[str] = None) -> HTMLResponse:
    frames: List[str] = list_frames(video) if video else []
    return templates.TemplateResponse(
        "segment.html",
        {
            "request": request,
            "active_tab": "segment",
            "videos": list_videos(),
            "selected": video,
            "frames": frames,
            "notice": request.query_params.get("notice"),
            "error": request.query_params.get("error"),
        },
    )


@app.post("/api/segment")
async def api_segment(request: Request, video: str = Form(...), frame: str = Form(...), x1: int = Form(...), y1: int = Form(...), x2: int = Form(...), y2: int = Form(...)):
    # Map frame URL back to filesystem path
    # Example frame: /videos/<stem>_frames/frame_0001.png
    if not frame.startswith("/videos/"):
        return RedirectResponse(url=f"/segment?video={video}&error=Invalid frame path", status_code=303)
    rel = frame[len("/videos/") :]
    frame_path = VIDEOS_DIR / rel

    # Frames directory from selected video
    frames_dir = VIDEOS_DIR / f"{video}{FRAMES_SUFFIX}"
    if not frames_dir.exists():
        return RedirectResponse(url=f"/segment?video={video}&error=Frames folder not found", status_code=303)

    # SAM2 model config and checkpoint
    try:
        model_cfg, checkpoint = _resolve_sam2_paths()
    except FileNotFoundError as e:
        return RedirectResponse(url=f"/segment?video={video}&error={str(e)}", status_code=303)

    try:
        _ = run_sam2_on_points(
            frames_dir=frames_dir,
            coords=[(float(x1), float(y1)), (float(x2), float(y2))],
            model_cfg=model_cfg,
            checkpoint=checkpoint,
        )
        notice = f"Segmentation started for {video}."
        return RedirectResponse(url=f"/segment?video={video}&notice={notice}", status_code=303)
    except Sam2NotAvailable as e:
        return RedirectResponse(url=f"/segment?video={video}&error={str(e)}", status_code=303)
    except Exception as e:
        return RedirectResponse(url=f"/segment?video={video}&error=Segmentation failed", status_code=303)


# Health endpoint
@app.get("/health")
async def health():
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8080, reload=True)


