import React, { useState, useEffect } from 'react';
import { getTracksState, startSimulation } from '../../services/mockData';
import './TrackMap.css';

const TrackMap = () => {
  const [tracks, setTracks] = useState(() => getTracksState());

  useEffect(() => {
    // Start simulation with real-time updates
    const unsubscribe = startSimulation((updatedTracks) => {
      setTracks(updatedTracks);
    });

    // Cleanup on unmount
    return () => unsubscribe();
  }, []);

  const getTrackStatusClass = (status) => {
    switch (status) {
      case 'occupied':
        return 'track-occupied';
      case 'anomaly':
        return 'track-anomaly';
      case 'free':
      default:
        return 'track-free';
    }
  };

  const getTrackStatusText = (status) => {
    switch (status) {
      case 'occupied':
        return 'Occupée';
      case 'anomaly':
        return 'Anomalie';
      case 'free':
      default:
        return 'Libre';
    }
  };

  return (
    <div className="card track-map-card">
      <div className="card-header">
        <h5 className="mb-0">🛤️ Vue des Voies</h5>
      </div>
      <div className="card-body">
        <div className="tracks-grid">
          {tracks.map((track) => (
            <div key={track.id} className="track-wrapper">
              <div className="track-label">
                <strong>Voie {track.id}</strong>
                <span className="track-status-text">{getTrackStatusText(track.status)}</span>
              </div>
              <div className={`track-rail ${getTrackStatusClass(track.status)}`}>
                {track.status === 'anomaly' && (
                  <span className="track-content">
                    <span className="alert-icon">⚠️</span>
                    {track.trainId && <span className="train-id">{track.trainId}</span>}
                  </span>
                )}
                {track.status === 'occupied' && track.trainId && (
                  <span className="track-content">
                    <span className="train-icon">🚂</span>
                    <span className="train-id">{track.trainId}</span>
                  </span>
                )}
                {track.status === 'free' && (
                  <span className="track-content">
                    <span className="free-text">Disponible</span>
                  </span>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default TrackMap;
