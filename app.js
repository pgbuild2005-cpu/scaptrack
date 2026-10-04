// SCAPTRACK Client-side Application Controller

const state = {
  activePage: 'dashboard',
  activePatientId: 'P-001',
  activePatient: null,
  patients: [],
  assessmentId: 1,
};

// DOM references
const pages = Array.from(document.querySelectorAll('.page'));
const navButtons = Array.from(document.querySelectorAll('.nav button'));
const crumb = document.getElementById('crumb');
const toast = document.getElementById('toast');

// Navigation handler
function go(id) {
  state.activePage = id;
  pages.forEach(p => p.classList.toggle('active', p.id === id));
  navButtons.forEach(b => b.classList.toggle('active', b.dataset.page === id));
  
  const activeBtn = navButtons.find(b => b.dataset.page === id);
  if (activeBtn && crumb) {
    crumb.textContent = activeBtn.textContent.trim();
  }

  window.scrollTo({ top: 0, behavior: 'smooth' });

  if (id === 'dashboard') {
    fetchDashboardStats();
    fetchPatients();
  } else if (id === 'reports' || id === 'research') {
    loadPatientNotes();
  }
}

// Attach sidebar listeners
navButtons.forEach(btn => {
  btn.addEventListener('click', () => go(btn.dataset.page));
});

// Toast notification helper
function showToast(message, duration = 3000) {
  if (!toast) return;
  toast.textContent = message;
  toast.style.display = 'block';
  setTimeout(() => {
    toast.style.display = 'none';
  }, duration);
}

// Fetch dashboard statistics
async function fetchDashboardStats() {
  try {
    const res = await fetch('/api/dashboard/stats');
    if (!res.ok) return;
    const data = await res.json();
    document.getElementById('stat-active-patients').textContent = data.active_patients;
    document.getElementById('stat-today-assessments').textContent = data.today_assessments < 10 ? `0${data.today_assessments}` : data.today_assessments;
    document.getElementById('stat-reports-pending').textContent = data.reports_pending < 10 ? `0${data.reports_pending}` : data.reports_pending;
    document.getElementById('stat-device-health').textContent = `${data.device_health}%`;
  } catch (err) {
    console.error('Failed to load dashboard stats:', err);
  }
}

// Fetch and render patients list
async function fetchPatients() {
  try {
    const res = await fetch('/api/patients');
    if (!res.ok) return;
    state.patients = await res.json();
    renderRecentPatients(state.patients);
    
    // Select active patient if available
    if (state.patients.length > 0 && !state.activePatient) {
      selectPatient(state.patients[0].id);
    }
  } catch (err) {
    console.error('Failed to load patients:', err);
  }
}

function renderRecentPatients(patientsList) {
  const container = document.getElementById('recent-patients-list');
  if (!container) return;

  if (patientsList.length === 0) {
    container.innerHTML = '<div class="muted" style="padding:10px 0;">No patients registered yet.</div>';
    return;
  }

  container.innerHTML = patientsList.slice(0, 4).map(p => {
    const isSelected = p.id === state.activePatientId;
    const statusBadge = p.assessment_type === 'Follow-up' 
      ? '<span class="badge warn">Pending</span>'
      : '<span class="badge good">Complete</span>';
    
    return `
      <div class="patient-row" style="${isSelected ? 'background:#f2fafc; border-radius:10px; padding:10px 8px;' : ''}">
        <div>
          <div class="patient-name">${p.id} · ${p.name}</div>
          <span class="muted">${p.assessment_type} · ${p.affected_side} side</span>
        </div>
        <span class="muted">${new Date(p.created_at).toLocaleDateString(undefined, { day: '2-digit', month: 'short' })}</span>
        ${statusBadge}
        <span>3 trials</span>
        <button class="btn outline" onclick="selectPatient('${p.id}'); go('reports');">View</button>
      </div>
    `;
  }).join('');
}

function selectPatient(patientId) {
  state.activePatientId = patientId;
  const p = state.patients.find(x => x.id === patientId);
  if (p) {
    state.activePatient = p;
    // Update labels across views
    const badge = document.getElementById('active-patient-badge');
    if (badge) badge.textContent = `Selected: ${p.id} (${p.name})`;
    
    const repHead = document.getElementById('report-patient-header');
    if (repHead) repHead.textContent = `Objective findings for ${p.id} (${p.name}) · Assessment Session`;

    const resId = document.getElementById('research-patient-id');
    if (resId) resId.textContent = p.id;

    // Fill form
    document.getElementById('patient-id-input').value = p.id;
    document.getElementById('patient-name-input').value = p.name;
    document.getElementById('patient-age-input').value = p.age;
    document.getElementById('patient-sex-input').value = p.sex;
    document.getElementById('patient-dom-input').value = p.dominant_side;
    document.getElementById('patient-aff-input').value = p.affected_side;
    document.getElementById('patient-nprs-input').value = p.nprs_pain;
    document.getElementById('patient-activity-input').value = p.activity || '';
    document.getElementById('patient-injury-input').value = p.prev_injury;
    document.getElementById('patient-type-input').value = p.assessment_type;
  }
}

// Handle Patient Form Submission
async function handleSavePatient(e) {
  e.preventDefault();
  const payload = {
    id: document.getElementById('patient-id-input').value.trim(),
    name: document.getElementById('patient-name-input').value.trim(),
    age: parseInt(document.getElementById('patient-age-input').value, 10) || 25,
    sex: document.getElementById('patient-sex-input').value,
    dominant_side: document.getElementById('patient-dom-input').value,
    affected_side: document.getElementById('patient-aff-input').value,
    nprs_pain: parseInt(document.getElementById('patient-nprs-input').value, 10) || 0,
    activity: document.getElementById('patient-activity-input').value.trim(),
    prev_injury: document.getElementById('patient-injury-input').value,
    assessment_type: document.getElementById('patient-type-input').value,
  };

  try {
    const res = await fetch('/api/patients', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });

    if (res.ok) {
      const saved = await res.json();
      showToast(`Patient ${saved.id} saved successfully!`);
      await fetchPatients();
      selectPatient(saved.id);
    } else {
      showToast('Error saving patient profile.');
    }
  } catch (err) {
    console.error('Error saving patient:', err);
    showToast('Failed to connect to backend.');
  }
}

// Static calibration simulation
function runStaticCalibration() {
  const display = document.getElementById('calib-score-display');
  if (display) display.textContent = 'Calibrating...';
  
  setTimeout(() => {
    if (display) display.textContent = '98%';
    showToast('Static Zero Calibration successfully locked.');
  }, 1200);
}

// Clinician Notes API Integration
async function loadPatientNotes() {
  if (!state.activePatientId) return;
  try {
    const res = await fetch(`/api/notes/${state.activePatientId}`);
    if (res.ok) {
      const data = await res.json();
      const notesArea = document.getElementById('clinician-notes-area');
      if (notesArea && data && data.note_text) {
        notesArea.value = data.note_text;
      }
    }
  } catch (err) {
    console.error('Failed to load notes:', err);
  }
}

async function saveClinicianNotes() {
  const notesArea = document.getElementById('clinician-notes-area');
  if (!notesArea) return;

  const payload = {
    patient_id: state.activePatientId || 'P-001',
    note_text: notesArea.value.trim()
  };

  try {
    const res = await fetch('/api/notes', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });

    if (res.ok) {
      showToast('Clinician notes saved to database ✓');
    }
  } catch (err) {
    console.error('Failed to save notes:', err);
  }
}

// Research CSV Export trigger
function triggerResearchExport() {
  const pId = state.activePatientId || 'P-001';
  showToast(`Preparing research CSV dataset for ${pId}...`);
  window.location.href = `/api/export/research/${pId}`;
}

// Save recorded motion trial
async function saveCurrentTrial() {
  const payload = {
    assessment_id: 1,
    trial_number: 1,
    arm_elevation_max: 120.0,
    scapula_r_max: 32.0,
    scapula_l_max: 24.0,
    asymmetry_deg: 8.0,
    symmetry_percent: 75.0,
    ut_r: 60.0,
    ut_l: 45.0,
    mt_r: 35.0,
    mt_l: 20.0,
    lt_r: 35.0,
    lt_l: 20.0,
    sa_r: 42.0,
    sa_l: 62.0
  };

  try {
    const res = await fetch('/api/trials', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    if (res.ok) {
      showToast('Trial 1 saved and recorded to database ✓');
    }
  } catch (err) {
    console.error('Failed to save trial:', err);
  }
}

// Initial bootstrap on load
document.addEventListener('DOMContentLoaded', () => {
  fetchDashboardStats();
  fetchPatients();
});
