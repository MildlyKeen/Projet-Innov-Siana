import React from 'react';
import './MaintenanceCameraFeed.css';

const MaintenanceCameraFeed = () => {
  return (
    <div className="maintenance-camera-feed">
      <div className="camera-header">
        <h5 className="mb-0">📹 Caméra de Maintenance</h5>
        <small className="text-muted">Flux en direct du site avec détection ML</small>
      </div>
      <div className="video-container">
        <div className="video-section">
          <h6>Vidéo</h6>
          <video
            className="maintenance-video"
            controls
            autoPlay
            muted
            loop
            src="/videos/video.mp4"
          >
            Votre navigateur ne supporte pas la lecture vidéo.
          </video>
        </div>
      </div>
    </div>
  );
};

export default MaintenanceCameraFeed;