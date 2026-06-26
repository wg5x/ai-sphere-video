# ai-sphere-video

固定国潮舞台背景的实时语音虚拟人原型。

## 运行

```bash
python3 -m pip install -r requirements.txt
cp .env.example .env.local
python3 -m uvicorn server.main:app --host 127.0.0.1 --port 8788
```

打开 `http://127.0.0.1:8788/`。

本地也会尝试读取 `~/gitee/ECHORURA/voice-engine/src/.env.local` 中的 `VOLC_*` 配置，方便复用已有豆包实时语音账号。

## 测试

```bash
python3 -m unittest tests/test_realtime_doubao.py tests/test_virtual_person_video.py
node --test tests/lip_sync.test.mjs tests/web_audio.test.mjs
```
