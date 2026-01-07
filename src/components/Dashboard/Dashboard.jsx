import React, { useMemo } from 'react';
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

const palette = ['#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0', '#9966FF', '#F67019'];

const Dashboard = ({ statistics, trafficData, trackUtilization, cameras = [], lastUpdated = null }) => {
  const utilizationColors = useMemo(() => {
    if (!trackUtilization.labels?.length) return [];
    return trackUtilization.labels.map((_, idx) => palette[idx % palette.length] + '99');
  }, [trackUtilization.labels]);

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
        text: 'Trafic Ferroviaire (dernières mesures)',
      },
    },
    scales: {
      y: {
        beginAtZero: true,
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
        backgroundColor: utilizationColors,
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

  const cameraCards = useMemo(() => {
    if (!Array.isArray(cameras)) return [];
    return cameras.map((cam, idx) => {
      const videoSrc = cam.video_url || null;
      const trains = cam.train_numbers?.length
        ? cam.train_numbers.join(', ')
        : (cam.occupancy?.occupancy_events?.length ? `${cam.occupancy.occupancy_events.length} passages` : 'Aucun train détecté');
      const voieLabel = cam.occupancy?.tracks?.map(t => t.global_label).join(', ') || 'Voies 1-6';
      return {
        key: `${cam.folder || 'camera'}-${idx}`,
        label: cam.camera_label || `Caméra ${idx + 1}`,
        voie: voieLabel,
        trains,
        src: videoSrc,
      };
    });
  }, [cameras]);

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
        <div className="col-12 col-lg-4 mb-4">
          <div className="card chart-card">
            <div className="card-body">
              <div className="chart-container-small">
                <Doughnut data={statsChartData} options={statsChartOptions} />
              </div>
            </div>
          </div>
        </div>
        <div className="col-12 col-lg-8 mb-4">
          <div className="card chart-card">
            <div className="card-body">
              <div className="chart-container">
                <Line data={trafficChartData} options={trafficChartOptions} />
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Utilization chart with camera feeds under each pair of tracks */}
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

      {/* Camera feeds directly under corresponding tracks */}
      <div className="row mt-3 voie-cameras-row">
        <div className="col-12">
          <div className="card">
            <div className="card-body">
              <div className="voie-cameras-grid-paired">
                {/* Camera 1 under voies 1-2 */}
                {cameraCards[0] && (
                  <div className="voie-camera-col">
                    <div className="voie-camera-label">{cameraCards[0].label}</div>
                    {cameraCards[0].src ? (
                      <video
                        className="voie-camera-video"
                        src={cameraCards[0].src}
                        controls
                        autoPlay
                        loop
                        muted
                        playsInline
                      />
                    ) : (
                      <div className="voie-camera-placeholder">Aucune vidéo</div>
                    )}
                    <div className="voie-camera-meta">
                      <div><strong>Voies :</strong> {cameraCards[0].voie}</div>
                      <div><strong>Trains :</strong> {cameraCards[0].trains}</div>
                    </div>
                  </div>
                )}
                {/* Camera 2 under voies 3-4 */}
                {cameraCards[1] && (
                  <div className="voie-camera-col">
                    <div className="voie-camera-label">{cameraCards[1].label}</div>
                    {cameraCards[1].src ? (
                      <video
                        className="voie-camera-video"
                        src={cameraCards[1].src}
                        controls
                        autoPlay
                        loop
                        muted
                        playsInline
                      />
                    ) : (
                      <div className="voie-camera-placeholder">Aucune vidéo</div>
                    )}
                    <div className="voie-camera-meta">
                      <div><strong>Voies :</strong> {cameraCards[1].voie}</div>
                      <div><strong>Trains :</strong> {cameraCards[1].trains}</div>
                    </div>
                  </div>
                )}
                {/* Camera 3 under voies 5-6 */}
                {cameraCards[2] && (
                  <div className="voie-camera-col">
                    <div className="voie-camera-label">{cameraCards[2].label}</div>
                    {cameraCards[2].src ? (
                      <video
                        className="voie-camera-video"
                        src={cameraCards[2].src}
                        controls
                        autoPlay
                        loop
                        muted
                        playsInline
                      />
                    ) : (
                      <div className="voie-camera-placeholder">Aucune vidéo</div>
                    )}
                    <div className="voie-camera-meta">
                      <div><strong>Voies :</strong> {cameraCards[2].voie}</div>
                      <div><strong>Trains :</strong> {cameraCards[2].trains}</div>
                    </div>
                  </div>
                )}
              </div>
              {lastUpdated && (
                <div className="text-end text-muted small mt-2">
                  Mise à jour : {lastUpdated.toLocaleTimeString('fr-FR')}
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
