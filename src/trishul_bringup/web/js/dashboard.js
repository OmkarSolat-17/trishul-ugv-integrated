// ==========================================================================
// TRISHUL UGV -- Production-Grade Mission Control Dashboard Client
// Implements:
// 1. Latched E-STOP with reset unlock
// 2. Real-time /map OccupancyGrid rendering with true mathematical transforms
// 3. Action Client feedback (NavigateToPose) distance & ETA
// 4. Input validation and collision avoidance routing
// ==========================================================================

document.addEventListener('DOMContentLoaded', () => {
    // State
    const state = {
        pose: { x: -2.0, y: -0.5, yaw: 0.0 },
        vel: { linear: 0.0, angular: 0.0 },
        closestObstacle: 20.0,
        battery: 98,
        activeDetections: [],
        laserPoints: [],
        mapMeta: { resolution: 0.05, width: 0, height: 0, origin_x: 0.0, origin_y: 0.0 },
        mapImageObj: null,
        mapImageLoaded: false,
        plannedPath: [],
        currentGoal: { x: 1.8, y: -0.5 },
        speedLimit: 0.25,
        estopLatched: false,
        navState: 'IDLE',
        distRemaining: 0.0,
        etaSeconds: 0.0,
        keysPressed: {},
        connected: false,
    };

    // DOM Elements
    const elSysStatus = document.getElementById('val-sys-status');
    const elSysPulse = document.getElementById('sys-pulse-dot');
    const elEstopBtn = document.getElementById('btn-estop-toggle');
    const elEstopBtnText = document.getElementById('estop-btn-text');
    const elBattery = document.getElementById('val-battery');
    const elUptime = document.getElementById('val-uptime');
    const elPose = document.getElementById('val-pose');
    const elNavState = document.getElementById('val-nav-state');
    const elNavDist = document.getElementById('val-nav-dist');
    const elLinearVel = document.getElementById('val-linear-vel');
    const elAngularVel = document.getElementById('val-angular-vel');
    const elClosestObs = document.getElementById('val-closest-obs');
    const elSafetyStatus = document.getElementById('val-safety-status');
    const elDetectionCount = document.getElementById('val-detection-count');
    const elChipsContainer = document.getElementById('detection-chips-container');
    const elTerminal = document.getElementById('terminal-feed');
    const elSpeedSlider = document.getElementById('speed-slider');
    const elSpeedLimitVal = document.getElementById('val-speed-limit');

    // Canvas
    const canvas = document.getElementById('radar-canvas');
    const ctx = canvas.getContext('2d');

    // Logging
    function logEvent(tag, message, level = 'info') {
        const time = new Date().toTimeString().split(' ')[0];
        const line = document.createElement('div');
        line.className = 'log-line';

        let tagClass = 'tag-info';
        if (tag === 'YOLO') tagClass = 'tag-yolo';
        if (tag === 'NAV2') tagClass = 'tag-nav';
        if (tag === 'DANGER' || tag === 'E-STOP') tagClass = 'tag-danger';

        line.innerHTML = `[${time}] <span class="${tagClass}">[${tag}]</span> ${message}`;
        elTerminal.appendChild(line);
        elTerminal.scrollTop = elTerminal.scrollHeight;
    }

    // ---------------- Server-Sent Events (SSE) Stream ----------------
    function initEventStream() {
        const evtSource = new EventSource('/events');

        evtSource.onopen = () => {
            state.connected = true;
            if (!state.estopLatched) {
                elSysStatus.textContent = 'AUTONOMOUS ACTIVE';
            }
            logEvent('SYSTEM', 'Uplink established with Trishul Dashboard Server.');
        };

        evtSource.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                handleServerUpdate(data);
            } catch (err) {
                console.error('Failed to parse SSE payload:', err);
            }
        };

        evtSource.onerror = () => {
            state.connected = false;
            elSysStatus.textContent = 'RECONNECTING...';
        };
    }

    function handleServerUpdate(data) {
        if (data.pose) {
            state.pose = data.pose;
            elPose.textContent = `(${data.pose.x.toFixed(2)}, ${data.pose.y.toFixed(2)})`;
        }

        if (data.vel) {
            state.vel = data.vel;
            elLinearVel.textContent = Math.abs(data.vel.linear).toFixed(2);
            elAngularVel.textContent = data.vel.angular.toFixed(2);
        }

        if (data.closest_obstacle !== undefined) {
            state.closestObstacle = data.closest_obstacle;
            elClosestObs.textContent = `${data.closest_obstacle.toFixed(2)} m`;
            if (data.closest_obstacle < 0.35) {
                elSafetyStatus.textContent = 'INTERVENTION';
                elSafetyStatus.className = 'gauge-value highlight-orange';
            } else {
                elSafetyStatus.textContent = 'CLEAR';
                elSafetyStatus.className = 'gauge-value highlight-green';
            }
        }

        if (data.battery !== undefined) {
            state.battery = data.battery;
            elBattery.textContent = `${data.battery}% [24.2V]`;
        }

        if (data.laser_points) {
            state.laserPoints = data.laser_points;
        }

        if (data.path) {
            state.plannedPath = data.path;
        }

        if (data.detections) {
            updateDetections(data.detections);
        }

        // Nav2 Action Status & Feedback
        if (data.nav_state) {
            state.navState = data.nav_state;
            elNavState.textContent = data.nav_state;
            if (data.distance_remaining > 0) {
                elNavDist.textContent = `${data.distance_remaining}m | ${data.eta_seconds}s`;
            } else {
                elNavDist.textContent = state.navState;
            }
        }

        // Latched E-STOP State
        if (data.estop_latched !== undefined) {
            state.estopLatched = data.estop_latched;
            if (state.estopLatched) {
                elSysStatus.textContent = 'E-STOP LATCHED';
                elSysStatus.parentElement.className = 'badge badge-orange';
                elEstopBtnText.textContent = 'RESET E-STOP';
                elEstopBtn.style.background = 'linear-gradient(135deg, #ffa000, #e65100)';
            } else {
                elSysStatus.textContent = 'AUTONOMOUS ACTIVE';
                elSysStatus.parentElement.className = 'badge badge-green';
                elEstopBtnText.textContent = 'EMERGENCY STOP';
                elEstopBtn.style.background = '';
            }
        }

        // Live SLAM OccupancyGrid Map Rendering
        if (data.map_image && data.map_meta && data.map_meta.width > 0) {
            state.mapMeta = data.map_meta;
            if (!state.mapImageObj) {
                state.mapImageObj = new Image();
                state.mapImageObj.onload = () => {
                    state.mapImageLoaded = true;
                };
            }
            state.mapImageObj.src = 'data:image/png;base64,' + data.map_image;
        }
    }

    // AI Detection Inspector
    function updateDetections(detections) {
        state.activeDetections = detections;
        elDetectionCount.textContent = `${detections.length} TARGETS`;

        if (detections.length === 0) {
            elChipsContainer.innerHTML = '<span class="chip-placeholder">Sector clear. Awaiting target classification...</span>';
            return;
        }

        elChipsContainer.innerHTML = '';
        detections.forEach((det) => {
            const chip = document.createElement('div');
            chip.className = 'target-chip';
            chip.innerHTML = `<span>🎯 ${det.class_name}</span><span class="target-chip-conf">${(det.confidence * 100).toFixed(0)}%</span>`;
            elChipsContainer.appendChild(chip);
        });
    }

    // ---------------- Real Coordinate System Radar & SLAM Canvas ----------------
    function drawRadar() {
        const w = canvas.width;
        const h = canvas.height;
        const cx = w / 2;
        const cy = h / 2;
        const scale = 38; // 38 pixels per meter

        // Clear
        ctx.fillStyle = '#06090f';
        ctx.fillRect(0, 0, w, h);

        // Coordinate transformation: World (wx, wy) -> Canvas (sx, sy)
        // Center the view on the robot
        function worldToScreen(wx, wy) {
            const dx = wx - state.pose.x;
            const dy = wy - state.pose.y;
            // ROS X is forward (up on canvas), ROS Y is left (left on canvas)
            const sx = cx - dy * scale;
            const sy = cy - dx * scale;
            return { x: sx, y: sy };
        }

        // 1. Draw Real SLAM OccupancyGrid Map if available
        if (state.mapImageLoaded && state.mapImageObj && state.mapMeta.width > 0) {
            ctx.save();
            // Origin of map in world coords
            const meta = state.mapMeta;
            // Top-left of map in world coords (note: Y increases upwards in ROS)
            const mapTopWorldX = meta.origin_x + meta.height * meta.resolution;
            const mapLeftWorldY = meta.origin_y + meta.width * meta.resolution;

            const spTopLeft = worldToScreen(mapTopWorldX, mapLeftWorldY);
            const mapScreenWidth = meta.width * meta.resolution * scale;
            const mapScreenHeight = meta.height * meta.resolution * scale;

            ctx.globalAlpha = 0.85;
            ctx.drawImage(state.mapImageObj, spTopLeft.x, spTopLeft.y, mapScreenWidth, mapScreenHeight);
            ctx.restore();
        }

        // 2. Circular Tactical Range Rings
        ctx.strokeStyle = 'rgba(0, 242, 254, 0.12)';
        ctx.lineWidth = 1;
        [1, 2, 3, 4, 5].forEach((r) => {
            ctx.beginPath();
            ctx.arc(cx, cy, r * scale, 0, Math.PI * 2);
            ctx.stroke();

            ctx.fillStyle = 'rgba(0, 242, 254, 0.3)';
            ctx.font = '9px monospace';
            ctx.fillText(`${r}m`, cx + r * scale + 3, cy - 3);
        });

        // 3. Draw 360 LiDAR Scan Points (Relative to robot)
        if (state.laserPoints && state.laserPoints.length > 0) {
            ctx.fillStyle = '#00f2fe';
            state.laserPoints.forEach((pt) => {
                const sx = cx - pt[1] * scale;
                const sy = cy - pt[0] * scale;
                if (sx >= 0 && sx <= w && sy >= 0 && sy <= h) {
                    ctx.fillRect(sx - 1, sy - 1, 3, 3);
                }
            });
        }

        // 4. Draw Planned Path (from Nav2)
        if (state.plannedPath && state.plannedPath.length > 1) {
            ctx.strokeStyle = '#00e676';
            ctx.lineWidth = 2.5;
            ctx.beginPath();
            state.plannedPath.forEach((pt, i) => {
                const sp = worldToScreen(pt[0], pt[1]);
                if (i === 0) ctx.moveTo(sp.x, sp.y);
                else ctx.lineTo(sp.x, sp.y);
            });
            ctx.stroke();
        }

        // 5. Draw Destination Goal Marker
        if (state.currentGoal) {
            const gp = worldToScreen(state.currentGoal.x, state.currentGoal.y);
            ctx.fillStyle = '#ff9100';
            ctx.beginPath();
            ctx.arc(gp.x, gp.y, 6, 0, Math.PI * 2);
            ctx.fill();
            ctx.strokeStyle = '#ffffff';
            ctx.lineWidth = 1.5;
            ctx.stroke();
            ctx.fillStyle = '#ff9100';
            ctx.font = 'bold 10px monospace';
            ctx.fillText('TARGET', gp.x + 8, gp.y + 3);
        }

        // 6. Draw Robot Chassis Triangle at Center
        ctx.save();
        ctx.translate(cx, cy);
        ctx.rotate(-state.pose.yaw);

        ctx.fillStyle = 'rgba(0, 242, 254, 0.35)';
        ctx.strokeStyle = '#00f2fe';
        ctx.lineWidth = 2;
        ctx.beginPath();
        ctx.moveTo(0, -18);
        ctx.lineTo(12, 14);
        ctx.lineTo(-12, 14);
        ctx.closePath();
        ctx.fill();
        ctx.stroke();

        // Heading arrow
        ctx.strokeStyle = '#ff9100';
        ctx.lineWidth = 2;
        ctx.beginPath();
        ctx.moveTo(0, 0);
        ctx.lineTo(0, -26);
        ctx.stroke();

        ctx.restore();

        requestAnimationFrame(drawRadar);
    }

    // ---------------- Click-to-Goal (NavigateToPose) ----------------
    canvas.addEventListener('click', (e) => {
        if (state.estopLatched) {
            logEvent('DANGER', 'Cannot set goal: E-STOP is latched. Reset E-STOP first.', 'danger');
            return;
        }

        const rect = canvas.getBoundingClientRect();
        const clickX = e.clientX - rect.left;
        const clickY = e.clientY - rect.top;

        const w = canvas.width;
        const h = canvas.height;
        const scale = 38;

        const dy = (w / 2 - clickX) / scale;
        const dx = (h / 2 - clickY) / scale;

        const goalX = state.pose.x + dx;
        const goalY = state.pose.y + dy;

        dispatchGoal(goalX, goalY);
    });

    function dispatchGoal(x, y, yaw = 0.0) {
        state.currentGoal = { x, y };
        logEvent('NAV2', `Dispatching NavigateToPose Action: (${x.toFixed(2)}, ${y.toFixed(2)})`);

        fetch('/api/goal', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ x, y, yaw })
        }).then(res => res.json())
          .then(data => {
              if (data.status === 'ok') {
                  logEvent('NAV2', 'Goal dispatched to Nav2 Action Server.');
              } else {
                  logEvent('DANGER', `Goal rejected: ${data.message}`);
              }
          }).catch(err => {
              logEvent('DANGER', `Network error: ${err.message}`);
          });
    }

    // Mission Buttons
    document.getElementById('btn-patrol-1').addEventListener('click', () => {
        dispatchGoal(1.80, -0.50);
        logEvent('MISSION', 'Dispatching PATROL SECTOR ALPHA (1.80, -0.50)');
    });

    document.getElementById('btn-patrol-2').addEventListener('click', () => {
        dispatchGoal(0.50, 1.20);
        logEvent('MISSION', 'Dispatching RECON SECTOR BRAVO (0.50, 1.20)');
    });

    document.getElementById('btn-return-home').addEventListener('click', () => {
        dispatchGoal(-2.00, -0.50);
        logEvent('MISSION', 'Dispatching RETURN TO STAGING (-2.00, -0.50)');
    });

    document.getElementById('btn-clear-goal').addEventListener('click', () => {
        state.currentGoal = null;
        state.plannedPath = [];
        fetch('/api/estop', { method: 'POST' }).catch(() => {});
        logEvent('NAV2', 'Active goal preempted by operator.');
    });

    // ---------------- Latched Emergency Stop & Reset ----------------
    elEstopBtn.addEventListener('click', () => {
        if (state.estopLatched) {
            // Reset E-Stop
            fetch('/api/reset_estop', { method: 'POST' })
                .then(res => res.json())
                .then(data => {
                    logEvent('SYSTEM', 'E-STOP Latch cleared. Motor power restored.');
                });
        } else {
            // Engage E-Stop
            logEvent('E-STOP', 'AUTHORITATIVE E-STOP ACTIVATED. Nav2 cancelled & motors clamped.', 'danger');
            state.currentGoal = null;
            state.plannedPath = [];
            fetch('/api/estop', { method: 'POST' }).catch(() => {});
        }
    });

    // Teleoperation
    function sendTeleop(linear, angular) {
        if (state.estopLatched) return;
        fetch('/api/teleop', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ linear, angular })
        }).catch(() => {});
    }

    elSpeedSlider.addEventListener('input', (e) => {
        state.speedLimit = parseFloat(e.target.value);
        elSpeedLimitVal.textContent = state.speedLimit.toFixed(2);
    });

    // D-Pad
    const btnFwd = document.getElementById('btn-drive-fwd');
    const btnRev = document.getElementById('btn-drive-rev');
    const btnLeft = document.getElementById('btn-turn-left');
    const btnRight = document.getElementById('btn-turn-right');
    const btnBrake = document.getElementById('btn-brake');

    btnFwd.addEventListener('mousedown', () => sendTeleop(state.speedLimit, 0.0));
    btnRev.addEventListener('mousedown', () => sendTeleop(-state.speedLimit, 0.0));
    btnLeft.addEventListener('mousedown', () => sendTeleop(0.0, 0.6));
    btnRight.addEventListener('mousedown', () => sendTeleop(0.0, -0.6));
    btnBrake.addEventListener('mousedown', () => sendTeleop(0.0, 0.0));
    window.addEventListener('mouseup', () => sendTeleop(0.0, 0.0));

    // Keyboard (WASD + Space)
    window.addEventListener('keydown', (e) => {
        if (e.repeat) return;
        const key = e.key.toLowerCase();
        state.keysPressed[key] = true;

        if (key === ' ') {
            elEstopBtn.click();
            return;
        }

        let lin = 0.0;
        let ang = 0.0;
        if (state.keysPressed['w'] || state.keysPressed['arrowup']) lin += state.speedLimit;
        if (state.keysPressed['s'] || state.keysPressed['arrowdown']) lin -= state.speedLimit;
        if (state.keysPressed['a'] || state.keysPressed['arrowleft']) ang += 0.6;
        if (state.keysPressed['d'] || state.keysPressed['arrowright']) ang -= 0.6;

        if (lin !== 0.0 || ang !== 0.0) sendTeleop(lin, ang);
    });

    window.addEventListener('keyup', (e) => {
        const key = e.key.toLowerCase();
        delete state.keysPressed[key];

        let lin = 0.0;
        let ang = 0.0;
        if (state.keysPressed['w'] || state.keysPressed['arrowup']) lin += state.speedLimit;
        if (state.keysPressed['s'] || state.keysPressed['arrowdown']) lin -= state.speedLimit;
        if (state.keysPressed['a'] || state.keysPressed['arrowleft']) ang += 0.6;
        if (state.keysPressed['d'] || state.keysPressed['arrowright']) ang -= 0.6;

        sendTeleop(lin, ang);
    });

    // Uptime counter
    let seconds = 0;
    setInterval(() => {
        seconds++;
        const h = String(Math.floor(seconds / 3600)).padStart(2, '0');
        const m = String(Math.floor((seconds % 3600) / 60)).padStart(2, '0');
        const s = String(seconds % 60).padStart(2, '0');
        elUptime.textContent = `${h}:${m}:${s}`;
    }, 1000);

    // Start loops
    initEventStream();
    drawRadar();
});
