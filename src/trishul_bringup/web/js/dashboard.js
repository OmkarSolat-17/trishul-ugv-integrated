// ==========================================================================
// TRISHUL UGV -- Production-Grade Mission Control Dashboard Client (v2.5)
// Implements:
// 1. Mathematically consistent Top-Down SLAM Map & LiDAR coordinate alignment
// 2. Interactive Click-to-Navigate with accurate world-coordinate projection
// 3. Mouse Wheel Canvas Zoom & Pan
// 4. Multi-feed Camera Stream Switcher (YOLO Annotated / Raw Camera / Overhead)
// 5. Authoritative E-STOP with clear visual latch & instant zero-clamp
// 6. Selectable Mission Event Stream log with instant copy
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
        zoomScale: 38, // Pixels per meter
        activeFeed: 'combined',
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
    const elSpeedVal = document.getElementById('speed-limit-val');
    const elVideoFeed = document.getElementById('live-video-feed');

    const canvas = document.getElementById('radar-canvas');
    const ctx = canvas.getContext('2d');

    // Auto-resize canvas for sharp rendering
    function resizeCanvas() {
        if (!canvas) return;
        const rect = canvas.getBoundingClientRect();
        if (canvas.width !== rect.width || canvas.height !== rect.height) {
            canvas.width = rect.width;
            canvas.height = rect.height;
        }
    }
    window.addEventListener('resize', resizeCanvas);
    resizeCanvas();

    // Mission Event Logging
    function logEvent(source, msg, level = 'info') {
        if (!elTerminal) return;
        const line = document.createElement('div');
        line.className = `terminal-line level-${level} selectable-text`;

        const time = new Date().toTimeString().split(' ')[0];
        line.innerHTML = `<span class="time">[${time}]</span> <span class="tag tag-${level.toLowerCase()}">[${source}]</span> <span class="msg">${msg}</span>`;

        elTerminal.appendChild(line);
        elTerminal.scrollTop = elTerminal.scrollHeight;

        // Keep last 150 lines
        while (elTerminal.children.length > 150) {
            elTerminal.removeChild(elTerminal.firstChild);
        }
    }

    logEvent('SYSTEM', 'Uplink established with Trishul Dashboard Server.');

    // ---------------- Real-Time Telemetry Polling ----------------
    let pollFailures = 0;
    async function pollTelemetry() {
        try {
            const resp = await fetch('/api/state');
            if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
            const data = await resp.json();

            state.connected = true;
            pollFailures = 0;

            // Update System Status Header
            if (elSysStatus) {
                if (data.estop_latched) {
                    elSysStatus.textContent = 'SYS: EMERGENCY STOP ENGAGED';
                    elSysStatus.className = 'status-badge danger';
                    if (elSysPulse) elSysPulse.className = 'pulse-dot danger';
                } else if (data.nav_state === 'NAVIGATING') {
                    elSysStatus.textContent = 'SYS: AUTONOMOUS MISSION ACTIVE';
                    elSysStatus.className = 'status-badge active';
                    if (elSysPulse) elSysPulse.className = 'pulse-dot active';
                } else {
                    elSysStatus.textContent = 'SYS: OPERATIONAL / STANDBY';
                    elSysStatus.className = 'status-badge active';
                    if (elSysPulse) elSysPulse.className = 'pulse-dot active';
                }
            }

            // Sync E-STOP Button state
            state.estopLatched = data.estop_latched;
            if (elEstopBtn) {
                if (state.estopLatched) {
                    elEstopBtn.classList.add('latched');
                    if (elEstopBtnText) elEstopBtnText.textContent = 'RESET E-STOP (LATCHED)';
                } else {
                    elEstopBtn.classList.remove('latched');
                    if (elEstopBtnText) elEstopBtnText.textContent = 'EMERGENCY STOP';
                }
            }

            // Pose & Velocity
            if (data.pose) state.pose = data.pose;
            if (data.vel) state.vel = data.vel;
            state.closestObstacle = data.closest_obstacle;
            state.battery = data.battery;
            state.navState = data.nav_state;
            state.distRemaining = data.distance_remaining;
            state.etaSeconds = data.eta_seconds;
            state.laserPoints = data.laser_points || [];
            state.plannedPath = data.path || [];

            // Map Image Synchronization
            if (data.map_image && data.map_meta) {
                state.mapMeta = data.map_meta;
                if (!state.mapImageObj) {
                    state.mapImageObj = new Image();
                    state.mapImageObj.onload = () => {
                        state.mapImageLoaded = true;
                    };
                }
                state.mapImageObj.src = 'data:image/png;base64,' + data.map_image;
            }

            // Update DOM Values
            if (elBattery) elBattery.textContent = `${state.battery}% [${(24.0 + (state.battery - 50) * 0.05).toFixed(1)}V]`;
            if (elPose) elPose.textContent = `(${state.pose.x.toFixed(2)}, ${state.pose.y.toFixed(2)}) @ ${(state.pose.yaw * 180 / Math.PI).toFixed(0)}°`;
            if (elNavState) {
                elNavState.textContent = state.navState;
                elNavState.className = `val ${state.navState === 'NAVIGATING' ? 'text-cyan' : state.navState === 'SUCCEEDED' ? 'text-green' : state.navState === 'FAILED' ? 'text-red' : ''}`;
            }
            if (elNavDist) {
                if (state.navState === 'NAVIGATING') {
                    elNavDist.textContent = `${state.distRemaining.toFixed(2)}m (${state.etaSeconds.toFixed(0)}s)`;
                } else {
                    elNavDist.textContent = state.navState;
                }
            }
            if (elLinearVel) elLinearVel.textContent = `${state.vel.linear.toFixed(2)}`;
            if (elAngularVel) elAngularVel.textContent = `${state.vel.angular.toFixed(2)}`;

            if (elClosestObs) {
                elClosestObs.textContent = `${state.closestObstacle.toFixed(2)} m`;
                if (state.closestObstacle < 0.35) {
                    elClosestObs.className = 'val text-red glow-red';
                    if (elSafetyStatus) {
                        elSafetyStatus.textContent = 'DANGER: COLLISION BRAKE';
                        elSafetyStatus.className = 'sub-val text-red';
                    }
                } else if (state.closestObstacle < 0.70) {
                    elClosestObs.className = 'val text-amber';
                    if (elSafetyStatus) {
                        elSafetyStatus.textContent = 'WARNING: PROXIMITY ALERT';
                        elSafetyStatus.className = 'sub-val text-amber';
                    }
                } else {
                    elClosestObs.className = 'val text-cyan';
                    if (elSafetyStatus) {
                        elSafetyStatus.textContent = 'PATH CLEAR';
                        elSafetyStatus.className = 'sub-val text-green';
                    }
                }
            }

            // Vision Detections
            if (data.detections) {
                state.activeDetections = data.detections;
                if (elDetectionCount) elDetectionCount.textContent = `${data.detections.length} TARGETS`;
                if (elChipsContainer) {
                    if (data.detections.length === 0) {
                        elChipsContainer.innerHTML = '<span class="empty-state">Sector clear. Awaiting target classification...</span>';
                    } else {
                        elChipsContainer.innerHTML = '';
                        data.detections.forEach((d) => {
                            const chip = document.createElement('div');
                            chip.className = 'target-chip';
                            chip.innerHTML = `<span class="target-name">${d.name}</span> <span class="target-conf">${(d.confidence * 100).toFixed(0)}%</span>`;
                            elChipsContainer.appendChild(chip);
                        });
                    }
                }
            }

        } catch (err) {
            pollFailures++;
            if (pollFailures > 4) {
                state.connected = false;
                if (elSysStatus) {
                    elSysStatus.textContent = 'SYS: TELEMETRY LINK OFFLINE';
                    elSysStatus.className = 'status-badge danger';
                    if (elSysPulse) elSysPulse.className = 'pulse-dot danger';
                }
            }
        }
    }
    setInterval(pollTelemetry, 150);

    // Uptime Counter
    let secondsElapsed = 0;
    setInterval(() => {
        secondsElapsed++;
        const mins = String(Math.floor(secondsElapsed / 60)).padStart(2, '0');
        const secs = String(secondsElapsed % 60).padStart(2, '0');
        const hrs = String(Math.floor(secondsElapsed / 3600)).padStart(2, '0');
        if (elUptime) elUptime.textContent = `${hrs}:${mins}:${secs}`;
    }, 1000);

    // ---------------- Mathematically Consistent Radar & SLAM Canvas ----------------
    function drawRadar() {
        resizeCanvas();
        const w = canvas.width;
        const h = canvas.height;
        const cx = w / 2;
        const cy = h / 2;
        const scale = state.zoomScale;

        // Clear Background
        ctx.fillStyle = '#06090f';
        ctx.fillRect(0, 0, w, h);

        // World (wx, wy) in meters -> Canvas (sx, sy) in pixels
        // Follow-Robot Mode: center (cx, cy) is robot position (state.pose.x, state.pose.y)
        // Standard Top-Down Map: +X is East (right), +Y is North (up)
        function worldToScreen(wx, wy) {
            const sx = cx + (wx - state.pose.x) * scale;
            const sy = cy - (wy - state.pose.y) * scale;
            return { x: sx, y: sy };
        }

        // 1. Draw Real SLAM OccupancyGrid Map
        if (state.mapImageLoaded && state.mapImageObj && state.mapMeta && state.mapMeta.width > 0) {
            ctx.save();
            const meta = state.mapMeta;
            // Top-left world coordinate of the map (column 0 = origin_x, top row = origin_y + height * resolution)
            const mapTopWorldX = meta.origin_x;
            const mapTopWorldY = meta.origin_y + meta.height * meta.resolution;

            const spTopLeft = worldToScreen(mapTopWorldX, mapTopWorldY);
            const mapScreenWidth = meta.width * meta.resolution * scale;
            const mapScreenHeight = meta.height * meta.resolution * scale;

            ctx.globalAlpha = 0.90;
            ctx.imageSmoothingEnabled = false;
            ctx.drawImage(state.mapImageObj, spTopLeft.x, spTopLeft.y, mapScreenWidth, mapScreenHeight);
            ctx.restore();
        }

        // 2. Tactical Range Rings (Centered on robot)
        ctx.strokeStyle = 'rgba(0, 242, 254, 0.12)';
        ctx.lineWidth = 1;
        [1, 2, 3, 5, 8].forEach((r) => {
            ctx.beginPath();
            ctx.arc(cx, cy, r * scale, 0, Math.PI * 2);
            ctx.stroke();

            ctx.fillStyle = 'rgba(0, 242, 254, 0.35)';
            ctx.font = '9px monospace';
            ctx.fillText(`${r}m`, cx + r * scale + 3, cy - 3);
        });

        // Crosshair Axes (East-West & North-South)
        ctx.strokeStyle = 'rgba(0, 242, 254, 0.10)';
        ctx.beginPath();
        ctx.moveTo(0, cy); ctx.lineTo(w, cy);
        ctx.moveTo(cx, 0); ctx.lineTo(cx, h);
        ctx.stroke();

        // 3. Draw 360 LiDAR Scan Points (Rotated to World Frame with Robot Yaw)
        if (state.laserPoints && state.laserPoints.length > 0) {
            ctx.fillStyle = '#00f2fe';
            const cos_yaw = Math.cos(state.pose.yaw);
            const sin_yaw = Math.sin(state.pose.yaw);

            state.laserPoints.forEach((pt) => {
                const rx = pt[0]; // Forward in robot body
                const ry = pt[1]; // Left in robot body
                // Transform to world coordinates
                const wx = state.pose.x + (rx * cos_yaw - ry * sin_yaw);
                const wy = state.pose.y + (rx * sin_yaw + ry * cos_yaw);

                const sp = worldToScreen(wx, wy);
                if (sp.x >= 0 && sp.x <= w && sp.y >= 0 && sp.y <= h) {
                    ctx.fillRect(sp.x - 1.5, sp.y - 1.5, 3, 3);
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

        // 5. Draw Destination Goal Marker (Target)
        if (state.currentGoal) {
            const gp = worldToScreen(state.currentGoal.x, state.currentGoal.y);
            ctx.fillStyle = '#ff9100';
            ctx.beginPath();
            ctx.arc(gp.x, gp.y, 6, 0, Math.PI * 2);
            ctx.fill();
            ctx.strokeStyle = '#ffffff';
            ctx.lineWidth = 1.5;
            ctx.stroke();

            // Pulsing target halo
            ctx.strokeStyle = 'rgba(255, 145, 0, 0.4)';
            ctx.lineWidth = 1;
            ctx.beginPath();
            ctx.arc(gp.x, gp.y, 12, 0, Math.PI * 2);
            ctx.stroke();

            ctx.fillStyle = '#ff9100';
            ctx.font = 'bold 10px monospace';
            ctx.fillText('TARGET', gp.x + 8, gp.y + 3);
        }

        // 6. Draw Robot Chassis at Center (cx, cy)
        ctx.save();
        ctx.translate(cx, cy);
        // Canvas rotation: standard ROS yaw angle (0 = East/right, pi/2 = North/up)
        // Canvas Y is downwards, so counter-clockwise rotation is negative
        ctx.rotate(-state.pose.yaw);

        // Robot Body (Nose points along +X, to the right when yaw=0)
        ctx.fillStyle = 'rgba(0, 242, 254, 0.45)';
        ctx.strokeStyle = '#00f2fe';
        ctx.lineWidth = 2;
        ctx.beginPath();
        ctx.moveTo(18, 0);     // Nose forward (+X)
        ctx.lineTo(-12, -10);  // Back left
        ctx.lineTo(-6, 0);     // Inset tail
        ctx.lineTo(-12, 10);   // Back right
        ctx.closePath();
        ctx.fill();
        ctx.stroke();

        // Heading Indicator Arrow
        ctx.strokeStyle = '#ff9100';
        ctx.lineWidth = 2.5;
        ctx.beginPath();
        ctx.moveTo(0, 0);
        ctx.lineTo(26, 0);
        ctx.stroke();

        ctx.restore();

        requestAnimationFrame(drawRadar);
    }
    requestAnimationFrame(drawRadar);

    // ---------------- Mouse Wheel Canvas Zoom ----------------
    canvas.addEventListener('wheel', (e) => {
        e.preventDefault();
        const delta = e.deltaY < 0 ? 1.15 : 0.87;
        state.zoomScale = Math.min(120, Math.max(10, state.zoomScale * delta));
        logEvent('MAP', `Zoom: ${state.zoomScale.toFixed(0)} px/m`);
    }, { passive: false });

    // ---------------- Click-to-Goal (Accurate Nav2 Goal Dispatch) ----------------
    canvas.addEventListener('click', (e) => {
        if (state.estopLatched) {
            logEvent('DANGER', 'Cannot set goal: E-STOP is latched. Reset E-STOP first.', 'danger');
            return;
        }

        const rect = canvas.getBoundingClientRect();
        const clickX = e.clientX - rect.left;
        const clickY = e.clientY - rect.top;

        const cx = canvas.width / 2;
        const cy = canvas.height / 2;
        const scale = state.zoomScale;

        // Invert worldToScreen:
        // sx = cx + (wx - pose.x) * scale => wx = pose.x + (sx - cx) / scale
        // sy = cy - (wy - pose.y) * scale => wy = pose.y - (sy - cy) / scale
        const goalX = state.pose.x + (clickX - cx) / scale;
        const goalY = state.pose.y - (clickY - cy) / scale;

        // Calculate direct heading angle to target
        const dx = goalX - state.pose.x;
        const dy = goalY - state.pose.y;
        const goalYaw = Math.atan2(dy, dx);

        dispatchGoal(goalX, goalY, goalYaw);
    });

    async function dispatchGoal(x, y, yaw = 0.0) {
        state.currentGoal = { x, y };
        logEvent('NAV2', `Dispatching NavigateToPose Action: (${x.toFixed(2)}, ${y.toFixed(2)})`);

        try {
            const resp = await fetch('/api/goal', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ x, y, yaw })
            });
            const data = await resp.json();
            if (data.status === 'ok') {
                logEvent('NAV2', `Goal accepted by Nav2 action server.`);
            } else {
                logEvent('NAV2', `Goal rejected: ${data.message}`, 'warn');
            }
        } catch (err) {
            logEvent('NAV2', `Failed to send goal: ${err.message}`, 'danger');
        }
    }

    // ---------------- Preset Missions ----------------
    document.getElementById('btn-patrol-1')?.addEventListener('click', () => {
        logEvent('MISSION', 'Dispatching Preset: Patrol Sector Alpha');
        dispatchGoal(1.8, -0.5, 0.0);
    });

    document.getElementById('btn-patrol-2')?.addEventListener('click', () => {
        logEvent('MISSION', 'Dispatching Preset: Recon Sector Bravo');
        dispatchGoal(-1.8, 1.2, 1.57);
    });

    document.getElementById('btn-return-home')?.addEventListener('click', () => {
        logEvent('MISSION', 'Dispatching Preset: Return to Staging (Home)');
        dispatchGoal(-2.0, -0.5, 0.0);
    });

    document.getElementById('btn-clear-goal')?.addEventListener('click', async () => {
        logEvent('NAV2', 'Preempting / Cancelling Active Goal');
        state.currentGoal = null;
        try {
            await fetch('/api/cancel', { method: 'POST' });
        } catch (err) {
            console.error(err);
        }
    });

    // ---------------- Camera Feed Switcher Buttons ----------------
    const camButtons = document.querySelectorAll('.cam-btn');
    camButtons.forEach((btn, index) => {
        btn.removeAttribute('disabled');
        btn.classList.remove('disabled');

        btn.addEventListener('click', () => {
            camButtons.forEach((b) => b.classList.remove('active'));
            btn.classList.add('active');

            if (index === 0) {
                state.activeFeed = 'combined';
                logEvent('CAMERA', 'Switched to FRONT (AI YOLO ANNOTATED)');
            } else if (index === 1) {
                state.activeFeed = 'raw';
                logEvent('CAMERA', 'Switched to RAW SENSOR FEED (/camera/image_raw)');
            } else {
                state.activeFeed = 'rear';
                logEvent('CAMERA', 'Switched to REAR / OVERHEAD PERSPECTIVE');
            }

            if (elVideoFeed) {
                elVideoFeed.src = `/stream/video?feed=${state.activeFeed}&t=${Date.now()}`;
            }
        });
    });

    // ---------------- Authoritative E-STOP Toggle ----------------
    if (elEstopBtn) {
        elEstopBtn.addEventListener('click', async () => {
            if (!state.estopLatched) {
                // Engage E-STOP
                logEvent('SAFETY', '>>> AUTHORITATIVE EMERGENCY STOP ENGAGED <<<', 'danger');
                try {
                    await fetch('/api/estop', { method: 'POST' });
                    state.estopLatched = true;
                    elEstopBtn.classList.add('latched');
                    if (elEstopBtnText) elEstopBtnText.textContent = 'RESET E-STOP (LATCHED)';
                } catch (err) {
                    logEvent('SAFETY', `Failed to engage E-STOP: ${err.message}`, 'danger');
                }
            } else {
                // Reset E-STOP
                logEvent('SYSTEM', 'E-STOP Latch cleared. Motor power restored.', 'active');
                try {
                    await fetch('/api/reset_estop', { method: 'POST' });
                    state.estopLatched = false;
                    elEstopBtn.classList.remove('latched');
                    if (elEstopBtnText) elEstopBtnText.textContent = 'EMERGENCY STOP';
                } catch (err) {
                    logEvent('SYSTEM', `Failed to reset E-STOP: ${err.message}`, 'danger');
                }
            }
        });
    }

    // ---------------- Manual Teleoperation ----------------
    function sendTeleop(lin, ang) {
        if (state.estopLatched) return;
        fetch('/api/teleop', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ linear: lin, angular: ang })
        }).catch(() => {});
    }

    const keyMap = {
        'KeyW': [1.0, 0.0],
        'KeyS': [-1.0, 0.0],
        'KeyA': [0.0, 1.2],
        'KeyD': [0.0, -1.2],
        'KeyX': [0.0, 0.0],
    };

    window.addEventListener('keydown', (e) => {
        if (['KeyW', 'KeyS', 'KeyA', 'KeyD', 'KeyX'].includes(e.code)) {
            e.preventDefault();
            const btn = document.getElementById(`btn-teleop-${e.code.replace('Key', '').toLowerCase()}`);
            if (btn) btn.classList.add('active');

            const [baseLin, baseAng] = keyMap[e.code];
            const lin = baseLin * state.speedLimit;
            sendTeleop(lin, baseAng);
        } else if (e.code === 'Space') {
            e.preventDefault();
            sendTeleop(0.0, 0.0);
            if (elEstopBtn) elEstopBtn.click();
        }
    });

    window.addEventListener('keyup', (e) => {
        if (['KeyW', 'KeyS', 'KeyA', 'KeyD'].includes(e.code)) {
            const btn = document.getElementById(`btn-teleop-${e.code.replace('Key', '').toLowerCase()}`);
            if (btn) btn.classList.remove('active');
            sendTeleop(0.0, 0.0);
        }
    });

    // Speed Slider
    if (elSpeedSlider) {
        elSpeedSlider.addEventListener('input', (e) => {
            const val = parseFloat(e.target.value);
            state.speedLimit = val;
            if (elSpeedVal) elSpeedVal.textContent = `${val.toFixed(2)} m/s`;
        });
    }
});
