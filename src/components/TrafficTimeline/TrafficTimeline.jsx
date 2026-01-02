import React, { useState, useEffect, useMemo } from 'react';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend,
} from 'chart.js';
import { Bar } from 'react-chartjs-2';
import { getTracksState, getPreviousDayDwell, startSimulation } from '../../services/mockData';
import './TrafficTimeline.css';

ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend
);

const TrafficTimeline = () => {
  const [tracks, setTracks] = useState([]);
  const [previousDayDwell, setPreviousDayDwell] = useState([]);

  useEffect(() => {
    const unsubscribe = startSimulation((newTracks) => {
      setTracks(newTracks);
      setPreviousDayDwell(getPreviousDayDwell());
    });

    // Initial load
    setTracks(getTracksState());
    setPreviousDayDwell(getPreviousDayDwell());

    return unsubscribe;
  }, []);

  const chartData = useMemo(() => {
    const labels = tracks.map(track => `Voie ${track.id}`);
    const data = tracks.map(track => {
      if (track.status === 'occupied' || track.status === 'anomaly') {
        // Calculate current session duration in hours
        const startTime = new Date(track.timestamp);
        const now = new Date();
        const durationMs = now - startTime;
        return Math.round((durationMs / 1000 / 60 / 60) * 10) / 10; // hours with 1 decimal
      }
      // For previous day dwell
      const prev = previousDayDwell.find(p => p.id === track.id);
      return prev ? prev.hours : 0;
    });

    return {
      labels,
      datasets: [
        {
          label: 'Heures d\'occupation (actuel/jour précédent)',
          data,
          backgroundColor: tracks.map(track => {
            if (track.status === 'occupied') return 'rgba(54, 162, 235, 0.8)';
            if (track.status === 'anomaly') return 'rgba(255, 99, 132, 0.8)';
            return 'rgba(75, 192, 192, 0.8)'; // free or previous
          }),
          borderColor: tracks.map(track => {
            if (track.status === 'occupied') return 'rgba(54, 162, 235, 1)';
            if (track.status === 'anomaly') return 'rgba(255, 99, 132, 1)';
            return 'rgba(75, 192, 192, 1)';
          }),
          borderWidth: 1,
        },
      ],
    };
  }, [tracks, previousDayDwell]);

  const options = {
    indexAxis: 'y', // Horizontal bars
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'top',
      },
      title: {
        display: true,
        text: 'Chronologie du Trafic des Voies',
      },
    },
    scales: {
      x: {
        beginAtZero: true,
        title: {
          display: true,
          text: 'Heures d\'occupation',
        },
      },
      y: {
        title: {
          display: true,
          text: 'Voies',
        },
      },
    },
  };

  return (
    <div className="traffic-timeline">
      <div className="chart-container">
        <Bar data={chartData} options={options} />
      </div>
    </div>
  );
};

export default TrafficTimeline;