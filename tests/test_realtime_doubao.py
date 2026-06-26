import unittest

from server.expression import pick_expression
from server.volc_frames import make_audio_frame, make_json_frame, parse_server_frame
from server.volc_payload import build_start_session_payload


class RealtimeDoubaoTests(unittest.TestCase):
    def test_json_frame_round_trips_event_session_and_payload(self):
        frame = make_json_frame(150, {"hello": "你好"}, "session-1")

        parsed = parse_server_frame(frame)

        self.assertIsNotNone(parsed)
        self.assertEqual(parsed.event, 150)
        self.assertEqual(parsed.session_id, "session-1")
        self.assertEqual(parsed.payload, {"hello": "你好"})

    def test_audio_frame_round_trips_binary_payload(self):
        frame = make_audio_frame(352, b"\x01\x02", "session-1")

        parsed = parse_server_frame(frame)

        self.assertIsNotNone(parsed)
        self.assertEqual(parsed.event, 352)
        self.assertEqual(parsed.session_id, "session-1")
        self.assertEqual(parsed.payload, b"\x01\x02")

    def test_start_session_payload_uses_doubao_realtime_audio_contract(self):
        session = build_start_session_payload(
            {
                "speaker": "zh_female_vv_jupiter_bigtts",
                "botName": "赛博国潮小孩",
                "systemRole": "你是一个会用简短中文回答的虚拟人。",
                "speakingStyle": "自然、活泼。",
            }
        )

        payload = session["payload"]

        self.assertEqual(payload["tts"]["speaker"], "zh_female_vv_jupiter_bigtts")
        self.assertEqual(payload["tts"]["audio_config"]["format"], "pcm_s16le")
        self.assertEqual(payload["tts"]["audio_config"]["sample_rate"], 24000)
        self.assertEqual(payload["dialog"]["bot_name"], "赛博国潮小孩")
        self.assertEqual(payload["dialog"]["extra"]["model"], "1.2.1.1")

    def test_expression_picker_prefers_strong_emotion_keywords(self):
        self.assertEqual(pick_expression("哈哈哈太开心了", role="assistant"), "大笑")
        self.assertEqual(pick_expression("我有点难过，想哭", role="assistant"), "委屈哭")
        self.assertEqual(pick_expression("这个答案让我很惊讶", role="assistant"), "惊讶")
        self.assertEqual(pick_expression("让我想一想", role="assistant"), "思考")
        self.assertEqual(pick_expression("用户正在说话", role="user"), "思考")


if __name__ == "__main__":
    unittest.main()
