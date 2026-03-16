/**
 * Complete phone sensor capture for Drishti v4.2.
 * Sends 1Hz aggregated summary to backend via WebSocket.
 *
 * Sensors used:
 * - Accelerometer (DeviceMotion): walking, steps, stairs, falls
 * - Gyroscope (DeviceMotion): rotation rate, head/body turns
 * - Compass (DeviceOrientation): heading 0-360, direction changes
 * - GPS (Geolocation): lat/lon, speed, heading, altitude
 * - Camera frame diff: visual change detection
 *
 * CRITICAL iOS RULE: DeviceMotionEvent.requestPermission() must be
 * called in app.js click handler BEFORE this class is constructed.
 * This class assumes permissions are ALREADY granted.
 */
class SensorStream {
    constructor(ws) {
        this.ws = ws;

        // --- Raw sensor state (updated at device frequency ~60Hz) ---
        this.accel = { x: 0, y: 0, z: 9.81 };
        this.accelPure = { x: 0, y: 0, z: 0 };
        this.rotationRate = { alpha: 0, beta: 0, gamma: 0 };
        this.orientation = { alpha: 0, beta: 0, gamma: 0 };

        // --- Derived per-second state ---
        this.heading = 0;
        this.headingDelta = 0;
        this.lastHeading = null;
        this.peakRotation = 0;

        // --- Step detection ---
        this.stepCount = 0;
        this.lastStepTime = 0;

        // --- Acceleration history (for variance computation) ---
        this.accelYHistory = [];

        // --- GPS state ---
        this.gps = {
            lat: null, lon: null, accuracy: null,
            speed: null, heading: null, altitude: null
        };

        // --- Frame differencing ---
        this.prevFrameData = null;

        // --- Status ---
        this.sensorsActive = false;

        this._initSensors();
        this._sendInterval = setInterval(() => this._sendSummary(), 1000);
    }

    _initSensors() {
        // ACCELEROMETER + GYROSCOPE (DeviceMotion)
        window.addEventListener('devicemotion', (e) => {
            this.sensorsActive = true;

            const ag = e.accelerationIncludingGravity;
            if (ag) {
                this.accel = {
                    x: ag.x || 0,
                    y: ag.y || 0,
                    z: ag.z || 9.81
                };
                this.accelYHistory.push(ag.y || 0);
                if (this.accelYHistory.length > 60) {
                    this.accelYHistory.shift();
                }
            }

            const a = e.acceleration;
            if (a) {
                this.accelPure = {
                    x: a.x || 0,
                    y: a.y || 0,
                    z: a.z || 0
                };

                // Step detection: peak in y-axis with 250ms debounce
                if (Math.abs(a.y) > 3.5) {
                    const now = Date.now();
                    if (now - this.lastStepTime > 250) {
                        this.stepCount++;
                        this.lastStepTime = now;
                    }
                }
            }

            const r = e.rotationRate;
            if (r) {
                this.rotationRate = {
                    alpha: r.alpha || 0,
                    beta: r.beta || 0,
                    gamma: r.gamma || 0
                };
                const totalRotation = Math.abs(r.alpha || 0) + Math.abs(r.beta || 0);
                this.peakRotation = Math.max(this.peakRotation, totalRotation);
            }
        });

        // COMPASS / ORIENTATION (DeviceOrientation)
        window.addEventListener('deviceorientation', (e) => {
            this.sensorsActive = true;

            this.orientation = {
                alpha: e.alpha || 0,
                beta: e.beta || 0,
                gamma: e.gamma || 0
            };

            const heading = e.alpha || 0;
            if (this.lastHeading !== null) {
                let delta = heading - this.lastHeading;
                if (delta > 180) delta -= 360;
                if (delta < -180) delta += 360;
                this.headingDelta = delta;
            }
            this.lastHeading = heading;
            this.heading = heading;
        });

        // GPS (Geolocation API)
        if (navigator.geolocation) {
            navigator.geolocation.watchPosition(
                (pos) => {
                    this.gps = {
                        lat: pos.coords.latitude,
                        lon: pos.coords.longitude,
                        accuracy: pos.coords.accuracy,
                        speed: pos.coords.speed,
                        heading: pos.coords.heading,
                        altitude: pos.coords.altitude
                    };
                },
                (err) => {
                    console.warn('GPS error:', err.message);
                },
                { enableHighAccuracy: true, maximumAge: 2000 }
            );
        }

        console.log('SensorStream: all listeners registered');
    }

    _computeAccelVariance() {
        if (this.accelYHistory.length < 10) return 0;
        const recent = this.accelYHistory.slice(-20);
        const mean = recent.reduce((s, v) => s + v, 0) / recent.length;
        return recent.reduce((s, v) => s + Math.pow(v - mean, 2), 0) / recent.length;
    }

    _sendSummary() {
        if (!this.ws || this.ws.readyState !== WebSocket.OPEN) return;

        const msg = {
            type: "sensors",
            speed: this.gps.speed || 0,
            heading: this.heading,
            heading_delta: Math.abs(this.headingDelta),
            rotation_rate: this.peakRotation,
            accel_x: this.accelPure.x,
            accel_y: this.accelPure.y,
            accel_z: this.accelPure.z,
            accel_gravity_z: this.accel.z,
            accel_variance: this._computeAccelVariance(),
            step_count: this.stepCount,
            beta: this.orientation.beta,
            gamma: this.orientation.gamma,
            gps_lat: this.gps.lat,
            gps_lon: this.gps.lon,
            gps_accuracy: this.gps.accuracy,
            gps_speed: this.gps.speed,
            gps_heading: this.gps.heading,
            gps_altitude: this.gps.altitude,
            sensors_active: this.sensorsActive,
        };

        this.ws.send(JSON.stringify(msg));

        // Reset per-second peaks
        this.peakRotation = 0;
        this.headingDelta = 0;
    }

    computeFrameChange(canvas) {
        const small = document.createElement('canvas');
        small.width = 64;
        small.height = 48;
        const sCtx = small.getContext('2d');
        sCtx.drawImage(canvas, 0, 0, 64, 48);

        const currentData = sCtx.getImageData(0, 0, 64, 48).data;
        let changeScore = 0;

        if (this.prevFrameData) {
            let diffPixels = 0;
            const totalPixels = 64 * 48;
            for (let i = 0; i < currentData.length; i += 4) {
                const dr = Math.abs(currentData[i] - this.prevFrameData[i]);
                const dg = Math.abs(currentData[i + 1] - this.prevFrameData[i + 1]);
                const db = Math.abs(currentData[i + 2] - this.prevFrameData[i + 2]);
                if ((dr + dg + db) / 3 > 30) diffPixels++;
            }
            changeScore = diffPixels / totalPixels;
        }

        this.prevFrameData = new Uint8Array(currentData);
        return changeScore;
    }

    destroy() {
        if (this._sendInterval) clearInterval(this._sendInterval);
    }
}
