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
  PointElement, // Added for the threshold line
  LineElement,  // Added for the threshold line
} from 'chart.js';
import { Doughnut, Bar } from 'react-chartjs-2';
import './AnalyticsDashboard.css';

// Register Chart.js components
ChartJS.register(
  ArcElement,
  Tooltip,
  Legend,
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  PointElement,
  LineElement
);

// OPTIMIZATION: Common chart options
const commonOptions = {
  maintainAspectRatio: false,
  responsive: true,
  interaction: {
    mode: 'index',
    intersect: false,
  },
};

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

const AnalyticsDashboard = ({ tracks = [], lastUpdated = null, previousDayDwell = [], tracksHistory = {}, alertThreshold = 4 }) => {
  const exportFileName = `suivi_voies_${new Date().toLocaleDateString('fr-FR').replace(/\//g, '-')}.csv`;

  // --- 1. COMPUTATIONS ---

  // Occupancy Stats
  const occupiedCount = tracks.filter((t) => t.status === 'occupied').length;
  const freeCount = tracks.filter((t) => t.status === 'free').length;
  const anomalyCount = tracks.filter((t) => t.status === 'anomaly').length;

  // Real-time Dwell Data
  const labels = tracks.map((t) => `Voie ${t.id}`);
  
  const hoursData = useMemo(() => {
    const nowMs = lastUpdated ? lastUpdated.getTime() : Date.now();
    return tracks.map((t) => {
      if (!t.timestamp) return 0;
      const diffMs = nowMs - new Date(t.timestamp).getTime();
      const hours = diffMs / 1000 / 60 / 60;
      return Math.round(hours * 10) / 10;
    });
  }, [tracks, lastUpdated]);

  // Insight: Calculate Today's Average
  const currentAvg = useMemo(() => {
    const activeTracks = hoursData.filter(h => h > 0);
    if (!activeTracks.length) return 0;
    return (activeTracks.reduce((a, b) => a + b, 0) / activeTracks.length).toFixed(1);
  }, [hoursData]);

  // Insight: Calculate Yesterday's Average
  const prevAvg = useMemo(() => {
    const vals = previousDayDwell.map(p => p.hours || 0).filter(h => h > 0);
    if (!vals.length) return 0;
    return (vals.reduce((a, b) => a + b, 0) / vals.length).toFixed(1);
  }, [previousDayDwell]);

  // --- 2. CHART CONFIGURATIONS ---

  // Doughnut Config
  const doughnutData = useMemo(() => ({
    labels: ['Voies occupées', 'Voies libres', 'Voies en anomalie'],
    datasets: [
      {
        data: [occupiedCount, freeCount, anomalyCount],
        backgroundColor: ['#dc3545', '#28a745', '#ffc107'],
        hoverBackgroundColor: ['#c82333', '#218838', '#e0a800'],
        borderWidth: 2,
      },
    ],
  }), [occupiedCount, freeCount, anomalyCount]);

  const doughnutOptions = useMemo(() => ({
    plugins: {
      legend: { position: 'bottom' },
      title: { display: true, text: "État Actuel du Parc", padding: { bottom: 20 } },
    },
    cutout: '60%', // Thinner doughnut for modern look
    ...commonOptions
  }), []);

  // Main Bar Chart Config (Mixed Chart: Bar + Threshold Line)
  const barData = useMemo(() => {
    const colors = hoursData.map((h) => {
      if (h >= alertThreshold) return '#dc3545'; // Red
      if (h >= alertThreshold * 0.75) return '#ffc107'; // Warning Yellow
      return '#0d6efd'; // Blue
    });

    return {
      labels,
      datasets: [
        {
          type: 'bar',
          label: 'Temps de séjour (h)',
          data: hoursData,
          backgroundColor: colors,
          order: 2,
          borderRadius: 4,
        },
        // INSIGHT: Threshold Line Dataset
        {
          type: 'line',
          label: `Seuil Alerte (${alertThreshold}h)`,
          data: Array(labels.length).fill(alertThreshold),
          borderColor: '#dc3545',
          borderWidth: 2,
          borderDash: [5, 5],
          pointRadius: 0,
          order: 1,
          tooltip: { enabled: false } // Don't show tooltip for the line
        }
      ],
    };
  }, [labels, hoursData, alertThreshold]);

  const barOptions = useMemo(() => ({
    plugins: {
      legend: { 
        display: true, 
        labels: { filter: (item) => item.text.includes('Seuil') } // Only show the Threshold in legend
      },
      title: { display: false },
      tooltip: {
        callbacks: {
          label: function (context) {
            if (context.dataset.type === 'line') return null;
            return ` Durée: ${formatDuration(context.raw)}`;
          },
        },
      },
    },
    scales: {
      y: { 
        beginAtZero: true, 
        title: { display: true, text: 'Heures' },
        grid: { borderDash: [2, 2] } 
      },
      x: { grid: { display: false } },
    },
    ...commonOptions
  }), []);

  // Previous Day Comparison Chart
  const prevBarData = useMemo(() => ({
    labels: previousDayDwell.map((p) => `Voie ${p.id}`),
    datasets: [{ 
      label: 'Hier (h)', 
      data: previousDayDwell.map((p) => p.hours || 0), 
      backgroundColor: '#6c757d', // Neutral gray for history
      borderRadius: 4
    }],
  }), [previousDayDwell]);

  // --- 3. EXPORT LOGIC ---

  const exportCSV = () => {
    // INSIGHT: Add more useful columns for technicians
    const header = ['id,status,train_id,duree_heures,duree_lisible,date_arrivee,depassement_seuil'];
    
    const rows = tracks.map((t, idx) => {
      const h = hoursData[idx];
      const isOver = h >= alertThreshold ? 'OUI' : 'NON';
      const arrivalDate = t.timestamp ? new Date(t.timestamp).toLocaleString('fr-FR') : '';
      
      return [
        t.id,
        t.status,
        t.trainId || 'N/A',
        String(h).replace('.', ','), // Excel friendly decimal
        `"${formatDuration(h)}"`,
        `"${arrivalDate}"`,
        isOver
      ].join(',');
    });

    const csvContent = [header, ...rows].join('\n');
    const blob = new Blob([`\uFEFF${csvContent}`], { type: 'text/csv;charset=utf-8;' }); // BOM for Excel encoding
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = exportFileName;
    a.click();
    URL.revokeObjectURL(url);
  };

  // --- 4. RENDER HELPERS ---
  
  const renderSparkline = (arr) => {
    // ... (Your existing sparkline code is fine) ...
    const w = 80; const h = 24;
    if (!arr || arr.length === 0) return <svg width={w} height={h}><rect width={w} height={h} fill="transparent"/></svg>;
    const max = Math.max(...arr, 1);
    const step = w / Math.max(arr.length - 1, 1);
    const points = arr.map((v, i) => `${Math.round(i * step)},${Math.round(h - (v / max) * (h - 4) - 2)}`).join(' ');
    return (
      <svg width={w} height={h} className="sparkline">
        <polyline points={points} fill="none" stroke="#0d6efd" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
      </svg>
    );
  };

  return (
    <div className="analytics-dashboard container-fluid mt-4">
      <div className="row g-3">
        {/* LEFT COLUMN: Occupancy */}
        <div className="col-12 col-md-4">
          <div className="card h-100 shadow-sm border-0">
            <div className="card-body">
              <h5 className="card-title text-muted mb-4">Occupation en Temps Réel</h5>
              <div className="chart-wrapper doughnut-wrapper" style={{ height: '220px' }}>
                <Doughnut data={doughnutData} options={doughnutOptions} />
              </div>
              <div className="d-flex justify-content-around mt-4 text-center">
                <div>
                  <h3 className="mb-0 fw-bold">{occupiedCount}</h3>
                  <small className="text-muted">Occupées</small>
                </div>
                <div>
                  <h3 className="mb-0 fw-bold">{freeCount}</h3>
                  <small className="text-muted">Libres</small>
                </div>
                <div>
                  <h3 className="mb-0 fw-bold text-warning">{anomalyCount}</h3>
                  <small className="text-muted">Anomalies</small>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* RIGHT COLUMN: Dwell Times & History */}
        <div className="col-12 col-md-8">
          <div className="card h-100 shadow-sm border-0">
            <div className="card-body">
              {/* Header with Actions */}
              <div className="d-flex justify-content-between align-items-center mb-3">
                <h5 className="card-title text-muted mb-0">Analyse des Temps de Séjour</h5>
                <button className="btn btn-sm btn-outline-primary d-flex align-items-center gap-2" onClick={exportCSV}>
                  <i className="bi bi-download"></i> Exporter le Rapport
                </button>
              </div>

              {/* Main Bar Chart */}
              <div className="chart-wrapper bar-wrapper" style={{ height: '250px' }}>
                <Bar data={barData} options={barOptions} />
              </div>

              {/* Data Table */}
              <div className="table-responsive mt-4">
                <table className="table table-hover table-sm align-middle">
                  <thead className="table-light">
                    <tr>
                      <th>Voie</th>
                      <th>Train</th>
                      <th>Arrivée</th>
                      <th>Durée</th>
                      <th>Historique (12h)</th>
                    </tr>
                  </thead>
                  <tbody>
                    {tracks.map((t, idx) => {
                      const h = hoursData[idx];
                      const history = tracksHistory[t.id] || [];
                      const isDanger = h >= alertThreshold;
                      const arrivalTime = t.timestamp ? new Date(t.timestamp).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'}) : '-';
                      
                      return (
                        <tr key={t.id} className={isDanger ? 'table-danger' : ''}>
                          <td className="fw-bold">Voie {t.id}</td>
                          <td>{t.trainId || <span className="text-muted">-</span>}</td>
                          <td>{arrivalTime}</td>
                          <td className={isDanger ? 'text-danger fw-bold' : ''}>
                            {formatDuration(h)}
                            {isDanger && <i className="bi bi-exclamation-triangle-fill ms-2"></i>}
                          </td>
                          <td style={{ width: '100px' }}>{renderSparkline(history)}</td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>

              <hr className="my-4" />

              {/* Previous Day Section (Cleaned up) */}
              <div className="row align-items-center">
                <div className="col-md-4">
                  <h6 className="text-muted">Comparaison : Journée Précédente</h6>
                  <p className="small text-muted mb-2">Moyenne globale des temps de stationnement.</p>
                  
                  <div className="d-flex align-items-end gap-3">
                    <div>
                      <span className="d-block small text-uppercase">Aujourd'hui</span>
                      <span className="fs-4 fw-bold text-primary">{currentAvg} h</span>
                    </div>
                    <div className="vr"></div>
                    <div>
                      <span className="d-block small text-uppercase">Hier</span>
                      <span className="fs-4 fw-bold text-secondary">{prevAvg} h</span>
                    </div>
                  </div>
                </div>
                <div className="col-md-8">
                  <div style={{ height: '120px' }}>
                     <Bar 
                       data={prevBarData} 
                       options={{
                         ...commonOptions, 
                         plugins: { legend: { display: false } },
                         scales: { x: { display: false }, y: { display: false } } // Sparkline style for history
                       }} 
                     />
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
