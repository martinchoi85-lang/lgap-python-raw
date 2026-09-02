import unittest
import typing

from core.protocol import (
    calculate_checksum,
    validate_packet,
    parse_packet,
    build_poll_packet,
    build_control_packet,
    PACKET_SIZE
)
from core.state import StateManager
from core.polling import LgapEngine
from tests.mock_aircon import MockSerial

class TestLgapProtocol(unittest.TestCase):
    def test_build_poll_packet_checksum(self) -> None:
        for unit_id in range(1, 16):
            packet = build_poll_packet(unit_id)
            self.assertEqual(len(packet), PACKET_SIZE)
            self.assertTrue(validate_packet(packet), f"Unit {unit_id} poll packet checksum failed")
            self.assertEqual(packet[0], 0x00)
            self.assertEqual(packet[1], unit_id)

    def test_build_control_packet_checksum(self) -> None:
        commands = [
            {"id": 1, "target_temp": 18, "mode": 0x00, "fan_speed": 0x04},
            {"id": 2, "target_temp": 26, "mode": 0x04, "fan_speed": 0x08},
            {"id": 3, "target_temp": 30},
            {"id": 4, "target_temp": 16},
        ]
        for cmd in commands:
            packet = build_control_packet(cmd)
            self.assertEqual(len(packet), PACKET_SIZE)
            self.assertTrue(validate_packet(packet), f"Command {cmd} control packet checksum failed")
            self.assertEqual(packet[0], 0x00)
            self.assertEqual(packet[1], cmd["id"])
            self.assertEqual(packet[2], 0xFF)
            self.assertEqual(packet[7] & 0x0F, (cmd["target_temp"] - 15) & 0x0F)

    def test_mock_serial_integration(self) -> None:
        state_mgr = StateManager()
        engine = LgapEngine(state_manager=state_mgr, serial_class=MockSerial)
        self.assertTrue(engine.connect_serial())

        # 1. 폴링 패킷 트랜잭션 검증 (Mock이 체크섬 확인 후 정상 응답 반환하는지)
        poll_pkt = build_poll_packet(1)
        rx = engine._execute_transaction(poll_pkt)
        self.assertIsNotNone(rx)
        self.assertTrue(validate_packet(rx))
        parsed = parse_packet(rx)
        self.assertEqual(parsed["target_temp"], 24)

        # 2. 제어 패킷 트랜잭션 검증
        ctrl_pkt = build_control_packet({"id": 1, "target_temp": 20})
        rx_ctrl = engine._execute_transaction(ctrl_pkt)
        self.assertIsNotNone(rx_ctrl)
        self.assertTrue(validate_packet(rx_ctrl))
        parsed_ctrl = parse_packet(rx_ctrl)
        self.assertEqual(parsed_ctrl["target_temp"], 20)

if __name__ == "__main__":
    unittest.main()
