import React, { useMemo } from 'react';
import './MaintenanceHeatmap.css';

const MaintenanceHeatmap = ({ tracks = [], previousDayDwell = [] }) => {
  const dwellMap = useMemo(() => {
    return previousDayDwell.reduce((acc, entry) => {
      acc[entry.id] = entry.hours || 0;
      return acc;
    }, {});
  }, [previousDayDwell]);

  const getTrackClass = (track) => {
    let baseClass = 'track-cell';
    if (track.status === 'occupied') baseClass += ' status-occupied';
    else if (track.status === 'anomaly') baseClass += ' status-anomaly';
    else baseClass += ' status-free';

    // Add health indicator based on dwell time
    const dwellHours = dwellMap[track.id] || 0;
    if (dwellHours > 20) baseClass += ' health-high-usage';
    else if (dwellHours > 10) baseClass += ' health-medium-usage';
    else baseClass += ' health-low-usage';

    return baseClass;
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'occupied': return '🚂';
      case 'anomaly': return '⚠️';
      case 'free': return '✅';
      default: return '❓';
    }
  };

  const getHealthScore = (track) => {
    const dwellHours = dwellMap[track.id] || 0;
    // Simple health score: lower dwell time = better health
    const score = Math.max(0, 100 - (dwellHours * 2));
    return Math.round(score);
  };

  return (
    <div className="maintenance-heatmap">
      <h5 className="heatmap-title">Carte Thermique de Maintenance</h5>
      <div className="heatmap-grid">
        {tracks.map((track) => (
          <div key={track.id} className={getTrackClass(track)}>
            <div className="track-header">
              <span className="track-id">Voie {track.id}</span>
              <span className="track-status-icon">{getStatusIcon(track.status)}</span>
            </div>
            <div className="track-info">
              <div className="track-status">{track.status.toUpperCase()}</div>
              {track.trainId && (
                <div className="track-train">{track.trainId}</div>
              )}
              <div className="track-health">
                Santé: {getHealthScore(track)}%
              </div>
              <div className="track-dwell">
                {dwellMap[track.id] || 0}h (hier)
              </div>
            </div>
          </div>
        ))}
      </div>
      <div className="heatmap-legend">
        <div className="legend-item">
          <div className="legend-color status-free"></div>
          <span>Libre</span>
        </div>
        <div className="legend-item">
          <div className="legend-color status-occupied"></div>
          <span>Occupé</span>
        </div>
        <div className="legend-item">
          <div className="legend-color status-anomaly"></div>
          <span>Anomalie</span>
        </div>
      </div>
    </div>
  );
};

export default MaintenanceHeatmap;