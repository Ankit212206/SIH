async function fetchDatabaseData() {
    try {
        const response = await fetch('/api/data');
        const data = await response.json();
        
        if (!data || data.error) return;

        // Environmental Telemetry
        if (data.temp !== undefined || data.Temp !== undefined) {
            document.getElementById('temp-val').innerText = data.temp !== undefined ? data.temp : data.Temp;
        }
        if (data.Humid !== undefined || data.humid !== undefined) {
            document.getElementById('humi-val').innerText = data.humid !== undefined ? data.humid : data.humid;
        }
        if (data.gas !== undefined) {
            document.getElementById('gas-val').innerText = data.gas;
        }
        if (data.dust !== undefined) {
            document.getElementById('dust-val').innerText = data.dust;
        }
        
        // NEW: AI Environmental Diagnostics (Bottom Left)
        const hazardStatus = document.getElementById('hazard-status');
        const hazardAnomalies = document.getElementById('hazard-anomalies');
        
        if (data.hazard_status === "HAZARD") {
            hazardStatus.innerText = "🚨 [HAZARD DETECTED]";
            hazardStatus.style.color = "#ff3333";
            hazardStatus.style.textShadow = "0 0 8px #ff3333";
            
            if (data.anomalies && data.anomalies.length > 0) {
                // Creates a bulleted list of all detected anomalies
                hazardAnomalies.innerHTML = "- " + data.anomalies.join("<br>- ");
                hazardAnomalies.style.display = "block";
            }
        } else if (data.hazard_status === "SAFE") {
            hazardStatus.innerText = "✅ [SYSTEM SAFE]";
            hazardStatus.style.color = "#00ff00";
            hazardStatus.style.textShadow = "0 0 5px #00ff00";
            hazardAnomalies.style.display = "none";
        } else {
            hazardStatus.innerText = "⏳ [WARMING UP]";
            hazardStatus.style.color = "#ffaa00";
            hazardStatus.style.textShadow = "none";
            hazardAnomalies.style.display = "none";
        }

        // Vision Tracking Logic (Bottom Right)
        let visionText = "";
        
        if (data.persons > 0 || data.miners > 0) {
            visionText += "<div style='color: #00ff00; margin-bottom: 5px; text-shadow: 0 0 5px #00ff00;'>[!] PERSON DETECTED</div>";
        }
        
        const visionOutput = document.getElementById('vision-output');
        if (visionText === "") {
            visionOutput.innerHTML = "<span style='color: #8faebf;'>[STANDBY] No targets detected in frame.</span>";
        } else {
            visionOutput.innerHTML = visionText;
        }
        
    } catch (error) {
        console.error("Error fetching data:", error);
    }
}

setInterval(fetchDatabaseData, 1000); 
fetchDatabaseData();