// Mock data service for simulating railway tracks state
// Simulates 6 railway tracks with real-time state changes

// Initial state for 6 railway tracks
let tracksState = [
  {
    id: 1,
    status: 'occupied',
    trainId: 'Rame-A',
    timestamp: new Date().toISOString(),
  },
  {
    id: 2,
    status: 'free',
    trainId: null,
    timestamp: null,
  },
  {
    id: 3,
    status: 'occupied',
    trainId: 'Rame-B',
    timestamp: new Date(Date.now() - 3600000).toISOString(), // 1 hour ago
  },
  {
    id: 4,
    status: 'free',
    trainId: null,
    timestamp: null,
  },
  {
    id: 5,
    status: 'anomaly',
    trainId: 'Rame-C',
    timestamp: new Date(Date.now() - 7200000).toISOString(), // 2 hours ago
  },
  {
    id: 6,
    status: 'occupied',
    trainId: 'Rame-D',
    timestamp: new Date(Date.now() - 1800000).toISOString(), // 30 minutes ago
  },
];

// Possible train IDs for simulation
const trainIds = ['Rame-A', 'Rame-B', 'Rame-C', 'Rame-D', 'Rame-E', 'Rame-F', 'TGV-2841', 'IC-1523', 'TER-9247'];

// Possible statuses with weights to bias simulation towards 'occupied'
const weightedStatuses = [
  { status: 'occupied', weight: 0.55 },
  { status: 'free', weight: 0.30 },
  { status: 'anomaly', weight: 0.15 },
];

// Plain list used for validations and manual setting
const statuses = ['free', 'occupied', 'anomaly'];

const pickStatus = () => {
  const r = Math.random();
  let cum = 0;
  for (const s of weightedStatuses) {
    cum += s.weight;
    if (r <= cum) return s.status;
  }
  return weightedStatuses[weightedStatuses.length - 1].status;
};

/**
 * Get current tracks state
 * @returns {Array} Array of 6 railway tracks with their current state
 */
export const getTracksState = () => {
  return [...tracksState]; // Return a copy to prevent external modifications
};

/**
 * Simulate random state change on a track
 * @private
 */
const simulateStateChange = () => {
  // Select a random track
  const trackIndex = Math.floor(Math.random() * tracksState.length);
  const track = tracksState[trackIndex];
  
  // Select a status (weighted) so that occupied states happen more often
  const newStatus = pickStatus();
  
  // Update track state
  track.status = newStatus;
  
  if (newStatus === 'occupied' || newStatus === 'anomaly') {
    // Assign a train ID if occupied or anomaly
    track.trainId = trainIds[Math.floor(Math.random() * trainIds.length)];
    track.timestamp = new Date().toISOString();
  } else {
    // Clear train ID if free
    track.trainId = null;
    track.timestamp = null;
  }
  
  console.log(`[MockData] Track ${track.id} state changed to: ${newStatus}`, track);
};

/**
 * Start simulating state changes every 3 seconds
 * Mimics a WebSocket flow with real-time updates
 * @param {Function} callback - Function to call when state changes (optional)
 * @returns {Function} Unsubscribe function to stop simulation
 */
// Single simulation loop with multiple subscribers support
let _simulationIntervalId = null;
const _subscribers = new Set();
let _simulationIntervalMs = 10000;

// Daily accumulators (milliseconds) per track id
let _currentDayAcc = {}; // { '1': ms, '2': ms }
let _previousDayAcc = {}; // persisted previous day totals
let _currentDay = new Date().toISOString().slice(0,10); // YYYY-MM-DD

// initialize accumulators with current tracks
const _initAccumulators = () => {
  _currentDayAcc = {};
  _previousDayAcc = _loadPreviousDayAcc();
  for (const t of tracksState) {
    _currentDayAcc[t.id] = _currentDayAcc[t.id] || 0;
    _previousDayAcc[t.id] = _previousDayAcc[t.id] || 0;
  }
};

const _loadPreviousDayAcc = () => {
  try {
    const raw = localStorage.getItem('mockdata_prev_day_acc');
    if (!raw) return {};
    return JSON.parse(raw);
  } catch {
    return {};
  }
};

const _savePreviousDayAcc = () => {
  try {
    localStorage.setItem('mockdata_prev_day_acc', JSON.stringify(_previousDayAcc));
  } catch {
    // ignore
  }
};

_initAccumulators();

export const startSimulation = (callback, intervalMs = 10000) => {
  if (callback && typeof callback === 'function') {
    _subscribers.add(callback);
  }

  // update configured interval if caller provided a value
  if (intervalMs && typeof intervalMs === 'number') _simulationIntervalMs = intervalMs;

  if (!_simulationIntervalId) {
    _simulationIntervalId = setInterval(() => {
      simulateStateChange();

      // update daily accumulators: for each occupied/anomaly track add intervalMs
      const now = new Date();
      const today = now.toISOString().slice(0,10);
      if (today !== _currentDay) {
        // roll over: move current -> previous, reset current
        _previousDayAcc = { ..._currentDayAcc };
        _currentDayAcc = {};
        _currentDay = today;
        _savePreviousDayAcc();
      }

      const snapshot = getTracksState();
      for (const t of snapshot) {
        if (t.status === 'occupied' || t.status === 'anomaly') {
          _currentDayAcc[t.id] = (_currentDayAcc[t.id] || 0) + _simulationIntervalMs;
        } else {
          _currentDayAcc[t.id] = _currentDayAcc[t.id] || 0;
        }
      }

      // notify all subscribers with a fresh snapshot
      for (const cb of _subscribers) {
        try {
          cb(snapshot);
        } catch (err) {
          console.error('[MockData] subscriber callback error', err);
        }
      }
    }, _simulationIntervalMs);

  console.log(`[MockData] Simulation started - state changes every ${_simulationIntervalMs} ms`);
  } else {
    console.log('[MockData] Simulation already running; added subscriber');
  }

  // Return unsubscribe function for this specific callback
  return () => {
    if (callback && typeof callback === 'function') {
      _subscribers.delete(callback);
    }
    if (_subscribers.size === 0 && _simulationIntervalId) {
      clearInterval(_simulationIntervalId);
      _simulationIntervalId = null;
      console.log('[MockData] Simulation stopped (no subscribers)');
    }
  };
};

/**
 * Manually set a track state (useful for testing)
 * @param {number} trackId - Track ID (1-6)
 * @param {string} status - Status ('free', 'occupied', 'anomaly')
 * @param {string} trainId - Train ID (optional)
 */
export const setTrackState = (trackId, status, trainId = null) => {
  const track = tracksState.find(t => t.id === trackId);
  
  if (!track) {
    console.error(`[MockData] Track ${trackId} not found`);
    return;
  }
  
  if (!statuses.includes(status)) {
    console.error(`[MockData] Invalid status: ${status}`);
    return;
  }
  
  track.status = status;
  track.trainId = trainId;
  track.timestamp = status !== 'free' ? new Date().toISOString() : null;
  
  console.log(`[MockData] Track ${trackId} manually set to ${status}`, track);
};

/**
 * Reset all tracks to initial state
 */
export const resetTracksState = () => {
  tracksState = [
    {
      id: 1,
      status: 'occupied',
      trainId: 'Rame-A',
      timestamp: new Date().toISOString(),
    },
    {
      id: 2,
      status: 'free',
      trainId: null,
      timestamp: null,
    },
    {
      id: 3,
      status: 'occupied',
      trainId: 'Rame-B',
      timestamp: new Date(Date.now() - 3600000).toISOString(),
    },
    {
      id: 4,
      status: 'free',
      trainId: null,
      timestamp: null,
    },
    {
      id: 5,
      status: 'anomaly',
      trainId: 'Rame-C',
      timestamp: new Date(Date.now() - 7200000).toISOString(),
    },
    {
      id: 6,
      status: 'occupied',
      trainId: 'Rame-D',
      timestamp: new Date(Date.now() - 1800000).toISOString(),
    },
  ];
  
  console.log('[MockData] Tracks state reset to initial values');
};

// Allow programmatic change of the simulation interval and restart loop
export const setSimulationInterval = (intervalMs) => {
  if (!intervalMs || typeof intervalMs !== 'number') return;
  _simulationIntervalMs = intervalMs;
  if (_simulationIntervalId) {
    clearInterval(_simulationIntervalId);
    _simulationIntervalId = null;
    // restart loop with new interval
    _simulationIntervalId = setInterval(() => {
      simulateStateChange();

      const now = new Date();
      const today = now.toISOString().slice(0,10);
      if (today !== _currentDay) {
        _previousDayAcc = { ..._currentDayAcc };
        _currentDayAcc = {};
        _currentDay = today;
        _savePreviousDayAcc();
      }

      const snapshot = getTracksState();
      for (const t of snapshot) {
        if (t.status === 'occupied' || t.status === 'anomaly') {
          _currentDayAcc[t.id] = (_currentDayAcc[t.id] || 0) + _simulationIntervalMs;
        } else {
          _currentDayAcc[t.id] = _currentDayAcc[t.id] || 0;
        }
      }

      for (const cb of _subscribers) {
        try { cb(snapshot); } catch (e) { console.error(e); }
      }
    }, _simulationIntervalMs);
  }
};

export const getPreviousDayDwell = () => {
  // returns array of { id, hours }
  const out = [];
  for (const t of tracksState) {
    const ms = _previousDayAcc[t.id] || 0;
    out.push({ id: t.id, hours: Math.round((ms / 1000 / 60 / 60) * 10) / 10 });
  }
  return out;
};
