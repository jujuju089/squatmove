import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="AI Multi-Exercise Recognizer", layout="wide")

st.title("🤖 AI Multi-Exercise Coach")
st.write("Diese KI erkennt automatisch, ob du Kniebeugen oder Liegestütze machst und zählt mit.")

html_code = """
<div id="ai-app" style="font-family: sans-serif; background: #1a1a1a; color: white; padding: 20px; border-radius: 20px; max-width: 900px; margin: auto;">
    
    <!-- DASHBOARD -->
    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px; margin-bottom: 20px;">
        <div style="background: #2d2d2d; padding: 15px; border-radius: 12px; border-bottom: 4px solid #00d4ff;">
            <div style="font-size: 0.8em; color: #888;">ERKANNTE ÜBUNG</div>
            <div id="exercise-type" style="font-size: 1.1em; font-weight: bold; color: #00d4ff;">Suche Übung...</div>
        </div>
        <div style="background: #2d2d2d; padding: 15px; border-radius: 12px; border-bottom: 4px solid #44ff44;">
            <div style="font-size: 0.8em; color: #888;">WIEDERHOLUNGEN</div>
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
        <h2 style="margin-top:0;">📊 Analyse-Bericht</h2>
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
let currentFacingMode = 'user'; 
let count = 0;
let stage = 'up';
let active = true;
let currentExercise = "Suche...";
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
        return new Promise(resolve => { video.onloadedmetadata = () => { video.play(); resolve(); }; });
    } catch (err) {
        alert("Kamerafehler: " + err.message);
    }
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
            const nose = kp[0], hip = kp[12], ankle = kp[16], shoulder = kp[6], knee = kp[14];

            // LOGIK: ÜBUNGSERKENNUNG (Horizontal vs. Vertikal)
            let bodyWidth = Math.abs(nose.x - ankle.x);
            let bodyHeight = Math.abs(nose.y - ankle.y);

            if (bodyHeight > bodyWidth * 1.2) {
                // MODUS: KNIEBEUGE
                if(currentExercise !== "Kniebeuge") { count = 0; stage = 'up'; } // Reset bei Wechsel
                currentExercise = "Kniebeuge";
                exerciseLabel.innerText = "🏋️ Übung: Kniebeugen";
                
                let dist = ankle.y - hip.y;
                if (dist < 220) stage = 'down';
                else if (dist > 270 && stage === 'down') { count++; stage = 'up'; }

            } else if (bodyWidth > bodyHeight && nose.score > 0.2) {
                // MODUS: LIEGESTÜTZ
                if(currentExercise !== "Liegestütz") { count = 0; stage = 'up'; }
                currentExercise = "Liegestütz";
                exerciseLabel.innerText = "💪 Übung: Liegestütze";

                // Push-up Logik: Nase sinkt unter Schulterniveau
                if (nose.y > shoulder.y + 20) stage = 'down';
                else if (nose.y < shoulder.y && stage === 'down') { count++; stage = 'up'; }
            }

            counterLabel.innerText = count;

            // Skelett zeichnen
            ctx.fillStyle = "#00d4ff";
            kp.forEach(p => { if(p.score > 0.2) { ctx.beginPath(); ctx.arc(p.x, p.y, 5, 0, 2*Math.PI); ctx.fill(); } });
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
        <p>⏱ <b>Dauer:</b> ${duration} Sekunden</p>
        <p>🔢 <b>Wiederholungen:</b> ${count}</p>
        <p>🏆 <b>Letzte Übung:</b> ${currentExercise}</p>
        <hr>
        <p><b>KI-Analyse:</b> Die App hat basierend auf dem Seitenverhältnis deines Körpers (Bounding Box) automatisch zwischen einer horizontalen (Liegestütz) und vertikalen (Kniebeuge) Pose unterschieden.</p>
    `;
    if (video.srcObject) video.srcObject.getTracks().forEach(t => t.stop());
    video.pause();
};

init();
</script>
"""

components.html(html_code, height=1000)
