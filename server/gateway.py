from __future__ import annotations

import asyncio
import base64
import json
import uuid
from datetime import datetime
from typing import Any

import websockets
from fastapi import WebSocket, WebSocketDisconnect

from .config import get_volc_headers, get_volc_ws_url, has_volc_credentials
from .events import CLIENT_EVENTS, SERVER_EVENTS
from .expression import pick_expression
from .volc_frames import make_audio_frame, make_json_frame, parse_server_frame
from .volc_payload import build_start_session_payload, redact_payload


class RealtimeGateway:
    def __init__(self, client_ws: WebSocket) -> None:
        self.client_ws = client_ws
        self.upstream = None
        self.upstream_task: asyncio.Task | None = None
        self.delayed_start_task: asyncio.Task | None = None
        self.session_id = ""
        self.upstream_ready = False
        self.closing = False
        self.assistant_output_seq = 0
        self.current_assistant_output_id = ""
        self.current_assistant_text = ""
        self.current_user_text = ""

    async def run(self) -> None:
        await self.client_ws.accept()
        try:
            while True:
                message = await self.client_ws.receive()
                if message.get("type") == "websocket.disconnect":
                    break
                if message.get("bytes") is not None:
                    await self._handle_binary(message["bytes"])
                    continue
                if message.get("text") is not None:
                    await self._handle_text(message["text"])
        except WebSocketDisconnect:
            pass
        finally:
            await self._close_upstream()
            await self._cancel_tasks()

    async def _handle_binary(self, raw: bytes) -> None:
        if self.upstream and self.session_id:
            try:
                await self.upstream.send(make_audio_frame(CLIENT_EVENTS["TASK_REQUEST"], raw, self.session_id))
            except Exception:
                await self._send_json({"type": "error", "message": "发送音频到豆包实时语音失败。"})

    async def _handle_text(self, raw: str) -> None:
        try:
            message = json.loads(raw)
        except json.JSONDecodeError:
            await self._send_json({"type": "error", "message": "无法解析客户端消息。"})
            return

        message_type = message.get("type")
        if message_type == "start":
            await self._cancel_tasks()
            await self._close_upstream()
            session = build_start_session_payload((message.get("payload") or {}).get("config") or {})

            if not has_volc_credentials():
                await self._send_json(
                    {
                        "type": "error",
                        "message": "缺少豆包实时语音配置：请配置 VOLC_API_APP_ID 和 VOLC_API_ACCESS_KEY。",
                        "payload": redact_payload(session["payload"]),
                    }
                )
                await self._send_json({"type": "status", "status": "idle"})
                return

            await self._start_session(session)
            return

        if message_type == "user_text":
            text = str(message.get("text") or "").strip()
            if self.upstream and self.session_id and text:
                await self._emit_user_text(text)
                await self.upstream.send(make_json_frame(CLIENT_EVENTS["CHAT_TEXT_QUERY"], {"content": text}, self.session_id))
            return

        if message_type == "interrupt":
            if self.upstream and self.session_id:
                await self.upstream.send(make_json_frame(CLIENT_EVENTS["CLIENT_INTERRUPT"], {}, self.session_id))
            await self._send_json({"type": "interrupt_ack", "targetOutputId": self.current_assistant_output_id})
            return

        if message_type == "finish":
            await self._finish()

    async def _start_session(self, session: dict[str, Any]) -> None:
        payload = session["payload"]
        connect_id = str(uuid.uuid4())
        self.session_id = str(uuid.uuid4())
        self.upstream_ready = False
        self.closing = False
        self.assistant_output_seq = 0
        self.current_assistant_output_id = ""
        self.current_assistant_text = ""
        self.current_user_text = ""

        await self._send_json({"type": "payload", "payload": redact_payload(payload), "mode": "volcengine"})
        await self._send_json({"type": "status", "status": "connecting", "mode": "volcengine", "sessionId": self.session_id})

        try:
            self.upstream = await websockets.connect(get_volc_ws_url(), additional_headers=get_volc_headers(connect_id))
            await self.upstream.send(make_json_frame(CLIENT_EVENTS["START_CONNECTION"], {}))
            self.delayed_start_task = asyncio.create_task(self._delayed_send_session_start(self.upstream, payload))
            self.upstream_task = asyncio.create_task(self._upstream_loop(self.upstream, payload, session["config"]))
        except Exception as exc:
            await self._send_json({"type": "error", "message": f"连接豆包实时语音 WebSocket 失败：{exc}"})
            await self._send_json({"type": "status", "status": "idle", "mode": "volcengine"})

    async def _upstream_loop(self, upstream, payload: dict[str, Any], config: dict[str, Any]) -> None:
        try:
            async for data in upstream:
                if self.upstream is not upstream:
                    return
                frame = parse_server_frame(data)
                if not frame:
                    continue

                if frame.message_type == 0x0F:
                    error_text = frame.payload.get("error") if isinstance(frame.payload, dict) else None
                    await self._send_json({"type": "error", "message": error_text or "豆包实时语音返回错误。"})
                    continue

                if frame.event == SERVER_EVENTS["CONNECTION_STARTED"]:
                    await self._send_session_start(upstream, payload)
                    continue

                if frame.event in (SERVER_EVENTS["CONNECTION_FAILED"], SERVER_EVENTS["SESSION_FAILED"]):
                    error_text = frame.payload.get("error") if isinstance(frame.payload, dict) else None
                    await self._send_json({"type": "error", "message": error_text or "豆包实时语音连接失败。"})
                    continue

                if frame.event == SERVER_EVENTS["SESSION_STARTED"]:
                    await self._send_json({"type": "status", "status": "connected", "mode": "volcengine"})
                    if config.get("openingLine"):
                        await self._emit_assistant_text(config["openingLine"], force_new=True)
                        await upstream.send(make_json_frame(CLIENT_EVENTS["SAY_HELLO"], {"content": config["openingLine"]}, self.session_id))
                    continue

                if frame.event == SERVER_EVENTS["ASR_RESPONSE"] and isinstance(frame.payload, dict):
                    text = _extract_asr_text(frame.payload)
                    if text:
                        await self._emit_user_text(text)
                    continue

                if frame.event == SERVER_EVENTS["CHAT_RESPONSE"] and isinstance(frame.payload, dict):
                    content = str(frame.payload.get("content") or "").strip()
                    if content:
                        await self._emit_assistant_text(_merge_stream_text(self.current_assistant_text, content))
                    continue

                if frame.event in (SERVER_EVENTS["TTS_SENTENCE_START"], SERVER_EVENTS["TTS_SENTENCE_END"]) and isinstance(frame.payload, dict):
                    text = str(frame.payload.get("text") or "").strip()
                    if text:
                        await self._emit_assistant_text(text)
                    continue

                if frame.event == SERVER_EVENTS["TTS_RESPONSE"] and isinstance(frame.payload, bytes):
                    await self._emit_audio(frame.payload)
                    continue

                if frame.event == SERVER_EVENTS["USAGE_RESPONSE"] and isinstance(frame.payload, dict):
                    await self._send_json({"type": "usage", "payload": frame.payload.get("usage")})
                    continue

                if frame.event in (SERVER_EVENTS["SESSION_FINISHED"], SERVER_EVENTS["CONNECTION_FINISHED"]):
                    await self._send_json({"type": "status", "status": "idle", "mode": "volcengine"})
                    self.session_id = ""
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            if not self.closing:
                await self._send_json({"type": "error", "message": f"豆包实时语音连接已中断：{exc}"})
                await self._send_json({"type": "status", "status": "idle", "mode": "volcengine"})
        finally:
            if self.upstream is upstream:
                self.upstream = None
                self.session_id = ""
                self.upstream_ready = False

    async def _send_session_start(self, upstream, payload: dict[str, Any]) -> None:
        if self.upstream is not upstream or self.upstream_ready or not self.session_id:
            return
        self.upstream_ready = True
        await upstream.send(make_json_frame(CLIENT_EVENTS["START_SESSION"], payload, self.session_id))

    async def _delayed_send_session_start(self, upstream, payload: dict[str, Any]) -> None:
        await asyncio.sleep(0.6)
        await self._send_session_start(upstream, payload)

    async def _finish(self) -> None:
        if self.upstream and self.session_id:
            try:
                await self.upstream.send(make_json_frame(CLIENT_EVENTS["FINISH_SESSION"], {}, self.session_id))
            except Exception:
                pass
        await self._send_json({"type": "status", "status": "idle", "mode": "volcengine"})
        await self._close_upstream()
        try:
            await self.client_ws.close()
        except RuntimeError:
            pass

    async def _close_upstream(self) -> None:
        self.closing = True
        upstream = self.upstream
        self.upstream = None
        self.session_id = ""
        self.upstream_ready = False
        if upstream:
            try:
                await upstream.close()
            except Exception:
                pass

    async def _cancel_tasks(self) -> None:
        for attr in ("delayed_start_task", "upstream_task"):
            task = getattr(self, attr)
            if task:
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
                setattr(self, attr, None)

    async def _emit_user_text(self, text: str) -> None:
        self.current_user_text = text
        await self._send_json({"type": "event", "event": _make_event("asr", f"ASRResponse: {text}", expression=pick_expression(text, role="user"))})

    async def _emit_assistant_text(self, text: str, *, force_new: bool = False) -> None:
        output_id = self._next_assistant_output_id() if force_new or not self.current_assistant_output_id else self.current_assistant_output_id
        self.current_assistant_output_id = output_id
        self.current_assistant_text = text
        await self._send_json(
            {
                "type": "event",
                "event": _make_event(
                    "assistant",
                    f"ChatResponse: {text}",
                    output_id=output_id,
                    expression=pick_expression(text, role="assistant"),
                ),
            }
        )

    async def _emit_audio(self, audio: bytes) -> None:
        output_id = self.current_assistant_output_id or self._next_assistant_output_id()
        await self._send_json(
            {
                "type": "audio",
                "mime": "audio/pcm; format=s16le; rate=24000",
                "data": base64.b64encode(audio).decode("ascii"),
                "outputId": output_id,
            }
        )

    async def _send_json(self, payload: dict[str, Any]) -> None:
        try:
            await self.client_ws.send_text(json.dumps(payload, ensure_ascii=False))
        except Exception:
            pass

    def _next_assistant_output_id(self) -> str:
        self.assistant_output_seq += 1
        return f"assistant-output-{self.assistant_output_seq}"


def _make_event(event_type: str, text: str, *, output_id: str | None = None, expression: str = "开心") -> dict[str, str]:
    event = {
        "id": str(uuid.uuid4()),
        "type": event_type,
        "text": text,
        "at": datetime.now().strftime("%H:%M:%S"),
        "expression": expression,
    }
    if output_id:
        event["outputId"] = output_id
    return event


def _extract_asr_text(payload: dict[str, Any]) -> str:
    results = payload.get("results")
    if not isinstance(results, list):
        return ""
    texts = [str(item.get("text") or "").strip() for item in results if isinstance(item, dict) and item.get("text")]
    return texts[-1] if texts else ""


def _merge_stream_text(previous: str, current: str) -> str:
    previous_text = str(previous or "").strip()
    current_text = str(current or "").strip()
    if not previous_text:
        return current_text
    if not current_text or current_text in previous_text:
        return previous_text
    if previous_text in current_text:
        return current_text
    return previous_text + current_text
