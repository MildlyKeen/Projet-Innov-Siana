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

// Possible statuses
const statuses = ['free', 'occupied', 'anomaly'];

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
  
  // Select a random status
  const newStatus = statuses[Math.floor(Math.random() * statuses.length)];
  
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
export const startSimulation = (callback) => {
  const interval = setInterval(() => {
    simulateStateChange();
    
    // Call callback with updated data if provided
    if (callback && typeof callback === 'function') {
      callback(getTracksState());
    }
  }, 3000); // Update every 3 seconds
  
  console.log('[MockData] Simulation started - state changes every 3 seconds');
  
  // Return unsubscribe function
  return () => {
    clearInterval(interval);
    console.log('[MockData] Simulation stopped');
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
