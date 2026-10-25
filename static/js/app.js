/**
 * Optimal UAV Task Offloading Simulator - Client Controller
 * Pure Vanilla JavaScript + Chart.js + Canvas Network Visualizer
 */

// Application State
const state = {
  config: {},
  presets: {},
  theories: {},
  currentTopology: null,
  charts: {},
  activeAlgorithm: 'greedy',
  lastComparison: null
};

// DOM References
const elements = {
  statUAVCount: document.getElementById('statUAVCount'),
  statTaskCount: document.getElementById('statTaskCount'),
  statEdgeCount: document.getElementById('statEdgeCount'),
  statCloudCount: document.getElementById('statCloudCount'),
  presetSelect: document.getElementById('presetSelect'),
  inputNumUAVs: document.getElementById('inputNumUAVs'),
  inputNumTasks: document.getElementById('inputNumTasks'),
  inputEdgeCpu: document.getElementById('inputEdgeCpu'),
  inputCloudCpu: document.getElementById('inputCloudCpu'),
  inputSeed: document.getElementById('inputSeed'),
  inputDPStep: document.getElementById('inputDPStep'),
  checkBenchmarkWorkload: document.getElementById('checkBenchmarkWorkload'),
  btnUpdateWorkload: document.getElementById('btnUpdateWorkload'),
  btnCompareAll: document.getElementById('btnCompareAll'),
  btnHealth: document.getElementById('btnHealth'),
  healthStatus: document.getElementById('healthStatus'),
  alertBanner: document.getElementById('alertBanner'),
  alertMessage: document.getElementById('alertMessage'),
  alertIcon: document.getElementById('alertIcon'),
  alertClose: document.getElementById('alertClose'),
  activeAlgorithmTitle: document.getElementById('activeAlgorithmTitle'),
  optimalityBadge: document.getElementById('optimalityBadge'),
  metricTotalDelay: document.getElementById('metricTotalDelay'),
  metricMeanDelay: document.getElementById('metricMeanDelay'),
  metricTasksSummary: document.getElementById('metricTasksSummary'),
  metricOnTime: document.getElementById('metricOnTime'),
  metricDeadlineMisses: document.getElementById('metricDeadlineMisses'),
  metricMakespan: document.getElementById('metricMakespan'),
  metricServerUtil: document.getElementById('metricServerUtil'),
  metricUavUtil: document.getElementById('metricUavUtil'),
  metricExecTime: document.getElementById('metricExecTime'),
  metricStates: document.getElementById('metricStates'),
  metricEnergy: document.getElementById('metricEnergy'),
  allocationTableBody: document.getElementById('allocationTableBody'),
  allocationCountBadge: document.getElementById('allocationCountBadge'),
  networkCanvas: document.getElementById('networkCanvas')
};

// ==========================================
// Initialization
// ==========================================
document.addEventListener('DOMContentLoaded', async () => {
  setupEventListeners();
  await loadInitialConfiguration();
  // Auto-run baseline Greedy simulation
  await runAlgorithm('greedy');
  // Auto-run initial comparison to populate charts
  await runComparison();
});

function setupEventListeners() {
  // Preset change handler
  elements.presetSelect.addEventListener('change', onPresetChange);

  // Regenerate workload
  elements.btnUpdateWorkload.addEventListener('click', async () => {
    elements.checkBenchmarkWorkload.checked = false;
    await runAlgorithm(state.activeAlgorithm);
    await runComparison();
  });

  // Algorithm buttons
  document.querySelectorAll('.btn-algo').forEach(btn => {
    btn.addEventListener('click', () => {
      const algo = btn.getAttribute('data-algo');
      runAlgorithm(algo);
    });
  });

  // Compare All button
  elements.btnCompareAll.addEventListener('click', () => {
    runComparison();
  });

  // Health check button
  elements.btnHealth.addEventListener('click', checkHealth);

  // Alert banner close
  elements.alertClose.addEventListener('click', () => {
    elements.alertBanner.classList.add('hidden');
  });

  // Window resize re-draws canvas
  window.addEventListener('resize', () => {
    if (state.currentTopology) {
      drawNetwork(state.currentTopology);
    }
  });
}

// ==========================================
// API Interaction
// ==========================================
async function loadInitialConfiguration() {
  try {
    const res = await fetch('/api/config');
    const data = await res.json();
    state.config = data.default_config;
    state.presets = data.presets;
    state.theories = data.algorithms;
    syncFormWithConfig(state.config);
  } catch (err) {
    showAlert('Failed to connect to backend configuration API. Ensure Flask is running.', 'error');
  }
}

async function checkHealth() {
  try {
    const res = await fetch('/api/health');
    const data = await res.json();
    if (data.status === 'healthy') {
      elements.healthStatus.textContent = 'Online';
      elements.healthStatus.className = 'status-indicator online';
      showAlert(`Backend health check OK: ${data.app} v${data.version}`, 'info');
    }
  } catch (err) {
    elements.healthStatus.textContent = 'Offline';
    elements.healthStatus.className = 'status-indicator text-danger';
    showAlert('Backend unreachable at http://127.0.0.1:5000', 'error');
  }
}

function getFormConfig() {
  return {
    num_uavs: parseInt(elements.inputNumUAVs.value, 10),
    num_tasks: parseInt(elements.inputNumTasks.value, 10),
    num_edge: 1,
    num_cloud: 1,
    edge_cpu_capacity: parseFloat(elements.inputEdgeCpu.value),
    cloud_cpu_capacity: parseFloat(elements.inputCloudCpu.value),
    random_seed: parseInt(elements.inputSeed.value, 10),
    discretization_step: parseFloat(elements.inputDPStep.value),
    use_benchmark_workload: elements.checkBenchmarkWorkload.checked
  };
}

function syncFormWithConfig(cfg) {
  elements.inputNumUAVs.value = cfg.num_uavs || 3;
  elements.inputNumTasks.value = cfg.num_tasks || 4;
  elements.inputEdgeCpu.value = cfg.edge_cpu_capacity || 10.0;
  elements.inputCloudCpu.value = cfg.cloud_cpu_capacity || 50.0;
  elements.inputSeed.value = cfg.random_seed || 42;
  elements.inputDPStep.value = cfg.discretization_step || 1.0;
  elements.checkBenchmarkWorkload.checked = !!cfg.use_benchmark_workload;

  elements.statUAVCount.textContent = cfg.num_uavs || 3;
  elements.statTaskCount.textContent = cfg.num_tasks || 4;
  elements.statEdgeCount.textContent = cfg.num_edge || 1;
  elements.statCloudCount.textContent = cfg.num_cloud || 1;
}

function onPresetChange(e) {
  const key = e.target.value;
  const preset = state.presets[key];
  if (!preset) return;
  syncFormWithConfig(preset);
  showAlert(`Loaded preset: ${preset.name} - ${preset.description}`, 'info');
  runAlgorithm(state.activeAlgorithm);
  runComparison();
}

// ==========================================
// Algorithm Execution
// ==========================================
async function runAlgorithm(algoKey) {
  state.activeAlgorithm = algoKey;
  const config = getFormConfig();

  // Optimistic UI feedback
  elements.activeAlgorithmTitle.textContent = formatAlgorithmName(algoKey);
  elements.statUAVCount.textContent = config.num_uavs;
  elements.statTaskCount.textContent = config.num_tasks;

  try {
    const res = await fetch('/api/simulate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ algorithm: algoKey, config: config })
    });

    const data = await res.json();

    if (!res.ok) {
      if (data.error === 'DP_INSTANCE_TOO_LARGE') {
        showAlert(
          `Exact DP Limit: ${data.message} ${data.recommendation}`,
          'warning'
        );
      } else {
        showAlert(`Error: ${data.error || 'Simulation execution failed.'}`, 'error');
      }
      return;
    }

    // Success: render results
    renderSimulationResult(data);
  } catch (err) {
    showAlert(`Network communication error: ${err.message}`, 'error');
  }
}

async function runComparison() {
  const config = getFormConfig();
  try {
    const res = await fetch('/api/compare', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ config: config })
    });

    const data = await res.json();
    if (!res.ok) {
      showAlert(`Comparison error: ${data.error || 'Failed to compare algorithms'}`, 'error');
      return;
    }

    state.lastComparison = data;
    renderComparisonCharts(data);
  } catch (err) {
    showAlert(`Comparison network error: ${err.message}`, 'error');
  }
}

// ==========================================
// UI Rendering Functions
// ==========================================
function renderSimulationResult(data) {
  const metrics = data.metrics;
  const allocations = data.allocations || [];

  // Update KPI Cards
  elements.activeAlgorithmTitle.textContent = data.algorithm;
  elements.statTaskCount.textContent = allocations.length;

  // Optimality Badge
  if (metrics.is_optimal) {
    elements.optimalityBadge.textContent = 'Mathematically Optimal (MMKP)';
    elements.optimalityBadge.className = 'badge badge-success';
  } else if (metrics.algorithm.includes('Greedy')) {
    elements.optimalityBadge.textContent = 'Heuristic (Local Optimum)';
    elements.optimalityBadge.className = 'badge badge-warning';
  } else {
    elements.optimalityBadge.textContent = 'Timeline Scheduling Heuristic';
    elements.optimalityBadge.className = 'badge badge-info';
  }

  // Metrics Boxes
  elements.metricTotalDelay.textContent = metrics.total_delay !== null ? `${metrics.total_delay.toFixed(2)} s` : '--';
  elements.metricMeanDelay.textContent = metrics.mean_delay !== null ? `Mean: ${metrics.mean_delay.toFixed(2)} s` : 'Mean: --';

  elements.metricTasksSummary.textContent = `${metrics.tasks_completed} / ${metrics.tasks_unallocated}`;
  elements.metricOnTime.textContent = `On-Time: ${metrics.on_time_tasks}`;

  elements.metricDeadlineMisses.textContent = `${metrics.deadline_misses}`;
  elements.metricMakespan.textContent = metrics.makespan ? `Makespan: ${metrics.makespan.toFixed(2)} s` : 'Single Batch';

  elements.metricServerUtil.textContent = `E: ${metrics.edge_cpu_utilization}% | C: ${metrics.cloud_cpu_utilization}%`;
  elements.metricUavUtil.textContent = `UAV CPU: ${metrics.uav_cpu_utilization}%`;

  elements.metricExecTime.textContent = `${metrics.execution_time_ms} ms`;
  elements.metricStates.textContent = metrics.dp_states_evaluated ? `DP States: ${metrics.dp_states_evaluated}` : 'Evaluated in 1-pass';

  elements.metricEnergy.textContent = `${metrics.total_energy || 0} J`;

  // Render Table
  renderAllocationsTable(allocations);

  // Update Network Topology
  if (data.network) {
    state.currentTopology = data.network;
    drawNetwork(data.network, allocations);
  }
}

function renderAllocationsTable(allocations) {
  elements.allocationCountBadge.textContent = `${allocations.length} Tasks`;
  elements.allocationTableBody.innerHTML = '';

  if (!allocations.length) {
    elements.allocationTableBody.innerHTML = `
      <tr><td colspan="10" class="empty-state">No tasks to display.</td></tr>
    `;
    return;
  }

  allocations.forEach(item => {
    const tr = document.createElement('tr');

    let statusBadgeClass = 'status-badge status-on-time';
    if (item.status === 'Missed Deadline') statusBadgeClass = 'status-badge status-missed';
    if (item.status === 'Infeasible') statusBadgeClass = 'status-badge status-infeasible';

    const delayStr = item.delay !== null && item.delay !== Infinity ? `${item.delay.toFixed(2)}s` : '∞ (Drop)';
    const waitStr = item.waiting_time ? ` (+${item.waiting_time.toFixed(2)}s wait)` : '';

    tr.innerHTML = `
      <td><strong>Task ${item.task_id}</strong></td>
      <td>UAV ${item.uav_id}</td>
      <td>${item.task_type}</td>
      <td><span class="location-tag">${item.location}</span></td>
      <td>${item.transmission_delay.toFixed(2)}s</td>
      <td>${item.network_latency.toFixed(2)}s</td>
      <td>${item.processing_delay.toFixed(2)}s</td>
      <td><strong>${delayStr}</strong><span style="font-size:0.75rem;color:#94a3b8">${waitStr}</span></td>
      <td>${item.deadline.toFixed(1)}s</td>
      <td><span class="${statusBadgeClass}">${item.status}</span></td>
    `;
    elements.allocationTableBody.appendChild(tr);
  });
}


// ==========================================
// Chart.js Comparative Visualizations
// ==========================================
function renderComparisonCharts(compData) {
  const results = compData.results;
  const labels = [];
  const delayData = [];
  const runtimeData = [];
  const completedData = [];
  const missedData = [];
  const edgeUtilData = [];
  const cloudUtilData = [];
  const uavUtilData = [];

  const algoKeys = ['greedy', 'dp', 'edf', 'priority', 'combined'];

  algoKeys.forEach(k => {
    const res = results[k];
    if (!res) return;

    const name = formatAlgorithmName(k);
    labels.push(name);

    if (res.status === 'unsupported') {
      delayData.push(0);
      runtimeData.push(0);
      completedData.push(0);
      missedData.push(0);
      edgeUtilData.push(0);
      cloudUtilData.push(0);
      uavUtilData.push(0);
    } else {
      const m = res.metrics;
      delayData.push(m.total_delay || 0);
      runtimeData.push(m.execution_time_ms || 0);
      completedData.push(m.tasks_completed || 0);
      missedData.push(m.deadline_misses || 0);
      edgeUtilData.push(m.edge_cpu_utilization || 0);
      cloudUtilData.push(m.cloud_cpu_utilization || 0);
      uavUtilData.push(m.uav_cpu_utilization || 0);
    }
  });

  // 1. Total Delay Chart
  updateChart('chartDelay', {
    type: 'bar',
    data: {
      labels: labels,
      datasets: [{
        label: 'Total Completion Delay (s)',
        data: delayData,
        backgroundColor: ['#00d2ff', '#6366f1', '#10b981', '#f59e0b', '#ec4899'],
        borderRadius: 4
      }]
    },
    options: getChartOptions('Total Delay (seconds)')
  });

  // 2. Runtime Chart
  updateChart('chartRuntime', {
    type: 'bar',
    data: {
      labels: labels,
      datasets: [{
        label: 'Execution Time (ms)',
        data: runtimeData,
        backgroundColor: '#38bdf8',
        borderRadius: 4
      }]
    },
    options: getChartOptions('Milliseconds (ms)')
  });

  // 3. Deadline Misses Chart
  updateChart('chartDeadlines', {
    type: 'bar',
    data: {
      labels: labels,
      datasets: [
        {
          label: 'Completed Tasks',
          data: completedData,
          backgroundColor: '#10b981',
          borderRadius: 4
        },
        {
          label: 'Deadline Misses',
          data: missedData,
          backgroundColor: '#ef4444',
          borderRadius: 4
        }
      ]
    },
    options: getChartOptions('Count')
  });

  // 4. Resource Utilization Chart
  updateChart('chartUtilization', {
    type: 'bar',
    data: {
      labels: labels,
      datasets: [
        { label: 'Edge CPU %', data: edgeUtilData, backgroundColor: '#10b981', borderRadius: 4 },
        { label: 'Cloud CPU %', data: cloudUtilData, backgroundColor: '#a78bfa', borderRadius: 4 },
        { label: 'UAV CPU %', data: uavUtilData, backgroundColor: '#38bdf8', borderRadius: 4 }
      ]
    },
    options: getChartOptions('CPU %')
  });
}

function getChartOptions(yAxisTitle) {
  return {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        labels: { color: '#94a3b8', font: { family: 'Outfit', size: 11 } }
      }
    },
    scales: {
      x: {
        ticks: { color: '#cbd5e1', font: { family: 'Outfit', size: 10 } },
        grid: { color: 'rgba(255, 255, 255, 0.05)' }
      },
      y: {
        title: { display: true, text: yAxisTitle, color: '#94a3b8', font: { size: 10 } },
        ticks: { color: '#94a3b8', font: { family: 'Outfit', size: 10 } },
        grid: { color: 'rgba(255, 255, 255, 0.05)' }
      }
    }
  };
}

function updateChart(canvasId, config) {
  if (state.charts[canvasId]) {
    state.charts[canvasId].destroy();
  }
  const canvas = document.getElementById(canvasId);
  if (!canvas) return;
  state.charts[canvasId] = new Chart(canvas, config);
}

// ==========================================
// Network Topology Canvas Visualizer
// ==========================================
function drawNetwork(topology, activeAllocations = []) {
  const canvas = elements.networkCanvas;
  if (!canvas) return;
  const ctx = canvas.getContext('2d');
  const dpr = window.devicePixelRatio || 1;

  // Adapt to container size
  const rect = canvas.getBoundingClientRect();
  canvas.width = rect.width * dpr;
  canvas.height = 260 * dpr;
  ctx.scale(dpr, dpr);

  const w = rect.width;
  const h = 260;

  ctx.clearRect(0, 0, w, h);

  const nodes = topology.nodes || [];
  const edges = topology.edges || [];

  // Group nodes by tier: UAVs (left), Edge (middle), Cloud (right)
  const uavNodes = nodes.filter(n => n.type === 'uav');
  const edgeNodes = nodes.filter(n => n.type === 'edge');
  const cloudNodes = nodes.filter(n => n.type === 'cloud');

  const positions = {};

  // Compute layout coordinates
  uavNodes.forEach((node, i) => {
    const spacing = h / (uavNodes.length + 1);
    positions[node.id] = { x: 70, y: spacing * (i + 1) };
  });

  edgeNodes.forEach((node, i) => {
    const spacing = h / (edgeNodes.length + 1);
    positions[node.id] = { x: w / 2, y: spacing * (i + 1) };
  });

  cloudNodes.forEach((node, i) => {
    const spacing = h / (cloudNodes.length + 1);
    positions[node.id] = { x: w - 70, y: spacing * (i + 1) };
  });

  // Draw Edges (Communication links with latencies)
  edges.forEach(edge => {
    const p1 = positions[edge.source];
    const p2 = positions[edge.target];
    if (!p1 || !p2) return;

    ctx.beginPath();
    ctx.moveTo(p1.x, p1.y);
    ctx.lineTo(p2.x, p2.y);
    ctx.strokeStyle = '#1e3359';
    ctx.lineWidth = 1.5;
    ctx.setLineDash([4, 4]);
    ctx.stroke();
    ctx.setLineDash([]);

    // Latency Label
    const midX = (p1.x + p2.x) / 2;
    const midY = (p1.y + p2.y) / 2;
    ctx.fillStyle = '#64748b';
    ctx.font = '10px "JetBrains Mono"';
    ctx.fillText(`${edge.latency.toFixed(1)}s`, midX - 10, midY - 6);
  });

  // Draw Nodes
  nodes.forEach(node => {
    const pos = positions[node.id];
    if (!pos) return;

    ctx.beginPath();
    let fillColor = '#38bdf8';
    let label = node.label;
    let radius = 16;

    if (node.type === 'edge') {
      fillColor = '#10b981';
      radius = 18;
    } else if (node.type === 'cloud') {
      fillColor = '#a78bfa';
      radius = 20;
    }

    // Outer glow ring
    ctx.arc(pos.x, pos.y, radius + 4, 0, Math.PI * 2);
    ctx.fillStyle = `${fillColor}22`;
    ctx.fill();

    // Node body
    ctx.beginPath();
    ctx.arc(pos.x, pos.y, radius, 0, Math.PI * 2);
    ctx.fillStyle = '#0d182e';
    ctx.fill();
    ctx.strokeStyle = fillColor;
    ctx.lineWidth = 2.5;
    ctx.stroke();

    // Node Label
    ctx.fillStyle = '#ffffff';
    ctx.font = '11px "Outfit"';
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.fillText(label, pos.x, pos.y + radius + 14);

    // Icon or short symbol inside
    ctx.fillStyle = fillColor;
    ctx.font = '12px "Outfit"';
    let symbol = '🛸';
    if (node.type === 'edge') symbol = '🏢';
    if (node.type === 'cloud') symbol = '☁️';
    ctx.fillText(symbol, pos.x, pos.y);
  });
}

// ==========================================
// Helper Utilities
// ==========================================
function formatAlgorithmName(algoKey) {
  const map = {
    greedy: 'Greedy Heuristic',
    dp: 'Exact Dynamic Programming',
    edf: 'Earliest Deadline First (EDF)',
    priority: 'Priority-Based Scheduling',
    combined: 'Combined Priority-Deadline'
  };
  return map[algoKey] || algoKey.toUpperCase();
}

function showAlert(message, type = 'error') {
  elements.alertBanner.classList.remove('hidden', 'info-style');
  if (type === 'info') {
    elements.alertBanner.classList.add('info-style');
    elements.alertIcon.textContent = 'ℹ️';
  } else if (type === 'warning') {
    elements.alertIcon.textContent = '⚠️';
  } else {
    elements.alertIcon.textContent = '❌';
  }
  elements.alertMessage.textContent = message;
}
