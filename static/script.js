let dataPollingTimer = null;
let controlRequestInProgress = false;


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

    const readings = [
        ['Record', data._id],
        ['Timestamp', data.timestamp],
        ['Temperature', data.temp ?? data.Temp],
        ['Humidity', data.humid ?? data.Humid],
        ['Gas', data.gas],
        ['Dust', data.dust]
    ].filter(([, value]) => value !== undefined && value !== null);

    output.textContent = readings
        .map(([label, value]) => `${label}: ${value}`)
        .join('\n');
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
