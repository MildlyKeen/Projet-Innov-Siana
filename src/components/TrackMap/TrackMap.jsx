import React, { useMemo, useRef, useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import './TrackMap.css';

/**
 * SmartYardMap (implemented in TrackMap.jsx slot)
 * - F1 telemetry inspired visual for a rail yard
 * - 6 parallel horizontal rails drawn in SVG
 * - 'Pucks' represent trains; their x is animated with framer-motion
 *
 * Props:
 * - tracksData: array of { id, label, train: { id, position, status, speed?, eta? } | null }
 */
const SmartYardMap = ({ tracksData = [] }) => {
  const containerRef = useRef(null);
  const [widthPx, setWidthPx] = useState(800);

  useEffect(() => {
    const el = containerRef.current;
    if (!el) return;
    const obs = new ResizeObserver((entries) => {
      for (const entry of entries) setWidthPx(entry.contentRect.width);
    });
    obs.observe(el);
    setWidthPx(el.clientWidth || 800);
    return () => obs.disconnect();
  }, []);

  const NUM = 6;
  // Normalize input to always have 6 tracks
  const tracks = useMemo(() => {
    const list = [];
    for (let i = 1; i <= NUM; i++) {
      const found = tracksData.find((t) => Number(t.id) === i);
      list.push(
        found || { id: i, label: `Voie ${i}`, train: null }
      );
    }
    return list;
  }, [tracksData]);

  // SVG layout constants
  const svgHeight = 160;
  const railPadding = 24;
  const trackSpacing = (svgHeight - railPadding * 2) / (NUM - 1);
  const leftMargin = 24;
  const rightMargin = 24;

  // helpers
  const xFromPct = (pct) => {
    const pctClamped = Math.max(0, Math.min(100, pct ?? 0));
    return leftMargin + ((widthPx - leftMargin - rightMargin) * pctClamped) / 100;
  };

  const colorFor = (status) => {
    if (status === 'occupied') return '#00ff85'; // neon green
    if (status === 'moving') return '#3b82f6'; // neon blue-ish
    if (status === 'anomaly') return '#ff4d4f'; // red
    return '#94a3b8';
  };

  return (
    <div ref={containerRef} className="smartyard-container rounded-md p-4 bg-slate-900">
      <div className="flex items-center justify-between mb-3">
        <h5 className="text-white text-sm font-semibold">SmartYard — Vue Synoptique</h5>
        <div className="text-xs text-slate-400">Mode: Télémétrie · {NUM} voies</div>
      </div>

      <div className="w-full overflow-hidden bg-transparent">
        <svg className="w-full" height={svgHeight} viewBox={`0 0 ${widthPx} ${svgHeight}`} preserveAspectRatio="xMidYMid meet">
          <defs>
            <linearGradient id="railGrad" x1="0" x2="1">
              <stop offset="0%" stopColor="#1f2937" stopOpacity="1" />
              <stop offset="50%" stopColor="#111827" stopOpacity="1" />
              <stop offset="100%" stopColor="#1f2937" stopOpacity="1" />
            </linearGradient>
            <filter id="glow" x="-50%" y="-50%" width="200%" height="200%">
              <feGaussianBlur stdDeviation="4" result="coloredBlur" />
              <feMerge>
                <feMergeNode in="coloredBlur" />
                <feMergeNode in="SourceGraphic" />
              </feMerge>
            </filter>
          </defs>

          {/* rails */}
          {tracks.map((t, i) => {
            const y = railPadding + i * trackSpacing;
            return (
              <g key={t.id}>
                {/* rail line */}
                <line x1={leftMargin} y1={y} x2={widthPx - rightMargin} y2={y}
                  stroke="url(#railGrad)" strokeWidth={2.2} strokeLinecap="round" />

                {/* markers: Arrival / Platform / Departure */}
                <rect x={leftMargin - 6} y={y - 6} width={12} height={12} rx={2} fill="#0f172a" stroke="#374151" />
                <rect x={(widthPx/2) - 6} y={y - 6} width={12} height={12} rx={2} fill="#0f172a" stroke="#374151" />
                <rect x={widthPx - rightMargin - 6} y={y - 6} width={12} height={12} rx={2} fill="#0f172a" stroke="#374151" />
              </g>
            );
          })}

          {/* trains (pucks) */}
          {tracks.map((t, i) => {
            const y = railPadding + i * trackSpacing;
            const train = t.train;
            if (!train) return null;
            const cx = xFromPct(train.position);
            const color = colorFor(train.status);

            return (
              <g key={`train-${t.id}`} className="train-group">
                <motion.circle
                  cx={cx}
                  cy={y}
                  r={8}
                  fill={color}
                  stroke="#001219"
                  strokeWidth={1}
                  filter="url(#glow)"
                  initial={{ cx: cx }}
                  animate={{ cx: cx }}
                  transition={{ type: 'tween', ease: 'linear', duration: 2 }}
                  whileHover={{ scale: 1.2 }}
                />

                <motion.text x={cx} y={y - 14} fontSize={11} fill="#ffffff" textAnchor="middle"
                  initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ duration: 0.6 }}>
                  {train.id}
                </motion.text>

                {/* tooltip as foreignObject */}
                <foreignObject x={cx - 60} y={y + 12} width={140} height={48} className="sy-fo">
                  <div xmlns="http://www.w3.org/1999/xhtml" className="sy-tooltip opacity-0 pointer-events-none">
                    <div className="text-xs text-slate-200"><strong>{train.id}</strong></div>
                    <div className="text-xs text-slate-300">Vitesse: {train.speed ?? '—'} km/h</div>
                    <div className="text-xs text-slate-300">ETA: {train.eta ?? '—'}</div>
                  </div>
                </foreignObject>
              </g>
            );
          })}
        </svg>
      </div>
    </div>
  );
};

export default SmartYardMap;
