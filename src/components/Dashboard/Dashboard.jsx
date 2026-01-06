import React, { useEffect, useState } from 'react';
import { Line, Bar, Doughnut } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  ArcElement,
  Title,
  Tooltip,
  Legend,
} from 'chart.js';
import './Dashboard.css';

// Register Chart.js components
ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  ArcElement,
  Title,
  Tooltip,
  Legend
);

const Dashboard = ({ statistics, trafficData, trackUtilization }) => {
  const [voies, setVoies] = useState([]);

  useEffect(() => {
    let mounted = true;
    async function fetchVoies() {
      try {
        const res = await fetch('/api/voies');
        if (!res.ok) return;
        const data = await res.json();
        if (mounted) setVoies(data);
      } catch (e) {
        // ignore
      }
    }
    fetchVoies();
    const iv = setInterval(fetchVoies, 3000);
    return () => { mounted = false; clearInterval(iv); };
  }, []);

  // Line chart configuration for traffic
  const trafficChartData = {
    labels: trafficData.labels,
    datasets: [
      {
        label: 'Flux maintenance (trains)',
        data: trafficData.values,
        borderColor: 'rgb(54, 162, 235)',
        backgroundColor: 'rgba(54, 162, 235, 0.15)',
        tension: 0.4,
      },
    ],
  };

  const trafficChartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'top',
      },
      title: {
        display: true,
        text: 'Trafic Ferroviaire (24h)',
      },
    },
    scales: {
      y: {
        beginAtZero: true,
        max: 6,
      },
    },
  };

  // Bar chart for track utilization
  const utilizationChartData = {
    labels: trackUtilization.labels,
    datasets: [
      {
        label: 'Taux d\'occupation (%)',
        data: trackUtilization.values,
        backgroundColor: [
          'rgba(255, 99, 132, 0.6)',
          'rgba(54, 162, 235, 0.6)',
          'rgba(255, 206, 86, 0.6)',
          'rgba(75, 192, 192, 0.6)',
          'rgba(153, 102, 255, 0.6)',
        ],
      },
    ],
  };

  const utilizationChartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        display: false,
      },
      title: {
        display: true,
        text: 'Utilisation des Voies',
      },
    },
    scales: {
      y: {
        beginAtZero: true,
        max: 100,
      },
    },
  };

  // Doughnut chart for statistics
  const statsChartData = {
    labels: ['Actifs', 'En Maintenance', 'Disponibles'],
    datasets: [
      {
        data: [
          statistics.activeTrains,
          statistics.maintenanceTrains,
          statistics.availableTrains,
        ],
        backgroundColor: [
          'rgba(40, 167, 69, 0.8)',
          'rgba(255, 193, 7, 0.8)',
          'rgba(23, 162, 184, 0.8)',
        ],
        borderWidth: 2,
        borderColor: '#fff',
      },
    ],
  };

  const statsChartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'bottom',
      },
      title: {
        display: true,
        text: 'État des Trains',
      },
    },
  };

  const fallbackCameraSources = [
    '/videos/trains_rails_overlay.mp4',
    '/videos/trains_rails_overlay2.mp4',
    '/videos/video.mp4',
    '/videos/video2.mp4',
    '/videos/trains_rails_overlay.mp4',
    '/videos/video2.mp4',
  ];

  return (
    <div className="dashboard">
      {/* Statistics Cards */}
      <div className="row mb-4">
        <div className="col-12 col-md-6 col-lg-3 mb-3">
          <div className="card stat-card stat-card-primary">
            <div className="card-body">
              <div className="d-flex justify-content-between align-items-center">
                <div>
                  <p className="text-muted mb-1">Trains Actifs</p>
                  <h3 className="mb-0">{statistics.activeTrains}</h3>
                </div>
                <div className="stat-icon">🚂</div>
              </div>
            </div>
          </div>
        </div>
        <div className="col-12 col-md-6 col-lg-3 mb-3">
          <div className="card stat-card stat-card-warning">
            <div className="card-body">
              <div className="d-flex justify-content-between align-items-center">
                <div>
                  <p className="text-muted mb-1">En Maintenance</p>
                  <h3 className="mb-0">{statistics.maintenanceTrains}</h3>
                </div>
                <div className="stat-icon">🔧</div>
              </div>
            </div>
          </div>
        </div>
        <div className="col-12 col-md-6 col-lg-3 mb-3">
          <div className="card stat-card stat-card-success">
            <div className="card-body">
              <div className="d-flex justify-content-between align-items-center">
                <div>
                  <p className="text-muted mb-1">Voies Libres</p>
                  <h3 className="mb-0">{statistics.availableTracks}</h3>
                </div>
                <div className="stat-icon">✓</div>
              </div>
            </div>
          </div>
        </div>
        <div className="col-12 col-md-6 col-lg-3 mb-3">
          <div className="card stat-card stat-card-info">
            <div className="card-body">
              <div className="d-flex justify-content-between align-items-center">
                <div>
                  <p className="text-muted mb-1">Trafic Moyen</p>
                  <h3 className="mb-0">{statistics.averageTraffic}/h</h3>
                </div>
                <div className="stat-icon">📊</div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Charts: show only the doughnut now (traffic chart removed) */}
      <div className="row">
        <div className="col-12 col-lg-4 mb-4 mx-auto">
          <div className="card chart-card">
            <div className="card-body">
              <div className="chart-container-small">
                <Doughnut data={statsChartData} options={statsChartOptions} />
              </div>
            </div>
          </div>
        </div>
      </div>

      <div className="row">
        <div className="col-12">
          <div className="card chart-card">
            <div className="card-body">
              <div className="chart-container">
                <Bar data={utilizationChartData} options={utilizationChartOptions} />
              </div>
            </div>
          </div>
        </div>
      </div>
      {/* Camera feeds aligned under each histogram bar */}
      <div className="row mt-3 voie-cameras-row">
        <div className="col-12">
          <div className="card">
            <div className="card-body">
              <div className="voie-cameras-grid">
                {Array.from({ length: 6 }, (_, i) => {
                  const voieNum = i + 1;
                  const v = voies.find((x) => x.voie_index === voieNum) || null;
                  const label = `Camera Voie ${voieNum}`;
                  const srcFromApi = v && v.video_url
                    ? (v.video_url.startsWith('http')
                      ? v.video_url
                      : `${import.meta.env.DEV ? 'http://localhost:3001' : ''}${v.video_url}`)
                    : null;
                  const src = srcFromApi || fallbackCameraSources[i] || null;
                  return (
                    <div key={voieNum} className="voie-camera-col">
                      <div className="voie-camera-label">{label}</div>
                      {src ? (
                        <video
                          className="voie-camera-video"
                          src={src}
                          controls
                          autoPlay
                          loop
                          muted
                          playsInline
                        />
                      ) : (
                        <div className="voie-camera-placeholder">Aucune vidéo</div>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
