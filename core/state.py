import typing
import threading
import time
from dataclasses import dataclass

@dataclass
class IndoorUnitState:
    unit_id: int
    target_temp: int
    room_temp: float
    pipe_temp: float
    op_mode: int
    fan_speed: int
    is_online: bool
    last_updated: float

class StateManager:
    def __init__(self) -> None:
        self._lock: threading.Lock = threading.Lock()
        self._states: typing.Dict[int, IndoorUnitState] = {}

    def update_state(self, unit_id: int, parsed_data: typing.Dict[str, typing.Any]) -> None:
        """스레드 안전하게 특정 실내기의 상태를 갱신합니다."""
        with self._lock:
            self._states[unit_id] = IndoorUnitState(
                unit_id=unit_id,
                target_temp=parsed_data.get("target_temp", 0),
                room_temp=parsed_data.get("room_temp", 0.0),
                pipe_temp=parsed_data.get("pipe_temp", 0.0),
                op_mode=parsed_data.get("mode", 0),
                fan_speed=parsed_data.get("fan_speed", 0),
                is_online=True,
                last_updated=time.time()
            )

    def get_unit_state(self, unit_id: int) -> typing.Optional[IndoorUnitState]:
        """특정 실내기의 상태를 안전하게 조회합니다."""
        with self._lock:
            return self._states.get(unit_id)

    def get_all_states(self) -> typing.Dict[int, IndoorUnitState]:
        """전체 실내기 상태 딕셔너리의 복사본을 반환합니다."""
        with self._lock:
            return self._states.copy()
