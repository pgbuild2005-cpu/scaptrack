// SCAPTRACK Live WebSocket & Biomechanical Motion Stream Engine

let socket = null;
let isStreaming = false;
let streamInterval = null;

// UI elements
const btnToggle = document.getElementById('btn-toggle-stream');
const badgeStatus = document.getElementById('badge-stream-status');
const valArmElev = document.getElementById('val-arm-elev');
const valScapR = document.getElementById('val-scap-r');
const valScapL = document.getElementById('val-scap-l');
const valScapDiff = document.getElementById('val-scap-diff');

const cursorLine = document.getElementById('curve-cursor');
const dynamicPosture = document.getElementById('dynamic-posture');
const poseValR = document.getElementById('pose-val-r');
const poseValL = document.getElementById('pose-val-l');

const emgWaveUT = document.getElementById('emg-wave-ut');
const emgWaveSA = document.getElementById('emg-wave-sa');

// EMG Waveform buffer
const emgPointsUT = [];
const emgPointsSA = [];
const maxEmgPoints = 35;

function toggleLiveStream() {
  if (isStreaming) {
    stopLiveStream();
  } else {
    startLiveStream();
  }
}

function startLiveStream() {
  isStreaming = true;
  if (btnToggle) {
    btnToggle.textContent = '⏹ Stop Live Stream';
    btnToggle.className = 'btn ghost';
  }
  if (badgeStatus) {
    badgeStatus.textContent = 'Recording 50Hz';
    badgeStatus.className = 'badge danger';
  }

  // Connect WebSocket or use high-frequency fallback
  const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  const wsUrl = `${wsProtocol}//${window.location.host}/ws/live`;

  try {
    socket = new WebSocket(wsUrl);

    socket.onmessage = (event) => {
      const data = JSON.parse(event.data);
      if (data.type === 'live_motion_frame') {
        renderLiveFrame(data);
      }
    };

    socket.onerror = () => {
      console.warn('WebSocket unavailable, switching to local streaming fallback.');
      startFallbackStream();
    };

    socket.onclose = () => {
      if (isStreaming) {
        startFallbackStream();
      }
    };
  } catch (err) {
    startFallbackStream();
  }
}

function stopLiveStream() {
  isStreaming = false;
  if (socket) {
    socket.close();
    socket = null;
  }
  if (streamInterval) {
    clearInterval(streamInterval);
    streamInterval = null;
  }
  if (btnToggle) {
    btnToggle.textContent = '▶ Start Live Stream';
    btnToggle.className = 'btn cyan';
  }
  if (badgeStatus) {
    badgeStatus.textContent = 'Stream Paused';
    badgeStatus.className = 'badge warn';
  }
}

function resetLiveStream() {
  stopLiveStream();
  if (valArmElev) valArmElev.textContent = '0.0°';
  if (valScapR) valScapR.textContent = '0.0°';
  if (valScapL) valScapL.textContent = '0.0°';
  if (valScapDiff) valScapDiff.textContent = '0.0° Asymmetry';
  if (cursorLine) cursorLine.setAttribute('x1', '60');
  if (cursorLine) cursorLine.setAttribute('x2', '60');
  if (badgeStatus) {
    badgeStatus.textContent = 'Ready';
    badgeStatus.className = 'badge info';
  }
}

function renderLiveFrame(frame) {
  const arm = frame.arm_elevation;
  const scapR = frame.scapula_r;
  const scapL = frame.scapula_l;
  const diff = frame.diff;

  // Update readouts
  if (valArmElev) valArmElev.textContent = `${arm.toFixed(1)}°`;
  if (valScapR) valScapR.textContent = `${scapR.toFixed(1)}°`;
  if (valScapL) valScapL.textContent = `${scapL.toFixed(1)}°`;
  if (valScapDiff) valScapDiff.textContent = `${diff.toFixed(1)}° Difference`;

  // Update cursor position on kinematic SVG (x: 60 to 760 for 0 to 120 deg)
  const cursorX = 60 + (arm / 120.0) * 700;
  if (cursorLine) {
    cursorLine.setAttribute('x1', cursorX);
    cursorLine.setAttribute('x2', cursorX);
  }

  // Update dynamic 3D posture visualizer
  if (dynamicPosture) {
    const tiltRot = (arm / 120.0) * 18 - 7;
    dynamicPosture.style.transform = `rotate(${tiltRot}deg)`;
  }
  if (poseValR) poseValR.textContent = `${scapR.toFixed(1)}°`;
  if (poseValL) poseValL.textContent = `${scapL.toFixed(1)}°`;

  // Update EMG Oscillogram
  updateEMGWaveform(frame.emg_ut, frame.emg_sa);
}

function updateEMGWaveform(rawUT, rawSA) {
  // Map microvolt signal (0 - 150uV) to SVG vertical coordinate (195 to 35)
  const yUT = Math.max(30, Math.min(195, 180 - (rawUT / 150.0) * 140));
  const ySA = Math.max(30, Math.min(195, 190 - (rawSA / 150.0) * 140));

  emgPointsUT.push(yUT);
  emgPointsSA.push(ySA);

  if (emgPointsUT.length > maxEmgPoints) emgPointsUT.shift();
  if (emgPointsSA.length > maxEmgPoints) emgPointsSA.shift();

  if (emgWaveUT) {
    const pts = emgPointsUT.map((val, idx) => `${idx * (900 / (maxEmgPoints - 1))},${val.toFixed(1)}`).join(' ');
    emgWaveUT.setAttribute('points', pts);
  }

  if (emgWaveSA) {
    const pts = emgPointsSA.map((val, idx) => `${idx * (900 / (maxEmgPoints - 1))},${val.toFixed(1)}`).join(' ');
    emgWaveSA.setAttribute('points', pts);
  }
}

// Local stream generator fallback if WebSocket is disconnected
function startFallbackStream() {
  if (streamInterval) clearInterval(streamInterval);
  let step = 0;
  streamInterval = setInterval(() => {
    if (!isStreaming) return;
    step = (step + 1) % 100;
    const phase = step / 100.0;
    const sinPhase = 0.5 - 0.5 * Math.cos(phase * 2.0 * Math.PI);

    const frame = {
      arm_elevation: 120.0 * sinPhase,
      scapula_r: 32.0 * Math.pow(sinPhase, 1.1),
      scapula_l: 24.0 * Math.pow(sinPhase, 1.25),
      diff: (32.0 * Math.pow(sinPhase, 1.1)) - (24.0 * Math.pow(sinPhase, 1.25)),
      emg_ut: 15.0 + 75.0 * sinPhase + (Math.random() - 0.5) * 20,
      emg_sa: 12.0 + 82.0 * sinPhase + (Math.random() - 0.5) * 16
    };
    renderLiveFrame(frame);
  }, 40);
}
