# TaiLOR – Video → Frames (FastAPI UI)

Elegant dashboard to upload a video and extract frames, inspired by TextMagic CRM dashboard patterns highlighted by Eleken.

- UI inspiration: https://www.eleken.co/blog-posts/dashboard-design-examples-that-catch-the-eye
- Target storage directory: `/home/morsestudio/sam2/videos`

## Run locally

Requirements:
- Python 3.11+
- ffmpeg installed and available on PATH (`ffmpeg -version`)

Install deps (optionally in `conda activate sam2`):

```bash
pip install -U fastapi uvicorn[standard] python-multipart jinja2
```

Start the server:

```bash
cd /home/morsestudio/TaiLOR/server
python main.py  # or: uvicorn main:app --host 0.0.0.0 --port 8080 --reload
```

Open: http://localhost:8080

## Endpoints

- GET `/` – Dashboard (Upload + Recent videos)
- POST `/upload` – Upload a video; saves to `/home/morsestudio/sam2/videos` and extracts frames
- GET `/gallery?video=<basename>` – Frames gallery
- GET `/api/frames?video=<basename>` – JSON list of frames
- Static mounts:
  - `/static/*` – UI assets
  - `/videos/*` – Raw videos and extracted frames (read-only)

## Notes

- Frames are written to `/home/morsestudio/sam2/videos/<video_basename>_frames/frame_0001.png` etc.
- If ffmpeg is not installed, uploads will succeed but extraction will fail with a helpful error.
- For production, consider placing the app behind a reverse proxy and a CDN for `/videos/*`.

## Deployment (Vercel vs Server)

- Vercel serverless file systems are ephemeral; writing to `/home/...` is not supported. Host this FastAPI app on a VM/container where `/home/morsestudio/sam2/videos` is available, or switch to object storage (S3/GCS/DO Spaces) and update paths.
- Custom domain: `tailor.morsestudio.dev` can be pointed to your server or Vercel. If you redeploy/rename projects, update DNS accordingly.




