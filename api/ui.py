"""
LGAP Web UI Module
독립적인 단일 페이지 HTML/CSS/JS 템플릿을 제공하여 백엔드 통신 로직과 완전히 분리된 프론트엔드 계층입니다.
외부 CDN이나 라이브러리 없이 순수 바닐라 환경(오프라인 현장)에서 100% 동작합니다.
"""

def render_dashboard_html() -> str:
    """
    실시간 모니터링 및 실내기 제어가 가능한 웹 대시보드 HTML 문자열을 반환합니다.
    """
    return """<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>LGAP 시스템 에어컨 관제 대시보드</title>
    <style>
        :root {
            --bg-color: #0f172a;
            --card-bg: #1e293b;
            --card-border: #334155;
            --text-primary: #f8fafc;
            --text-secondary: #94a3b8;
            --accent-color: #38bdf8;
            --accent-hover: #0284c7;
            --success-color: #22c55e;
            --danger-color: #ef4444;
            --font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
        }

        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }

        body {
            background-color: var(--bg-color);
            color: var(--text-primary);
            font-family: var(--font-family);
            min-height: 100vh;
            padding: 24px;
        }

        .header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            max-width: 1200px;
            margin: 0 auto 32px auto;
            padding-bottom: 16px;
            border-bottom: 1px solid var(--card-border);
        }

        .header-title h1 {
            font-size: 1.5rem;
            font-weight: 700;
            color: var(--text-primary);
        }

        .header-title p {
            font-size: 0.875rem;
            color: var(--text-secondary);
            margin-top: 4px;
        }

        .status-badge {
            display: flex;
            align-items: center;
            gap: 8px;
            background: rgba(34, 197, 94, 0.1);
            color: var(--success-color);
            border: 1px solid rgba(34, 197, 94, 0.2);
            padding: 6px 12px;
            border-radius: 9999px;
            font-size: 0.8125rem;
            font-weight: 600;
        }

        .status-dot {
            width: 8px;
            height: 8px;
            background-color: var(--success-color);
            border-radius: 50%;
            animation: pulse 2s infinite;
        }

        @keyframes pulse {
            0%, 100% { opacity: 1; transform: scale(1); }
            50% { opacity: 0.4; transform: scale(0.85); }
        }

        .container {
            max-width: 1200px;
            margin: 0 auto;
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
            gap: 20px;
        }

        .unit-card {
            background-color: var(--card-bg);
            border: 1px solid var(--card-border);
            border-radius: 12px;
            padding: 20px;
            transition: transform 0.15s ease, border-color 0.15s ease;
        }

        .unit-card:hover {
            border-color: var(--accent-color);
            transform: translateY(-2px);
        }

        .card-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 16px;
        }

        .unit-name {
            font-size: 1.125rem;
            font-weight: 700;
        }

        .unit-tag {
            font-size: 0.75rem;
            padding: 3px 8px;
            border-radius: 4px;
            background: rgba(56, 189, 248, 0.15);
            color: var(--accent-color);
        }

        .temp-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 12px;
            margin-bottom: 20px;
        }

        .temp-item {
            background: rgba(15, 23, 42, 0.5);
            padding: 12px;
            border-radius: 8px;
            text-align: center;
        }

        .temp-label {
            font-size: 0.75rem;
            color: var(--text-secondary);
            margin-bottom: 4px;
        }

        .temp-val {
            font-size: 1.375rem;
            font-weight: 700;
            color: var(--text-primary);
        }

        .target-control {
            background: rgba(15, 23, 42, 0.7);
            border-radius: 8px;
            padding: 12px;
            margin-bottom: 16px;
        }

        .target-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            font-size: 0.8125rem;
            color: var(--text-secondary);
            margin-bottom: 8px;
        }

        .control-row {
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 12px;
        }

        .target-val {
            font-size: 1.5rem;
            font-weight: 700;
            color: var(--accent-color);
            min-width: 60px;
            text-align: center;
        }

        .btn-round {
            background: var(--card-border);
            color: var(--text-primary);
            border: none;
            width: 36px;
            height: 36px;
            border-radius: 50%;
            font-size: 1.25rem;
            font-weight: 700;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: background-color 0.15s ease;
        }

        .btn-round:hover {
            background: var(--accent-color);
            color: #000;
        }

        .btn-submit {
            width: 100%;
            background: var(--accent-color);
            color: #0f172a;
            border: none;
            padding: 10px;
            border-radius: 8px;
            font-weight: 700;
            font-size: 0.875rem;
            cursor: pointer;
            transition: background-color 0.15s ease;
        }

        .btn-submit:hover {
            background: var(--accent-hover);
            color: #fff;
        }

        .btn-submit:disabled {
            background: var(--card-border);
            color: var(--text-secondary);
            cursor: not-allowed;
        }

        .card-footer {
            margin-top: 12px;
            padding-top: 12px;
            border-top: 1px solid rgba(255, 255, 255, 0.05);
            display: flex;
            justify-content: space-between;
            font-size: 0.75rem;
            color: var(--text-secondary);
        }

        #toast {
            position: fixed;
            bottom: 24px;
            right: 24px;
            background: var(--card-bg);
            border: 1px solid var(--accent-color);
            color: var(--text-primary);
            padding: 12px 20px;
            border-radius: 8px;
            box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.5);
            transform: translateY(100px);
            opacity: 0;
            transition: all 0.3s ease;
            font-size: 0.875rem;
            z-index: 1000;
        }

        #toast.show {
            transform: translateY(0);
            opacity: 1;
        }

        .empty-state {
            grid-column: 1 / -1;
            text-align: center;
            padding: 48px;
            color: var(--text-secondary);
        }
    </style>
</head>
<body>

    <div class="header">
        <div class="header-title">
            <h1>LGAP 실내기 모니터링 & 제어기</h1>
            <p>RS-485 유선 직결 Direct Daemon Controller</p>
        </div>
        <div class="status-badge">
            <span class="status-dot"></span>
            <span id="conn-text">데몬 연결됨 (1초 동기화)</span>
        </div>
    </div>

    <div class="container" id="units-container">
        <div class="empty-state">실내기 상태 데이터를 불러오는 중입니다...</div>
    </div>

    <div id="toast"></div>

    <script>
        const pendingTargets = {};

        function showToast(message, isError = false) {
            const toast = document.getElementById('toast');
            toast.textContent = message;
            toast.style.borderColor = isError ? 'var(--danger-color)' : 'var(--accent-color)';
            toast.classList.add('show');
            setTimeout(() => {
                toast.classList.remove('show');
            }, 2500);
        }

        function adjustTemp(unitId, delta) {
            const current = pendingTargets[unitId] || 24;
            const updated = Math.max(16, Math.min(30, current + delta));
            pendingTargets[unitId] = updated;
            
            const label = document.getElementById(`target-val-${unitId}`);
            if (label) {
                label.textContent = `${updated}°C`;
            }
        }

        async function sendControl(unitId) {
            const targetTemp = pendingTargets[unitId];
            if (!targetTemp) return;

            const btn = document.getElementById(`btn-submit-${unitId}`);
            if (btn) btn.disabled = true;

            try {
                const res = await fetch('/control', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ id: Number(unitId), target_temp: Number(targetTemp) })
                });

                if (res.ok) {
                    showToast(`[실내기 #${unitId}] 목표 온도(${targetTemp}°C) 제어 명령 전송 완료`);
                } else {
                    const err = await res.json();
                    showToast(`제어 실패: ${err.error || '오류 발생'}`, true);
                }
            } catch (e) {
                showToast(`네트워크 오류: ${e.message}`, true);
            } finally {
                if (btn) btn.disabled = false;
            }
        }

        function getModeText(modeCode) {
            const modes = { 0: '냉방', 1: '제습', 2: '송풍', 3: '자동', 4: '난방' };
            return modes[modeCode] ?? `모드(${modeCode})`;
        }

        function getFanText(fanCode) {
            const fans = { 1: '약', 2: '자동', 4: '중', 8: '강', 16: '파워' };
            return fans[fanCode] ?? `풍량(${fanCode})`;
        }

        async function fetchStates() {
            try {
                const res = await fetch('/states');
                if (!res.ok) throw new Error('서버 응답 오류');
                const states = await res.json();
                
                const container = document.getElementById('units-container');
                const unitIds = Object.keys(states).map(Number).sort((a, b) => a - b);

                if (unitIds.length === 0) {
                    container.innerHTML = '<div class="empty-state">등록된 실내기 응답이 없습니다. (폴링 진행 중)</div>';
                    return;
                }

                let html = '';
                unitIds.forEach(id => {
                    const state = states[id];
                    if (!(id in pendingTargets)) {
                        pendingTargets[id] = state.target_temp || 24;
                    }
                    const selectedTarget = pendingTargets[id];

                    html += `
                    <div class="unit-card">
                        <div class="card-header">
                            <div class="unit-name">실내기 #${id}</div>
                            <div class="unit-tag">${state.is_online ? '온라인' : '오프라인'}</div>
                        </div>

                        <div class="temp-grid">
                            <div class="temp-item">
                                <div class="temp-label">실내 현재온도</div>
                                <div class="temp-val">${state.room_temp}°C</div>
                            </div>
                            <div class="temp-item">
                                <div class="temp-label">배관 온도</div>
                                <div class="temp-val">${state.pipe_temp}°C</div>
                            </div>
                        </div>

                        <div class="target-control">
                            <div class="target-header">
                                <span>희망 온도 설정</span>
                                <span>현재 설정: ${state.target_temp}°C</span>
                            </div>
                            <div class="control-row">
                                <button class="btn-round" onclick="adjustTemp(${id}, -1)">-</button>
                                <div class="target-val" id="target-val-${id}">${selectedTarget}°C</div>
                                <button class="btn-round" onclick="adjustTemp(${id}, 1)">+</button>
                            </div>
                        </div>

                        <button class="btn-submit" id="btn-submit-${id}" onclick="sendControl(${id})">
                            희망 온도로 즉시 제어
                        </button>

                        <div class="card-footer">
                            <span>운전: ${getModeText(state.op_mode)} / ${getFanText(state.fan_speed)}</span>
                            <span>수신: ${new Date(state.last_updated * 1000).toLocaleTimeString()}</span>
                        </div>
                    </div>
                    `;
                });

                container.innerHTML = html;
                document.getElementById('conn-text').textContent = '데몬 정상 동작 중';
            } catch (e) {
                document.getElementById('conn-text').textContent = '데몬 통신 끊김';
            }
        }

        // 1초 주기 실시간 상태 갱신
        setInterval(fetchStates, 1000);
        fetchStates();
    </script>
</body>
</html>
"""
