import { useState, useEffect } from 'react';
import Header from './components/Header/Header';
import Dashboard from './components/Dashboard/Dashboard';
import TrackMap from './components/TrackMap/TrackMap';
import {
  getStatistics,
  getTrafficData,
  getTrackUtilization,
  getTracks,
} from './services/smartYardApi';
import './App.css';

function App() {
  const [statistics, setStatistics] = useState(null);
  const [trafficData, setTrafficData] = useState(null);
  const [trackUtilization, setTrackUtilization] = useState(null);
  const [tracks, setTracks] = useState([]);

  useEffect(() => {
    // Function to load data
    const loadData = () => {
      setStatistics(getStatistics());
      setTrafficData(getTrafficData());
      setTrackUtilization(getTrackUtilization());
      setTracks(getTracks());
    };

    // Initial data load
    loadData();

    // Simulate periodic updates
    const interval = setInterval(loadData, 30000); // Update every 30 seconds

    return () => clearInterval(interval);
  }, []);

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
        <Dashboard
          statistics={statistics}
          trafficData={trafficData}
          trackUtilization={trackUtilization}
        />
        <div className="row mt-4">
          <div className="col-12">
            <TrackMap tracks={tracks} />
          </div>
        </div>
      </main>
    </div>
  );
}

export default App;
