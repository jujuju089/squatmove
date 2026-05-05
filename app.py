import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="AI Exercise Recognizer", layout="wide")

st.title("🤖 AI Multi-Exercise Recognizer")
st.write("Diese App erkennt automatisch, ob du **Kniebeugen** oder **Liegestütze** machst.")

html_code = """
<div id="ai-app" style="font-family: sans-serif; background: #1a1a1a; color: white; padding: 20px; border-radius: 20px; max-width: 900px; margin: auto;">
    
    <!-- DASHBOARD -->
    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px; margin-bottom: 20px;">
        <div style="background: #2d2d2d; padding: 15px; border-radius: 12px; border-left: 5px solid #00d4ff;">
            <div style="font-size: 0.8em; color: #888;">ERKANNTE ÜBUNG</div>
            <div id="exercise-type" style="font-size: 1.2em; font-weight: bold; color: #00d4ff;">Suche...</div>
        </div>
        <div style="background: #2d2d2d; padding: 15px; border-radius: 12px; border-left: 5px solid #44ff44;">
            <div style="font-size: 0.8em; color: #888;">WIEDERHOLUNGEN</div>
            <div id="counter-label" style="font-size: 1.5em; font-weight: bold; color: #44ff44;">0</div>
        </div>
    </div>

    <!-- VIDEO -->
    <div style="position: relative; border-radius: 15px; overflow: hidden; background: #000;">
        <video id="video" autoplay playsinline muted style="width: 100%; height: auto;"></video>
        <canvas id="canvas" style="position: absolute; top: 0; left: 0; width: 100%; height: 100%;"></canvas>
    </div>

    <button id="stop-btn" style="width: 100%; margin-top: 20px; padding: 15px; background: #ff4b4b; color: white; border: none; border-radius: 8px; cursor: pointer; font-weight: bold;">SESSION BEENDEN</button>

    <div id="summary" style="display:none; margin-top: 20px; padding: 20px; background: white; color: black; border-radius: 10px;">
        <h3>📊 Ergebnis</h3>
        <div id="summary-text"></div>
        <button onclick="window.location.reload()">Neustart</button>
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

let detector;
let count = 0;
let stage = 'up';
let active = true;
let currentExercise = "Unbekannt";

async function init() {
    detector = await poseDetection.createDetector(
        poseDetection.SupportedModels.MoveNet,
        { modelType: poseDetection.movenet.modelType.SINGLEPOSE_LIGHTNING }
    );
    const stream = await navigator.mediaDevices.getUserMedia({ video: true });
    video.srcObject = stream;
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

            // 1. ÜBUNGSERKENNUNG LOGIK
            // Wir prüfen, ob der Körper eher horizontal (Push-up) oder vertikal (Squat) ist
            let bodyWidth = Math.abs(nose.x - ankle.x);
            let bodyHeight = Math.abs(nose.y - ankle.y);

            if (bodyHeight > bodyWidth) {
                currentExercise = "Kniebeuge (Squat)";
                exerciseLabel.innerText = "🏋️ " + currentExercise;
                
                // Squat Counter
                let dist = ankle.y - hip.y;
                if (dist < 230) stage = 'down';
                else if (dist > 280 && stage === 'down') { count++; stage = 'up'; }

            } else if (bodyWidth > bodyHeight && nose.score > 0.3) {
                currentExercise = "Liegestütz (Push-up)";
                exerciseLabel.innerText = "💪 " + currentExercise;

                // Push-up Counter (Abstand Nase zum Boden/Handgelenk)
                if (nose.y > shoulder.y + 30) stage = 'down';
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

document.getElementById('stop-btn').onclick = () => {
    active = false;
    document.getElementById('summary').style.display = "block";
    document.getElementById('summary-text').innerHTML = `Du hast ${count} Wiederholungen der Übung "${currentExercise}" gemacht.`;
    video.pause();
};

init();
</script>
"""

components.html(html_code, height=1000)
