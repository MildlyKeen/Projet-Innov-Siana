// Mock API service for Smart Yard MVP

/**
 * Get current statistics for the dashboard
 */
export const getStatistics = () => {
  return {
    activeTrains: 12,
    maintenanceTrains: 3,
    availableTrains: 8,
    availableTracks: 5,
    averageTraffic: 18,
  };
};

/**
 * Get traffic data for the last 24 hours
 */
export const getTrafficData = () => {
  const hours = [];
  const values = [];
  
  for (let i = 23; i >= 0; i--) {
    const hour = new Date();
    hour.setHours(hour.getHours() - i);
    hours.push(`${hour.getHours()}h`);
    // Generate random traffic data
    values.push(Math.floor(Math.random() * 15) + 8);
  }
  
  return {
    labels: hours,
    values: values,
  };
};

/**
 * Get track utilization data
 */
export const getTrackUtilization = () => {
  return {
    labels: ['Voie 1', 'Voie 2', 'Voie 3', 'Voie 4', 'Voie 5'],
    values: [85, 45, 92, 38, 67],
  };
};

/**
 * Get all tracks with their current status
 */
export const getTracks = () => {
  return [
    {
      id: 1,
      status: 'occupied',
      capacity: 100,
      currentLoad: 85,
      trainId: 'TGV-2841',
    },
    {
      id: 2,
      status: 'available',
      capacity: 100,
      currentLoad: 45,
      trainId: null,
    },
    {
      id: 3,
      status: 'occupied',
      capacity: 100,
      currentLoad: 92,
      trainId: 'IC-1523',
    },
    {
      id: 4,
      status: 'available',
      capacity: 100,
      currentLoad: 38,
      trainId: null,
    },
    {
      id: 5,
      status: 'occupied',
      capacity: 100,
      currentLoad: 67,
      trainId: 'TER-9247',
    },
  ];
};

/**
 * Simulate real-time data update
 * In a real application, this would be a WebSocket connection
 */
export const subscribeToUpdates = (callback) => {
  const interval = setInterval(() => {
    const data = {
      statistics: getStatistics(),
      trafficData: getTrafficData(),
      trackUtilization: getTrackUtilization(),
      tracks: getTracks(),
    };
    callback(data);
  }, 5000); // Update every 5 seconds

  // Return unsubscribe function
  return () => clearInterval(interval);
};
