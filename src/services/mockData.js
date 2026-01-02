/**
 * Advanced Mock Data Service for Smart Yard
 * Simulates realistic railway yard operations with state transitions,
 * scheduling, and historical event logging.
 */

// --- CONSTANTS & CONFIGURATION ---

const TRACK_COUNT = 6;
const DEFAULT_INTERVAL_MS = 10000;
const STORAGE_KEY_ACC = 'smartyard_daily_stats';
const STORAGE_KEY_STATE = 'smartyard_current_state';

// Train Metadata Generators
const OPERATORS = ['SNCF', 'DB', 'Renfe', 'SBB', 'Eurostar'];
const TRAIN_TYPES = ['TGV', 'TER', 'Intercités', 'FRET', 'Maintenance'];
const TRAIN_NAMES = [
  'TGV-8842', 'TER-9001', 'FRET-X22', 'IC-1102', 'TGV-LYRIA',
  'TGV-INOUI', 'Z-50000', 'B-81500', 'Maintenance-01'
];

// Probabilities (0-1)
const PROB_NEW_ARRIVAL = 0.4; // Chance a free track gets a train per tick
const PROB_DEPARTURE = 0.2;   // Chance a train leaves early per tick
const PROB_ANOMALY = 0.05;    // Chance of equipment failure
const PROB_RECOVERY = 0.2;    // Chance an anomaly is fixed per tick

// --- STATE MANAGEMENT ---

let _simulationIntervalId = null;
let _simulationIntervalMs = DEFAULT_INTERVAL_MS;
const _subscribers = new Set();

// Event Log (Circular Buffer)
const MAX_LOG_SIZE = 50;
let _eventLog = [];

// Daily Accumulators (Time in 'occupied' state per track)
let _currentDayAcc = {}; 
let _previousDayAcc = {};
let _currentDayStr = new Date().toISOString().slice(0, 10);

// Initial State Generation (or Load from LocalStorage)
const generateInitialState = () => {
  const savedState = localStorage.getItem(STORAGE_KEY_STATE);
  if (savedState) {
    try {
      const parsed = JSON.parse(savedState);
      // Validate structure roughly
      if (Array.isArray(parsed) && parsed.length === TRACK_COUNT) {
        return parsed;
      }
    } catch (e) {
      console.warn('[MockData] Failed to load saved state, resetting.');
    }
  }

  // Default fresh state
  return Array.from({ length: TRACK_COUNT }, (_, i) => ({
    id: i + 1,
    status: 'free',
    trainId: null,
    trainType: null,
    operator: null,
    timestamp: null,
    plannedDeparture: null,
  }));
};

let tracksState = generateInitialState();

// Initialize accumulators
try {
  const rawAcc = localStorage.getItem(STORAGE_KEY_ACC);
  _previousDayAcc = rawAcc ? JSON.parse(rawAcc) : {};
} catch (e) {
  _previousDayAcc = {};
}
tracksState.forEach(t => { _currentDayAcc[t.id] = 0; });

// --- HELPER FUNCTIONS ---

const getRandomItem = (arr) => arr[Math.floor(Math.random() * arr.length)];

const logEvent = (type, message, trackId) => {
  const event = {
    id: Date.now() + Math.random(), // simple unique id
    timestamp: new Date().toISOString(),
    type, // 'info', 'warning', 'success', 'error'
    message,
    trackId
  };
  _eventLog.unshift(event);
  if (_eventLog.length > MAX_LOG_SIZE) _eventLog.pop();
  return event;
};

// --- SIMULATION LOGIC (The "Tick") ---

const simulateTick = () => {
  const now = new Date();
  
  // 1. Handle Day Rollover for Stats
  const todayStr = now.toISOString().slice(0, 10);
  if (todayStr !== _currentDayStr) {
    _previousDayAcc = { ..._currentDayAcc };
    _currentDayAcc = {}; // Reset for new day
    tracksState.forEach(t => { _currentDayAcc[t.id] = 0; });
    _currentDayStr = todayStr;
    localStorage.setItem(STORAGE_KEY_ACC, JSON.stringify(_previousDayAcc));
    logEvent('info', 'Stats journalières réinitialisées', null);
  }

  // 2. Process Each Track
  tracksState.forEach(track => {
    // A. Update Accumulators
    if (track.status === 'occupied' || track.status === 'anomaly') {
      _currentDayAcc[track.id] = (_currentDayAcc[track.id] || 0) + _simulationIntervalMs;
    }

    // B. State Machine Transitions
    
    // Case 1: Track is FREE -> Maybe a train arrives
    if (track.status === 'free') {
      if (Math.random() < PROB_NEW_ARRIVAL) {
        const train = getRandomItem(TRAIN_NAMES);
        track.status = 'occupied';
        track.trainId = train;
        track.trainType = getRandomItem(TRAIN_TYPES);
        track.operator = getRandomItem(OPERATORS);
        track.timestamp = now.toISOString();
        
        // Schedule departure 1-4 hours from now
        const durationHours = 1 + Math.random() * 3;
        track.plannedDeparture = new Date(now.getTime() + durationHours * 60 * 60 * 1000).toISOString();
        
        logEvent('success', `Arrivée du train ${train} (${track.trainType})`, track.id);
      }
    }

    // Case 2: Track is OCCUPIED -> Maybe it leaves OR has an anomaly
    else if (track.status === 'occupied') {
      // Anomaly Check
      if (Math.random() < PROB_ANOMALY) {
        track.status = 'anomaly';
        logEvent('error', `Anomalie détectée sur la voie ${track.id} (Train ${track.trainId})`, track.id);
      } 
      // Scheduled Departure Check
      else {
        const isScheduledToLeave = track.plannedDeparture && new Date(track.plannedDeparture) <= now;
        const isEarlyDeparture = Math.random() < PROB_DEPARTURE;
        
        if (isScheduledToLeave || isEarlyDeparture) {
          logEvent('info', `Départ du train ${track.trainId}`, track.id);
          // Reset track
          track.status = 'free';
          track.trainId = null;
          track.trainType = null;
          track.operator = null;
          track.timestamp = null;
          track.plannedDeparture = null;
        }
      }
    }

    // Case 3: Track has ANOMALY -> Maybe it gets fixed
    else if (track.status === 'anomaly') {
      if (Math.random() < PROB_RECOVERY) {
        track.status = 'occupied'; // Returns to occupied (train didn't leave yet)
        logEvent('success', `Anomalie résolue sur la voie ${track.id}`, track.id);
      }
    }
  });

  // 3. Persist State (to survive page refresh)
  localStorage.setItem(STORAGE_KEY_STATE, JSON.stringify(tracksState));

  // 4. Notify Subscribers
  notifySubscribers();
};

const notifySubscribers = () => {
  const snapshot = getTracksState();
  _subscribers.forEach(cb => {
    try { cb(snapshot); } catch (e) { console.error(e); }
  });
};

// --- PUBLIC API ---

/**
 * Get current immutable snapshot of tracks
 */
export const getTracksState = () => {
  // Deep copy to prevent mutation bugs in React
  return JSON.parse(JSON.stringify(tracksState));
};

/**
 * Get recent event history
 */
export const getRecentEvents = () => {
  return [..._eventLog];
};

/**
 * Get yesterday's dwell hours per track
 */
export const getPreviousDayDwell = () => {
  return tracksState.map(t => ({
    id: t.id,
    hours: Math.round(((_previousDayAcc[t.id] || 0) / 1000 / 60 / 60) * 10) / 10
  }));
};

/**
 * Start or join the simulation loop
 */
export const startSimulation = (callback, intervalMs = DEFAULT_INTERVAL_MS) => {
  if (callback && typeof callback === 'function') {
    _subscribers.add(callback);
    // Send immediate initial data
    callback(getTracksState());
  }

  // Update interval if different
  if (intervalMs !== _simulationIntervalMs) {
    setSimulationInterval(intervalMs);
  }

  // Ensure loop is running
  if (!_simulationIntervalId) {
    _simulationIntervalId = setInterval(simulateTick, _simulationIntervalMs);
    console.log(`[MockData] Simulation started (${_simulationIntervalMs}ms)`);
  }

  // Unsubscribe function
  return () => {
    if (callback) _subscribers.delete(callback);
    if (_subscribers.size === 0 && _simulationIntervalId) {
      clearInterval(_simulationIntervalId);
      _simulationIntervalId = null;
      console.log('[MockData] Simulation stopped');
    }
  };
};

/**
 * Change simulation speed dynamically
 */
export const setSimulationInterval = (intervalMs) => {
  if (!intervalMs || typeof intervalMs !== 'number') return;
  _simulationIntervalMs = intervalMs;

  if (_simulationIntervalId) {
    clearInterval(_simulationIntervalId);
    _simulationIntervalId = setInterval(simulateTick, _simulationIntervalMs);
    console.log(`[MockData] Interval updated to ${_simulationIntervalMs}ms`);
  }
};

/**
 * Manual override for testing/demos
 */
export const setTrackState = (trackId, status, trainId = null) => {
  const track = tracksState.find(t => t.id === trackId);
  if (!track) return;

  track.status = status;
  if (status === 'free') {
    track.trainId = null;
    track.trainType = null;
    track.timestamp = null;
  } else {
    track.trainId = trainId || 'MANUAL-TEST';
    track.trainType = 'TEST';
    track.timestamp = new Date().toISOString();
  }
  
  logEvent('warning', `Modification manuelle de la voie ${trackId}`, trackId);
  notifySubscribers();
};

/**
 * Reset everything (Panic Button)
 */
export const resetTracksState = () => {
  tracksState = generateInitialState().map(t => ({ ...t, status: 'free', trainId: null, timestamp: null }));
  localStorage.removeItem(STORAGE_KEY_STATE);
  logEvent('warning', 'Réinitialisation complète du système', null);
  notifySubscribers();
};
