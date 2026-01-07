import { useState, useEffect, useMemo } from 'react';
import Header from './components/Header/Header';
import Dashboard from './components/Dashboard/Dashboard';
import AnalyticsDashboard from './components/AnalyticsDashboard';
import LiveOperationsFeed from './components/LiveOperationsFeed';
import MaintenanceHeatmap from './components/MaintenanceHeatmap';
import { fetchDashboardSnapshot, transformSnapshot } from './services/smartYardApi';
import './App.css';

function App() {
  const [statistics, setStatistics] = useState(null);
  const [trafficData, setTrafficData] = useState({ labels: [], values: [] });
  const [trackUtilization, setTrackUtilization] = useState({ labels: [], values: [] });
  const [tracks, setTracks] = useState([]);
  const [tracksHistory, setTracksHistory] = useState({});
  const [previousDayDwell, setPreviousDayDwell] = useState([]);
  const [cameras, setCameras] = useState([]);
  const [events, setEvents] = useState([]);
  const [lastUpdated, setLastUpdated] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [alertThreshold, setAlertThreshold] = useState(() => {
    const raw = localStorage.getItem('alert_threshold_h');
    return raw ? Number(raw) : 4;
  });

  useEffect(() => {
    let cancelled = false;

    const loadSnapshot = async () => {
      try {
        const raw = await fetchDashboardSnapshot();
        if (cancelled) return;
        const parsed = transformSnapshot(raw);
        setStatistics(parsed.statistics);
        setTrafficData(parsed.trafficData);
        setTrackUtilization(parsed.trackUtilization);
        setTracks(parsed.tracks);
        setTracksHistory(parsed.tracksHistory);
        setPreviousDayDwell(parsed.previousDayDwell);
        setCameras(parsed.cameras);
        setEvents(parsed.events || []);
        setLastUpdated(parsed.lastUpdated || new Date());
        setError(null);
        setLoading(false);
      } catch (err) {
        if (cancelled) return;
        setError(err.message || 'Erreur de chargement');
        setLoading(false);
      }
    };

    loadSnapshot();
    const interval = setInterval(loadSnapshot, 15000);

    return () => {
      cancelled = true;
      clearInterval(interval);
    };
  }, []);

  const applyThreshold = (value) => {
    setAlertThreshold(value);
    localStorage.setItem('alert_threshold_h', String(value));
  };

  const maxDwellHours = useMemo(() => {
    if (!lastUpdated) return 0;
    const nowMs = lastUpdated.getTime();
    return tracks.reduce((max, track) => {
      if (!track.timestamp) return max;
      const diffMs = nowMs - new Date(track.timestamp).getTime();
      const hours = Math.round((diffMs / 3600000) * 10) / 10;
      return hours > max ? hours : max;
    }, 0);
  }, [tracks, lastUpdated]);

  const recentEvents = useMemo(() => {
    return (events || []).slice(0, 20).map(evt => {
      const label = evt.track_label || (evt.track_id ? `Voie ${evt.track_id}` : null);
      const type = evt.state === 'OCCUPIED' ? 'warning' : 'info';
      return {
        id: `${evt.event_id || evt.track_id || 'evt'}-${evt.generated_at || Math.random()}`,
        type,
        message: evt.train_number && label
          ? `Train ${evt.train_number} détecté sur ${label}`
          : label
            ? `Occupation détectée sur ${label}`
            : 'Événement détecté',
        timestamp: evt.generated_at || new Date().toISOString(),
        trackId: evt.track_id || null,
        trackLabel: label,
      };
    });
  }, [events]);

  if (loading) {
    return (
      <div className="loading-container">
        <div className="spinner-border text-primary" role="status">
          <span className="visually-hidden">Chargement...</span>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="loading-container">
        <div className="alert alert-danger" role="alert">
          {error}
        </div>
      </div>
    );
  }

  return (
    <div className="app">
      <Header />
      <main className="container-fluid py-4">
        <div className="row mb-3">
          <div className="col-12 d-flex flex-column flex-md-row justify-content-between align-items-md-center">
            <div className="small text-muted mb-2 mb-md-0">
              Dernière mise à jour&nbsp;: {lastUpdated ? lastUpdated.toLocaleString('fr-FR') : '---'}
            </div>
            <div className="d-flex align-items-center">
              <label className="me-2 small text-muted">Seuil alerte (h)&nbsp;:</label>
              <input
                type="number"
                className="form-control form-control-sm me-2"
                style={{ width: '80px' }}
                min={0}
                step={0.5}
                value={alertThreshold}
                onChange={(e) => setAlertThreshold(Number(e.target.value))}
              />
              <button className="btn btn-sm btn-outline-secondary" onClick={() => applyThreshold(alertThreshold)}>Enregistrer</button>
            </div>
          </div>
        </div>
        {maxDwellHours > alertThreshold && (
          <div className="row mb-3">
            <div className="col-12">
              <div className="alert alert-danger mb-0" role="alert">
                Alerte : durée maximale actuelle = {maxDwellHours} h (seuil {alertThreshold} h)
              </div>
            </div>
          </div>
        )}
        <Dashboard
          statistics={statistics}
          trafficData={trafficData}
          trackUtilization={trackUtilization}
          cameras={cameras}
          lastUpdated={lastUpdated}
        />
        <div className="row mt-4">
          <div className="col-12 mb-3">
            <div className="card h-100">
              <div className="card-body">
                <AnalyticsDashboard
                  tracks={tracks}
                  lastUpdated={lastUpdated}
                  previousDayDwell={previousDayDwell}
                  tracksHistory={tracksHistory}
                  alertThreshold={alertThreshold}
                />
              </div>
            </div>
          </div>
        </div>
        <div className="row mt-4">
          <div className="col-12 col-md-6 mb-3">
            <div className="card h-100">
              <div className="card-body">
                <LiveOperationsFeed events={recentEvents} />
              </div>
            </div>
          </div>

          <div className="col-12 col-md-6 mb-3">
            <div className="card h-100">
              <div className="card-body">
                <MaintenanceHeatmap tracks={tracks} previousDayDwell={previousDayDwell} />
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}

export default App;
