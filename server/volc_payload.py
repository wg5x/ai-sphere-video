from __future__ import annotations

from typing import Any


DEFAULT_SPEAKER = "zh_female_vv_jupiter_bigtts"
DEFAULT_BOT_NAME = "赛博国潮小孩"
DEFAULT_SYSTEM_ROLE = "你是一个国潮风格的虚拟人，用简短、自然、友好的中文回答。"
DEFAULT_SPEAKING_STYLE = "活泼、清晰、不要太长。"


def build_start_session_payload(raw_config: dict[str, Any] | None) -> dict[str, Any]:
    config = _normalize_config(raw_config or {})
    payload = {
        "asr": {"extra": {}},
        "tts": {
            "speaker": config["speaker"],
            "extra": {},
            "audio_config": {
                "channel": 1,
                "format": "pcm_s16le",
                "sample_rate": 24000,
                "speech_rate": config["speechRate"],
                "loudness_rate": config["loudnessRate"],
            },
        },
        "dialog": {
            "bot_name": config["botName"],
            "system_role": config["systemRole"],
            "speaking_style": config["speakingStyle"],
            "dialog_id": "",
            "extra": {
                "strict_audit": True,
                "enable_conversation_truncate": True,
                "enable_user_query_exit": False,
                "model": "1.2.1.1",
            },
        },
    }
    return {"config": config, "payload": clean_object(payload), "warnings": []}


def clean_object(value: Any) -> Any:
    if isinstance(value, list):
        return [clean_object(item) for item in value]
    if not isinstance(value, dict):
        return value

    result: dict[str, Any] = {}
    for key, entry in value.items():
        if entry is None or entry == "":
            continue
        if isinstance(entry, (dict, list)):
            cleaned = clean_object(entry)
            if isinstance(cleaned, list) or cleaned:
                result[key] = cleaned
            continue
        result[key] = entry
    return result


def redact_payload(value: Any) -> Any:
    if isinstance(value, list):
        return [redact_payload(item) for item in value]
    if not isinstance(value, dict):
        return value

    result: dict[str, Any] = {}
    for key, entry in value.items():
        if any(token in key.lower() for token in ("key", "token", "secret")) and entry:
            result[key] = "<redacted>"
        else:
            result[key] = redact_payload(entry)
    return result


def _normalize_config(raw: dict[str, Any]) -> dict[str, Any]:
    return {
        "speaker": _string(raw.get("speaker"), DEFAULT_SPEAKER),
        "botName": _string(raw.get("botName"), DEFAULT_BOT_NAME)[:20],
        "systemRole": _string(raw.get("systemRole"), DEFAULT_SYSTEM_ROLE),
        "speakingStyle": _string(raw.get("speakingStyle"), DEFAULT_SPEAKING_STYLE),
        "openingLine": _string(raw.get("openingLine")),
        "speechRate": _int_range(raw.get("speechRate"), 0, -50, 100),
        "loudnessRate": _int_range(raw.get("loudnessRate"), 0, -50, 100),
    }


def _string(value: Any, default: str = "") -> str:
    text = str(value if value is not None else "").strip()
    return text or default


def _int_range(value: Any, default: int, minimum: int, maximum: int) -> int:
    try:
        number = int(value)
    except (TypeError, ValueError):
        number = default
    return max(minimum, min(maximum, number))
