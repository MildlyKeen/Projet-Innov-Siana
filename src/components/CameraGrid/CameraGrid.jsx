import React, { useEffect, useState } from 'react';
import './CameraGrid.css';

export default function CameraGrid() {
  const [voies, setVoies] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchVoies = async () => {
      try {
        console.log('Fetching from /api/voies...');
        const res = await fetch('/api/voies');
        console.log('Response status:', res.status);
        if (!res.ok) {
          const text = await res.text();
          throw new Error(`HTTP ${res.status}: ${text}`);
        }
        const data = await res.json();
        console.log('Fetched data:', data);
        setVoies(data);
        setError(null);
        setLoading(false);
      } catch (err) {
        console.error('Fetch error:', err);
        setError(err.message);
        setLoading(false);
      }
    };

    fetchVoies();
    const interval = setInterval(fetchVoies, 5000); // Refresh every 5s
    return () => clearInterval(interval);
  }, []);

  if (loading) {
    return (
      <div style={{ padding: '20px', textAlign: 'center', color: '#666' }}>
        <h3>Loading cameras...</h3>
        <p>Fetching data from backend API</p>
      </div>
    );
  }

  if (error) {
    return (
      <div style={{ padding: '20px', background: '#ffebee', border: '1px solid #ef5350', borderRadius: '4px', color: '#c62828' }}>
        <h3>Error loading cameras:</h3>
        <p>{error}</p>
        <details style={{ marginTop: '10px', cursor: 'pointer' }}>
          <summary>Debug Info</summary>
          <pre style={{ background: '#fff', padding: '10px', marginTop: '10px', overflowX: 'auto' }}>
Check browser console (F12) for full error details
          </pre>
        </details>
      </div>
    );
  }

  return (
    <div className="camera-grid-container">
      <h2>Caméras des Voies</h2>
      <div className="camera-grid">
        {voies.map(voie => (
          <div key={voie.voie_index} className="camera-card">
            <div className="camera-header">
              <h3>{voie.camera_label}</h3>
              <span className="event-count">
                {voie.occupancy?.total_events || 0} événements
              </span>
            </div>
            
            {voie.video_url ? (
              <video
                className="camera-video"
                src={voie.video_url}
                controls
                muted
                playsInline
              />
            ) : (
              <div className="camera-placeholder">Vidéo non disponible</div>
            )}
            
            {voie.occupancy?.tracks && voie.occupancy.tracks.length > 0 && (
              <div className="camera-occupancy">
                <h4>Voies Occupées</h4>
                {voie.occupancy.tracks.map((track, idx) => (
                  <div key={idx} className="track-info">
                    <span className="track-label">{track.label}</span>
                    <span className="track-stats">
                      {track.count} x {track.total_duration_sec?.toFixed(1)}s
                    </span>
                  </div>
                ))}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
