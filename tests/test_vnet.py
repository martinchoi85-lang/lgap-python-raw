import unittest
import typing

from core.protocol import (
    VNetProtocol,
    FrameSyncStream,
    validate_packet,
    build_poll_packet
)

class TestVNetProtocol(unittest.TestCase):
    def test_vnet_poll_frame_generation(self) -> None:
        frame = VNetProtocol.build_poll_frame(unit_id=4, central_addr=0x00, seq=0x68)
        self.assertEqual(len(frame), 23)
        self.assertEqual(frame[0], 0xC1)
        self.assertEqual(frame[3], 0x04)
        self.assertEqual(frame[6], 0x01)
        self.assertEqual(frame[7], 0x68)
        self.assertEqual(frame[22], 0xFE)

    def test_vnet_control_frame_generation(self) -> None:
        cmd = {"id": 5, "target_temp": 22, "mode": 0x04}
        frame = VNetProtocol.build_control_frame(command=cmd, central_addr=0x00, seq=0x6A)
        self.assertEqual(len(frame), 23)
        self.assertEqual(frame[0], 0xC1)
        self.assertEqual(frame[3], 0x05)
        self.assertEqual(frame[6], 0x02)
        self.assertEqual(frame[7], 0x6A)
        self.assertEqual(frame[10], (22 - 15) & 0x0F)

    def test_vnet_frame_parsing(self) -> None:
        # 실측된 36바이트 응답 패킷
        raw_response = bytes.fromhex("41 E0 EF 0F 00 00 01 8A 00 80 21 00 00 06 68 06 01 01 00 00 00 00 00 01 00 00 02 02 07 03 01 06 88 89 46 EE")
        parsed = VNetProtocol.parse_frame(raw_response)
        self.assertEqual(parsed["raw_len"], 36)
        self.assertIn("target_temp", parsed)
        self.assertIn("room_temp", parsed)
        self.assertTrue(parsed["is_online"])

    def test_multi_frame_sync_stream(self) -> None:
        stream = FrameSyncStream()
        
        # 1. 23바이트 V-Net 질문 프레임 주입
        vnet_req = bytes.fromhex("C1 00 00 04 00 00 01 68 00 00 02 03 01 01 01 01 02 02 06 02 2C 4A FE")
        # 2. 36바이트 V-Net 응답 프레임 주입
        vnet_res = bytes.fromhex("41 E0 EF 0F 00 00 01 8A 00 80 21 00 00 06 68 06 01 01 00 00 00 00 00 01 00 00 02 02 07 03 01 06 88 89 46 EE")
        
        frames = stream.feed(vnet_req + vnet_res)
        self.assertEqual(len(frames), 2)
        self.assertEqual(frames[0][0], 0xC1)
        self.assertEqual(len(frames[0]), 23)
        self.assertEqual(frames[1][0], 0x41)
        self.assertEqual(len(frames[1]), 36)

if __name__ == "__main__":
    unittest.main()
