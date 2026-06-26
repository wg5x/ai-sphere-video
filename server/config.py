from __future__ import annotations

import os
from pathlib import Path


DEFAULT_VOLC_WS_URL = "wss://openspeech.bytedance.com/api/v3/realtime/dialogue"
DEFAULT_VOLC_RESOURCE_ID = "volc.speech.dialog"
PUBLIC_APP_KEY = "PlgvMymc7f3tQnJ6"
ROOT = Path(__file__).resolve().parents[1]
LOCAL_ENV_FILES = (
    ROOT / ".env.local",
    ROOT / ".env",
    ROOT / "config" / "env" / ".env.local",
    Path.home() / "gitee" / "ECHORURA" / "voice-engine" / "src" / ".env.local",
)


def load_local_env() -> None:
    for path in LOCAL_ENV_FILES:
        if not path.exists():
            continue
        for line in path.read_text(encoding="utf-8").splitlines():
            trimmed = line.strip()
            if not trimmed or trimmed.startswith("#") or "=" not in trimmed:
                continue
            key, value = trimmed.split("=", 1)
            key = key.strip()
            if key and key not in os.environ:
                os.environ[key] = value.strip().strip("'\"")


def has_volc_credentials() -> bool:
    return bool(os.environ.get("VOLC_API_APP_ID") and os.environ.get("VOLC_API_ACCESS_KEY"))


def get_volc_ws_url() -> str:
    return os.environ.get("VOLC_WS_URL") or DEFAULT_VOLC_WS_URL


def get_volc_headers(connect_id: str) -> dict[str, str]:
    return {
        "X-Api-App-ID": os.environ.get("VOLC_API_APP_ID", ""),
        "X-Api-Access-Key": os.environ.get("VOLC_API_ACCESS_KEY", ""),
        "X-Api-Resource-Id": os.environ.get("VOLC_API_RESOURCE_ID") or DEFAULT_VOLC_RESOURCE_ID,
        "X-Api-App-Key": os.environ.get("VOLC_API_APP_KEY") or PUBLIC_APP_KEY,
        "X-Api-Connect-Id": connect_id,
    }
