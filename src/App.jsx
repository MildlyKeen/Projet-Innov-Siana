import { useState, useEffect } from 'react';
import Header from './components/Header/Header';
import Dashboard from './components/Dashboard/Dashboard';
import MaintenanceCameraFeed from './components/MaintenanceCameraFeed';
import AnalyticsDashboard from './components/AnalyticsDashboard';
import LiveOperationsFeed from './components/LiveOperationsFeed';
import TrafficTimeline from './components/TrafficTimeline';
import MaintenanceHeatmap from './components/MaintenanceHeatmap';
import { startSimulation, getTracksState, setSimulationInterval, getPreviousDayDwell } from './services/mockData';
import {
  getStatistics,
  getTrafficData,
  
} from './services/smartYardApi';
import './App.css';

function App() {
  const [statistics, setStatistics] = useState(() => getStatistics());
  const [trafficData, setTrafficData] = useState(() => getTrafficData());
  const [tracks, setTracks] = useState(() => getTracksState());
  const [tracksHistory, setTracksHistory] = useState(() => {
    const init = {};
    const t = getTracksState();
    for (const tr of t) init[tr.id] = [];
    return init;
  });
  const [trackUtilization, setTrackUtilization] = useState(() => {
    const initTracks = getTracksState();
    const labels = initTracks.map((t) => `Voie ${t.id}`);
    const values = initTracks.map((t) => (t.status === 'occupied' || t.status === 'anomaly' ? 100 : 0));
    return { labels, values };
  });
  const [lastUpdated, setLastUpdated] = useState(null);
  const [simulationInterval, setSimulationIntervalState] = useState(() => {
    const raw = localStorage.getItem('sim_interval_ms');
    return raw ? Number(raw) : 10000;
  });
  const [alertThreshold, setAlertThreshold] = useState(() => {
    const raw = localStorage.getItem('alert_threshold_h');
    return raw ? Number(raw) : 4;
  });

  useEffect(() => {
    // Centralized simulation/subscriptions
    // Start the mock simulation which triggers updates every 10 seconds
    // Centralized subscription: update `tracks`, `trackUtilization` and `statistics`.
    const unsubscribe = startSimulation((updatedTracks) => {
      setTracks(updatedTracks.map(t => ({...t})));

      const now = Date.now();
      setLastUpdated(new Date(now));

      const labels = updatedTracks.map((t) => `Voie ${t.id}`);
      const values = updatedTracks.map((t) => (t.status === 'occupied' || t.status === 'anomaly' ? 100 : 0));
      setTrackUtilization({ labels, values });

      // Derive statistics from tracks for consistency
      const activeTrains = updatedTracks.filter((t) => t.status === 'occupied').length;
      const anomalyTrains = updatedTracks.filter((t) => t.status === 'anomaly').length;
      const availableTracks = updatedTracks.filter((t) => t.status === 'free').length;
      setStatistics((prev) => ({
        activeTrains: activeTrains,
        maintenanceTrains: anomalyTrains,
        availableTrains: prev ? prev.availableTrains : 0,
        availableTracks: availableTracks,
        averageTraffic: prev ? prev.averageTraffic : 0,
      }));

      // Update per-track history (hours) - keep last 12 points
      setTracksHistory((prev) => {
        const next = { ...prev };
        const nowMs = now;
        for (const t of updatedTracks) {
          const id = t.id;
          const hours = t.timestamp ? Math.round(((nowMs - new Date(t.timestamp).getTime()) / 1000 / 60 / 60) * 10) / 10 : 0;
          const arr = (next[id] || []).slice();
          arr.push(hours);
          if (arr.length > 12) arr.shift();
          next[id] = arr;
        }
        return next;
      });
    }, simulationInterval);

  // Traffic data should update less frequently (e.g., every 5 minutes) to be realistic
    const trafficInterval = setInterval(() => {
      setTrafficData(getTrafficData());
    }, 5 * 60 * 1000); // 5 minutes

    // New: Poll for live inference results
    /* const pollInterval = setInterval(async () => {
      try {
        const [response1, response2] = await Promise.all([
          fetch('/live_results.json').catch(() => null),
          fetch('/live_results2.json').catch(() => null)
        ]);
        const data1 = response1 ? await response1.json() : null;
        const data2 = response2 ? await response2.json() : null;
        
        const occupancy = {};
        for (let i = 1; i <= 6; i++) {
          const key = `voie${i}`;
          const occ1 = data1?.occupancy?.[key] || false;
          const occ2 = data2?.occupancy?.[key] || false;
          occupancy[key] = occ1 || occ2;  // Mark occupied if either video detects it
        }
        
        if (Object.keys(occupancy).length > 0) {
          // Update tracks based on occupancy
          setTracks((prev) => prev.map((track) => ({
            ...track,
            status: occupancy[`voie${track.id}`] ? 'occupied' : 'free'
          })));
          // Update utilization
          const labels = prev.map((t) => `Voie ${t.id}`);
          const values = prev.map((t) => occupancy[`voie${t.id}`] ? 100 : 0);
          setTrackUtilization({ labels, values });
        }
      } catch (err) {
        // No live data yet or error
      }
    }, 2000);  // Poll every 2 seconds
    */

    // trackUtilization already initialized when component mounts

    return () => {
      if (unsubscribe) unsubscribe();
      clearInterval(trafficInterval);
      /* clearInterval(pollInterval); */
    };
  }, [simulationInterval]);

  // previous day dwell data (fetch on render)
  const previousDayDwell = getPreviousDayDwell();

  // derived: max current dwell (hours) to show alerts
  const maxDwellHours = (() => {
    if (!lastUpdated) return 0;
    const nowMs = lastUpdated.getTime();
    let maxH = 0;
    for (const t of tracks) {
      if (!t.timestamp) continue;
      const diffMs = nowMs - new Date(t.timestamp).getTime();
      const h = Math.round((diffMs / 1000 / 60 / 60) * 10) / 10;
      if (h > maxH) maxH = h;
    }
    return maxH;
  })();

  const applyInterval = (ms) => {
    setSimulationInterval(ms);
    setSimulationIntervalState(ms);
    localStorage.setItem('sim_interval_ms', String(ms));
  };

  const applyThreshold = (h) => {
    setAlertThreshold(h);
    localStorage.setItem('alert_threshold_h', String(h));
  };

  if (!statistics || !trafficData || !trackUtilization) {
    return (
      <div className="loading-container">
        <div className="spinner-border text-primary" role="status">
          <span className="visually-hidden">Chargement...</span>
        </div>
      </div>
    );
  }

  return (
    <div className="app">
      <Header />
      <main className="container-fluid py-4">
        <div className="row mb-3">
          <div className="col-12 d-flex justify-content-between align-items-center">
            <div className="d-flex align-items-center">
              <label className="me-2 small text-muted">Fréquence simulation :</label>
              <select
                className="form-select form-select-sm d-inline-block w-auto me-2"
                value={simulationInterval}
                onChange={(e) => setSimulationIntervalState(Number(e.target.value))}
              >
                <option value={5000}>5 s</option>
                <option value={10000}>10 s</option>
                <option value={30000}>30 s</option>
              </select>
              <button className="btn btn-sm btn-primary me-3" onClick={() => applyInterval(simulationInterval)}>Appliquer</button>

              <label className="me-2 small text-muted">Seuil alerte (h) :</label>
              <input
                type="number"
                className="form-control form-control-sm me-2"
                style={{ width: '80px' }}
                value={alertThreshold}
                onChange={(e) => setAlertThreshold(Number(e.target.value))}
              />
              <button className="btn btn-sm btn-outline-secondary" onClick={() => applyThreshold(alertThreshold)}>Enregistrer</button>
            </div>
            <div>
              {maxDwellHours > alertThreshold && (
                <div className="alert alert-danger mb-0 py-1" role="alert">
                  <strong>Alerte :</strong> Durée maximale actuelle = {maxDwellHours} h (seuil {alertThreshold} h)
                </div>
              )}
            </div>
          </div>
        </div>
        <Dashboard
          statistics={statistics}
          trafficData={trafficData}
          trackUtilization={trackUtilization}
        />
        <div className="row mt-4">
          <div className="col-12 col-lg-7 mb-3">
            <div className="card h-100">
              <div className="card-body p-0">
                <MaintenanceCameraFeed />
              </div>
            </div>
          </div>
          <div className="col-12 col-lg-5 mb-3">
            <AnalyticsDashboard tracks={tracks} lastUpdated={lastUpdated} previousDayDwell={getPreviousDayDwell()} tracksHistory={tracksHistory} alertThreshold={alertThreshold} />
          </div>
        </div>
        <div className="row mt-4">
          <div className="col-12 col-md-4 mb-3">
            <div className="card h-100">
              <div className="card-body">
                <LiveOperationsFeed />
              </div>
            </div>
          </div>
          <div className="col-12 col-md-4 mb-3">
            <div className="card h-100">
              <div className="card-body">
                <TrafficTimeline />
              </div>
            </div>
          </div>
          <div className="col-12 col-md-4 mb-3">
            <div className="card h-100">
              <div className="card-body">
                <MaintenanceHeatmap />
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}

export default App;
