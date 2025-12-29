import React, { useMemo } from 'react';
import {
  Chart as ChartJS,
  ArcElement,
  Tooltip,
  Legend,
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
} from 'chart.js';
import { Doughnut, Bar } from 'react-chartjs-2';
// Receive tracks and lastUpdated via props from App (single source of truth)
import './AnalyticsDashboard.css';

// Register Chart.js components
ChartJS.register(
  ArcElement,
  Tooltip,
  Legend,
  CategoryScale,
  LinearScale,
  BarElement,
  Title
);

const AnalyticsDashboard = ({ tracks = [], lastUpdated = null, previousDayDwell = [], tracksHistory = {}, alertThreshold = 4 }) => {
  // export filename state for quick tweak later
  const exportFileName = 'track_dwell_times.csv';

  // Compute occupancy
  const occupiedCount = tracks.filter(
    (t) => t.status === 'occupied' || t.status === 'anomaly'
  ).length;
  const freeCount = tracks.length - occupiedCount;

  const formatDuration = (hours) => {
    if (!hours || hours <= 0) return '0 h';
    if (hours < 1) {
      const mins = Math.round(hours * 60);
      return `${mins} min`;
    }
    const h = Math.floor(hours);
    const rem = Math.round((hours - h) * 60);
    return rem === 0 ? `${h} h` : `${h} h ${rem} min`;
  };

  // Doughnut chart data
  const doughnutData = {
    labels: ['Voies occupées', 'Voies libres'],
    datasets: [
      {
        data: [occupiedCount, freeCount],
        backgroundColor: ['#dc3545', '#28a745'],
        hoverBackgroundColor: ['#c82333', '#218838'],
      },
    ],
  };

  const doughnutOptions = {
    plugins: {
      legend: {
        position: 'bottom',
      },
      title: {
        display: true,
        text: "Taux d'occupation global",
      },
    },
    maintainAspectRatio: false,
  };

  // Bar chart: dwell time per track (hours)
  const labels = tracks.map((t) => `Voie ${t.id}`);
  const hoursData = useMemo(() => {
    const nowMs = lastUpdated ? lastUpdated.getTime() : null;
    return tracks.map((t) => {
      if (!t.timestamp) return 0;
      if (!nowMs) return 0;
      const diffMs = nowMs - new Date(t.timestamp).getTime();
      const hours = diffMs / 1000 / 60 / 60;
      return Math.round(hours * 10) / 10; // one decimal
    });
  }, [tracks, lastUpdated]);

  // colorize bars by dwell time (long stays highlighted)
  const barColors = hoursData.map((h) => {
    if (h >= 4) return '#dc3545'; // red for long stay >=4h
    if (h >= 1.5) return '#ffc107'; // amber for medium stay
    if (h > 0) return '#0d6efd'; // blue for short stay
    return '#6c757d'; // gray for 0
  });

  const barData = {
    labels,
    datasets: [
      {
        label: 'Temps de séjour (heures)',
        data: hoursData,
        backgroundColor: barColors,
      },
    ],
  };

  const barOptions = {
    plugins: {
      legend: { display: false },
      title: { display: true, text: "Temps de séjour par voie" },
      tooltip: {
        callbacks: {
          label: function (context) {
            const value = context.raw;
            return `Durée: ${formatDuration(value)}`;
          },
        },
      },
    },
    scales: {
      y: {
        beginAtZero: true,
        title: { display: true, text: 'Heures' },
      },
      x: {
        title: { display: true, text: 'Voies' },
      },
    },
    maintainAspectRatio: false,
  };

  const tracksTable = useMemo(() => {
    return tracks.map((t, idx) => ({
      id: t.id,
      status: t.status,
      trainId: t.trainId,
      rawHours: hoursData[idx],
      formatted: formatDuration(hoursData[idx]),
      timestamp: t.timestamp,
    }));
  }, [tracks, hoursData]);

  const renderSparkline = (arr = []) => {
    const w = 80;
    const h = 24;
    if (!arr || arr.length === 0) {
      return (
        <svg width={w} height={h} className="sparkline" aria-hidden>
          <rect width={w} height={h} fill="transparent" />
          <polyline points="0,12 80,12" fill="none" stroke="#6c757d" strokeWidth="1" />
        </svg>
      );
    }
    const max = Math.max(...arr, 1);
    const step = w / Math.max(arr.length - 1, 1);
    const points = arr.map((v, i) => `${Math.round(i * step)},${Math.round(h - (v / max) * (h - 4) - 2)}`).join(' ');
    return (
      <svg width={w} height={h} className="sparkline" aria-hidden>
        <polyline points={points} fill="none" stroke="#0d6efd" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
      </svg>
    );
  };

  // previous day dwell chart data
  const prevLabels = previousDayDwell.map((p) => `Voie ${p.id}`);
  const prevData = previousDayDwell.map((p) => p.hours || 0);
  const prevBarData = {
    labels: prevLabels,
    datasets: [{ label: 'Temps (h) - veille', data: prevData, backgroundColor: '#198754' }],
  };
  const prevBarOptions = {
    plugins: { legend: { display: false }, title: { display: true, text: "Temps de séjour - journée précédente" } },
    scales: { y: { beginAtZero: true, title: { display: true, text: 'Heures' } } },
    maintainAspectRatio: false,
  };

  const exportCSV = () => {
    const header = ['id,status,trainId,duration_hours,duration_readable,timestamp'];
    const rows = tracksTable.map((r) => `${r.id},${r.status},${r.trainId || ''},${r.rawHours},"${r.formatted}",${r.timestamp || ''}`);
    const csv = header.concat(rows).join('\n');
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = exportFileName;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="analytics-dashboard container-fluid mt-4">
      <div className="row g-3">
        <div className="col-12 col-md-6">
          <div className="card h-100">
            <div className="card-body">
              <h5 className="card-title">Taux d'occupation global</h5>
              <div className="chart-wrapper doughnut-wrapper">
                <Doughnut data={doughnutData} options={doughnutOptions} />
              </div>
              <p className="card-text mt-3">
                <strong>{occupiedCount}</strong> voies occupées • <strong>{freeCount}</strong> voies libres
              </p>
            </div>
          </div>
        </div>

        <div className="col-12 col-md-6">
          <div className="card h-100">
            <div className="card-body">
              <h5 className="card-title">Temps de séjour par voie</h5>
              <div className="d-flex justify-content-between align-items-center mb-2">
                <small className="text-muted">Données simulées (mise à jour automatique)</small>
                <div>
                  <button className="btn btn-sm btn-outline-secondary me-2" onClick={exportCSV}>Exporter CSV</button>
                  <small className="text-muted">Mise à jour: {lastUpdated ? lastUpdated.toLocaleTimeString() : '—'}</small>
                </div>
              </div>
              <div className="chart-wrapper bar-wrapper">
                <Bar data={barData} options={barOptions} />
              </div>
              <div className="mt-3">
                <table className="table table-sm">
                  <thead>
                    <tr>
                      <th>Voie</th>
                      <th>Status</th>
                      <th>Train</th>
                      <th>Durée</th>
                      <th>Trend</th>
                    </tr>
                  </thead>
                  <tbody>
                    {tracksTable.map((r) => {
                      const history = tracksHistory && tracksHistory[r.id] ? tracksHistory[r.id] : [];
                      const danger = r.rawHours >= alertThreshold;
                      return (
                        <tr key={r.id} className={danger ? 'table-danger' : ''}>
                          <td>Voie {r.id}</td>
                          <td>{r.status}</td>
                          <td>{r.trainId || '-'}</td>
                          <td>{r.formatted}</td>
                          <td style={{ width: 100 }}>{renderSparkline(history)}</td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
              <div className="mt-3">
                <div className="card">
                  <div className="card-body">
                    <h6 className="card-title">Temps de séjour — journée précédente</h6>
                    <div className="chart-wrapper bar-wrapper">
                      <Bar data={prevBarData} options={prevBarOptions} />
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AnalyticsDashboard;
