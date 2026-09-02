import json
import logging
import typing
from http.server import BaseHTTPRequestHandler, HTTPServer
import threading
import queue

import config
from core.state import StateManager
from core.polling import LgapEngine
from api.ui import render_dashboard_html

def create_handler(state_manager: StateManager, engine: LgapEngine) -> typing.Type[BaseHTTPRequestHandler]:
    class ApiHandler(BaseHTTPRequestHandler):
        def _send_response(self, status_code: int, data: typing.Dict[str, typing.Any]) -> None:
            self.send_response(status_code)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(data).encode('utf-8'))

        def do_GET(self) -> None:
            if self.path in ('/', '/index.html'):
                html_content = render_dashboard_html().encode('utf-8')
                self.send_response(200)
                self.send_header('Content-Type', 'text/html; charset=utf-8')
                self.send_header('Content-Length', str(len(html_content)))
                self.end_headers()
                self.wfile.write(html_content)
            elif self.path == '/info':
                mode = getattr(config, 'PROTOCOL_MODE', 'LGAP')
                target_units = getattr(config, 'TARGET_INDOOR_UNITS', [1, 2, 3, 4]) if mode == 'LGAP' else getattr(config, 'VNET_TARGET_UNITS', [4, 5])
                info_data = {
                    "protocol_mode": mode,
                    "baudrate": getattr(config, 'BAUDRATE', 9600),
                    "port": getattr(config, 'SERIAL_PORT', 'COM6'),
                    "poll_interval": getattr(config, 'POLL_INTERVAL', 1.0),
                    "target_units": target_units
                }
                self._send_response(200, info_data)
            elif self.path == '/states':
                states = state_manager.get_all_states()
                response_data = {
                    k: {
                        "target_temp": v.target_temp,
                        "room_temp": v.room_temp,
                        "pipe_temp": v.pipe_temp,
                        "op_mode": v.op_mode,
                        "fan_speed": v.fan_speed,
                        "is_online": v.is_online,
                        "last_updated": v.last_updated
                    } for k, v in states.items()
                }
                self._send_response(200, response_data)
            else:
                self._send_response(404, {"error": "Not Found"})

        def do_POST(self) -> None:
            if self.path == '/control':
                content_length_str = self.headers.get('Content-Length')
                if not content_length_str:
                    self._send_response(400, {"error": "Content-Length is missing"})
                    return
                    
                content_length = int(content_length_str)
                post_data = self.rfile.read(content_length)
                
                try:
                    command = json.loads(post_data.decode('utf-8'))
                except json.JSONDecodeError:
                    self._send_response(400, {"error": "Invalid JSON"})
                    return
                
                unit_id = command.get("id")
                if not isinstance(unit_id, int):
                    self._send_response(400, {"error": "'id' must be an integer"})
                    return
                    
                target_temp = command.get("target_temp")
                if target_temp is not None and not (16 <= target_temp <= 30):
                    self._send_response(400, {"error": "target_temp must be between 16 and 30"})
                    return
                    
                mode_val = command.get("mode")
                if mode_val is not None and not isinstance(mode_val, int):
                    self._send_response(400, {"error": "mode must be an integer"})
                    return
                    
                fan_val = command.get("fan_speed")
                if fan_val is not None and not isinstance(fan_val, int):
                    self._send_response(400, {"error": "fan_speed must be an integer"})
                    return

                # 큐에 명령 주입 (Preemption 유도)
                try:
                    engine.command_queue.put_nowait(command)
                    self._send_response(200, {"status": "Command enqueued", "command": command})
                except queue.Full:
                    self._send_response(503, {"error": "Command queue is full"})
            else:
                self._send_response(404, {"error": "Not Found"})

        def log_message(self, format: str, *args: typing.Any) -> None:
            # 로깅 규격 통일을 위해 표준 로깅 사용
            logging.debug(f"API Request: {self.client_address[0]} - {format % args}")

    return ApiHandler

class ApiInterfaceServer:
    def __init__(self, state_manager: StateManager, engine: LgapEngine, port: int = 8080) -> None:
        self.port: int = port
        self.handler_class = create_handler(state_manager, engine)
        self.server: typing.Optional[HTTPServer] = None
        self.server_thread: typing.Optional[threading.Thread] = None

    def start(self) -> None:
        self.server = HTTPServer(('0.0.0.0', self.port), self.handler_class)
        self.server_thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.server_thread.start()
        logging.info(f"API Server started on port {self.port}")

    def stop(self) -> None:
        if self.server:
            self.server.shutdown()
            self.server.server_close()
        if self.server_thread:
            self.server_thread.join()
        logging.info("API Server stopped")
