import React from 'react';
import './MaintenanceCameraFeed.css';

const MaintenanceCameraFeed = () => {
  return (
    <div className="maintenance-camera-feed">
      <div className="camera-header">
        <h5 className="mb-0">📹 Caméra de Maintenance</h5>
        <small className="text-muted">Flux en direct du site</small>
      </div>
      <div className="video-container">
        <video
          className="maintenance-video"
          controls
          autoPlay
          muted
          loop
          src="/maintenance-video.mp4"
          poster="/maintenance-poster.jpg" // optional poster image
        >
          Votre navigateur ne supporte pas la lecture vidéo.
        </video>
      </div>
    </div>
  );
};

export default MaintenanceCameraFeed;