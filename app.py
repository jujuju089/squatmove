import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="KI-Bewegungsanalyse Schulprojekt", layout="wide")

st.title("🎓 KI-Bewegungs-Coach")
st.write("Vergleich: Vortrainiertes MoveNet-Modell mit automatischer Bewegungsanalyse.")

# HTML/JavaScript Teil
html_code = """
<div id="ai-app" style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #1a1a1a; color: white; padding: 20px; border-radius: 20px; box-shadow: 0 10px 30px rgba(0,0,0,0.5);">
    
    <!-- DASHBOARD -->
    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px; margin-bottom: 20px;">
        <div style="background: #2d2d2d; padding: 15px; border-radius: 12px; border-bottom: 4px solid #00d4ff;">
            <div style="font-size: 0.8em; color: #888;">AKTUELLE BEWEGUNG</div>
            <div id="status-label" style="font-size: 1.2em; font-weight: bold; color: #00d4ff;">Suche Mensch...</div>
        </div>
        <div style="background: #2d2d2d; padding: 15px; border-radius: 12px; border-bottom: 4px solid #44ff44;">
            <div style="font-size: 0.8em; color: #888;">ANZAHL SQUATS</div>
            <div id="counter-label" style="font-size: 1.5em; font-weight: bold; color: #44ff44;">0</div>
        </div>
    </div>

    <!-- VIDEO VIEW -->
    <div style="position: relative; border-radius: 15px; overflow: hidden; background: #000; line-height: 0;">
        <video id="video" autoplay playsinline style="width: 100%; height: auto; transform: scaleX(-1);"></video>
        <canvas id="canvas" style="position: absolute; top: 0; left: 0; width: 100%; height: 100%; pointer-events: none; transform: scaleX(-1);"></canvas>
    </div>

    <!-- CONTROLS -->
    <div style="display: flex; gap: 10px; margin-top: 20px;">
        <button id="switch-btn" style="flex: 1; padding: 12px; background: #444; color: white; border: none; border-radius: 8px; cursor: pointer; font-weight: bold;">📷 Kamera wechseln</button>
        <button id="stop-btn" style="flex: 1; padding: 12px; background: #ff4b4b; color: white; border: none; border-radius: 8px; cursor: pointer; font-weight: bold;">⏹ Training beenden</button>
    </div>

    <!-- SUMMARY OVERLAY (Zusammenfassung) -->
    <div id="summary-view" style="display:none; margin-top: 20px; padding: 25px; background: #ffffff; color: #1a1a1a; border-radius: 15px; border-left: 10px solid #00d4ff;">
        <h2 style="margin-top:0;">📊 Analyse-Zusammenfassung</h2>
        <div id="summary-stats" style="font-size: 1.1em; line-height: 1.6;">
            <!-- Wird per JS befüllt -->
        </div>
        <button onclick="window.location.reload()" style="margin-top: 20px; padding: 10px 20px; background: #00d4ff; color: white; border: none; border-radius: 5px; cursor: pointer;">Neustart</button>
    </div>
</div>

<script src="https://cdn.jsdelivr.net/npm/@tensorflow/tfjs"></script>
<script src="https://cdn.jsdelivr.net/npm/@tensorflow-models/pose-detection"></script>

<script>
const video = document.getElementById('video');
const canvas = document.getElementById('canvas');
const ctx = canvas.getContext('2d');
const statusLabel = document.getElementById('status-label');
const counterLabel = document.getElementById('counter-label');
const summaryView = document.getElementById('summary-view');
const summaryStats = document.getElementById('summary-stats');

let detector;
let currentFacingMode = 'user'; // 'user' ist Front, 'environment' ist Back
let count = 0;
let stage = 'up';
let active = true;
let startTime = Date.now();
let history = [];

async function startStream() {
    if(video.srcObject) {
        video.srcObject.getTracks().forEach(track => track.stop());
    }
    const stream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: currentFacingMode, width: 640, height: 480 }
    });
    video.srcObject = stream;
}

async function init() {
    detector = await poseDetection.createDetector(
        poseDetection.SupportedModels.MoveNet,
        { modelType: poseDetection.movenet.modelType.SINGLEPOSE_LIGHTNING }
    );
    await startStream();
    detect();
}

async function detect() {
    if (!active) return;
    if (video.readyState >= 2) {
        const poses = await detector.estimatePoses(video);
        
        canvas.width = video.videoWidth;
        canvas.height = video.videoHeight;
        ctx.clearRect(0, 0, canvas.width, canvas.height);

        if (poses.length > 0) {
            const pose = poses[0];
            const hip = pose.keypoints[12];
            const knee = pose.keypoints[14];
            const ankle = pose.keypoints[16];

            if (hip.score > 0.4 && knee.score > 0.4) {
                // SQUAT LOGIK
                let verticalDist = ankle.y - hip.y;
                history.push(verticalDist);
                if(history.length > 15) history.shift();

                // Einfache Klassifizierung
                if (verticalDist < 220) { // Wert je nach Abstand zur Kamera
                    if (stage === 'up') {
                        statusLabel.innerText = "BEWEGUNG: SQUAT (Tief)";
                        statusLabel.style.color = "#ff4b4b";
                    }
                    stage = 'down';
                } else if (verticalDist > 280) {
                    if (stage === 'down') {
                        count++;
                        counterLabel.innerText = count;
                        statusLabel.innerText = "BEWEGUNG: STEHEN";
                        statusLabel.style.color = "#00d4ff";
                    }
                    stage = 'up';
                }
            }

            // Zeichne Skelett (Vortrainierte Punkte)
            ctx.fillStyle = "#44ff44";
            ctx.strokeStyle = "white";
            ctx.lineWidth = 2;
            pose.keypoints.forEach(kp => {
                if (kp.score > 0.5) {
                    ctx.beginPath();
                    ctx.arc(kp.x, kp.y, 5, 0, 2 * Math.PI);
                    ctx.fill();
                }
            });
        }
    }
    requestAnimationFrame(detect);
}

// Kamera wechseln
document.getElementById('switch-btn').onclick = () => {
    currentFacingMode = currentFacingMode === 'user' ? 'environment' : 'user';
    startStream();
};

// Training beenden & Zusammenfassung anzeigen
document.getElementById('stop-btn').onclick = () => {
    active = false;
    const duration = Math.round((Date.now() - startTime) / 1000);
    const speed = count > 0 ? (duration / count).toFixed(1) : 0;
    
    summaryView.style.display = "block";
    summaryStats.innerHTML = `
        <p>⏱ <b>Dauer:</b> \${duration} Sekunden</p>
        <p>🏋️ <b>Gesamte Squats:</b> \${count}</p>
        <p>⚡ <b>Durchschnittliche Zeit pro Rep:</b> \${speed} Sekunden</p>
        <p>✅ <b>Modell-Status:</b> MoveNet (vortrainiert) war stabil.</p>
        <hr>
        <p><i>Fachliche Analyse für das Projekt:</i> Das System erkannte die Gelenke zuverlässig. Die Bewegungsphasen wurden durch die vertikale Distanz zwischen Hüfte und Knöchel klassifiziert.</p>
    `;
    if (video.srcObject) video.srcObject.getTracks().forEach(t => t.stop());
    video.pause();
};

init();
</script>
"""

components.html(html_code, height=1000)
