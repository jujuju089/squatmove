import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="AI Exercise Recognition", layout="wide")

st.title("🤖 AI Exercise Recognizer")
st.write("Diese App erkennt automatisch die Art der Übung basierend auf deiner Körperhaltung.")

html_code = """
<div id="ai-app" style="font-family: sans-serif; background: #1a1a1a; color: white; padding: 20px; border-radius: 20px; max-width: 900px; margin: auto;">
    
    <!-- DASHBOARD -->
    <div style="background: #2d2d2d; padding: 20px; border-radius: 12px; border-bottom: 4px solid #00d4ff; margin-bottom: 20px; text-align: center;">
        <div style="font-size: 0.9em; color: #888; text-transform: uppercase; letter-spacing: 1px;">Aktuelle Übungspose</div>
        <div id="exercise-type" style="font-size: 2em; font-weight: bold; color: #00d4ff; margin-top: 5px;">Suche Mensch...</div>
    </div>

    <!-- VIDEO VIEW -->
    <div style="position: relative; border-radius: 15px; overflow: hidden; background: #000; line-height: 0;">
        <video id="video" autoplay playsinline muted style="width: 100%; height: auto;"></video>
        <canvas id="canvas" style="position: absolute; top: 0; left: 0; width: 100%; height: 100%; pointer-events: none;"></canvas>
    </div>

    <!-- CONTROLS -->
    <div style="display: flex; gap: 10px; margin-top: 20px;">
        <button id="switch-btn" style="flex: 1; padding: 15px; background: #444; color: white; border: none; border-radius: 8px; cursor: pointer; font-weight: bold;">📷 Kamera wechseln</button>
        <button id="stop-btn" style="flex: 1; padding: 15px; background: #ff4b4b; color: white; border: none; border-radius: 8px; cursor: pointer; font-weight: bold;">⏹ Analyse stoppen</button>
    </div>
</div>

<script src="https://cdn.jsdelivr.net/npm/@tensorflow/tfjs"></script>
<script src="https://cdn.jsdelivr.net/npm/@tensorflow-models/pose-detection"></script>

<script>
const video = document.getElementById('video');
const canvas = document.getElementById('canvas');
const ctx = canvas.getContext('2d');
const exerciseLabel = document.getElementById('exercise-type');

let detector;
let currentFacingMode = 'environment'; // Optimiert für Rückkamera (Tab S7)
let active = true;

async function startStream() {
    try {
        if(video.srcObject) { video.srcObject.getTracks().forEach(t => t.stop()); }
        const stream = await navigator.mediaDevices.getUserMedia({
            video: { facingMode: currentFacingMode, width: { ideal: 1280 }, height: { ideal: 720 } }
        });
        video.srcObject = stream;
        return new Promise(resolve => { video.onloadedmetadata = () => { video.play(); resolve(); }; });
    } catch (err) { alert("Kamera-Zugriff verweigert."); }
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
            const kp = poses[0].keypoints;
            const nose = kp[0], ankle = kp[16];

            // LOGIK: Nur Übungserkennung ohne Counter
            let bWidth = Math.abs(nose.x - ankle.x);
            let bHeight = Math.abs(nose.y - ankle.y);

            if (bHeight > bWidth * 1.1) {
                exerciseLabel.innerText = "🏋️ Kniebeuge-Position";
            } else if (bWidth > bHeight && nose.score > 0.2) {
                exerciseLabel.innerText = "💪 Liegestütz-Position";
            } else {
                exerciseLabel.innerText = "Suche Mensch...";
            }

            // Skelett zeichnen zur Visualisierung
            ctx.fillStyle = "#00d4ff";
            kp.forEach(p => { 
                if(p.score > 0.3) { 
                    ctx.beginPath(); 
                    ctx.arc(p.x, p.y, 6, 0, 2*Math.PI); 
                    ctx.fill(); 
                } 
            });
        }
    }
    requestAnimationFrame(detect);
}

document.getElementById('switch-btn').onclick = async () => {
    currentFacingMode = (currentFacingMode === 'user') ? 'environment' : 'user';
    await startStream();
};

document.getElementById('stop-btn').onclick = () => {
    active = false;
    exerciseLabel.innerText = "Analyse beendet";
    if (video.srcObject) video.srcObject.getTracks().forEach(t => t.stop());
    video.pause();
};

init();
</script>
"""

components.html(html_code, height=900)
