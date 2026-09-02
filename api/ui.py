"""
LGAP & V-Net Web UI Module
독립적인 단일 페이지 HTML/CSS/JS 템플릿을 제공하여 백엔드 통신 로직과 완전히 분리된 프론트엔드 계층입니다.
외부 CDN이나 라이브러리 없이 순수 바닐라 환경(오프라인 현장)에서 100% 동작합니다.
"""

def render_dashboard_html() -> str:
    """
    실시간 모니터링 및 실내기 통합 제어(온도/모드/풍량)가 가능한 웹 대시보드 HTML 문자열을 반환합니다.
    """
    return """<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>LG 시스템 에어컨 관제 대시보드</title>
    <style>
        :root {
            --bg-color: #0b0f19;
            --card-bg: #151d2f;
            --card-hover: #1c263d;
            --card-border: #23304c;
            --text-primary: #f8fafc;
            --text-secondary: #94a3b8;
            --text-muted: #64748b;
            --accent-color: #38bdf8;
            --accent-glow: rgba(56, 189, 248, 0.2);
            --accent-hover: #0284c7;
            --success-color: #22c55e;
            --warning-color: #f59e0b;
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
            max-width: 1280px;
            margin: 0 auto 28px auto;
            padding-bottom: 20px;
            border-bottom: 1px solid var(--card-border);
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 16px;
        }

        .header-left h1 {
            font-size: 1.6rem;
            font-weight: 700;
            letter-spacing: -0.02em;
            color: var(--text-primary);
            display: flex;
            align-items: center;
            gap: 10px;
        }

        .header-left p {
            font-size: 0.875rem;
            color: var(--text-secondary);
            margin-top: 4px;
        }

        .header-meta {
            display: flex;
            align-items: center;
            gap: 10px;
            flex-wrap: wrap;
        }

        .meta-tag {
            background: rgba(30, 41, 59, 0.8);
            border: 1px solid var(--card-border);
            color: var(--text-secondary);
            padding: 6px 12px;
            border-radius: 8px;
            font-size: 0.8125rem;
            font-weight: 600;
        }

        .meta-tag.highlight {
            border-color: var(--accent-color);
            color: var(--accent-color);
            background: rgba(56, 189, 248, 0.1);
        }

        .status-badge {
            display: flex;
            align-items: center;
            gap: 8px;
            background: rgba(34, 197, 94, 0.1);
            color: var(--success-color);
            border: 1px solid rgba(34, 197, 94, 0.25);
            padding: 6px 14px;
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
            50% { opacity: 0.3; transform: scale(0.85); }
        }

        .container {
            max-width: 1280px;
            margin: 0 auto;
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(360px, 1fr));
            gap: 24px;
        }

        .unit-card {
            background-color: var(--card-bg);
            border: 1px solid var(--card-border);
            border-radius: 14px;
            padding: 22px;
            display: flex;
            flex-direction: column;
            gap: 16px;
            transition: transform 0.15s ease, border-color 0.15s ease, box-shadow 0.15s ease;
        }

        .unit-card:hover {
            border-color: var(--accent-color);
            transform: translateY(-2px);
            box-shadow: 0 8px 24px var(--accent-glow);
        }

        .card-top {
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .unit-title {
            font-size: 1.25rem;
            font-weight: 700;
            display: flex;
            align-items: center;
            gap: 8px;
        }

        .online-tag {
            font-size: 0.75rem;
            padding: 4px 10px;
            border-radius: 6px;
            font-weight: 600;
            background: rgba(34, 197, 94, 0.15);
            color: var(--success-color);
            border: 1px solid rgba(34, 197, 94, 0.3);
        }

        .online-tag.offline {
            background: rgba(148, 163, 184, 0.1);
            color: var(--text-muted);
            border-color: rgba(148, 163, 184, 0.2);
        }

        .sensor-grid {
            display: grid;
            grid-template-columns: 1fr 1fr 1fr;
            gap: 10px;
        }

        .sensor-box {
            background: rgba(11, 15, 25, 0.6);
            border: 1px solid rgba(255, 255, 255, 0.05);
            padding: 10px 8px;
            border-radius: 10px;
            text-align: center;
        }

        .sensor-label {
            font-size: 0.75rem;
            color: var(--text-secondary);
            margin-bottom: 4px;
        }

        .sensor-val {
            font-size: 1.25rem;
            font-weight: 700;
            color: var(--text-primary);
        }

        .sensor-val.accent {
            color: var(--accent-color);
        }

        .control-section {
            background: rgba(11, 15, 25, 0.4);
            border: 1px solid var(--card-border);
            border-radius: 10px;
            padding: 14px;
            display: flex;
            flex-direction: column;
            gap: 14px;
        }

        .control-group-title {
            font-size: 0.75rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            color: var(--text-secondary);
            margin-bottom: 6px;
            display: flex;
            justify-content: space-between;
        }

        .option-group {
            display: grid;
            grid-template-columns: repeat(5, 1fr);
            gap: 6px;
        }

        .option-btn {
            background: var(--card-border);
            color: var(--text-secondary);
            border: 1px solid transparent;
            padding: 8px 4px;
            border-radius: 6px;
            font-size: 0.8125rem;
            font-weight: 600;
            cursor: pointer;
            text-align: center;
            transition: all 0.15s ease;
        }

        .option-btn:hover {
            color: var(--text-primary);
            background: #2d3c5e;
        }

        .option-btn.active {
            background: var(--accent-color);
            color: #0b0f19;
            font-weight: 700;
            box-shadow: 0 2px 8px var(--accent-glow);
        }

        .temp-stepper-row {
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 12px;
            background: rgba(11, 15, 25, 0.7);
            border-radius: 8px;
            padding: 8px 14px;
        }

        .btn-stepper {
            background: var(--card-border);
            color: var(--text-primary);
            border: none;
            width: 38px;
            height: 38px;
            border-radius: 8px;
            font-size: 1.3rem;
            font-weight: 700;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: background 0.15s ease, color 0.15s ease;
        }

        .btn-stepper:hover {
            background: var(--accent-color);
            color: #0b0f19;
        }

        .target-temp-display {
            font-size: 1.6rem;
            font-weight: 800;
            color: var(--accent-color);
        }

        .btn-submit {
            width: 100%;
            background: var(--accent-color);
            color: #0b0f19;
            border: none;
            padding: 12px;
            border-radius: 8px;
            font-weight: 700;
            font-size: 0.9375rem;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 8px;
            transition: background 0.15s ease, transform 0.1s ease;
        }

        .btn-submit:hover {
            background: var(--accent-hover);
            color: #fff;
        }

        .btn-submit:disabled {
            background: var(--card-border);
            color: var(--text-muted);
            cursor: not-allowed;
            transform: none;
        }

        .card-footer {
            margin-top: auto;
            padding-top: 10px;
            border-top: 1px solid rgba(255, 255, 255, 0.05);
            display: flex;
            justify-content: space-between;
            font-size: 0.75rem;
            color: var(--text-muted);
        }

        #toast {
            position: fixed;
            bottom: 28px;
            right: 28px;
            background: var(--card-bg);
            border: 1px solid var(--accent-color);
            color: var(--text-primary);
            padding: 14px 24px;
            border-radius: 10px;
            box-shadow: 0 12px 30px rgba(0, 0, 0, 0.6);
            transform: translateY(120px);
            opacity: 0;
            transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1);
            font-size: 0.9rem;
            z-index: 1000;
            font-weight: 600;
        }

        #toast.show {
            transform: translateY(0);
            opacity: 1;
        }

        .empty-state {
            grid-column: 1 / -1;
            text-align: center;
            padding: 60px 20px;
            color: var(--text-secondary);
            background: var(--card-bg);
            border: 1px dashed var(--card-border);
            border-radius: 12px;
        }
    </style>
</head>
<body>

    <div class="header">
        <div class="header-left">
            <h1>LG 시스템 에어컨 관제 대시보드</h1>
            <p>RS-485 Half-Duplex Direct Daemon Controller</p>
        </div>
        <div class="header-meta">
            <span class="meta-tag highlight" id="protocol-badge">프로토콜: LGAP (16B)</span>
            <span class="meta-tag" id="port-baud-badge">COM6 @ 9600 bps</span>
            <div class="status-badge">
                <span class="status-dot"></span>
                <span id="conn-text">데몬 연결됨</span>
            </div>
        </div>
    </div>

    <div class="container" id="units-container">
        <div class="empty-state">실내기 장치 목록을 조회 중입니다...</div>
    </div>

    <div id="toast"></div>

    <script>
        const pendingSettings = {};
        let systemInfo = null;

        const MODES = [
            { code: 0, label: '냉방' },
            { code: 4, label: '난방' },
            { code: 1, label: '제습' },
            { code: 2, label: '송풍' },
            { code: 3, label: '자동' }
        ];

        const FANS = [
            { code: 1, label: '약' },
            { code: 4, label: '중' },
            { code: 8, label: '강' },
            { code: 2, label: '자동' },
            { code: 16, label: '파워' }
        ];

        function showToast(message, isError = false) {
            const toast = document.getElementById('toast');
            toast.textContent = message;
            toast.style.borderColor = isError ? 'var(--danger-color)' : 'var(--accent-color)';
            toast.classList.add('show');
            setTimeout(() => {
                toast.classList.remove('show');
            }, 2500);
        }

        async function fetchSystemInfo() {
            try {
                const res = await fetch('/info');
                if (res.ok) {
                    systemInfo = await res.json();
                    document.getElementById('protocol-badge').textContent = `프로토콜: ${systemInfo.protocol_mode} 모드`;
                    document.getElementById('port-baud-badge').textContent = `${systemInfo.port} @ ${systemInfo.baudrate} bps`;
                }
            } catch (e) {
                console.warn('시스템 정보 로드 실패:', e);
            }
        }

        function setMode(unitId, modeCode) {
            if (!pendingSettings[unitId]) pendingSettings[unitId] = {};
            pendingSettings[unitId].mode = modeCode;
            
            // UI 버튼 활성화 갱신
            document.querySelectorAll(`.btn-mode-${unitId}`).forEach(btn => {
                btn.classList.toggle('active', Number(btn.dataset.code) === modeCode);
            });
        }

        function setFan(unitId, fanCode) {
            if (!pendingSettings[unitId]) pendingSettings[unitId] = {};
            pendingSettings[unitId].fan_speed = fanCode;
            
            // UI 버튼 활성화 갱신
            document.querySelectorAll(`.btn-fan-${unitId}`).forEach(btn => {
                btn.classList.toggle('active', Number(btn.dataset.code) === fanCode);
            });
        }

        function adjustTemp(unitId, delta) {
            if (!pendingSettings[unitId]) pendingSettings[unitId] = {};
            const current = pendingSettings[unitId].target_temp || 24;
            const updated = Math.max(16, Math.min(30, current + delta));
            pendingSettings[unitId].target_temp = updated;
            
            const label = document.getElementById(`target-val-${unitId}`);
            if (label) {
                label.textContent = `${updated}°C`;
            }
        }

        async function sendControl(unitId) {
            const settings = pendingSettings[unitId];
            if (!settings) return;

            const btn = document.getElementById(`btn-submit-${unitId}`);
            if (btn) btn.disabled = true;

            const payload = {
                id: Number(unitId),
                target_temp: Number(settings.target_temp || 24),
                mode: Number(settings.mode ?? 0),
                fan_speed: Number(settings.fan_speed ?? 4)
            };

            try {
                const res = await fetch('/control', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload)
                });

                if (res.ok) {
                    const modeObj = MODES.find(m => m.code === payload.mode);
                    const fanObj = FANS.find(f => f.code === payload.fan_speed);
                    showToast(`[실내기 #${unitId}] ${payload.target_temp}°C / ${modeObj ? modeObj.label : '모드'} / ${fanObj ? fanObj.label : '풍량'} 전송 완료`);
                } else {
                    const err = await res.json();
                    showToast(`제어 실패: ${err.error || '오류'}`, true);
                }
            } catch (e) {
                showToast(`통신 오류: ${e.message}`, true);
            } finally {
                if (btn) btn.disabled = false;
            }
        }

        function getModeText(modeCode) {
            const m = MODES.find(item => item.code === modeCode);
            return m ? m.label : `모드(${modeCode})`;
        }

        function getFanText(fanCode) {
            const f = FANS.find(item => item.code === fanCode);
            return f ? f.label : `풍량(${fanCode})`;
        }

        async function fetchStates() {
            try {
                const res = await fetch('/states');
                if (!res.ok) throw new Error('서버 응답 오류');
                const states = await res.json();
                
                const container = document.getElementById('units-container');
                
                // 설정된 타겟 실내기 목록 또는 응답 실내기 목록 종합
                const activeIds = Object.keys(states).map(Number);
                const configIds = systemInfo && systemInfo.target_units ? systemInfo.target_units : [];
                const allIds = Array.from(new Set([...activeIds, ...configIds])).sort((a, b) => a - b);

                if (allIds.length === 0) {
                    container.innerHTML = '<div class="empty-state">등록된 실내기 응답이 없습니다. (시리얼 통신 폴링 진행 중)</div>';
                    return;
                }

                allIds.forEach(id => {
                    const state = states[id] || {
                        target_temp: 24,
                        room_temp: 0.0,
                        pipe_temp: 0.0,
                        op_mode: 0,
                        fan_speed: 4,
                        is_online: false,
                        last_updated: Date.now() / 1000
                    };

                    if (!pendingSettings[id]) {
                        pendingSettings[id] = {
                            target_temp: state.target_temp || 24,
                            mode: state.op_mode ?? 0,
                            fan_speed: state.fan_speed ?? 4
                        };
                    }

                    const curPending = pendingSettings[id];
                    let card = document.getElementById(`unit-card-${id}`);

                    if (!card) {
                        // 최초 카드 렌더링
                        const cardDiv = document.createElement('div');
                        cardDiv.id = `unit-card-${id}`;
                        cardDiv.className = 'unit-card';
                        cardDiv.innerHTML = buildCardHtml(id, state, curPending);
                        container.appendChild(cardDiv);
                    } else {
                        // 센서 및 실시간 텍스트 부분만 선택적 갱신
                        updateCardValues(id, state);
                    }
                });

                document.getElementById('conn-text').textContent = '데몬 정상 동작 중';
            } catch (e) {
                document.getElementById('conn-text').textContent = '데몬 통신 끊김';
            }
        }

        function buildCardHtml(id, state, pending) {
            const modeButtons = MODES.map(m => `
                <button class="option-btn btn-mode-${id} ${pending.mode === m.code ? 'active' : ''}" 
                        data-code="${m.code}" 
                        onclick="setMode(${id}, ${m.code})">${m.label}</button>
            `).join('');

            const fanButtons = FANS.map(f => `
                <button class="option-btn btn-fan-${id} ${pending.fan_speed === f.code ? 'active' : ''}" 
                        data-code="${f.code}" 
                        onclick="setFan(${id}, ${f.code})">${f.label}</button>
            `).join('');

            return `
                <div class="card-top">
                    <div class="unit-title">실내기 #${id}</div>
                    <div class="online-tag ${state.is_online ? '' : 'offline'}" id="online-tag-${id}">
                        ${state.is_online ? '온라인' : '대기중'}
                    </div>
                </div>

                <div class="sensor-grid">
                    <div class="sensor-box">
                        <div class="sensor-label">실내 현재온도</div>
                        <div class="sensor-val" id="room-temp-${id}">${state.room_temp > 0 ? state.room_temp + '°C' : '-'}</div>
                    </div>
                    <div class="sensor-box">
                        <div class="sensor-label">배관 온도</div>
                        <div class="sensor-val" id="pipe-temp-${id}">${state.pipe_temp > 0 ? state.pipe_temp + '°C' : '-'}</div>
                    </div>
                    <div class="sensor-box">
                        <div class="sensor-label">현재 설정</div>
                        <div class="sensor-val accent" id="cur-target-${id}">${state.target_temp ? state.target_temp + '°C' : '-'}</div>
                    </div>
                </div>

                <div class="control-section">
                    <div>
                        <div class="control-group-title">
                            <span>운전 모드 선택</span>
                            <span id="cur-mode-label-${id}">현재: ${getModeText(state.op_mode)}</span>
                        </div>
                        <div class="option-group">
                            ${modeButtons}
                        </div>
                    </div>

                    <div>
                        <div class="control-group-title">
                            <span>풍량 선택</span>
                            <span id="cur-fan-label-${id}">현재: ${getFanText(state.fan_speed)}</span>
                        </div>
                        <div class="option-group">
                            ${fanButtons}
                        </div>
                    </div>

                    <div>
                        <div class="control-group-title">
                            <span>희망 온도 조절</span>
                        </div>
                        <div class="temp-stepper-row">
                            <button class="btn-stepper" onclick="adjustTemp(${id}, -1)">-</button>
                            <div class="target-temp-display" id="target-val-${id}">${pending.target_temp}°C</div>
                            <button class="btn-stepper" onclick="adjustTemp(${id}, 1)">+</button>
                        </div>
                    </div>

                    <button class="btn-submit" id="btn-submit-${id}" onclick="sendControl(${id})">
                        설정값 즉시 전송 (온도/모드/풍량)
                    </button>
                </div>

                <div class="card-footer">
                    <span id="footer-status-${id}">상태: ${getModeText(state.op_mode)} / ${getFanText(state.fan_speed)}</span>
                    <span id="footer-time-${id}">수신: ${new Date(state.last_updated * 1000).toLocaleTimeString()}</span>
                </div>
            `;
        }

        function updateCardValues(id, state) {
            const roomEl = document.getElementById(`room-temp-${id}`);
            if (roomEl) roomEl.textContent = state.room_temp > 0 ? `${state.room_temp}°C` : '-';

            const pipeEl = document.getElementById(`pipe-temp-${id}`);
            if (pipeEl) pipeEl.textContent = state.pipe_temp > 0 ? `${state.pipe_temp}°C` : '-';

            const curTargetEl = document.getElementById(`cur-target-${id}`);
            if (curTargetEl) curTargetEl.textContent = state.target_temp ? `${state.target_temp}°C` : '-';

            const tagEl = document.getElementById(`online-tag-${id}`);
            if (tagEl) {
                tagEl.textContent = state.is_online ? '온라인' : '대기중';
                tagEl.className = `online-tag ${state.is_online ? '' : 'offline'}`;
            }

            const modeLabel = document.getElementById(`cur-mode-label-${id}`);
            if (modeLabel) modeLabel.textContent = `현재: ${getModeText(state.op_mode)}`;

            const fanLabel = document.getElementById(`cur-fan-label-${id}`);
            if (fanLabel) fanLabel.textContent = `현재: ${getFanText(state.fan_speed)}`;

            const footerStatus = document.getElementById(`footer-status-${id}`);
            if (footerStatus) footerStatus.textContent = `상태: ${getModeText(state.op_mode)} / ${getFanText(state.fan_speed)}`;

            const footerTime = document.getElementById(`footer-time-${id}`);
            if (footerTime) footerTime.textContent = `수신: ${new Date(state.last_updated * 1000).toLocaleTimeString()}`;
        }

        // 초기화 및 주기적 갱신
        fetchSystemInfo().then(() => {
            fetchStates();
            setInterval(fetchStates, 1000);
        });
    </script>
</body>
</html>
"""
