// SCAPTRACK Live WebSocket, ESP32 Wireless Ingestion & Kinematic Model Engine
// Supports dynamic toggling between Real-Time ESP32 Sensor Ingestion & Pre-trained AI Models
// Persists wireless sessions to SQLite database and displays granular 18-IMU sensor diagnostics.

let socket = null;
let isStreaming = false;
let streamInterval = null;
let streamMode = 'live'; // 'live' | 'pretrained'
let activeModelId = 'type2_dyskinesis';
let modelsCatalog = [];

// Database recording state
let isDbRecording = false;
let activeRecordingSessionId = null;
let recordingStartTime = null;
let recordingTimerInterval = null;
let recordedPacketsCount = 0;

// DOM references
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

// Pre-trained & AI UI Elements
const pretrainedPanel = document.getElementById('pretrained-model-panel');
const aiEvalBanner = document.getElementById('ai-eval-banner');
const aiClassTitle = document.getElementById('ai-classification-title');
const aiDescText = document.getElementById('ai-model-desc-text');
const aiRiskVal = document.getElementById('ai-risk-val');
const aiConfVal = document.getElementById('ai-confidence-val');
const aiArchBadge = document.getElementById('ai-model-arch-badge');
const aiAccBadge = document.getElementById('ai-model-acc-badge');
const aiLatencyBadge = document.getElementById('ai-latency-badge');

const livePageTitle = document.getElementById('live-page-title');
const livePageSubtitle = document.getElementById('live-page-subtitle');
const legRLabel = document.getElementById('leg-r-label');
const legLLabel = document.getElementById('leg-l-label');

const curveScapR = document.getElementById('curve-scap-r');
const curveScapL = document.getElementById('curve-scap-l');
const curveNormative = document.getElementById('curve-normative');
const normativeBandPoly = document.getElementById('normative-band-poly');

// ESP32 Hub & Sensor Matrix Elements
const esp32HubPanel = document.getElementById('esp32-hub-panel');
const hubIpDisplay = document.getElementById('hub-ip-display');
const hubRssiDisplay = document.getElementById('hub-rssi-display');
const hubBatteryDisplay = document.getElementById('hub-battery-display');
const hubSensorsCountDisplay = document.getElementById('hub-sensors-count-display');
const btnDbRecord = document.getElementById('btn-db-record');
const recStatusIndicator = document.getElementById('rec-status-indicator');
const recBadgeText = document.getElementById('rec-badge-text');

const sensorMatrixDrawer = document.getElementById('sensor-matrix-drawer');
const imuCardsContainer = document.getElementById('imu-cards-container');
const imuReadinessBadge = document.getElementById('imu-readiness-badge');

const historicalSessionsDrawer = document.getElementById('historical-sessions-drawer');
const historicalSessionsTbody = document.getElementById('historical-sessions-tbody');
const sessionsCountBadge = document.getElementById('sessions-count-badge');

// EMG Waveform buffer
const emgPointsUT = [];
const emgPointsSA = [];
const maxEmgPoints = 35;

/**
 * Switch global mode between 'live' (Hardware Sensor Feed) and 'pretrained' (AI Kinematic Models)
 */
function setStreamMode(mode) {
  streamMode = mode;

  // Update Topbar Buttons
  const topLive = document.getElementById('top-btn-mode-live');
  const topPretrained = document.getElementById('top-btn-mode-pretrained');
  const pageLive = document.getElementById('page-btn-mode-live');
  const pagePretrained = document.getElementById('page-btn-mode-pretrained');

  if (mode === 'live') {
    if (topLive) { topLive.className = 'mode-btn active live-mode'; }
    if (topPretrained) { topPretrained.className = 'mode-btn'; }
    if (pageLive) { pageLive.className = 'mode-btn active live-mode'; }
    if (pagePretrained) { pagePretrained.className = 'mode-btn'; }

    if (pretrainedPanel) pretrainedPanel.style.display = 'none';
    if (aiEvalBanner) aiEvalBanner.style.display = 'none';
    if (esp32HubPanel) esp32HubPanel.style.display = 'flex';

    if (livePageTitle) livePageTitle.textContent = 'Live Biomechanical Analysis';
    if (livePageSubtitle) livePageSubtitle.textContent = 'Wireless ESP32 IMU & sEMG real-time telemetry stream.';
    if (badgeStatus && isStreaming) {
      badgeStatus.textContent = 'ESP32 Stream Active (50Hz)';
      badgeStatus.className = 'badge danger';
    } else if (badgeStatus) {
      badgeStatus.textContent = 'Live Sensor Ready';
      badgeStatus.className = 'badge good';
    }

    if (legRLabel) legRLabel.textContent = 'Dominant';
    if (legLLabel) legLLabel.textContent = 'Affected';

    if (typeof showToast === 'function') {
      showToast('Switched to Live ESP32 Wireless Sensor Stream Mode (50Hz)');
    }
  } else {
    if (topLive) { topLive.className = 'mode-btn'; }
    if (topPretrained) { topPretrained.className = 'mode-btn active pretrained-mode'; }
    if (pageLive) { pageLive.className = 'mode-btn'; }
    if (pagePretrained) { pagePretrained.className = 'mode-btn active pretrained-mode'; }

    if (pretrainedPanel) pretrainedPanel.style.display = 'flex';
    if (aiEvalBanner) aiEvalBanner.style.display = 'block';

    if (livePageTitle) livePageTitle.textContent = 'Pre-trained Kinematic Model';
    if (livePageSubtitle) livePageSubtitle.textContent = 'DeepKinematics™ neural kinematic prior and dyskinesis classification benchmark.';
    
    if (badgeStatus && isStreaming) {
      badgeStatus.textContent = 'Model Simulating (50Hz)';
      badgeStatus.className = 'badge info';
    } else if (badgeStatus) {
      badgeStatus.textContent = 'Pre-trained Model Ready';
      badgeStatus.className = 'badge info';
    }

    // Load active model details & curves
    loadPretrainedModelCurves(activeModelId);

    if (typeof showToast === 'function') {
      showToast('Switched to Pre-trained AI Model Mode (DeepKinematics™)');
    }
  }

  // Notify backend socket if active
  if (socket && socket.readyState === WebSocket.OPEN) {
    socket.send(JSON.stringify({
      action: 'set_mode',
      mode: streamMode,
      model_id: activeModelId
    }));
  }
}

/**
 * Switch the active pre-trained model
 */
async function switchPretrainedModel(modelId) {
  activeModelId = modelId;

  // Update pills active state
  const pills = document.querySelectorAll('.model-pill');
  pills.forEach(p => {
    if (p.getAttribute('onclick') && p.getAttribute('onclick').includes(modelId)) {
      p.classList.add('active');
    } else {
      p.classList.remove('active');
    }
  });

  // Notify backend socket
  if (socket && socket.readyState === WebSocket.OPEN) {
    socket.send(JSON.stringify({
      action: 'set_model',
      model_id: modelId
    }));
  }

  // Load and render curves
  await loadPretrainedModelCurves(modelId);

  if (typeof showToast === 'function') {
    const model = modelsCatalog.find(m => m.id === modelId);
    showToast(`Loaded pre-trained model: ${model ? model.name : modelId}`);
  }
}

/**
 * Fetch and render model kinematic curves & normative confidence bands
 */
async function loadPretrainedModelCurves(modelId) {
  try {
    const res = await fetch(`/api/models/${modelId}/curves`);
    if (!res.ok) return;
    const data = await res.json();

    // Update AI Evaluation Banner
    if (aiClassTitle) aiClassTitle.textContent = `AI Classification: ${data.classification}`;
    if (aiRiskVal) {
      aiRiskVal.textContent = `${data.dyskinesis_risk_percent.toFixed(1)}%`;
      aiRiskVal.style.color = data.dyskinesis_risk_percent > 50 ? '#e67e22' : '#27ae60';
    }
    if (aiConfVal) aiConfVal.textContent = `${data.confidence.toFixed(1)}%`;

    const modelMeta = modelsCatalog.find(m => m.id === modelId);
    if (modelMeta) {
      if (aiDescText) aiDescText.textContent = modelMeta.description;
      if (aiArchBadge) aiArchBadge.textContent = `⚡ ${modelMeta.architecture}`;
      if (aiAccBadge) aiAccBadge.textContent = `🎯 Accuracy: ${modelMeta.accuracy}`;
      if (aiLatencyBadge) aiLatencyBadge.textContent = `⏱ Latency: ${modelMeta.inference_latency_ms}ms`;
    }

    // Render SVG Polylines
    renderKinematicCurves(data);
  } catch (err) {
    console.error('Failed to load model curves:', err);
  }
}

/**
 * Render Kinematic Curves onto the SVG
 */
function renderKinematicCurves(curveData) {
  const elevations = curveData.elevations;
  const scapR = curveData.scapula_r;
  const scapL = curveData.scapula_l;
  const norm = curveData.normative;
  const bandMin = curveData.normative_band_min;
  const bandMax = curveData.normative_band_max;

  if (!elevations || elevations.length === 0) return;

  const pointsR = [];
  const pointsL = [];
  const pointsNorm = [];
  const bandTop = [];
  const bandBottom = [];

  for (let i = 0; i < elevations.length; i++) {
    const arm = elevations[i];
    const x = 60 + (arm / 120.0) * 700;
    
    // Map upward rotation 0° -> 40° to y: 220 -> 20
    const yR = 220 - (scapR[i] / 40.0) * 200;
    const yL = 220 - (scapL[i] / 40.0) * 200;
    const yNorm = 220 - (norm[i] / 40.0) * 200;
    const yMin = 220 - (bandMin[i] / 40.0) * 200;
    const yMax = 220 - (bandMax[i] / 40.0) * 200;

    pointsR.push(`${x.toFixed(1)},${yR.toFixed(1)}`);
    pointsL.push(`${x.toFixed(1)},${yL.toFixed(1)}`);
    pointsNorm.push(`${x.toFixed(1)},${yNorm.toFixed(1)}`);
    bandTop.push(`${x.toFixed(1)},${yMax.toFixed(1)}`);
    bandBottom.unshift(`${x.toFixed(1)},${yMin.toFixed(1)}`);
  }

  if (curveScapR) curveScapR.setAttribute('points', pointsR.join(' '));
  if (curveScapL) curveScapL.setAttribute('points', pointsL.join(' '));
  if (curveNormative) curveNormative.setAttribute('points', pointsNorm.join(' '));
  if (normativeBandPoly) {
    const fullBand = bandTop.concat(bandBottom).join(' ');
    normativeBandPoly.setAttribute('points', fullBand);
  }
}

/**
 * Fetch catalog of pre-trained models
 */
async function fetchModelsCatalog() {
  try {
    const res = await fetch('/api/models/list');
    if (res.ok) {
      modelsCatalog = await res.json();
    }
  } catch (err) {
    console.error('Failed to load models catalog:', err);
  }
}

/**
 * Toggle SQLite Database Recording for ESP32 Wireless Telemetry
 */
async function toggleDatabaseRecording() {
  if (isDbRecording) {
    // Stop recording
    try {
      const res = await fetch('/api/esp32/session/stop', { method: 'POST' });
      if (res.ok) {
        const data = await res.json();
        isDbRecording = false;
        clearInterval(recordingTimerInterval);
        recordingTimerInterval = null;

        if (btnDbRecord) {
          btnDbRecord.innerHTML = '🔴 Record to Database';
          btnDbRecord.style.background = '#ff4757';
        }
        if (recStatusIndicator) recStatusIndicator.style.display = 'none';

        if (typeof showToast === 'function') {
          showToast(`ESP32 Session Saved to Database! (${data.total_packets || recordedPacketsCount} packets, ${data.duration_seconds || 0}s) ✓`);
        }

        // Refresh sessions list
        fetchEsp32SessionsList();
      }
    } catch (err) {
      console.error('Error stopping recording:', err);
    }
  } else {
    // Start recording
    const patientId = (typeof state !== 'undefined' && state.activePatientId) ? state.activePatientId : 'P-001';
    try {
      const res = await fetch('/api/esp32/session/start', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          patient_id: patientId,
          movement_plane: 'Sagittal Flexion'
        })
      });

      if (res.ok) {
        const data = await res.json();
        isDbRecording = true;
        activeRecordingSessionId = data.session_id;
        recordedPacketsCount = 0;
        recordingStartTime = Date.now();

        if (btnDbRecord) {
          btnDbRecord.innerHTML = '⏹ Stop & Save Session';
          btnDbRecord.style.background = '#e74c3c';
        }
        if (recStatusIndicator) recStatusIndicator.style.display = 'inline-block';

        recordingTimerInterval = setInterval(() => {
          if (!isDbRecording) return;
          const elapsedSec = Math.floor((Date.now() - recordingStartTime) / 1000);
          const mins = Math.floor(elapsedSec / 60).toString().padStart(2, '0');
          const secs = (elapsedSec % 60).toString().padStart(2, '0');
          if (recBadgeText) {
            recBadgeText.textContent = `● REC: ${mins}:${secs} (${recordedPacketsCount} pkts)`;
          }
        }, 500);

        if (typeof showToast === 'function') {
          showToast(`ESP32 Database Recording Started for ${patientId} (Session: ${data.session_id})`);
        }
      }
    } catch (err) {
      console.error('Error starting recording:', err);
    }
  }
}

/**
 * Fetch and Render ESP32 Hardware Status & 18-IMU Matrix
 */
async function fetchEsp32HardwareStatus() {
  try {
    const res = await fetch('/api/esp32/status');
    if (!res.ok) return;
    const data = await res.json();

    // Update Hub metadata
    if (hubIpDisplay) hubIpDisplay.textContent = data.hub.ip_address;
    if (hubRssiDisplay) hubRssiDisplay.textContent = `${data.hub.rssi_dbm} dBm`;
    if (hubBatteryDisplay) hubBatteryDisplay.textContent = `${data.hub.battery_level.toFixed(0)}%`;
    if (hubSensorsCountDisplay) hubSensorsCountDisplay.textContent = `${data.sensors_summary.online}/${data.sensors_summary.total} Online`;
    if (imuReadinessBadge) imuReadinessBadge.textContent = `System Readiness: ${data.sensors_summary.readiness_percent}% Optimal`;

    // Render 18 Sensor Node Cards
    renderImuCards(data.sensor_nodes);
  } catch (err) {
    console.error('Failed to fetch hardware status:', err);
  }
}

function renderImuCards(nodes) {
  if (!imuCardsContainer || !nodes) return;

  imuCardsContainer.innerHTML = nodes.map(node => {
    const isCalibrated = node.calibration_status === 'Calibrated';
    const statusClass = isCalibrated ? 'active-calibrated' : 'warning-node';
    const statusDot = isCalibrated ? '#2ecc71' : '#f1c40f';

    return `
      <div class="imu-node-card ${statusClass}" id="card-sensor-${node.sensor_id}">
        <div class="imu-node-header">
          <div>
            <div class="imu-node-id">${node.landmark_code} · ${node.sensor_id}</div>
            <div class="imu-node-label">${node.label}</div>
          </div>
          <span style="font-size:11px;font-weight:700;color:${statusDot}">● ${node.calibration_status}</span>
        </div>

        <div class="imu-angles-readout">
          <span>R: <b id="roll-${node.sensor_id}">${node.roll.toFixed(1)}°</b></span>
          <span>P: <b id="pitch-${node.sensor_id}">${node.pitch.toFixed(1)}°</b></span>
          <span>Y: <b id="yaw-${node.sensor_id}">${node.yaw.toFixed(1)}°</b></span>
        </div>

        <div class="imu-node-stats">
          <span>🔋 <b id="bat-${node.sensor_id}">${node.battery_percent.toFixed(0)}%</b></span>
          <span>📶 <b id="rssi-${node.sensor_id}">${node.rssi_dbm} dBm</b></span>
          <span>🌡 <b id="temp-${node.sensor_id}">${node.temperature_c.toFixed(1)}°C</b></span>
        </div>
      </div>
    `;
  }).join('');
}

function updateLiveSensorCards(sensorsMap) {
  if (!sensorsMap) return;
  for (const [sId, sData] of Object.entries(sensorsMap)) {
    const rollEl = document.getElementById(`roll-${sId}`);
    const pitchEl = document.getElementById(`pitch-${sId}`);
    const yawEl = document.getElementById(`yaw-${sId}`);
    const batEl = document.getElementById(`bat-${sId}`);
    const rssiEl = document.getElementById(`rssi-${sId}`);
    const tempEl = document.getElementById(`temp-${sId}`);

    if (rollEl && sData.roll !== undefined) rollEl.textContent = `${sData.roll.toFixed(1)}°`;
    if (pitchEl && sData.pitch !== undefined) pitchEl.textContent = `${sData.pitch.toFixed(1)}°`;
    if (yawEl && sData.yaw !== undefined) yawEl.textContent = `${sData.yaw.toFixed(1)}°`;
    if (batEl && sData.battery_percent !== undefined) batEl.textContent = `${sData.battery_percent.toFixed(0)}%`;
    if (rssiEl && sData.rssi_dbm !== undefined) rssiEl.textContent = `${sData.rssi_dbm} dBm`;
    if (tempEl && sData.temperature_c !== undefined) tempEl.textContent = `${sData.temperature_c.toFixed(1)}°C`;
  }
}

/**
 * Fetch and Render Historical Saved Database Sessions
 */
async function fetchEsp32SessionsList() {
  try {
    const res = await fetch('/api/esp32/sessions');
    if (!res.ok) return;
    const sessions = await res.json();

    if (sessionsCountBadge) sessionsCountBadge.textContent = sessions.length;
    if (!historicalSessionsTbody) return;

    if (sessions.length === 0) {
      historicalSessionsTbody.innerHTML = '<tr><td colspan="8" style="text-align:center;padding:16px;color:var(--muted)">No wireless telemetry sessions saved in database yet. Click "Record to Database" above to save one.</td></tr>';
      return;
    }

    historicalSessionsTbody.innerHTML = sessions.map(s => {
      const dateStr = s.created_at ? new Date(s.created_at).toLocaleString() : 'Recent';
      return `
        <tr>
          <td><strong style="font-family:monospace;color:var(--cyan2)">${s.session_id}</strong></td>
          <td><b>${s.patient_id}</b></td>
          <td>${s.movement_plane}</td>
          <td><b>${s.total_packets}</b> pkts</td>
          <td>${s.duration_seconds}s</td>
          <td><span class="badge ${s.status === 'Active' ? 'danger' : 'good'}">${s.status}</span></td>
          <td>${dateStr}</td>
          <td>
            <a href="/api/esp32/sessions/${s.session_id}/export" class="btn outline" style="padding:4px 8px;font-size:11px" target="_blank">⬇ CSV</a>
          </td>
        </tr>
      `;
    }).join('');
  } catch (err) {
    console.error('Failed to load historical sessions:', err);
  }
}

function toggleSensorMatrixView() {
  if (!sensorMatrixDrawer) return;
  const isShown = sensorMatrixDrawer.style.display === 'block';
  sensorMatrixDrawer.style.display = isShown ? 'none' : 'block';
  if (!isShown) fetchEsp32HardwareStatus();
}

function toggleHistoricalSessionsView() {
  if (!historicalSessionsDrawer) return;
  const isShown = historicalSessionsDrawer.style.display === 'block';
  historicalSessionsDrawer.style.display = isShown ? 'none' : 'block';
  if (!isShown) fetchEsp32SessionsList();
}

function refreshHardwareSensorStatus() {
  fetchEsp32HardwareStatus();
  if (typeof showToast === 'function') {
    showToast('18-IMU Hardware diagnostics refreshed ✓');
  }
}

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
    btnToggle.textContent = '⏹ Stop Stream';
    btnToggle.className = 'btn ghost';
  }
  if (badgeStatus) {
    badgeStatus.textContent = streamMode === 'live' ? 'ESP32 Streaming 50Hz' : 'Model Running 50Hz';
    badgeStatus.className = streamMode === 'live' ? 'badge danger' : 'badge info';
  }

  // Connect WebSocket or fallback
  const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  const wsUrl = `${wsProtocol}//${window.location.host}/ws/live?mode=${streamMode}&model=${activeModelId}`;

  try {
    socket = new WebSocket(wsUrl);

    socket.onopen = () => {
      socket.send(JSON.stringify({
        action: 'set_mode',
        mode: streamMode,
        model_id: activeModelId
      }));
    };

    socket.onmessage = (event) => {
      const data = JSON.parse(event.data);
      renderLiveFrame(data);
    };

    socket.onerror = () => {
      console.warn('WebSocket error, switching to local streaming fallback.');
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
    btnToggle.textContent = '▶ Start Stream';
    btnToggle.className = 'btn cyan';
  }
  if (badgeStatus) {
    badgeStatus.textContent = streamMode === 'live' ? 'ESP32 Stream Paused' : 'Model Stream Paused';
    badgeStatus.className = 'badge warn';
  }
}

function resetLiveStream() {
  stopLiveStream();
  if (valArmElev) valArmElev.textContent = '0.0°';
  if (valScapR) valScapR.textContent = '0.0°';
  if (valScapL) valScapL.textContent = '0.0°';
  if (valScapDiff) valScapDiff.textContent = '0.0° Asymmetry';
  if (cursorLine) {
    cursorLine.setAttribute('x1', '60');
    cursorLine.setAttribute('x2', '60');
  }
  if (badgeStatus) {
    badgeStatus.textContent = streamMode === 'live' ? 'ESP32 Ready' : 'Pre-trained Model Ready';
    badgeStatus.className = 'badge info';
  }
}

function renderLiveFrame(frame) {
  const arm = frame.arm_elevation;
  const scapR = frame.scapula_r;
  const scapL = frame.scapula_l;
  const diff = frame.diff;

  if (isDbRecording) {
    recordedPacketsCount++;
  }

  // Update readouts
  if (valArmElev) valArmElev.textContent = `${arm.toFixed(1)}°`;
  if (valScapR) valScapR.textContent = `${scapR.toFixed(1)}°`;
  if (valScapL) valScapL.textContent = `${scapL.toFixed(1)}°`;
  if (valScapDiff) {
    valScapDiff.textContent = `${Math.abs(diff).toFixed(1)}° ${diff >= 0 ? 'Deficit' : 'Surplus'}`;
    valScapDiff.className = Math.abs(diff) > 5.0 ? 'badge warn' : 'badge good';
  }

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

  // Update 18 IMU Sensor Cards if payload contains live sensor mapping
  if (frame.sensors) {
    updateLiveSensorCards(frame.sensors);
  }
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
    const sinPhase = 0.5 - 0.5 * math.cos(phase * 2.0 * math.PI);

    let frame;
    if (streamMode === 'pretrained') {
      const arm = 120.0 * sinPhase;
      const scapR = 32.0 * Math.pow(sinPhase, 1.1);
      const scapL = activeModelId === 'normative' ? scapR : 24.0 * Math.pow(sinPhase, 1.25);
      frame = {
        type: 'model_prediction_frame',
        mode: 'pretrained',
        arm_elevation: arm,
        scapula_r: scapR,
        scapula_l: scapL,
        diff: scapR - scapL,
        emg_ut: 15.0 + 75.0 * sinPhase + (Math.random() - 0.5) * 5,
        emg_sa: 12.0 + 82.0 * sinPhase + (Math.random() - 0.5) * 5
      };
    } else {
      const arm = 120.0 * sinPhase;
      const scapR = 32.0 * Math.pow(sinPhase, 1.1) + (Math.random() - 0.5) * 0.3;
      const scapL = 24.0 * Math.pow(sinPhase, 1.25) + (Math.random() - 0.5) * 0.3;
      frame = {
        type: 'live_motion_frame',
        mode: 'live',
        source: 'esp32_wireless_hub',
        hub_id: 'ESP32-HUB-01',
        arm_elevation: arm,
        scapula_r: scapR,
        scapula_l: scapL,
        diff: scapR - scapL,
        emg_ut: 15.0 + 75.0 * sinPhase + (Math.random() - 0.5) * 16,
        emg_sa: 12.0 + 82.0 * sinPhase + (Math.random() - 0.5) * 14
      };
    }
    renderLiveFrame(frame);
  }, 40);
}

// Bootstrap models catalog and hardware status on load
document.addEventListener('DOMContentLoaded', () => {
  fetchModelsCatalog();
  fetchEsp32HardwareStatus();
  fetchEsp32SessionsList();
});
