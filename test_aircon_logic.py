import unittest
from unittest.mock import MagicMock, patch
import json

from mapping_helper import MappingHelper
from mqtt_manager import MqttManager
from app_logger import AppLogger

class TestAirconLogic(unittest.TestCase):
    
    def setUp(self):
        AppLogger.log("TestAirconLogic.setUp", {}, "Initialize test environment")
        
    def test_mapping_helper(self):
        AppLogger.log("TestAirconLogic.test_mapping_helper", {}, "Test map_mode_to_homey and map_mode_to_esp")
        
        # 1. map_mode_to_homey 검증
        self.assertEqual(MappingHelper.map_mode_to_homey("cool"), "cool")
        self.assertEqual(MappingHelper.map_mode_to_homey("dry"), "auto")
        # 잘못된 모드 입력 (Fallback: None)
        self.assertIsNone(MappingHelper.map_mode_to_homey("UNKNOWN_MODE"))
        
        # 2. map_mode_to_esp 검증
        self.assertEqual(MappingHelper.map_mode_to_esp("HEAT"), "heat")
        self.assertEqual(MappingHelper.map_mode_to_esp("off"), "off")
        # 잘못된 모드 입력 (Fallback: 'auto')
        self.assertEqual(MappingHelper.map_mode_to_esp("INVALID_MODE"), "auto")

    def test_validate_temperature(self):
        AppLogger.log("TestAirconLogic.test_validate_temperature", {}, "Test validate_temperature guard clause")
        
        # 난방(HEAT) 모드: 16 ~ 30
        self.assertTrue(MappingHelper.validate_temperature("heat", 16))
        self.assertTrue(MappingHelper.validate_temperature("HEAT", 30))
        self.assertTrue(MappingHelper.validate_temperature("heat", 23))
        self.assertFalse(MappingHelper.validate_temperature("heat", 15))
        self.assertFalse(MappingHelper.validate_temperature("heat", 31))
        
        # 그 외 모드: 18 ~ 30
        self.assertTrue(MappingHelper.validate_temperature("cool", 18))
        self.assertTrue(MappingHelper.validate_temperature("auto", 30))
        self.assertFalse(MappingHelper.validate_temperature("cool", 17))
        self.assertFalse(MappingHelper.validate_temperature("fan_only", 31))


    @patch('mqtt_manager.mqtt.Client')
    def test_mqtt_virtual_packet_injection(self, mock_mqtt_client_class):
        payload_dict = {
            "mode": "COOL", 
            "target_temperature": 24.0, 
            "current_temperature": 25.5
        }
        payload_json = json.dumps(payload_dict)
        
        AppLogger.log("TestAirconLogic.test_mqtt_virtual_packet_injection", {"payload": payload_json}, "Inject virtual payload and verify callback")

        manager = MqttManager()
        mock_listener = MagicMock()
        manager.add_listener(mock_listener)
        
        manager.connect("127.0.0.1", 1883)
        
        class DummyMsg:
            topic = "lgap/climate/state"
            payload = payload_json.encode('utf-8')
            
        dummy_msg = DummyMsg()
        manager.on_message(manager.client, None, dummy_msg)
        
        mock_listener.assert_called_once_with("lgap/climate/state", payload_json)
        
        AppLogger.log("TestAirconLogic.test_mqtt_virtual_packet_injection", {}, "Verified that listener received payload")

    @patch('mock_bridge.mqtt.Client')
    def test_mock_bridge_message_handling(self, mock_mqtt_client_class):
        AppLogger.log("TestAirconLogic.test_mock_bridge_message_handling", {}, "Test mock_bridge message receipt and state feedback")
        import mock_bridge
        
        # 1. state 초기값 설정 및 백업
        original_state = mock_bridge.state.copy()
        mock_bridge.state = {
            "mode": "cool",
            "target_temperature": 24.0,
            "current_temperature": 25.5
        }
        
        # 2. Mock client 준비
        mock_client = MagicMock()
        
        # 3. 제어 명령 수신 시뮬레이션 (mode: heat, target: 25.0)
        class DummyMsg:
            topic = "lgap/climate/ac_livingroom/set"
            payload = b'{"mode": "heat", "target_temperature": 25.0}'
            
        dummy_msg = DummyMsg()
        mock_bridge.on_message(mock_client, None, dummy_msg)
        
        # 4. 상태 변경 및 피드백 발행 검증
        self.assertEqual(mock_bridge.state["mode"], "heat")
        self.assertEqual(mock_bridge.state["target_temperature"], 25.0)
        
        expected_payload = json.dumps({
            "mode": "heat",
            "target_temperature": 25.0,
            "current_temperature": 25.5
        })
        mock_client.publish.assert_called_with("lgap/climate/state", expected_payload)
        
        # 상태 복구
        mock_bridge.state = original_state


if __name__ == '__main__':
    unittest.main()
