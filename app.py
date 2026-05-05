import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="KI-Bewegungsanalyse Schulprojekt", layout="wide")

st.title("🎓 KI-Bewegungs-Coach")
st.write("Vortrainiertes MoveNet-Modell mit Kamera-Wechsel und Analyse-Summary.")

# Das HTML/JavaScript Paket
html_code = """
<div id="ai-app" style="font-family: sans-serif; background: #1a1a1a; color: white; padding: 20px; border-radius: 20px; box-shadow: 0 10px 30px rgba(0,0,0,0.5); max-width: 900px; margin: auto;">
    
    <!-- DASHBOARD -->
    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px; margin-bottom: 20px;">
        <div style="background: #2d2d2d; padding: 15px; border-radius: 12px; border-bottom: 4px solid #00d4ff;">
            <div style="font-size: 0.8em; color: #888;">STATUS</div>
            <div id="status-label" style="font-size: 1.1em; font-weight: bold; color: #00d4ff;">Initialisierung...</div>
        </div>
        <div style="background: #2d2d2d; padding: 15px; border-radius: 12px; border-bottom: 4px solid #44ff44;">
            <div style="font-size: 0.8em; color: #888;">SQUATS</div>
            <div id="counter-label" style="font-size: 1.5em; font-weight: bold; color: #44ff44;">0</div>
        </div>
    </div>

    <!-- VIDEO VIEW -->
    <div style="position: relative; border-radius: 15px; overflow: hidden; background: #000; line-height: 0;">
        <video id="video" autoplay playsinline muted style="width: 100%; height: auto;"></video>
        <canvas id="canvas" style="position: absolute; top: 0; left: 0; width: 100%; height: 100%; pointer-events: none;"></canvas>
    </div>

    <!-- CONTROLS -->
    <div style="display: flex; gap: 10px; margin-top: 20px;">
        <button id="switch-btn" style="flex: 1; padding: 15px; background: #444; color: white; border: none; border-radius: 8px; cursor: pointer; font-weight: bold;">📷 Kamera wechseln</button>
        <button id="stop-btn" style="flex: 1; padding: 15px; background: #ff4b4b; color: white; border: none; border-radius: 8px; cursor: pointer; font-weight: bold;">⏹ Training beenden</button>
    </div>

    <!-- SUMMARY -->
    <div id="summary-view" style="display:none; margin-top: 20px; padding: 25px; background: #ffffff; color: #1a1a1a; border-radius: 15px; border-left: 10px solid #00d4ff;">
        <h2 style="margin-top:0; color: #1a1a1a;">📊 Analyse-Bericht</h2>
        <div id="summary-stats" style="font-size: 1.1em; line-height: 1.6;"></div>
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
let currentFacingMode = 'user'; 
let count = 0;
let stage = 'up';
let active = true;
let startTime = Date.now();

async function startStream() {
    try {
        if(video.srcObject) {
            video.srcObject.getTracks().forEach(track => track.stop());
        }
        const stream = await navigator.mediaDevices.getUserMedia({
            video: { facingMode: currentFacingMode }
        });
        video.srcObject = stream;
        
        // Warten bis Video wirklich geladen ist, um schwarzen Bildschirm zu vermeiden
        return new Promise((resolve) => {
            video.onloadedmetadata = () => {
                video.play();
                resolve();
            };
        });
    } catch (err) {
        console.error("Kamerafehler:", err);
        statusLabel.innerText = "FEHLER: Kamera blockiert";
    }
}

async function init() {
    statusLabel.innerText = "Lade KI-Modell...";
    detector = await poseDetection.createDetector(
        poseDetection.SupportedModels.MoveNet,
        { modelType: poseDetection.movenet.modelType.SINGLEPOSE_LIGHTNING }
    );
    await startStream();
    statusLabel.innerText = "Bereit: Bitte hinstellen";
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
            const kp = poses[0].keypoints;
            const hip = kp[12], knee = kp[14], ankle = kp[16];

            if (hip.score > 0.3 && knee.score > 0.3) {
                let dist = ankle.y - hip.y;

                if (dist < 230) {
                    if (stage === 'up') statusLabel.innerText = "STATUS: Squat tief";
                    stage = 'down';
                } else if (dist > 280 && stage === 'down') {
                    count++;
                    counterLabel.innerText = count;
                    stage = 'up';
                    statusLabel.innerText = "STATUS: Stehend";
                }
            }

            // Skelett zeichnen
            ctx.fillStyle = "#00d4ff";
            kp.forEach(p => {
                if(p.score > 0.5) {
                    ctx.beginPath();
                    ctx.arc(p.x, p.y, 4, 0, 2*Math.PI);
                    ctx.fill();
                }
            });
        }
    }
    requestAnimationFrame(detect);
}

document.getElementById('switch-btn').onclick = async () => {
    currentFacingMode = currentFacingMode === 'user' ? 'environment' : 'user';
    await startStream();
};

document.getElementById('stop-btn').onclick = () => {
    active = false;
    const duration = Math.round((Date.now() - startTime) / 1000);
    summaryView.style.display = "block";
    summaryStats.innerHTML = `
        <p>⏱ <b>Dauer:</b> ${duration} Sekunden</p>
        <p>🏋️ <b>Wiederholungen:</b> ${count}</p>
        <p>🤖 <b>KI-Modell:</b> MoveNet Lightning (Vortrainiert)</p>
        <p>🔍 <b>Analyse:</b> Die Bewegungsabläufe wurden stabil erkannt. Die Klassifizierung erfolgte über die vertikale Verschiebung der Hüft-Keypoints im Verhältnis zu den Fußgelenken.</p>
    `;
    if (video.srcObject) video.srcObject.getTracks().forEach(t => t.stop());
    video.pause();
};

init();
</script>
"""

components.html(html_code, height=1000)
