import React from 'react';
import './TrackMap.css';

const TrackMap = ({ tracks }) => {
  return (
    <div className="card track-map-card">
      <div className="card-header">
        <h5 className="mb-0">🛤️ Vue des Voies</h5>
      </div>
      <div className="card-body">
        <div className="track-container">
          {tracks.map((track) => (
            <div key={track.id} className="track-item mb-3">
              <div className="d-flex justify-content-between align-items-center mb-2">
                <div>
                  <strong>Voie {track.id}</strong>
                  <span className={`badge ms-2 ${track.status === 'occupied' ? 'bg-danger' : 'bg-success'}`}>
                    {track.status === 'occupied' ? 'Occupée' : 'Disponible'}
                  </span>
                </div>
                <div className="text-muted small">
                  Capacité: {track.currentLoad}/{track.capacity}
                </div>
              </div>
              <div className="track-visual">
                <div 
                  className="track-fill"
                  style={{ width: `${(track.currentLoad / track.capacity) * 100}%` }}
                >
                  {track.trainId && (
                    <span className="train-indicator">
                      🚂 {track.trainId}
                    </span>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default TrackMap;
