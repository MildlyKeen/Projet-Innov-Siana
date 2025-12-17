import React from 'react';
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
  // Line chart configuration for traffic
  const trafficChartData = {
    labels: trafficData.labels,
    datasets: [
      {
        label: 'Trains par heure',
        data: trafficData.values,
        borderColor: 'rgb(75, 192, 192)',
        backgroundColor: 'rgba(75, 192, 192, 0.2)',
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

      {/* Charts */}
      <div className="row">
        <div className="col-12 col-lg-8 mb-4">
          <div className="card chart-card">
            <div className="card-body">
              <div className="chart-container">
                <Line data={trafficChartData} options={trafficChartOptions} />
              </div>
            </div>
          </div>
        </div>
        <div className="col-12 col-lg-4 mb-4">
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
    </div>
  );
};

export default Dashboard;
