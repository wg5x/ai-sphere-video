from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, Request, WebSocket
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from .config import has_volc_credentials, load_local_env
from .gateway import RealtimeGateway
from .volc_payload import build_start_session_payload, redact_payload


ROOT = Path(__file__).resolve().parents[1]
WEB_DIR = ROOT / "web"

load_local_env()

app = FastAPI(title="ai-sphere-video realtime voice")
app.mount("/raw", StaticFiles(directory=ROOT / "raw"), name="raw")
app.mount("/outputs", StaticFiles(directory=ROOT / "outputs"), name="outputs")
app.mount("/web", StaticFiles(directory=WEB_DIR), name="web")


@app.get("/")
async def index():
    return FileResponse(WEB_DIR / "index.html")


@app.get("/health")
async def health():
    return {"ok": True, "volcengine": has_volc_credentials()}


@app.post("/payload-preview")
async def payload_preview(request: Request):
    try:
        body = await request.json()
        session = build_start_session_payload((body or {}).get("config") or {})
        warnings = list(session["warnings"])
        if not has_volc_credentials():
            warnings.append("缺少豆包实时语音配置：请配置 VOLC_API_APP_ID 和 VOLC_API_ACCESS_KEY。")
        return {"mode": "volcengine", "payload": redact_payload(session["payload"]), "warnings": warnings}
    except Exception as exc:
        return JSONResponse({"error": str(exc) or "无法生成 payload。"}, status_code=400)


@app.websocket("/realtime")
async def realtime(websocket: WebSocket):
    await RealtimeGateway(websocket).run()
