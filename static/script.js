let dataPollingTimer = null;
let controlRequestInProgress = false;
const chartSeries = [
    { key: 'temperature_c', label: 'Temperature', color: '#ff9f43', aliases: ['temperature_c', 'temp', 'Temp'] },
    { key: 'humidity_pct', label: 'Humidity', color: '#38bdf8', aliases: ['humidity_pct', 'humid', 'Humid'] },
    { key: 'gas_level_ppm', label: 'Gas', color: '#ef5da8', aliases: ['gas_level_ppm', 'gas'] },
    { key: 'dust', label: 'Dust', color: '#a3e635', aliases: ['dust'] }
];


function updateTerminalLogs(logs) {
    const terminalOutput = document.getElementById('terminal-output');
    if (!terminalOutput || !Array.isArray(logs)) return;

    terminalOutput.textContent = logs.join('\n');
    terminalOutput.scrollTop = terminalOutput.scrollHeight;
}


function updateAnomalyStatus(data) {
    const anomalyStatus = document.getElementById('anomaly-status');
    if (!anomalyStatus) return;

    const anomalies = Array.isArray(data.anomalies)
        ? data.anomalies.filter((anomaly) => typeof anomaly === 'string' && anomaly.trim())
        : [];

    if (data.running === false) {
        anomalyStatus.textContent = 'System stopped.';
        anomalyStatus.style.color = '#8faebf';
    } else if (data.hazard_status === 'HAZARD') {
        anomalyStatus.textContent = anomalies.length
            ? anomalies.join(' | ')
            : 'Hazard detected. No sensor details were provided.';
        anomalyStatus.style.color = '#ff3333';
    } else if (data.hazard_status === 'SAFE') {
        anomalyStatus.textContent = 'No anomalies detected.';
        anomalyStatus.style.color = '#00ffcc';
    } else {
        anomalyStatus.textContent = 'Collecting readings...';
        anomalyStatus.style.color = '#ffaa00';
    }
}


function updatePersonDetection(data) {
    const personOutput = document.getElementById('person-detected');
    if (!personOutput) return;

    if (data.running === false) {
        personOutput.textContent = 'System stopped.';
        personOutput.style.color = '#8faebf';
        return;
    }

    const personDetected = Number(data.persons) > 0 || Number(data.miners) > 0;
    if (personDetected) {
        personOutput.textContent = '[!] PERSON DETECTED';
        personOutput.style.color = '#00ff00';

        if ('speechSynthesis' in window && !window.speechSynthesis.speaking) {
            const speech = new SpeechSynthesisUtterance('Person detected');
            speech.rate = 1.1;
            speech.pitch = 1.0;
            window.speechSynthesis.speak(speech);
        }
    } else {
        personOutput.textContent = '[STANDBY] No targets detected in frame.';
        personOutput.style.color = '#8faebf';
    }
}


function updateCurrentData(data) {
    const output = document.getElementById('current-data-output');
    if (!output) return;

    if (data.running === false) {
        output.textContent = 'System stopped. \n Press Start to load the latest MongoDB record.';
        return;
    }

    if (data.error) {
        output.textContent = data.error;
        return;
    }

    const imu = data.imu || {};
    const lidar = Array.isArray(data.lidar_scan) ? data.lidar_scan : [];
    const lidarSummary = lidar.length
        ? lidar.map((scan) => `${scan.angle_deg}\u00b0: ${scan.dist_mm} mm`).join(' | ')
        : null;
    const readings = [
        ['Record', data._id],
        ['Timestamp', data.timestamp],
        ['Temperature', data.temperature_c ?? data.temp ?? data.Temp],
        ['Humidity', data.humidity_pct ?? data.humid ?? data.Humid],
        ['Gas level', data.gas_level_ppm ?? data.gas],
        ['Dust', data.dust],
        ['Motion detected', data.motion_detected],
        ['IMU acceleration X', imu.accel_x],
        ['IMU acceleration Y', imu.accel_y],
        ['IMU acceleration Z', imu.accel_z],
        ['LiDAR scan', lidarSummary]
    ].filter(([, value]) => value !== undefined && value !== null);

    output.textContent = readings
        .map(([label, value]) => `${label}: ${value}`)
        .join('\n');
}


function sensorValue(reading, aliases) {
    const value = aliases.map((key) => reading[key]).find((item) => item !== undefined && item !== null);
    const numeric = Number(value);
    return Number.isFinite(numeric) ? numeric : null;
}


function updateTelemetryChart(history, running = true) {
    const chart = document.getElementById('telemetry-chart');
    const emptyMessage = document.getElementById('telemetry-chart-empty');
    if (!chart || !emptyMessage) return;

    const readings = Array.isArray(history) ? history : [];
    const points = chartSeries.map((series) => ({
        ...series,
        values: readings.map((reading) => sensorValue(reading, series.aliases))
    }));
    const hasData = points.some((series) => series.values.some((value) => value !== null));

    if (!running || !hasData) {
        chart.replaceChildren();
        chart.hidden = true;
        emptyMessage.hidden = false;
        emptyMessage.textContent = running ? 'Waiting for sensor readings…' : 'Start the system to view live trends.';
        return;
    }

    chart.hidden = false;
    emptyMessage.hidden = true;
    const width = 360, height = 180, padding = 24;
    const x = (index) => padding + (index * (width - padding * 2)) / Math.max(readings.length - 1, 1);
    const namespace = 'http://www.w3.org/2000/svg';
    chart.replaceChildren();

    [0, 0.25, 0.5, 0.75, 1].forEach((position) => {
        const line = document.createElementNS(namespace, 'line');
        const lineY = padding + position * (height - padding * 2);
        line.setAttribute('x1', padding); line.setAttribute('x2', width - padding);
        line.setAttribute('y1', lineY); line.setAttribute('y2', lineY);
        line.setAttribute('class', 'chart-grid-line');
        chart.append(line);
    });

    const verticalGridLines = Math.min(Math.max(readings.length - 1, 1), 6);
    for (let index = 0; index <= verticalGridLines; index += 1) {
        const line = document.createElementNS(namespace, 'line');
        const lineX = padding + (index * (width - padding * 2)) / verticalGridLines;
        line.setAttribute('x1', lineX); line.setAttribute('x2', lineX);
        line.setAttribute('y1', padding); line.setAttribute('y2', height - padding);
        line.setAttribute('class', 'chart-grid-line');
        chart.append(line);
    }

    points.forEach((series) => {
        // Temperature, humidity, gas and dust use different units and ranges.
        // Scale each independently so every sensor has a visible colored line.
        const seriesValues = series.values.filter((value) => value !== null);
        if (!seriesValues.length) return;
        let min = Math.min(...seriesValues);
        let max = Math.max(...seriesValues);
        if (min === max) { min -= 1; max += 1; }
        const y = (value) => height - padding
            - ((value - min) * (height - padding * 2)) / (max - min);
        const validPoints = series.values
            .map((value, index) => value === null ? null : { x: x(index), y: y(value) })
            .filter(Boolean);
        if (!validPoints.length) return;

        let pathData = `M ${validPoints[0].x} ${validPoints[0].y}`;
        for (let index = 1; index < validPoints.length; index += 1) {
            const previous = validPoints[index - 1];
            const point = validPoints[index];
            const midpointX = (previous.x + point.x) / 2;
            // Quadratic curves retain the actual reading points while removing sharp corners.
            pathData += ` Q ${previous.x} ${previous.y} ${midpointX} ${(previous.y + point.y) / 2}`;
        }
        if (validPoints.length > 1) {
            const previous = validPoints[validPoints.length - 2];
            const point = validPoints[validPoints.length - 1];
            pathData += ` Q ${previous.x} ${previous.y} ${point.x} ${point.y}`;
        }
        if (!pathData) return;
        const path = document.createElementNS(namespace, 'path');
        path.setAttribute('d', pathData);
        path.setAttribute('stroke', series.color);
        path.setAttribute('class', 'chart-line');
        path.setAttribute('aria-label', series.label);
        chart.append(path);
    });
}


function setControlState(running, busy = false) {
    const startButton = document.getElementById('start-butt');
    const stopButton = document.getElementById('stop-butt');

    if (startButton) startButton.disabled = busy || running;
    if (stopButton) stopButton.disabled = busy || !running;
}


function setCameraStream(active) {
    const cameraStream = document.getElementById('camera-stream');
    if (!cameraStream) return;

    if (active) {
        // A unique query value forces the browser to start a fresh MJPEG stream.
        cameraStream.src = `/video-feed?started=${Date.now()}`;
    } else {
        cameraStream.removeAttribute('src');
    }
}


async function fetchDatabaseData() {
    try {
        const response = await fetch('/api/data');
        const data = await response.json();
        if (!data || typeof data !== 'object') return;

        updateTerminalLogs(data.logs);
        updateAnomalyStatus(data);
        updatePersonDetection(data);
        updateCurrentData(data);
        updateTelemetryChart(data.history, data.running);

        if (data.running === false) {
            stopDataPolling();
            setCameraStream(false);
            setControlState(false);
        }

        if (!response.ok && !data.logs) {
            console.warn(data.error || 'Unable to fetch MongoDB data.');
        }
    } catch (error) {
        console.error('Error fetching dashboard data:', error);
    }
}


function startDataPolling() {
    if (dataPollingTimer !== null) return;

    fetchDatabaseData();
    dataPollingTimer = window.setInterval(fetchDatabaseData, 1000);
}


function stopDataPolling() {
    if (dataPollingTimer === null) return;

    window.clearInterval(dataPollingTimer);
    dataPollingTimer = null;
}


async function startSystem() {
    if (controlRequestInProgress) return;

    controlRequestInProgress = true;
    setControlState(false, true);

    try {
        const response = await fetch('/api/start', { method: 'POST' });
        const data = await response.json();
        updateTerminalLogs(data.logs);

        if (!response.ok || !data.running) {
            throw new Error(data.message || 'The system could not be started.');
        }

        setCameraStream(true);
        setControlState(true);
        startDataPolling();
    } catch (error) {
        console.error('Error starting system:', error);
        updateAnomalyStatus({ hazard_status: 'WARMING UP' });
        setControlState(false);
    } finally {
        controlRequestInProgress = false;
    }
}


async function stopSystem() {
    if (controlRequestInProgress) return;

    controlRequestInProgress = true;
    setControlState(true, true);

    try {
        const response = await fetch('/api/stop', { method: 'POST' });
        const data = await response.json();
        updateTerminalLogs(data.logs);

        if (!response.ok || data.running) {
            throw new Error(data.message || 'The system could not be stopped.');
        }

        stopDataPolling();
        setCameraStream(false);
        updateAnomalyStatus(data);
        updatePersonDetection(data);
        updateCurrentData(data);
        updateTelemetryChart([], false);
        setControlState(false);
    } catch (error) {
        console.error('Error stopping system:', error);
        // Keep the controls in the running state because the server may still
        // own the camera and be processing data.
        setControlState(true);
    } finally {
        controlRequestInProgress = false;
    }
}


document.getElementById('start-butt')?.addEventListener('click', startSystem);
document.getElementById('stop-butt')?.addEventListener('click', stopSystem);
setControlState(false);
