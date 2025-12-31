import React, { useState, useEffect } from 'react';
import { getRecentEvents, startSimulation } from '../../services/mockData';
import './LiveOperationsFeed.css';

const LiveOperationsFeed = () => {
  const [events, setEvents] = useState([]);

  useEffect(() => {
    const unsubscribe = startSimulation((tracks) => {
      // Update events whenever simulation ticks
      setEvents(getRecentEvents());
    });

    // Initial load
    setEvents(getRecentEvents());

    return unsubscribe;
  }, []);

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
                    {new Date(event.timestamp).toLocaleTimeString()}
                  </small>
                  {event.trackId && (
                    <small className="event-track">Voie {event.trackId}</small>
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