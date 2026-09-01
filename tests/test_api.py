import unittest
import urllib.request
import json
import time

from core.state import StateManager
from core.polling import LgapEngine
from api.interface import ApiInterfaceServer
from tests.mock_aircon import MockSerial

class TestApiInterface(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.state_mgr = StateManager()
        cls.engine = LgapEngine(state_manager=cls.state_mgr, serial_class=MockSerial)
        cls.engine.connect_serial()
        cls.server = ApiInterfaceServer(state_manager=cls.state_mgr, engine=cls.engine, port=8888)
        cls.server.start()
        time.sleep(0.2)

    @classmethod
    def tearDownClass(cls) -> None:
        cls.server.stop()

    def test_get_root_ui(self) -> None:
        req = urllib.request.urlopen("http://localhost:8888/")
        self.assertEqual(req.status, 200)
        self.assertIn("text/html", req.headers.get("Content-Type", ""))
        html = req.read().decode('utf-8')
        self.assertIn("LGAP 실내기 모니터링 & 제어기", html)

    def test_get_states(self) -> None:
        # 상태 주입
        self.state_mgr.update_state(1, {"target_temp": 24, "room_temp": 26.0, "pipe_temp": 15.0, "mode": 0, "fan_speed": 4})
        req = urllib.request.urlopen("http://localhost:8888/states")
        self.assertEqual(req.status, 200)
        data = json.loads(req.read().decode('utf-8'))
        self.assertIn("1", data)
        self.assertEqual(data["1"]["target_temp"], 24)

    def test_post_control(self) -> None:
        payload = json.dumps({"id": 1, "target_temp": 22}).encode('utf-8')
        req = urllib.request.Request("http://localhost:8888/control", data=payload, headers={"Content-Type": "application/json"})
        response = urllib.request.urlopen(req)
        self.assertEqual(response.status, 200)
        res_data = json.loads(response.read().decode('utf-8'))
        self.assertEqual(res_data["status"], "Command enqueued")

if __name__ == "__main__":
    unittest.main()
