async function fetchDatabaseData() {
    try {
        const response = await fetch('/api/data');
        const data = await response.json();
        
        if (!data || data.error) return;

        // Safely update environmental telemetry if data is present
        if (data.temp !== undefined || data.Temp !== undefined) {
            document.getElementById('temp-val').innerText = data.temp !== undefined ? data.temp : data.Temp;
        }
        if (data.humid !== undefined || data.Humid !== undefined) {
            document.getElementById('humi-val').innerText = data.humid !== undefined ? data.humid : data.Humid;
        }
        if (data.gas !== undefined) {
            document.getElementById('gas-val').innerText = data.gas;
        }
        if (data.dust !== undefined) {
            document.getElementById('dust-val').innerText = data.dust;
        }
        
        // Safely update AI Detections retrieved from the camera inference
        if (data.persons !== undefined) {
            document.getElementById('person-count').innerText = data.persons;
        }
        if (data.miners !== undefined) {
            document.getElementById('miner-count').innerText = data.miners;
        }
        
    } catch (error) {
        console.error("Error fetching data:", error);
    }
}

// Poll the API every 1 second
setInterval(fetchDatabaseData, 1000); 
fetchDatabaseData();