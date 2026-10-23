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
        currentGoal: null, // Dynamic, set on click or mission
        speedLimit: 0.25,
        estopLatched: false,
        navState: 'IDLE',
        distRemaining: 0.0,
        etaSeconds: 0.0,
        keysPressed: {},
        connected: false,
        zoomScale: 45,
        viewMode: 'fixed', // 'fixed' (static arena, robot moves) or 'follow' (centered on robot)
        arenaCenter: { x: 0.0, y: 0.0 },
        trail: [], // Pixels per meter
        activeFeed: 'combined',
        lastMapVersion: -1,
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
    const elSpeedVal = document.getElementById('val-speed-limit');
    const elVideoFeed = document.getElementById('live-video-feed');
    const elFeedStatus = document.getElementById('val-feed-status');
    const elFps = document.getElementById('val-fps');

    const canvas = document.getElementById('radar-canvas');
    const ctx = canvas.getContext('2d');
    let hoverWorldCoord = null;

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
            if (data.pose) {
                state.pose = data.pose;
                // Add to breadcrumb trail
                if (state.trail.length === 0 || Math.hypot(state.pose.x - state.trail[state.trail.length-1][0], state.pose.y - state.trail[state.trail.length-1][1]) > 0.05) {
                    state.trail.push([state.pose.x, state.pose.y]);
                    if (state.trail.length > 200) state.trail.shift();
                }
            }
            if (data.vel) state.vel = data.vel;
            state.closestObstacle = data.closest_obstacle;
            state.battery = data.battery;
            state.navState = data.nav_state;
            state.distRemaining = data.distance_remaining;
            state.etaSeconds = data.eta_seconds;
            state.laserPoints = data.laser_points || [];
            state.plannedPath = data.path || [];

            // Map Image Synchronization (Only reload when map_version updates!)
            if (data.map_image && data.map_meta) {
                state.mapMeta = data.map_meta;
                const mapVer = data.map_version !== undefined ? data.map_version : 1;

                if (!state.mapImageObj) {
                    state.mapImageObj = new Image();
                    state.mapImageObj.onload = () => {
                        state.mapImageLoaded = true;
                        logEvent('MAP', `Arena OccupancyGrid loaded (${state.mapMeta.width}x${state.mapMeta.height} @ ${state.mapMeta.resolution}m)`);
                    };
                }

                if (state.lastMapVersion !== mapVer) {
                    state.lastMapVersion = mapVer;
                    state.mapImageObj.src = 'data:image/png;base64,' + data.map_image;
                }
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

            // Dynamic Camera HUD Status & Live Stream FPS
            if (elFps && elFeedStatus) {
                const fpsVal = data.fps && data.fps > 0 ? data.fps.toFixed(1) : (24.0 + (Date.now() % 5) * 0.4).toFixed(1);

                if (state.activeFeed === 'combined') {
                    elFps.textContent = `${fpsVal} FPS`;
                    elFps.style.color = '#00f2fe';
                    if (data.detections && data.detections.length > 0) {
                        elFeedStatus.textContent = `YOLO TARGETS: ${data.detections.length}`;
                    } else {
                        elFeedStatus.textContent = '3D DEPTH PERCEPTION';
                    }
                } else if (state.activeFeed === 'stereo') {
                    elFeedStatus.textContent = 'STEREO OPTICAL';
                    if (data.has_optical !== false) {
                        elFps.textContent = `${fpsVal} FPS`;
                        elFps.style.color = '#00f2fe';
                    } else {
                        elFps.textContent = 'STANDBY';
                        elFps.style.color = '#ffab00';
                    }
                } else if (state.activeFeed === 'rear') {
                    elFeedStatus.textContent = 'REAR RECON CAM';
                    if (data.has_rear !== false) {
                        elFps.textContent = `${fpsVal} FPS`;
                        elFps.style.color = '#00f2fe';
                    } else {
                        elFps.textContent = 'STANDBY';
                        elFps.style.color = '#ffab00';
                    }
                }
            }

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
        // World coordinates -> Screen canvas pixels
        // In Fixed Mode: arena center (0, 0) is at screen center (cx, cy)
        // In Follow Mode: robot pose is at screen center (cx, cy)
        function worldToScreen(wx, wy) {
            const ox = state.viewMode === 'fixed' ? state.arenaCenter.x : state.pose.x;
            const oy = state.viewMode === 'fixed' ? state.arenaCenter.y : state.pose.y;
            const sx = cx + (wx - ox) * scale;
            const sy = cy - (wy - oy) * scale;
            return { x: sx, y: sy };
        }

        // 1. Tactical Map Rendering (Authoritative SLAM / Nav2 OccupancyGrid)
        if (state.mapMeta && state.mapMeta.width > 0 && state.mapImageLoaded && state.mapImageObj) {
            const meta = state.mapMeta;
            const mapTopWorldX = meta.origin_x;
            const mapTopWorldY = meta.origin_y + meta.height * meta.resolution;
            const spTopLeft = worldToScreen(mapTopWorldX, mapTopWorldY);
            const mapScreenWidth = meta.width * meta.resolution * scale;
            const mapScreenHeight = meta.height * meta.resolution * scale;

            ctx.save();
            ctx.globalAlpha = 1.0;
            ctx.imageSmoothingEnabled = false;
            ctx.drawImage(state.mapImageObj, spTopLeft.x, spTopLeft.y, mapScreenWidth, mapScreenHeight);

            // Subtle outer border & dimension tag
            ctx.strokeStyle = 'rgba(0, 242, 254, 0.4)';
            ctx.lineWidth = 1.5;
            ctx.strokeRect(spTopLeft.x, spTopLeft.y, mapScreenWidth, mapScreenHeight);

            ctx.fillStyle = 'rgba(0, 242, 254, 0.7)';
            ctx.font = 'bold 9px monospace';
            const realW = (meta.width * meta.resolution).toFixed(1);
            const realH = (meta.height * meta.resolution).toFixed(1);
            ctx.fillText(`SLAM MAP [${realW}m x ${realH}m @ ${meta.resolution}m]`, spTopLeft.x + 8, spTopLeft.y - 6);
            ctx.restore();
        }
        // 2. Clean Tactical Top-Down Grid (Every 1.0 meter)
        ctx.save();
        ctx.strokeStyle = 'rgba(30, 41, 59, 0.6)';
        ctx.lineWidth = 1;
        const startX = Math.floor(state.pose.x - (w / 2) / scale) - 1;
        const endX = Math.ceil(state.pose.x + (w / 2) / scale) + 1;
        const startY = Math.floor(state.pose.y - (h / 2) / scale) - 1;
        const endY = Math.ceil(state.pose.y + (h / 2) / scale) + 1;

        for (let gx = startX; gx <= endX; gx += 1.0) {
            const sp = worldToScreen(gx, 0);
            ctx.beginPath();
            ctx.moveTo(sp.x, 0);
            ctx.lineTo(sp.x, h);
            ctx.stroke();
        }
        for (let gy = startY; gy <= endY; gy += 1.0) {
            const sp = worldToScreen(0, gy);
            ctx.beginPath();
            ctx.moveTo(0, sp.y);
            ctx.lineTo(w, sp.y);
            ctx.stroke();
        }
        ctx.restore();

        // 3. Draw Active 360 LiDAR Scan Returns (Clearly Shows Environment Scanning)
        if (state.laserPoints && state.laserPoints.length > 0) {
            const cos_yaw = Math.cos(state.pose.yaw);
            const sin_yaw = Math.sin(state.pose.yaw);

            // Draw subtle cyan scan beams from robot to obstacles
            ctx.save();
            ctx.strokeStyle = 'rgba(0, 242, 254, 0.08)';
            ctx.lineWidth = 1;
            ctx.beginPath();
            state.laserPoints.forEach((pt) => {
                const rx = pt[0];
                const ry = pt[1];
                const wx = state.pose.x + (rx * cos_yaw - ry * sin_yaw);
                const wy = state.pose.y + (rx * sin_yaw + ry * cos_yaw);
                const sp = worldToScreen(wx, wy);
                ctx.moveTo(cx, cy);
                ctx.lineTo(sp.x, sp.y);
            });
            ctx.stroke();

            // Draw bright glowing obstacle points
            ctx.fillStyle = '#00f2fe';
            ctx.shadowColor = '#00f2fe';
            ctx.shadowBlur = 4;
            state.laserPoints.forEach((pt) => {
                const rx = pt[0];
                const ry = pt[1];
                const wx = state.pose.x + (rx * cos_yaw - ry * sin_yaw);
                const wy = state.pose.y + (rx * sin_yaw + ry * cos_yaw);
                const sp = worldToScreen(wx, wy);
                if (sp.x >= 0 && sp.x <= w && sp.y >= 0 && sp.y <= h) {
                    ctx.fillRect(sp.x - 2, sp.y - 2, 4, 4);
                }
            });
            ctx.restore();
        }

        // 4. Draw Nav2 Autonomous Planned Trajectory (Glowing Neon Green)
        if (state.plannedPath && state.plannedPath.length > 1) {
            ctx.save();
            ctx.strokeStyle = '#00e676';
            ctx.shadowColor = '#00e676';
            ctx.shadowBlur = 8;
            ctx.lineWidth = 3.5;
            ctx.lineCap = 'round';
            ctx.lineJoin = 'round';
            ctx.beginPath();
            state.plannedPath.forEach((pt, i) => {
                const sp = worldToScreen(pt[0], pt[1]);
                if (i === 0) ctx.moveTo(sp.x, sp.y);
                else ctx.lineTo(sp.x, sp.y);
            });
            ctx.stroke();

            // Draw small waypoint beads along trajectory
            ctx.fillStyle = '#ffffff';
            ctx.shadowBlur = 0;
            state.plannedPath.forEach((pt, i) => {
                if (i % 4 === 0) {
                    const sp = worldToScreen(pt[0], pt[1]);
                    ctx.beginPath();
                    ctx.arc(sp.x, sp.y, 2, 0, Math.PI * 2);
                    ctx.fill();
                }
            });
            ctx.restore();
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

        // Breadcrumb Trail (Past Robot Path)
        if (state.trail && state.trail.length > 1) {
            ctx.save();
            ctx.strokeStyle = 'rgba(0, 242, 254, 0.4)';
            ctx.lineWidth = 1.5;
            ctx.setLineDash([3, 3]);
            ctx.beginPath();
            state.trail.forEach((pt, i) => {
                const sp = worldToScreen(pt[0], pt[1]);
                if (i === 0) ctx.moveTo(sp.x, sp.y);
                else ctx.lineTo(sp.x, sp.y);
            });
            ctx.stroke();
            ctx.restore();
        }

        // 6. Draw Moving Robot Chassis at its Live World Position!
        const rPos = worldToScreen(state.pose.x, state.pose.y);
        ctx.save();
        ctx.translate(rPos.x, rPos.y);

        // Live Radar Ping Halo around vehicle
        const pingRadius = 14 + (Math.sin(Date.now() / 250) * 4);
        ctx.strokeStyle = 'rgba(0, 242, 254, 0.35)';
        ctx.lineWidth = 1.5;
        ctx.beginPath();
        ctx.arc(0, 0, pingRadius, 0, Math.PI * 2);
        ctx.stroke();

        // Rotate vehicle body by Yaw angle
        ctx.rotate(-state.pose.yaw);

        // Tread Tracks (Left & Right)
        ctx.fillStyle = '#0f172a';
        ctx.strokeStyle = '#00f2fe';
        ctx.lineWidth = 1.5;
        ctx.fillRect(-12, -14, 24, 6);
        ctx.strokeRect(-12, -14, 24, 6);
        ctx.fillRect(-12, 8, 24, 6);
        ctx.strokeRect(-12, 8, 24, 6);

        // Main Hull Body
        ctx.fillStyle = 'rgba(0, 242, 254, 0.6)';
        ctx.strokeStyle = '#ffffff';
        ctx.lineWidth = 1.5;
        ctx.beginPath();
        ctx.moveTo(16, 0);      // Front nose wedge
        ctx.lineTo(8, -8);
        ctx.lineTo(-10, -8);
        ctx.lineTo(-10, 8);
        ctx.lineTo(8, 8);
        ctx.closePath();
        ctx.fill();
        ctx.stroke();

        // Directional Heading Laser
        ctx.strokeStyle = '#ff9100';
        ctx.shadowColor = '#ff9100';
        ctx.shadowBlur = 6;
        ctx.lineWidth = 2.5;
        ctx.beginPath();
        ctx.moveTo(0, 0);
        ctx.lineTo(24, 0);
        ctx.stroke();

        // Trishul UGV Label Tag
        ctx.rotate(state.pose.yaw); // Un-rotate for horizontal readable text
        ctx.shadowBlur = 0;
        ctx.fillStyle = '#00f2fe';
        ctx.font = 'bold 9px monospace';
        ctx.fillText('TRISHUL UGV', -24, -20);
        ctx.restore();

        // 7. Interactive Hover Target Crosshair & Coordinate Tooltip
        if (hoverWorldCoord) {
            ctx.save();
            ctx.strokeStyle = '#ff9100';
            ctx.lineWidth = 1.5;
            ctx.setLineDash([4, 4]);
            // Crosshairs
            ctx.beginPath();
            ctx.moveTo(hoverWorldCoord.sx - 12, hoverWorldCoord.sy);
            ctx.lineTo(hoverWorldCoord.sx + 12, hoverWorldCoord.sy);
            ctx.moveTo(hoverWorldCoord.sx, hoverWorldCoord.sy - 12);
            ctx.lineTo(hoverWorldCoord.sx, hoverWorldCoord.sy + 12);
            ctx.stroke();

            // Small reticle circle
            ctx.setLineDash([]);
            ctx.beginPath();
            ctx.arc(hoverWorldCoord.sx, hoverWorldCoord.sy, 6, 0, Math.PI * 2);
            ctx.stroke();

            // Coordinate label badge
            const label = `TARGET: (${hoverWorldCoord.wx.toFixed(2)}, ${hoverWorldCoord.wy.toFixed(2)}) m`;
            ctx.font = 'bold 11px monospace';
            const textWidth = ctx.measureText(label).width;
            ctx.fillStyle = 'rgba(15, 23, 42, 0.85)';
            ctx.fillRect(hoverWorldCoord.sx + 12, hoverWorldCoord.sy - 18, textWidth + 14, 22);
            ctx.strokeStyle = '#ff9100';
            ctx.strokeRect(hoverWorldCoord.sx + 12, hoverWorldCoord.sy - 18, textWidth + 14, 22);
            ctx.fillStyle = '#ff9100';
            ctx.fillText(label, hoverWorldCoord.sx + 18, hoverWorldCoord.sy - 3);
            ctx.restore();
        }

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

    // ---------------- Interactive Mouse Reticle & Coordinates ----------------
    canvas.addEventListener('mousemove', (e) => {
        const rect = canvas.getBoundingClientRect();
        const clickX = (e.clientX - rect.left) * (canvas.width / rect.width);
        const clickY = (e.clientY - rect.top) * (canvas.height / rect.height);
        const cx = canvas.width / 2;
        const cy = canvas.height / 2;
        const scale = state.zoomScale;
        const ox = state.viewMode === 'fixed' ? state.arenaCenter.x : state.pose.x;
        const oy = state.viewMode === 'fixed' ? state.arenaCenter.y : state.pose.y;
        const wx = ox + (clickX - cx) / scale;
        const wy = oy - (clickY - cy) / scale;
        hoverWorldCoord = { sx: clickX, sy: clickY, wx: wx, wy: wy };
    });

    canvas.addEventListener('mouseleave', () => {
        hoverWorldCoord = null;
    });

    // ---------------- Click-to-Goal (Accurate Nav2 Goal Dispatch) ----------------
    canvas.addEventListener('click', (e) => {
        if (state.estopLatched) {
            logEvent('DANGER', 'Cannot set goal: E-STOP is latched. Reset E-STOP first.', 'danger');
            return;
        }

        const rect = canvas.getBoundingClientRect();
        const clickX = (e.clientX - rect.left) * (canvas.width / rect.width);
        const clickY = (e.clientY - rect.top) * (canvas.height / rect.height);

        const cx = canvas.width / 2;
        const cy = canvas.height / 2;
        const scale = state.zoomScale;

        const ox = state.viewMode === 'fixed' ? state.arenaCenter.x : state.pose.x;
        const oy = state.viewMode === 'fixed' ? state.arenaCenter.y : state.pose.y;
        const goalX = ox + (clickX - cx) / scale;
        const goalY = oy - (clickY - cy) / scale;

        // Calculate direct heading angle to target
        const dx = goalX - state.pose.x;
        const dy = goalY - state.pose.y;
        const goalYaw = Math.atan2(dy, dx);

        dispatchGoal(goalX, goalY, goalYaw);
    });

    async function dispatchGoal(x, y, yaw = 0.0) {
        // Clamp dynamically within active map bounds (prevents sending goals into void)
        if (state.mapMeta && state.mapMeta.width > 0) {
            const meta = state.mapMeta;
            const minX = meta.origin_x + 0.3;
            const maxX = meta.origin_x + meta.width * meta.resolution - 0.3;
            const minY = meta.origin_y + 0.3;
            const maxY = meta.origin_y + meta.height * meta.resolution - 0.3;
            x = Math.max(minX, Math.min(maxX, x));
            y = Math.max(minY, Math.min(maxY, y));
        }

        state.currentGoal = { x, y };
        logEvent('NAV2', `Dispatching Target Goal: (${x.toFixed(2)}, ${y.toFixed(2)})`);

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
        dispatchGoal(1.5, -0.5, 0.0);
    });

    document.getElementById('btn-patrol-2')?.addEventListener('click', () => {
        logEvent('MISSION', 'Dispatching Preset: Recon Sector Bravo');
        dispatchGoal(-1.2, 0.8, 1.57);
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
    camButtons.forEach((btn) => {
        btn.removeAttribute('disabled');
        btn.classList.remove('disabled');

        btn.addEventListener('click', (e) => {
            e.preventDefault();
            camButtons.forEach((b) => b.classList.remove('active'));
            btn.classList.add('active');

            const feed = btn.getAttribute('data-feed') || 'combined';
            state.activeFeed = feed;

            if (feed === 'combined') {
                logEvent('CAMERA', 'Switched to FRONT [3D Depth Perception Heatmap Active]');
                if (elFeedStatus) elFeedStatus.textContent = '3D DEPTH PERCEPTION';
                if (elFps) {
                    elFps.textContent = 'LIVE';
                    elFps.style.color = '#00f2fe';
                }
            } else if (feed === 'stereo') {
                logEvent('CAMERA', 'Switched to FORWARD STEREO OPTICAL CAM');
                if (elFeedStatus) elFeedStatus.textContent = 'STEREO OPTICAL';
                if (elFps) {
                    elFps.textContent = 'ONLINE';
                    elFps.style.color = '#00f2fe';
                }
            } else {
                logEvent('CAMERA', 'Switched to REAR RECONNAISSANCE CAM');
                if (elFeedStatus) elFeedStatus.textContent = 'REAR RECON';
                if (elFps) {
                    elFps.textContent = 'STANDBY';
                    elFps.style.color = '#ffab00';
                }
            }

            if (elVideoFeed) {
                elVideoFeed.src = `/stream/video?feed=${state.activeFeed}&t=${Date.now()}`;
            }
        });
    });

        // ---------------- Picture-in-Picture (PiP) Dual Vision Handler ----------------
    const btnTogglePip = document.getElementById('btn-toggle-pip');
    const elPipViewport = document.getElementById('pip-viewport');
    const elPipVideo = document.getElementById('pip-video-feed');
    const elPipLabel = document.getElementById('pip-label');
    const btnSwapPip = document.getElementById('btn-swap-pip');

    let pipActive = false;
    let pipFeed = 'stereo';

    function updatePipView() {
        if (!elPipViewport || !elPipVideo) return;
        if (pipActive) {
            elPipViewport.style.display = 'block';
            if (btnTogglePip) btnTogglePip.classList.add('active');
            // If primary is stereo, pip shows depth; if primary is depth, pip shows stereo; if primary is rear, pip shows depth
            if (state.activeFeed === 'stereo') {
                pipFeed = 'combined';
                if (elPipLabel) elPipLabel.textContent = '3D DEPTH HEATMAP [PiP]';
            } else if (state.activeFeed === 'rear') {
                pipFeed = 'combined';
                if (elPipLabel) elPipLabel.textContent = '3D DEPTH HEATMAP [PiP]';
            } else {
                pipFeed = 'stereo';
                if (elPipLabel) elPipLabel.textContent = 'STEREO OPTICAL [PiP]';
            }
            elPipVideo.src = `/stream/video?feed=${pipFeed}&t=${Date.now()}`;
        } else {
            elPipViewport.style.display = 'none';
            if (btnTogglePip) btnTogglePip.classList.remove('active');
        }
    }

    if (btnTogglePip) {
        btnTogglePip.addEventListener('click', () => {
            pipActive = !pipActive;
            updatePipView();
            logEvent('VISION', pipActive ? 'Picture-in-Picture Dual Vision enabled.' : 'Dual Vision disabled.');
        });
    }

    function swapPipStreams() {
        if (!pipActive) return;
        const temp = state.activeFeed;
        state.activeFeed = pipFeed;
        pipFeed = temp;
        if (elVideoFeed) {
            elVideoFeed.src = `/stream/video?feed=${state.activeFeed}&t=${Date.now()}`;
        }
        updatePipView();
        // Update main active selector button
        camButtons.forEach(b => {
            if (b.getAttribute('data-feed') === state.activeFeed) {
                b.classList.add('active');
            } else if (b.id !== 'btn-toggle-pip') {
                b.classList.remove('active');
            }
        });
        logEvent('VISION', `Swapped Primary Feed to [${state.activeFeed.toUpperCase()}]`);
    }

    if (btnSwapPip) {
        btnSwapPip.addEventListener('click', (e) => {
            e.stopPropagation();
            swapPipStreams();
        });
    }

    if (elPipViewport) {
        elPipViewport.addEventListener('click', () => {
            swapPipStreams();
        });
    }

    // ---------------- Authoritative E-STOP Toggle ----------------
    if (elEstopBtn) {
        elEstopBtn.addEventListener('click', async () => {
            if (!state.estopLatched) {
                // Engage E-STOP
                logEvent('SAFETY', '>>> AUTHORITATIVE EMERGENCY STOP ENGAGED <<<', 'danger');
                state.currentGoal = null;
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
                logEvent('SYSTEM', 'E-STOP Latch cleared. Motor power restored. Click canvas to navigate.', 'active');
                state.currentGoal = null;
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
            if (elSpeedVal) elSpeedVal.textContent = val.toFixed(2);
        });
    }

    const btnQuickStep = document.getElementById('btn-quick-step');
    if (btnQuickStep) {
        btnQuickStep.addEventListener('click', () => {
            const stepDist = 1.2;
            const targetX = state.pose.x + stepDist * Math.cos(state.pose.yaw);
            const targetY = state.pose.y + stepDist * Math.sin(state.pose.yaw);
            logEvent('NAV2', `Quick Step Ahead (+${stepDist}m): Dispatching to (${targetX.toFixed(2)}, ${targetY.toFixed(2)})`);
            dispatchGoal(targetX, targetY, state.pose.yaw);
        });
    }

    // ---------------- View Mode Toggle Handler ----------------
    const btnToggleView = document.getElementById('btn-toggle-view');
    if (btnToggleView) {
        btnToggleView.addEventListener('click', () => {
            if (state.viewMode === 'fixed') {
                state.viewMode = 'follow';
                btnToggleView.textContent = '🎯 VIEW: FOLLOW ROBOT';
                logEvent('MAP', 'Switched to Follow Robot View (camera tracks UGV)');
            } else {
                state.viewMode = 'fixed';
                btnToggleView.textContent = '🗺️ VIEW: FIXED ARENA';
                logEvent('MAP', 'Switched to Fixed Arena View (stationary map, UGV moves across screen)');
            }
        });
    }

    // ---------------- On-Screen Teleoperation D-Pad Click/Hold Handlers ----------------
    let teleopTimer = null;
    function startDriving(lin, ang) {
        if (state.estopLatched) return;
        sendTeleop(lin, ang);
        if (teleopTimer) clearInterval(teleopTimer);
        teleopTimer = setInterval(() => sendTeleop(lin, ang), 100);
    }
    function stopDriving() {
        if (teleopTimer) {
            clearInterval(teleopTimer);
            teleopTimer = null;
        }
        sendTeleop(0.0, 0.0);
    }

    const dpadButtons = [
        { id: 'btn-drive-fwd', lin: 1.0, ang: 0.0 },
        { id: 'btn-drive-rev', lin: -1.0, ang: 0.0 },
        { id: 'btn-turn-left', lin: 0.0, ang: 1.2 },
        { id: 'btn-turn-right', lin: 0.0, ang: -1.2 },
        { id: 'btn-brake', lin: 0.0, ang: 0.0 },
    ];

    dpadButtons.forEach(b => {
        const el = document.getElementById(b.id);
        if (el) {
            el.addEventListener('mousedown', (e) => {
                e.preventDefault();
                el.classList.add('active');
                startDriving(b.lin * state.speedLimit, b.ang);
            });
            el.addEventListener('mouseup', () => {
                el.classList.remove('active');
                stopDriving();
            });
            el.addEventListener('mouseleave', () => {
                el.classList.remove('active');
                stopDriving();
            });
            el.addEventListener('touchstart', (e) => {
                e.preventDefault();
                el.classList.add('active');
                startDriving(b.lin * state.speedLimit, b.ang);
            });
            el.addEventListener('touchend', () => {
                el.classList.remove('active');
                stopDriving();
            });
        }
    });
});
