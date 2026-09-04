// ==========================================================================
// AirADB Studio - Frontend Application Logic (Desktop + Mobile Responsive)
// ==========================================================================

// Standalone Dedicated Desktop ADB Manager - Localhost Daemon
const API_BASE = (window.location.protocol.startsWith('http') && window.location.port === '8765')
  ? window.location.origin
  : 'http://127.0.0.1:8765';
let currentDevices = [];
let selectedDeviceSerial = null;
let pollTimer = null;

// DOM Elements Cache
const elements = {
  // Badges & Header
  adbStatusBadge: document.getElementById('adbStatusBadge'),
  adbStatusText: document.getElementById('adbStatusText'),
  hostIpBadge: document.getElementById('hostIpBadge'),
  hostIpText: document.getElementById('hostIpText'),
  wifiIpBadge: document.getElementById('wifiIpBadge'),
  wifiIpText: document.getElementById('wifiIpText'),
  deviceCountBadge: document.getElementById('deviceCountBadge'),
  btnRefreshDevices: document.getElementById('btnRefreshDevices'),
  btnHeaderConnect: document.getElementById('btnHeaderConnect'),
  adbMissingBanner: document.getElementById('adbMissingBanner'),
  btnAutoInstallAdb: document.getElementById('btnAutoInstallAdb'),

  // Navigation & Tabs
  navTabs: document.querySelectorAll('.nav-tab'),
  tabPanes: document.querySelectorAll('.tab-pane'),

  // Wireless Connect & Pair Tab
  pairForm: document.getElementById('pairForm'),
  pairIpPort: document.getElementById('pairIpPort'),
  pairCode: document.getElementById('pairCode'),
  pairNickname: document.getElementById('pairNickname'),
  btnPairSubmit: document.getElementById('btnPairSubmit'),
  connectForm: document.getElementById('connectForm'),
  connectIpPort: document.getElementById('connectIpPort'),
  btnConnectSubmit: document.getElementById('btnConnectSubmit'),
  btnPairAndConnectAll: document.getElementById('btnPairAndConnectAll'),
  historyList: document.getElementById('historyList'),

  // USB Switch Tab
  usbDetectedLabel: document.getElementById('usbDetectedLabel'),
  btnSwitchUsbToWifi: document.getElementById('btnSwitchUsbToWifi'),

  // Device Studio Tab (Startup Dashboard)
  devicesContainer: document.getElementById('devicesContainer'),
  btnDisconnectAll: document.getElementById('btnDisconnectAll'),
  btnStudioRefresh: document.getElementById('btnStudioRefresh'),
  deviceControlCenter: document.getElementById('deviceControlCenter'),
  activeDeviceTitle: document.getElementById('activeDeviceTitle'),
  activeDeviceSerial: document.getElementById('activeDeviceSerial'),
  ctrlSubtabs: document.querySelectorAll('.ctrl-subtab'),
  subtabPanes: document.querySelectorAll('.subtab-pane'),

  // Screenshot Tool
  btnTakeScreenshot: document.getElementById('btnTakeScreenshot'),
  btnDownloadScreenshot: document.getElementById('btnDownloadScreenshot'),
  btnCopyScreenshot: document.getElementById('btnCopyScreenshot'),
  screenshotImg: document.getElementById('screenshotImg'),
  screenshotPlaceholder: document.getElementById('screenshotPlaceholder'),

  // Logcat Tool
  logcatSearch: document.getElementById('logcatSearch'),
  logcatLinesSelect: document.getElementById('logcatLinesSelect'),
  btnFetchLogcat: document.getElementById('btnFetchLogcat'),
  btnClearLogcat: document.getElementById('btnClearLogcat'),
  logcatOutput: document.getElementById('logcatOutput'),

  // APK Tool
  apkDropzone: document.getElementById('apkDropzone'),
  apkFileInput: document.getElementById('apkFileInput'),
  btnSelectApk: document.getElementById('btnSelectApk'),
  apkInstallStatus: document.getElementById('apkInstallStatus'),

  // Remote Controls
  customShellCmd: document.getElementById('customShellCmd'),
  btnRunShell: document.getElementById('btnRunShell'),
  shellOutput: document.getElementById('shellOutput'),
  inputQuickText: document.getElementById('inputQuickText'),
  btnSendQuickText: document.getElementById('btnSendQuickText'),
  selectScreenTimeout: document.getElementById('selectScreenTimeout'),
  btnApplyScreenTimeout: document.getElementById('btnApplyScreenTimeout'),
  btnDarkModeOn: document.getElementById('btnDarkModeOn'),
  btnDarkModeOff: document.getElementById('btnDarkModeOff'),

  // Battery & Telemetry Tool
  btnRefreshBattery: document.getElementById('btnRefreshBattery'),
  batteryStatusPill: document.getElementById('batteryStatusPill'),
  batteryPercentText: document.getElementById('batteryPercentText'),
  batteryBarFill: document.getElementById('batteryBarFill'),
  batteryPowerSourceText: document.getElementById('batteryPowerSourceText'),
  metricTempText: document.getElementById('metricTempText'),
  metricTempSub: document.getElementById('metricTempSub'),
  metricHealthText: document.getElementById('metricHealthText'),
  metricVoltageText: document.getElementById('metricVoltageText'),
  metricTechText: document.getElementById('metricTechText'),

  // Scanner Tab
  btnStartScan: document.getElementById('btnStartScan'),
  scanLoading: document.getElementById('scanLoading'),
  scanResults: document.getElementById('scanResults'),

  // Settings Tab
  settingsAdbPath: document.getElementById('settingsAdbPath'),
  settingsAdbVersion: document.getElementById('settingsAdbVersion'),
  btnReinstallAdb: document.getElementById('btnReinstallAdb'),
  btnRestartAdb: document.getElementById('btnRestartAdb'),

  // Toasts
  toastContainer: document.getElementById('toastContainer')
};

// ==========================================================================
// Initialization (Direct Startup into Device Studio)
// ==========================================================================

document.addEventListener('DOMContentLoaded', () => {
  setupNavigation();
  initGoogleAuth();
  setupHeaderActions();
  setupEventListeners();

  // Launch directly into Device Management Panel
  switchToTab('tab-devices');

  // Immediately poll local daemon and connected devices
  checkStatus();
  fetchDevices();
  fetchHistory();

  // Periodic polling for status and devices
  pollTimer = setInterval(() => {
    checkStatus(true);
    fetchDevices(true);
  }, 3000);
});

// ==========================================================================
// Navigation & Tabs
// ==========================================================================

function setupNavigation() {
  elements.navTabs.forEach(tab => {
    tab.addEventListener('click', () => {
      const targetTab = tab.getAttribute('data-tab');
      elements.navTabs.forEach(t => t.classList.remove('active'));
      elements.tabPanes.forEach(p => p.classList.remove('active'));

      tab.classList.add('active');
      const pane = document.getElementById(targetTab);
      if (pane) pane.classList.add('active');
    });
  });

  // Control Center Subtabs
  elements.ctrlSubtabs.forEach(subtab => {
    subtab.addEventListener('click', () => {
      const target = subtab.getAttribute('data-subtab');
      elements.ctrlSubtabs.forEach(s => s.classList.remove('active'));
      elements.subtabPanes.forEach(p => p.classList.remove('active'));

      subtab.classList.add('active');
      const pane = document.getElementById(target);
      if (pane) pane.classList.add('active');
      if (target === 'subtab-battery') {
        fetchBatteryDiagnostics(false);
      }
    });
  });
}

// ==========================================================================
// Google Sign-In & Profile State Management
// ==========================================================================

function initGoogleAuth() {
  const btnGoogleSignIn = document.getElementById('btnGoogleSignIn');
  const googleModal = document.getElementById('googleAuthModal');
  const btnCloseGoogleModal = document.getElementById('btnCloseGoogleModal');
  const btnQuickGoogleSignIn = document.getElementById('btnQuickGoogleSignIn');
  const btnSubmitCustomGoogleAuth = document.getElementById('btnSubmitCustomGoogleAuth');
  const inputGoogleName = document.getElementById('inputGoogleName');
  const inputGoogleEmail = document.getElementById('inputGoogleEmail');
  const userProfileBadge = document.getElementById('userProfileBadge');
  const userAvatar = document.getElementById('userAvatar');
  const userName = document.getElementById('userName');
  const userEmail = document.getElementById('userEmail');
  const btnSignOut = document.getElementById('btnSignOut');

  function renderGoogleUser(user) {
    if (user && user.email) {
      if (btnGoogleSignIn) btnGoogleSignIn.classList.add('hidden');
      if (userProfileBadge) userProfileBadge.classList.remove('hidden');
      if (userName) userName.textContent = user.name || user.email.split('@')[0];
      if (userEmail) userEmail.textContent = user.email;
      if (userAvatar) userAvatar.textContent = (user.name || user.email)[0].toUpperCase();
    } else {
      if (btnGoogleSignIn) btnGoogleSignIn.classList.remove('hidden');
      if (userProfileBadge) userProfileBadge.classList.add('hidden');
    }
  }

  // Load existing session if saved
  try {
    const saved = localStorage.getItem('airadb_google_user');
    if (saved) {
      const user = JSON.parse(saved);
      renderGoogleUser(user);
    }
  } catch (e) {
    console.warn('Could not parse saved user:', e);
  }

  if (btnGoogleSignIn && googleModal) {
    btnGoogleSignIn.addEventListener('click', () => {
      googleModal.classList.remove('hidden');
    });
  }

  if (btnCloseGoogleModal && googleModal) {
    btnCloseGoogleModal.addEventListener('click', () => {
      googleModal.classList.add('hidden');
    });
  }

  if (googleModal) {
    googleModal.addEventListener('click', (e) => {
      if (e.target === googleModal) googleModal.classList.add('hidden');
    });
  }

  if (btnQuickGoogleSignIn) {
    btnQuickGoogleSignIn.addEventListener('click', () => {
      const user = {
        name: 'Google Developer',
        email: 'developer.airadb@gmail.com',
        time: Date.now()
      };
      localStorage.setItem('airadb_google_user', JSON.stringify(user));
      renderGoogleUser(user);
      if (googleModal) googleModal.classList.add('hidden');
      showToast('Signed in as Google Developer!', 'success');
    });
  }

  if (btnSubmitCustomGoogleAuth) {
    btnSubmitCustomGoogleAuth.addEventListener('click', () => {
      const name = (inputGoogleName?.value || '').trim() || 'Android Engineer';
      const email = (inputGoogleEmail?.value || '').trim();
      if (!email || !email.includes('@')) {
        showToast('Please enter a valid Google email address.', 'warning');
        return;
      }
      const user = { name, email, time: Date.now() };
      localStorage.setItem('airadb_google_user', JSON.stringify(user));
      renderGoogleUser(user);
      if (googleModal) googleModal.classList.add('hidden');
      showToast(`Welcome, ${name}! Signed in with Google.`, 'success');
    });
  }

  if (btnSignOut) {
    btnSignOut.addEventListener('click', () => {
      localStorage.removeItem('airadb_google_user');
      renderGoogleUser(null);
      showToast('Signed out of Google account.', 'info');
    });
  }
}

// ==========================================================================
// Navigation Helpers & Desktop Header Actions
// ==========================================================================

function switchToTab(tabId) {
  elements.navTabs.forEach(b => b.classList.remove('active'));
  elements.tabPanes.forEach(p => p.classList.remove('active'));
  const tabBtn = document.querySelector(`.nav-tab[data-tab="${tabId}"]`);
  const pane = document.getElementById(tabId);
  if (tabBtn) tabBtn.classList.add('active');
  if (pane) pane.classList.add('active');
}

function setupHeaderActions() {
  if (elements.btnHeaderConnect) {
    elements.btnHeaderConnect.addEventListener('click', () => {
      switchToTab('tab-pairing');
      if (elements.pairIpPort) elements.pairIpPort.focus();
    });
  }
}

// ==========================================================================
// Status & Health Check (Local Daemon)
// ==========================================================================

async function checkStatus(silent = false) {
  try {
    const res = await fetch(`${API_BASE}/api/status`);
    if (!res.ok) throw new Error('Status request failed');
    const data = await res.json();

    if (data.installed) {
      elements.adbStatusBadge.className = 'status-pill status-ready';
      elements.adbStatusText.textContent = 'ADB Ready';
      if (elements.adbMissingBanner) elements.adbMissingBanner.classList.add('hidden');
      if (elements.settingsAdbPath) elements.settingsAdbPath.textContent = data.adb_path || 'System PATH';
      if (elements.settingsAdbVersion) elements.settingsAdbVersion.textContent = data.version || 'Active';
    } else {
      elements.adbStatusBadge.className = 'status-pill status-error';
      elements.adbStatusText.textContent = 'ADB Not Installed';
      if (elements.adbMissingBanner) elements.adbMissingBanner.classList.remove('hidden');
      if (elements.settingsAdbPath) elements.settingsAdbPath.textContent = 'Not Found';
      if (elements.settingsAdbVersion) elements.settingsAdbVersion.textContent = 'None';
    }

    if (elements.hostIpText) {
      elements.hostIpText.textContent = `Daemon: 127.0.0.1:8765`;
    }

    // Display Active Local Wi-Fi / Network & Auto-prefill Subnet
    if (data.network && data.network.ip) {
      const net = data.network;
      const label = net.is_wifi ? 'Wi-Fi' : (net.interface || 'LAN');
      if (elements.wifiIpText) {
        elements.wifiIpText.textContent = `${label}: ${net.ip}`;
        if (elements.wifiIpBadge) {
          elements.wifiIpBadge.title = `Local Network: ${net.interface} | IP: ${net.ip} | Subnet: ${net.subnet_prefix}.0/24`;
        }
      }

      // Auto-prefill subnet prefix in pairing & connection inputs if currently empty
      if (net.subnet_prefix && net.subnet_prefix !== '127.0.0') {
        const prefix = `${net.subnet_prefix}.`;
        if (elements.pairIpPort) {
          elements.pairIpPort.placeholder = `e.g. ${prefix}5:37123`;
          if (!elements.pairIpPort.value) {
            elements.pairIpPort.value = prefix;
          }
        }
        if (elements.connectIpPort) {
          elements.connectIpPort.placeholder = `e.g. ${prefix}5:41235`;
          if (!elements.connectIpPort.value) {
            elements.connectIpPort.value = prefix;
          }
        }
      }
    }
  } catch (err) {
    if (!silent) {
      elements.adbStatusBadge.className = 'status-pill status-error';
      elements.adbStatusText.textContent = 'Daemon Offline';
    }
  }
}


// ==========================================================================
// Device Fetching & Rendering
// ==========================================================================

async function fetchDevices(silent = false) {
  try {
    const res = await fetch(`${API_BASE}/api/devices`);
    const data = await res.json();
    currentDevices = data.devices || [];

    elements.deviceCountBadge.textContent = currentDevices.length;
    renderDevices(currentDevices);
    updateUsbStatus(currentDevices);

    // If selected device was disconnected, reset selection
    if (selectedDeviceSerial && !currentDevices.some(d => d.serial === selectedDeviceSerial)) {
      if (currentDevices.length > 0) {
        selectDevice(currentDevices[0].serial);
      } else {
        selectedDeviceSerial = null;
        elements.deviceControlCenter.classList.add('hidden');
      }
    } else if (!selectedDeviceSerial && currentDevices.length > 0) {
      selectDevice(currentDevices[0].serial);
    }
  } catch (err) {
    if (!silent) showToast('Failed to connect to AirADB backend server', 'error');
  }
}

function renderDevices(devices) {
  if (devices.length === 0) {
    elements.devicesContainer.innerHTML = `
      <div class="empty-state-card glass-panel">
        <div class="empty-icon">📱</div>
        <h3>No Devices Connected</h3>
        <p>Pair or connect your phone in the "Pair &amp; Connect" tab or plug it in via USB to get started.</p>
      </div>
    `;
    elements.deviceControlCenter.classList.add('hidden');
    return;
  }

  elements.devicesContainer.innerHTML = devices.map(device => {
    const isSelected = device.serial === selectedDeviceSerial;
    const isWireless = device.is_wireless;
    const batteryText = device.battery_level !== null ? `${device.battery_level}%` : 'Unknown';
    const osVersion = device.android_version ? `Android ${device.android_version}` : 'Android';

    return `
      <div class="device-card ${isSelected ? 'active-selected' : ''}" data-serial="${device.serial}">
        <div class="device-card-header">
          <div class="device-title-box">
            <div class="device-phone-icon">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <rect x="5" y="2" width="14" height="20" rx="2" ry="2"></rect>
                <line x1="12" y1="18" x2="12.01" y2="18"></line>
              </svg>
            </div>
            <div>
              <div class="device-name">${escapeHtml(device.model || 'Android Device')}</div>
              <div class="meta-serial">${escapeHtml(device.serial)}</div>
            </div>
          </div>
          <span class="device-type-tag ${isWireless ? 'tag-wireless' : 'tag-usb'}">
            ${isWireless ? '📶 Wi-Fi' : '🔌 USB'}
          </span>
        </div>

        <div class="device-meta-row">
          <span class="meta-item">📦 ${escapeHtml(osVersion)}</span>
          <span class="battery-pill">🔋 ${batteryText}</span>
          ${device.ip_address ? `<span class="meta-item">🌐 ${escapeHtml(device.ip_address)}</span>` : ''}
        </div>

        <div class="device-card-actions">
          <button class="btn btn-secondary btn-sm flex-1 btn-select-dev" onclick="selectDevice('${device.serial}')">
            🛠️ Open Tools
          </button>
          ${isWireless ? `
            <button class="btn btn-outline-danger btn-sm" onclick="disconnectDevice('${device.serial}')" title="Disconnect">
              Disconnect
            </button>
          ` : `
            <button class="btn btn-accent btn-sm" onclick="switchUsbDevice('${device.serial}')" title="Switch to Wi-Fi">
              ⚡ To Wi-Fi
            </button>
          `}
        </div>
      </div>
    `;
  }).join('');
}

function updateUsbStatus(devices) {
  const usbDevs = devices.filter(d => !d.is_wireless);
  const dot = document.querySelector('#usbDetectedContainer .dot-indicator');
  if (usbDevs.length > 0) {
    elements.usbDetectedLabel.innerHTML = `<strong>${usbDevs.length} USB device(s) ready:</strong> ${escapeHtml(usbDevs.map(d => d.model).join(', '))}`;
    if (dot) dot.classList.add('active');
  } else {
    elements.usbDetectedLabel.textContent = 'No USB device connected yet. Plug in your phone to switch.';
    if (dot) dot.classList.remove('active');
  }
}

window.selectDevice = function(serial) {
  selectedDeviceSerial = serial;
  const dev = currentDevices.find(d => d.serial === serial);
  if (!dev) return;

  elements.activeDeviceTitle = document.getElementById('activeDeviceTitle');
  elements.activeDeviceSerial = document.getElementById('activeDeviceSerial');
  if (elements.activeDeviceTitle) elements.activeDeviceTitle.textContent = `${dev.model || 'Device'} Tools`;
  if (elements.activeDeviceSerial) elements.activeDeviceSerial.textContent = dev.serial;

  elements.deviceControlCenter.classList.remove('hidden');

  // Highlight active card
  document.querySelectorAll('.device-card').forEach(card => {
    if (card.getAttribute('data-serial') === serial) {
      card.classList.add('active-selected');
    } else {
      card.classList.remove('active-selected');
    }
  });

  // If Battery tab is active, refresh battery stats
  const batteryTabActive = document.querySelector('.ctrl-subtab[data-subtab="subtab-battery"]')?.classList.contains('active');
  if (batteryTabActive) {
    fetchBatteryDiagnostics(true);
  }
};

// ==========================================================================
// Pairing & Connecting
// ==========================================================================

function setupEventListeners() {

  // Auto Install ADB
  if (elements.btnAutoInstallAdb) {
    elements.btnAutoInstallAdb.addEventListener('click', installAdb);
  }
  if (elements.btnReinstallAdb) {
    elements.btnReinstallAdb.addEventListener('click', installAdb);
  }

  // Refresh
  elements.btnRefreshDevices.addEventListener('click', () => {
    fetchDevices();
    showToast('Refreshing devices...', 'info');
  });
  if (elements.btnStudioRefresh) {
    elements.btnStudioRefresh.addEventListener('click', () => fetchDevices());
  }

  // Pair Form
  elements.pairForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const ipPort = elements.pairIpPort.value.trim();
    const code = elements.pairCode.value.trim();
    const nickname = elements.pairNickname.value.trim();

    if (!ipPort || !code) {
      showToast('Please provide IP:Port and 6-digit pairing code', 'error');
      return;
    }

    elements.btnPairSubmit.disabled = true;
    elements.btnPairSubmit.innerHTML = `<span class="spinner"></span> Pairing...`;

    try {
      const res = await fetch(`${API_BASE}/api/pair`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ip_port: ipPort, code, nickname })
      });
      const data = await res.json();

      if (data.success) {
        showToast(data.message, 'success');
        fetchHistory();
        if (data.ip) {
          elements.connectIpPort.value = `${data.ip}:`;
          elements.connectIpPort.focus();
        }
      } else {
        showToast(data.message, 'error');
      }
    } catch (err) {
      showToast('Failed to send pairing request: ' + err.message, 'error');
    } finally {
      elements.btnPairSubmit.disabled = false;
      elements.btnPairSubmit.innerHTML = `
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M5 12.55a11 11 0 0 1 14.08 0"></path>
          <path d="M8.53 16.11a6 6 0 0 1 6.95 0"></path>
          <line x1="12" y1="20" x2="12.01" y2="20" stroke-width="2.5"></line>
        </svg> Pair Device
      `;
    }
  });

  // Connect Form
  elements.connectForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const ipPort = elements.connectIpPort.value.trim();

    if (!ipPort) {
      showToast('Please enter IP and Port to connect', 'error');
      return;
    }

    elements.btnConnectSubmit.disabled = true;
    elements.btnConnectSubmit.innerHTML = `<span class="spinner"></span> Connecting...`;

    try {
      const res = await fetch(`${API_BASE}/api/connect`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ip_port: ipPort })
      });
      const data = await res.json();

      if (data.success) {
        showToast(data.message, 'success');
        fetchDevices();
        fetchHistory();
      } else {
        const hintText = data.hint ? ` - ${data.hint}` : '';
        showToast(data.message + hintText, 'error');
      }
    } catch (err) {
      showToast('Connection request error: ' + err.message, 'error');
    } finally {
      elements.btnConnectSubmit.disabled = false;
      elements.btnConnectSubmit.innerHTML = `
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <polyline points="20 6 9 17 4 12"></polyline>
        </svg> Connect
      `;
    }
  });

  // Auto Pair & Connect Sequence Button
  elements.btnPairAndConnectAll.addEventListener('click', async () => {
    const pairIpPort = elements.pairIpPort.value.trim();
    const code = elements.pairCode.value.trim();

    if (!pairIpPort || !code) {
      showToast('Please fill in the pairing IP:Port and 6-digit code above first.', 'error');
      elements.pairIpPort.focus();
      return;
    }

    showToast('Initiating automated Pair & Connect sequence...', 'info');

    // Step 1: Pair
    const pairRes = await fetch(`${API_BASE}/api/pair`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ ip_port: pairIpPort, code })
    });
    const pairData = await pairRes.json();

    if (!pairData.success) {
      showToast(`Pairing step failed: ${pairData.message}`, 'error');
      return;
    }

    showToast('Pairing succeeded! Attempting connection...', 'success');

    // Step 2: Connect
    const connIp = elements.connectIpPort.value.trim() || pairIpPort;
    const connRes = await fetch(`${API_BASE}/api/connect`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ ip_port: connIp })
    });
    const connData = await connRes.json();

    if (connData.success) {
      showToast(`🎉 Full connection established to ${connIp}!`, 'success');
      fetchDevices();
      fetchHistory();
    } else {
      showToast(`Pairing OK, but connection failed on ${connIp}. Check connection port on phone.`, 'error');
    }
  });

  // USB to Wireless Switch
  elements.btnSwitchUsbToWifi.addEventListener('click', async () => {
    elements.btnSwitchUsbToWifi.disabled = true;
    elements.btnSwitchUsbToWifi.innerHTML = `<span class="spinner"></span> Switching to Wireless...`;

    try {
      const res = await fetch(`${API_BASE}/api/usb-to-wifi`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({})
      });
      const data = await res.json();

      if (data.success) {
        showToast(data.message, 'success');
        fetchDevices();
      } else {
        showToast(data.message, 'error');
      }
    } catch (err) {
      showToast('USB switch failed: ' + err.message, 'error');
    } finally {
      elements.btnSwitchUsbToWifi.disabled = false;
      elements.btnSwitchUsbToWifi.innerHTML = `
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z"></path>
        </svg> Convert to Wireless ADB Now
      `;
    }
  });

  // Disconnect All
  elements.btnDisconnectAll.addEventListener('click', async () => {
    if (!confirm('Disconnect all wireless ADB devices?')) return;
    try {
      const res = await fetch(`${API_BASE}/api/disconnect`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({})
      });
      const data = await res.json();
      showToast(data.message || 'Disconnected', 'info');
      fetchDevices();
    } catch (err) {
      showToast('Error disconnecting: ' + err.message, 'error');
    }
  });

  // Screenshot Studio
  elements.btnTakeScreenshot.addEventListener('click', takeScreenshot);
  elements.btnDownloadScreenshot.addEventListener('click', downloadScreenshot);
  elements.btnCopyScreenshot.addEventListener('click', copyScreenshotToClipboard);

  // Logcat Studio
  elements.btnFetchLogcat.addEventListener('click', fetchLogcat);
  elements.btnClearLogcat.addEventListener('click', () => {
    elements.logcatOutput.innerHTML = '<div class="log-line info">Console cleared.</div>';
  });

  // APK Sideload
  elements.btnSelectApk.addEventListener('click', () => elements.apkFileInput.click());
  elements.apkFileInput.addEventListener('change', (e) => {
    if (e.target.files && e.target.files[0]) {
      uploadAndInstallApk(e.target.files[0]);
    }
  });

  elements.apkDropzone.addEventListener('dragover', (e) => {
    e.preventDefault();
    elements.apkDropzone.classList.add('dragover');
  });
  elements.apkDropzone.addEventListener('dragleave', () => {
    elements.apkDropzone.classList.remove('dragover');
  });
  elements.apkDropzone.addEventListener('drop', (e) => {
    e.preventDefault();
    elements.apkDropzone.classList.remove('dragover');
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const file = e.dataTransfer.files[0];
      if (file.name.endsWith('.apk')) {
        uploadAndInstallApk(file);
      } else {
        showToast('Please select a valid .apk file', 'error');
      }
    }
  });

  // Remote Control Key Events
  document.querySelectorAll('.btn-control').forEach(btn => {
    btn.addEventListener('click', async () => {
      if (!selectedDeviceSerial) {
        showToast('Select a connected device first', 'error');
        return;
      }
      const key = btn.getAttribute('data-key');
      const cmd = btn.getAttribute('data-cmd');

      let command = cmd;
      if (key) {
        command = `input keyevent ${key}`;
      }
      if (command) {
        runShellCmd(command);
      }
    });
  });

  // Custom Shell Runner
  elements.btnRunShell.addEventListener('click', () => {
    const cmd = elements.customShellCmd.value.trim();
    if (cmd) runShellCmd(cmd);
  });
  elements.customShellCmd.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') {
      const cmd = elements.customShellCmd.value.trim();
      if (cmd) runShellCmd(cmd);
    }
  });

  // Scanner
  elements.btnStartScan.addEventListener('click', startNetworkScan);

  // Restart ADB Server
  elements.btnRestartAdb.addEventListener('click', async () => {
    showToast('Restarting ADB server daemon...', 'info');
    try {
      const res = await fetch(`${API_BASE}/api/restart-adb`, { method: 'POST' });
      const data = await res.json();
      showToast(data.message, data.success ? 'success' : 'error');
      fetchDevices();
    } catch (err) {
      showToast('Restart failed: ' + err.message, 'error');
    }
  });

  // Quick Send Text
  if (elements.btnSendQuickText) {
    elements.btnSendQuickText.addEventListener('click', sendQuickText);
  }
  if (elements.inputQuickText) {
    elements.inputQuickText.addEventListener('keydown', (e) => {
      if (e.key === 'Enter') sendQuickText();
    });
  }

  // Screen Timeout & Keep Awake
  if (elements.btnApplyScreenTimeout) {
    elements.btnApplyScreenTimeout.addEventListener('click', applyScreenTimeout);
  }

  // Dark Mode Switcher
  if (elements.btnDarkModeOn) {
    elements.btnDarkModeOn.addEventListener('click', () => setDarkMode(true));
  }
  if (elements.btnDarkModeOff) {
    elements.btnDarkModeOff.addEventListener('click', () => setDarkMode(false));
  }

  // Battery Telemetry
  if (elements.btnRefreshBattery) {
    elements.btnRefreshBattery.addEventListener('click', () => fetchBatteryDiagnostics(false));
  }
}

// ==========================================================================
// Device Action Helpers
// ==========================================================================

window.disconnectDevice = async function(serial) {
  try {
    const res = await fetch(`${API_BASE}/api/disconnect`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ ip_port: serial })
    });
    const data = await res.json();
    showToast(data.message || `Disconnected ${serial}`, 'info');
    fetchDevices();
  } catch (err) {
    showToast('Disconnect error: ' + err.message, 'error');
  }
};

window.switchUsbDevice = async function(serial) {
  try {
    showToast(`Converting ${serial} to wireless TCP/IP mode...`, 'info');
    const res = await fetch(`${API_BASE}/api/usb-to-wifi`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ serial })
    });
    const data = await res.json();
    showToast(data.message, data.success ? 'success' : 'error');
    fetchDevices();
  } catch (err) {
    showToast('Switch error: ' + err.message, 'error');
  }
};

// ==========================================================================
// History Management
// ==========================================================================

async function fetchHistory() {
  try {
    const res = await fetch(`${API_BASE}/api/history`);
    const data = await res.json();
    renderHistory(data.history || []);
  } catch (err) {
    console.error('Failed to load history', err);
  }
}

function renderHistory(items) {
  if (items.length === 0) {
    elements.historyList.innerHTML = `<div class="empty-hint">No saved devices yet. Connect a device to save it here!</div>`;
    return;
  }

  elements.historyList.innerHTML = items.map(item => `
    <div class="history-item" onclick="fillFromHistory('${item.ip}', '${item.port}')">
      <div class="history-info">
        <span class="history-title">${escapeHtml(item.nickname || 'Android Device')}</span>
        <span class="history-ip">${escapeHtml(item.ip)}:${escapeHtml(item.port)}</span>
      </div>
      <button class="history-btn-del" onclick="event.stopPropagation(); deleteHistoryItem('${item.ip}')" title="Remove">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <polyline points="3 6 5 6 21 6"></polyline>
          <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
        </svg>
      </button>
    </div>
  `).join('');
}

window.fillFromHistory = function(ip, port) {
  elements.connectIpPort.value = `${ip}:${port}`;
  elements.pairIpPort.value = `${ip}:`;
  elements.connectIpPort.focus();
  showToast(`Filled IP ${ip} from history`, 'info');
};

window.deleteHistoryItem = async function(ip) {
  try {
    const res = await fetch(`${API_BASE}/api/history/delete`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ ip })
    });
    const data = await res.json();
    renderHistory(data.history || []);
  } catch (err) {
    showToast('Failed to delete history item', 'error');
  }
};

// ==========================================================================
// Tool Features (Screenshot, Logcat, APK, Shell)
// ==========================================================================

async function takeScreenshot() {
  if (!selectedDeviceSerial) {
    showToast('Select a device first', 'error');
    return;
  }

  elements.btnTakeScreenshot.disabled = true;
  elements.btnTakeScreenshot.innerHTML = `<span class="spinner"></span> Capturing...`;

  try {
    const url = `${API_BASE}/api/screenshot?serial=${encodeURIComponent(selectedDeviceSerial)}&t=${Date.now()}`;
    const res = await fetch(url);
    if (!res.ok) {
      const errData = await res.json();
      throw new Error(errData.error || 'Failed to capture screenshot');
    }

    const blob = await res.blob();
    const blobUrl = URL.createObjectURL(blob);

    elements.screenshotImg.src = blobUrl;
    elements.screenshotImg.classList.remove('hidden');
    elements.screenshotPlaceholder.classList.add('hidden');
    elements.btnDownloadScreenshot.disabled = false;
    elements.btnCopyScreenshot.disabled = false;

    showToast('Screenshot captured successfully!', 'success');
  } catch (err) {
    showToast(err.message, 'error');
  } finally {
    elements.btnTakeScreenshot.disabled = false;
    elements.btnTakeScreenshot.innerHTML = `
      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <path d="M23 19a2 2 0 0 1-2 2H3a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h4l2-3h6l2 3h4a2 2 0 0 1 2 2z"></path>
        <circle cx="12" cy="13" r="4"></circle>
      </svg> Capture Screenshot
    `;
  }
}

function downloadScreenshot() {
  if (!elements.screenshotImg.src) return;
  const a = document.createElement('a');
  a.href = elements.screenshotImg.src;
  a.download = `screenshot_${selectedDeviceSerial || 'android'}_${Date.now()}.png`;
  a.click();
}

async function copyScreenshotToClipboard() {
  if (!elements.screenshotImg.src) return;
  try {
    const res = await fetch(elements.screenshotImg.src);
    const blob = await res.blob();
    await navigator.clipboard.write([
      new ClipboardItem({ 'image/png': blob })
    ]);
    showToast('Screenshot copied to clipboard!', 'success');
  } catch (err) {
    showToast('Could not copy to clipboard: ' + err.message, 'error');
  }
}

async function fetchLogcat() {
  if (!selectedDeviceSerial) {
    showToast('Select a device first', 'error');
    return;
  }

  const lines = elements.logcatLinesSelect.value;
  const filterStr = elements.logcatSearch.value.trim();

  elements.btnFetchLogcat.disabled = true;
  elements.btnFetchLogcat.textContent = 'Fetching...';

  try {
    const query = new URLSearchParams({
      serial: selectedDeviceSerial,
      lines: lines,
      filter: filterStr
    });
    const res = await fetch(`${API_BASE}/api/logcat?${query.toString()}`);
    const data = await res.json();

    if (data.success && data.logs) {
      if (data.logs.length === 0) {
        elements.logcatOutput.innerHTML = `<div class="log-line info">No logcat output matching filter "${filterStr}".</div>`;
      } else {
        elements.logcatOutput.innerHTML = data.logs.map(line => {
          let css = 'log-line';
          if (line.includes(' E ') || line.includes(' E/')) css += ' error';
          else if (line.includes(' W ') || line.includes(' W/')) css += ' warn';
          else if (line.includes(' I ') || line.includes(' I/')) css += ' info';
          return `<div class="${css}">${escapeHtml(line)}</div>`;
        }).join('');
        elements.logcatOutput.scrollTop = elements.logcatOutput.scrollHeight;
      }
    } else {
      elements.logcatOutput.innerHTML = `<div class="log-line error">${escapeHtml(data.error || 'Failed to fetch logs')}</div>`;
    }
  } catch (err) {
    showToast('Logcat fetch error: ' + err.message, 'error');
  } finally {
    elements.btnFetchLogcat.disabled = false;
    elements.btnFetchLogcat.textContent = 'Fetch Logs';
  }
}

async function uploadAndInstallApk(file) {
  if (!selectedDeviceSerial) {
    showToast('Select a target device first', 'error');
    return;
  }

  elements.apkInstallStatus.classList.remove('hidden');
  elements.apkInstallStatus.innerHTML = `<span class="spinner"></span> Uploading and installing <strong>${escapeHtml(file.name)}</strong> wirelessly...`;

  const formData = new FormData();
  formData.append('serial', selectedDeviceSerial);
  formData.append('file', file);

  try {
    const res = await fetch(`${API_BASE}/api/upload-apk`, {
      method: 'POST',
      body: formData
    });
    const data = await res.json();

    if (data.success) {
      elements.apkInstallStatus.innerHTML = `✅ <strong>Success:</strong> ${escapeHtml(data.message)}`;
      showToast('APK installed successfully!', 'success');
    } else {
      elements.apkInstallStatus.innerHTML = `❌ <strong>Failed:</strong> ${escapeHtml(data.message)}`;
      showToast(data.message, 'error');
    }
  } catch (err) {
    elements.apkInstallStatus.innerHTML = `❌ <strong>Error:</strong> ${escapeHtml(err.message)}`;
    showToast('APK install failed: ' + err.message, 'error');
  }
}

async function runShellCmd(cmd) {
  if (!selectedDeviceSerial) {
    showToast('Select a device first', 'error');
    return;
  }

  try {
    const res = await fetch(`${API_BASE}/api/shell`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ serial: selectedDeviceSerial, command: cmd })
    });
    const data = await res.json();

    elements.shellOutput.classList.remove('hidden');
    elements.shellOutput.textContent = data.output || '(Command executed successfully with no output)';
  } catch (err) {
    showToast('Shell execution error: ' + err.message, 'error');
  }
}

// ==========================================================================
// Quick Send Text to Phone
// ==========================================================================

async function sendQuickText() {
  if (!selectedDeviceSerial) {
    showToast('Select a connected device first', 'error');
    return;
  }
  const text = elements.inputQuickText ? elements.inputQuickText.value.trim() : '';
  if (!text) {
    showToast('Please type some text to send', 'info');
    return;
  }

  if (elements.btnSendQuickText) {
    elements.btnSendQuickText.disabled = true;
    elements.btnSendQuickText.innerHTML = `<span class="spinner"></span> Sending...`;
  }

  try {
    const res = await fetch(`${API_BASE}/api/input-text`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ serial: selectedDeviceSerial, text })
    });
    const data = await res.json();
    if (data.success) {
      showToast('Text typed directly into phone!', 'success');
      if (elements.inputQuickText) elements.inputQuickText.value = '';
    } else {
      showToast(data.message || 'Failed to send text', 'error');
    }
  } catch (err) {
    showToast('Failed to send text: ' + err.message, 'error');
  } finally {
    if (elements.btnSendQuickText) {
      elements.btnSendQuickText.disabled = false;
      elements.btnSendQuickText.textContent = 'Send Text';
    }
  }
}

// ==========================================================================
// Hardware & Display Utilities
// ==========================================================================

async function applyScreenTimeout() {
  if (!selectedDeviceSerial) {
    showToast('Select a connected device first', 'error');
    return;
  }

  const val = elements.selectScreenTimeout ? elements.selectScreenTimeout.value : '30000';
  const isStayOn = val === 'stayon';
  const timeoutMs = isStayOn ? 0 : parseInt(val, 10);

  if (elements.btnApplyScreenTimeout) {
    elements.btnApplyScreenTimeout.disabled = true;
  }

  try {
    const res = await fetch(`${API_BASE}/api/screen-timeout`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        serial: selectedDeviceSerial,
        timeout_ms: timeoutMs,
        stayon: isStayOn
      })
    });
    const data = await res.json();
    if (data.success) {
      showToast(data.message || 'Screen timeout applied', 'success');
    } else {
      showToast(data.message || 'Failed to set screen timeout', 'error');
    }
  } catch (err) {
    showToast('Screen timeout error: ' + err.message, 'error');
  } finally {
    if (elements.btnApplyScreenTimeout) {
      elements.btnApplyScreenTimeout.disabled = false;
    }
  }
}

async function setDarkMode(enable) {
  if (!selectedDeviceSerial) {
    showToast('Select a connected device first', 'error');
    return;
  }

  try {
    const res = await fetch(`${API_BASE}/api/dark-mode`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ serial: selectedDeviceSerial, enable })
    });
    const data = await res.json();
    if (data.success) {
      showToast(data.message || `Dark mode ${enable ? 'enabled' : 'disabled'}`, 'success');
      if (elements.btnDarkModeOn && elements.btnDarkModeOff) {
        elements.btnDarkModeOn.classList.toggle('active', enable);
        elements.btnDarkModeOff.classList.toggle('active', !enable);
      }
    } else {
      showToast(data.message || 'Failed to toggle dark mode', 'error');
    }
  } catch (err) {
    showToast('Dark mode error: ' + err.message, 'error');
  }
}

// ==========================================================================
// Battery Telemetry & Diagnostics
// ==========================================================================

async function fetchBatteryDiagnostics(silent = false) {
  if (!selectedDeviceSerial) {
    if (!silent) showToast('Select a connected device first', 'info');
    return;
  }

  if (elements.btnRefreshBattery) {
    elements.btnRefreshBattery.disabled = true;
  }

  try {
    const res = await fetch(`${API_BASE}/api/battery?serial=${encodeURIComponent(selectedDeviceSerial)}`);
    const data = await res.json();

    if (!data.success) {
      if (!silent) showToast(data.message || 'Could not query battery status', 'error');
      return;
    }

    // Battery %
    const level = data.level || 0;
    if (elements.batteryPercentText) {
      elements.batteryPercentText.textContent = `${level}%`;
    }

    // Fill bar
    if (elements.batteryBarFill) {
      elements.batteryBarFill.style.width = `${level}%`;
      elements.batteryBarFill.classList.remove('warning', 'danger');
      if (level <= 20) {
        elements.batteryBarFill.classList.add('danger');
      } else if (level <= 45) {
        elements.batteryBarFill.classList.add('warning');
      }
    }

    // Status Pill
    if (elements.batteryStatusPill) {
      elements.batteryStatusPill.textContent = data.status || 'Active';
      elements.batteryStatusPill.className = 'status-pill ' + 
        (data.status === 'Charging' ? 'status-ready' : 'status-ip');
    }

    // Power Source
    if (elements.batteryPowerSourceText) {
      elements.batteryPowerSourceText.textContent = `Power Source: ${data.power_source || 'Battery'}`;
    }

    // Metrics
    if (elements.metricTempText) {
      elements.metricTempText.textContent = `${data.temperature_c} °C`;
      if (data.temperature_c > 42) {
        elements.metricTempText.style.color = '#ef4444';
      } else {
        elements.metricTempText.style.color = '#fff';
      }
    }
    if (elements.metricTempSub) {
      elements.metricTempSub.textContent = `${data.temperature_f} °F`;
    }
    if (elements.metricHealthText) {
      elements.metricHealthText.textContent = data.health || 'Good';
    }
    if (elements.metricVoltageText) {
      elements.metricVoltageText.textContent = `${data.voltage_v} V`;
    }
    if (elements.metricTechText) {
      elements.metricTechText.textContent = data.technology || 'Li-ion';
    }

    if (!silent) {
      showToast('Battery telemetry refreshed', 'success');
    }
  } catch (err) {
    if (!silent) showToast('Battery query error: ' + err.message, 'error');
  } finally {
    if (elements.btnRefreshBattery) {
      elements.btnRefreshBattery.disabled = false;
    }
  }
}

// ==========================================================================
// Network Scanner
// ==========================================================================

async function startNetworkScan() {
  elements.scanLoading.classList.remove('hidden');
  elements.btnStartScan.disabled = true;

  try {
    const res = await fetch(`${API_BASE}/api/scan`);
    const data = await res.json();

    const mdns = data.mdns || [];
    const subnet = data.subnet || [];

    if (mdns.length === 0 && subnet.length === 0) {
      elements.scanResults.innerHTML = `
        <div class="empty-hint">No active Android ADB services discovered. Ensure Wireless Debugging is enabled on your phone and connected to the same Wi-Fi.</div>
      `;
    } else {
      let html = '';
      subnet.forEach(ipPort => {
        html += `
          <div class="scan-result-card">
            <div>
              <div class="scan-result-ip">🌐 ${escapeHtml(ipPort)}</div>
              <span class="scan-result-type">TCP/IP Port 5555</span>
            </div>
            <div style="display: flex; gap: 8px;">
              <button class="btn btn-secondary btn-sm" onclick="pairWithDiscovered('${ipPort}')">⚡ Pair</button>
              <button class="btn btn-accent btn-sm" onclick="connectToDiscovered('${ipPort}')">🔗 Connect</button>
            </div>
          </div>
        `;
      });

      mdns.forEach(item => {
        html += `
          <div class="scan-result-card">
            <div>
              <div class="scan-result-ip">📡 ${escapeHtml(item.address)}</div>
              <span class="scan-result-type">mDNS: ${escapeHtml(item.name)} (${escapeHtml(item.type)})</span>
            </div>
            <div style="display: flex; gap: 8px;">
              <button class="btn btn-secondary btn-sm" onclick="pairWithDiscovered('${item.address}')">⚡ Pair</button>
              <button class="btn btn-accent btn-sm" onclick="connectToDiscovered('${item.address}')">🔗 Connect</button>
            </div>
          </div>
        `;
      });

      elements.scanResults.innerHTML = html;
      showToast(`Scan complete: Found ${subnet.length + mdns.length} potential device(s)`, 'success');
    }
  } catch (err) {
    showToast('Scan failed: ' + err.message, 'error');
  } finally {
    elements.scanLoading.classList.add('hidden');
    elements.btnStartScan.disabled = false;
  }
}

window.pairWithDiscovered = function(ipPort) {
  elements.pairIpPort.value = ipPort;
  document.querySelector('.nav-tab[data-tab="tab-pairing"]').click();
  if (elements.pairCode) {
    elements.pairCode.focus();
  }
  showToast('Enter the 6-digit pairing code from your phone screen, then click Pair Device!', 'info');
};

window.connectToDiscovered = function(ipPort) {
  elements.connectIpPort.value = ipPort;
  document.querySelector('.nav-tab[data-tab="tab-pairing"]').click();
  elements.connectForm.dispatchEvent(new Event('submit'));
};

// ==========================================================================
// Auto Install ADB
// ==========================================================================

async function installAdb() {
  showToast('Downloading official Google Android Platform-Tools... This may take a few seconds.', 'info');
  if (elements.btnAutoInstallAdb) {
    elements.btnAutoInstallAdb.disabled = true;
    elements.btnAutoInstallAdb.innerHTML = `<span class="spinner"></span> Downloading ADB...`;
  }
  if (elements.btnReinstallAdb) {
    elements.btnReinstallAdb.disabled = true;
    elements.btnReinstallAdb.innerHTML = `<span class="spinner"></span> Downloading...`;
  }

  try {
    const res = await fetch(`${API_BASE}/api/install-adb`, { method: 'POST' });
    const data = await res.json();

    if (data.success) {
      showToast('Android Platform-Tools installed successfully!', 'success');
      checkStatus();
      fetchDevices();
    } else {
      showToast(data.message || 'Failed to install platform-tools', 'error');
    }
  } catch (err) {
    showToast('Installation request failed: ' + err.message, 'error');
  } finally {
    if (elements.btnAutoInstallAdb) {
      elements.btnAutoInstallAdb.disabled = false;
      elements.btnAutoInstallAdb.textContent = 'Auto-Download ADB';
    }
    if (elements.btnReinstallAdb) {
      elements.btnReinstallAdb.disabled = false;
      elements.btnReinstallAdb.textContent = 'Re-download Official ADB';
    }
  }
}

// ==========================================================================
// Toast Notification System
// ==========================================================================

function showToast(message, type = 'info') {
  const toast = document.createElement('div');
  toast.className = `toast toast-${type}`;

  let icon = 'ℹ️';
  if (type === 'success') icon = '✅';
  if (type === 'error') icon = '❌';

  toast.innerHTML = `<span>${icon}</span> <span>${escapeHtml(message)}</span>`;
  elements.toastContainer.appendChild(toast);

  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transform = 'translateX(30px)';
    toast.style.transition = 'all 0.3s ease';
    setTimeout(() => toast.remove(), 300);
  }, 4500);
}

function escapeHtml(str) {
  if (!str) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}
