# 🏗️ LG Aircon Raspberry Pi PoC Project Structure

**Generated:** 2026-07-15 10:25:11

### 🌳 Folder Tree
```text
lgap-python-raw/
├── .gitignore
├── LGAP_Github_source_check_report-v2.md
├── README.md
├── act
├── api
│   └── interface.py
├── app_logger.py
├── config.py
├── core
│   ├── polling.py
│   ├── protocol.py
│   └── state.py
├── deployment
│   ├── README_production.md
│   └── lgap-daemon.service
├── main.py
├── next_to_do(need to be updated).md
├── requirements.txt
├── temp_AI_initial_command.md
├── test_aircon_logic.py
└── tests
    ├── README_test.md
    ├── mock_aircon.py
    └── test_serial_loopback.py
```

### 📂 주요 함수 목록

**[app_logger.py]**
- log
- error


**[main.py]**
- __init__
- start
- request_shutdown
- _cleanup


**[test_aircon_logic.py]**
- setUp
- test_mapping_helper
- test_validate_temperature
- test_mqtt_virtual_packet_injection
- test_mock_bridge_message_handling


**[api/interface.py]**
- create_handler
- _send_response
- do_GET
- do_POST
- log_message
- __init__
- start
- stop


**[core/polling.py]**
- __init__
- connect_serial
- _execute_transaction
- start_engine
- stop_engine
- _build_poll_packet
- _build_control_packet
- _engine_loop


**[core/protocol.py]**
- calculate_checksum
- validate_packet
- parse_packet
- __init__
- feed


**[core/state.py]**
- __init__
- update_state
- get_unit_state
- get_all_states


**[tests/mock_aircon.py]**
- __init__
- close
- flush
- in_waiting
- write
- read
- _generate_response


**[tests/test_serial_loopback.py]**
- __init__
- open_port
- close_port
- test_loopback

