import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="AI Fitness Coach Tab S7", layout="wide")

st.title("🤖 AI Multi-Exercise Coach")
st.write("Optimiert für Tablets und Rückkamera-Nutzung.")

html_code = """
<div id="ai-app" style="font-family: sans-serif; background: #1a1a1a; color: white; padding: 20px; border-radius: 20px; max-width: 900px; margin: auto;">
    
    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px; margin-bottom: 20px;">
        <div style="background: #2d2d2d; padding: 15px; border-radius: 12px; border-bottom: 4px solid #00d4ff;">
            <div style="font-size: 0.8em; color: #888;">ÜBUNG</div>
            <div id="exercise-type" style="font-size: 1.1em; font-weight: bold; color: #00d4ff;">Suche...</div>
        </div>
        <div style="background: #2d2d2d; padding: 15px; border-radius: 12px; border-bottom: 4px solid #44ff44;">
            <div style="font-size: 0.8em; color: #888;">REPS</div>
            <div id="counter-label" style="font-size: 1.5em; font-weight: bold; color: #44ff44;">0</div>
        </div>
    </div>

    <div style="position: relative; border-radius: 15px; overflow: hidden; background: #000; line-height: 0;">
        <video id="video" autoplay playsinline muted style="width: 100%; height: auto;"></video>
        <canvas id="canvas" style="position: absolute; top: 0; left: 0; width: 100%; height: 100%; pointer-events: none;"></canvas>
    </div>

    <div style="display: flex; gap: 10px; margin-top: 20px;">
        <button id="switch-btn" style="flex: 1; padding: 15px; background: #444; color: white; border: none; border-radius: 8px; cursor: pointer; font-weight: bold;">📷 Kamera wechseln</button>
        <button id="stop-btn" style="flex: 1; padding: 15px; background: #ff4b4b; color: white; border: none; border-radius: 8px; cursor: pointer; font-weight: bold;">⏹ Session beenden</button>
    </div>

    <div id="summary-view" style="display:none; margin-top: 20px; padding: 25px; background: #ffffff; color: #1a1a1a; border-radius: 15px; border-left: 10px solid #00d4ff;">
        <h2 style="margin-top:0;">📊 Ergebnis</h2>
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
const exerciseLabel = document.getElementById('exercise-type');
const counterLabel = document.getElementById('counter-label');
const summaryView = document.getElementById('summary-view');
const summaryStats = document.getElementById('summary-stats');

let detector;
let currentFacingMode = 'environment'; // Startet direkt mit Rückkamera
let count = 0;
let stage = 'up';
let active = true;
let currentExercise = "Suche...";
let startTime = Date.now();

async function startStream() {
    try {
        if(video.srcObject) { video.srcObject.getTracks().forEach(t => t.stop()); }
        const stream = await navigator.mediaDevices.getUserMedia({
            video: { facingMode: currentFacingMode, width: { ideal: 1280 }, height: { ideal: 720 } }
        });
        video.srcObject = stream;
        return new Promise(resolve => { video.onloadedmetadata = () => { video.play(); resolve(); }; });
    } catch (err) { alert("Kamera-Fehler: Bitte Berechtigung prüfen!"); }
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
            const nose = kp[0], hip = kp[12], ankle = kp[16], shoulder = kp[6];

            // Erkennung der Körperlage (Breite vs Höhe)
            let bWidth = Math.abs(nose.x - ankle.x);
            let bHeight = Math.abs(nose.y - ankle.y);

            if (bHeight > bWidth * 1.1) {
                // MODUS: KNIEBEUGE
                if(currentExercise !== "Kniebeuge") { count = 0; stage = 'up'; currentExercise = "Kniebeuge"; }
                exerciseLabel.innerText = "🏋️ Kniebeugen";
                
                let dist = ankle.y - hip.y;
                // Empfindlichere Werte für Tablet-Distanz
                if (dist < 260) stage = 'down'; 
                else if (dist > 310 && stage === 'down') { count++; stage = 'up'; }

            } else if (bWidth > bHeight && nose.score > 0.2) {
                // MODUS: LIEGESTÜTZ
                if(currentExercise !== "Liegestütz") { count = 0; stage = 'up'; currentExercise = "Liegestütz"; }
                exerciseLabel.innerText = "💪 Liegestütze";

                // Nase sinkt unter Schulter-Linie
                if (nose.y > shoulder.y + 15) stage = 'down';
                else if (nose.y < shoulder.y - 5 && stage === 'down') { count++; stage = 'up'; }
            }

            counterLabel.innerText = count;

            // Zeichnen
            ctx.fillStyle = "#00d4ff";
            kp.forEach(p => { if(p.score > 0.3) { ctx.beginPath(); ctx.arc(p.x, p.y, 6, 0, 2*Math.PI); ctx.fill(); } });
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
    const duration = Math.round((Date.now() - startTime) / 1000);
    summaryView.style.display = "block";
    summaryStats.innerHTML = `
        <p>⏱ <b>Zeit:</b> ${duration} Sek.</p>
        <p>🔢 <b>Reps:</b> ${count}</p>
        <p>🏆 <b>Übung:</b> ${currentExercise}</p>
    `;
    if (video.srcObject) video.srcObject.getTracks().forEach(t => t.stop());
    video.pause();
};

init();
</script>
"""

components.html(html_code, height=1000)
