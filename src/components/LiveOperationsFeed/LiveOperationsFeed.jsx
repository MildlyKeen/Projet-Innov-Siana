import React from 'react';
import './LiveOperationsFeed.css';

const LiveOperationsFeed = ({ events = [] }) => {
  const getEventIcon = (type) => {
    switch (type) {
      case 'success': return '✅';
      case 'error': return '❌';
      case 'warning': return '⚠️';
      case 'info': return 'ℹ️';
      default: return '📝';
    }
  };

  const getEventClass = (type) => {
    return `event-item event-${type}`;
  };

  return (
    <div className="live-operations-feed">
      <h5 className="feed-title">Flux d'Opérations en Direct</h5>
      <div className="feed-container">
        {events.length === 0 ? (
          <div className="no-events">Aucun événement récent</div>
        ) : (
          events.map((event) => (
            <div key={event.id} className={getEventClass(event.type)}>
              <div className="event-icon">{getEventIcon(event.type)}</div>
              <div className="event-content">
                <div className="event-message">{event.message}</div>
                <div className="event-meta">
                  <small className="event-time">
                    {new Date(event.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                  </small>
                  {event.trackLabel && (
                    <small className="event-track">{event.trackLabel}</small>
                  )}
                </div>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
};

export default LiveOperationsFeed;