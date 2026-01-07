import { getMockSnapshot } from './mockSnapshot';

const inferApiBase = () => {
  if (typeof window === 'undefined') return '';
  if (import.meta.env.VITE_API_BASE_URL) {
    return import.meta.env.VITE_API_BASE_URL.replace(/\/$/, '');
  }

  const { protocol, hostname, port } = window.location;
  if (port === '5173' || port === '4173') {
    return `${protocol}//${hostname}:3001`;
  }
  return `${protocol}//${hostname}${port ? `:${port}` : ''}`;
};

const API_BASE = inferApiBase();
const API_ENDPOINT = `${API_BASE}/api/voies`;

const toHours = (seconds) => {
  if (!seconds || Number.isNaN(seconds)) return 0;
  return seconds / 3600;
};

const ensureArray = (value) => (Array.isArray(value) ? value : []);

const deriveVideoDuration = (events) => {
  if (!events.length) return 0;
  const maxDeparture = events.reduce((max, evt) => {
    const departure = evt?.departure_time_sec ?? evt?.arrival_time_sec ?? 0;
    return departure > max ? departure : max;
  }, 0);
  return maxDeparture > 0 ? maxDeparture + 1 : 0;
};

const normalizeCamera = (camera, index) => {
  const voieIndex = camera?.voie_index ?? index + 1;
  const occupancy = camera?.occupancy || {};
  const events = ensureArray(occupancy.occupancy_events)
    .filter(Boolean)
    .map(evt => ({ ...evt }));

  const eventsByTrack = new Map();
  events.forEach(evt => {
    const key = (evt.track_label || `track_${evt.track_id || ''}`).toLowerCase();
    if (!eventsByTrack.has(key)) {
      eventsByTrack.set(key, []);
    }
    eventsByTrack.get(key).push(evt);
  });

  const tracksWithMeta = ensureArray(occupancy.tracks).map((track, trackIdx) => {
    const label = track?.label || `Voie ${trackIdx + 1}`;
    const labelKey = label.toLowerCase();
    const trackEvents = (eventsByTrack.get(labelKey) || []).slice().sort((a, b) => {
      const timeA = a?.generated_at ? new Date(a.generated_at).getTime() : 0;
      const timeB = b?.generated_at ? new Date(b.generated_at).getTime() : 0;
      return timeB - timeA;
    });
    const explicitIndex = Number(track?.global_index);
    const baseOffset = (Math.max(voieIndex, 1) - 1) * 2;
    const fallbackIndex = Number.isFinite(explicitIndex) && explicitIndex > 0
      ? explicitIndex
      : baseOffset + trackIdx + 1;
    const globalIndex = fallbackIndex;
    const uniqueTrains = track?.unique_trains
      || Array.from(new Set(trackEvents.map(evt => evt.train_number).filter(Boolean)));
    return {
      ...track,
      label,
      global_label: track?.global_label || `Voie ${globalIndex}`,
      global_index: globalIndex,
      total_duration_sec: track?.total_duration_sec || 0,
      count: track?.count ?? trackEvents.length,
      unique_trains: uniqueTrains,
      last_event: track?.last_event || trackEvents[0] || null,
    };
  });

  eventsByTrack.forEach((trackEvents, labelKey) => {
    const hasTrack = tracksWithMeta.some(track => (track.label || '').toLowerCase() === labelKey);
    if (hasTrack) return;
    const first = trackEvents[0];
    const baseOffset = (Math.max(voieIndex, 1) - 1) * 2;
    const derivedPosition = tracksWithMeta.length;
    const globalIndex = baseOffset + derivedPosition + 1;
    const label = first?.track_label || `Voie ${globalIndex}`;
    const uniqueTrains = Array.from(new Set(trackEvents.map(evt => evt.train_number).filter(Boolean)));
    tracksWithMeta.push({
      label,
      global_label: `Voie ${globalIndex}`,
      global_index: globalIndex,
      total_duration_sec: trackEvents.reduce((sum, evt) => sum + (evt.duration_sec || 0), 0),
      count: trackEvents.length,
      unique_trains: uniqueTrains,
      last_event: trackEvents.slice().sort((a, b) => {
        const timeA = a?.generated_at ? new Date(a.generated_at).getTime() : 0;
        const timeB = b?.generated_at ? new Date(b.generated_at).getTime() : 0;
        return timeB - timeA;
      })[0] || null,
    });
  });

  const trainNumbers = camera?.train_numbers
    || Array.from(new Set(events.map(evt => evt.train_number).filter(Boolean)));
  const videoDurationSec = camera?.video_duration_sec || deriveVideoDuration(events);

  return {
    ...camera,
    voie_index: voieIndex,
    occupancy: {
      ...occupancy,
      occupancy_events: events,
      tracks: tracksWithMeta,
    },
    train_numbers: trainNumbers,
    video_duration_sec: videoDurationSec,
  };
};

const deriveLastUpdated = (cameras) => {
  const timestamps = cameras.flatMap(cam => ensureArray(cam.occupancy?.occupancy_events)
    .map(evt => evt?.generated_at)
    .filter(Boolean));
  if (!timestamps.length) return null;
  const latest = timestamps.reduce((max, value) => {
    const ts = new Date(value).getTime();
    return ts > max ? ts : max;
  }, 0);
  return latest ? new Date(latest).toISOString() : null;
};

const normalizeSnapshot = (raw) => {
  if (!raw) {
    return { cameras: [], last_updated: null };
  }

  if (Array.isArray(raw)) {
    const normalizedCameras = raw.map((cam, idx) => normalizeCamera(cam, idx));
    return {
      cameras: normalizedCameras,
      last_updated: deriveLastUpdated(normalizedCameras),
    };
  }

  const sourceCameras = Array.isArray(raw.cameras)
    ? raw.cameras
    : Array.isArray(raw.selectedCameras)
      ? raw.selectedCameras
      : [];
  const normalizedCameras = sourceCameras.map((cam, idx) => normalizeCamera(cam, idx));
  return {
    ...raw,
    cameras: normalizedCameras,
    last_updated: raw.last_updated || deriveLastUpdated(normalizedCameras),
  };
};

const shouldUseMockData = () => {
  const flag = (import.meta.env?.VITE_USE_MOCK_DATA || '').toString().toLowerCase();
  return flag === 'true' || flag === '1';
};

const MOCK_CYCLE_SETTINGS = {
  2: {
    partner: 1,
    partnerPercent: 5,
    cycleLengthSec: 40,
    segments: [
      { start: 0, end: 40, percent: 100 },
    ],
  },
  4: {
    partner: 3,
    partnerPercent: 5,
    cycleLengthSec: 30,
    segments: [
      { start: 0, end: 30, percent: 100 },
    ],
  },
  6: {
    partner: 5,
    partnerPercent: 5,
    cycleLengthSec: 24,
    segments: [
      { start: 0, end: 24, percent: 100 },
    ],
  },
};

const findSegmentForPhase = (segments, phase) => {
  if (!Array.isArray(segments) || !segments.length) {
    return null;
  }
  const match = segments.find(segment => phase >= segment.start && phase < segment.end);
  return match || segments[segments.length - 1];
};

const applyMockCycleAdjustments = (tracks, referenceTs) => {
  if (!Array.isArray(tracks) || !tracks.length) {
    return;
  }

  const trackById = new Map(tracks.map(track => [track.id, track]));
  const nowSeconds = referenceTs / 1000;
  const timestampIso = new Date(referenceTs).toISOString();

  Object.entries(MOCK_CYCLE_SETTINGS).forEach(([trackIdStr, config]) => {
    const trackId = Number(trackIdStr);
    const targetTrack = trackById.get(trackId);
    if (!targetTrack) return;

    const cycleLength = config.cycleLengthSec || targetTrack.videoDurationSec || 1;
    const phase = ((nowSeconds % cycleLength) + cycleLength) % cycleLength;
    const segment = findSegmentForPhase(config.segments, phase);
    const percent = segment?.percent ?? 0;

    const videoDuration = targetTrack.videoDurationSec || cycleLength;
    const totalDurationSec = Number(((videoDuration * percent) / 100).toFixed(3));
    targetTrack.totalDurationSec = totalDurationSec;
    targetTrack.status = percent > 0 ? 'occupied' : 'free';
    targetTrack.utilizationPercent = percent;
    targetTrack.timestamp = timestampIso;
    if (!targetTrack.trainId && Array.isArray(targetTrack.uniqueTrains) && targetTrack.uniqueTrains.length) {
      targetTrack.trainId = targetTrack.uniqueTrains[targetTrack.uniqueTrains.length - 1];
    }
    targetTrack.history = [Number(toHours(totalDurationSec).toFixed(3))];

      const partnerTrack = config.partner ? trackById.get(config.partner) : null;
      if (partnerTrack) {
        const partnerPercent = config.partnerPercent ?? 5;
        const partnerVideo = partnerTrack.videoDurationSec || videoDuration;
        const partnerDurationSec = Number(((partnerVideo * partnerPercent) / 100).toFixed(3));
        partnerTrack.totalDurationSec = partnerDurationSec;
        partnerTrack.status = 'free';
        partnerTrack.utilizationPercent = partnerPercent;
        partnerTrack.timestamp = timestampIso;
        partnerTrack.trainId = null;
        partnerTrack.history = [Number(toHours(partnerDurationSec).toFixed(3))];
      }
  });
};

export async function fetchDashboardSnapshot() {
  if (!shouldUseMockData()) {
    try {
      const response = await fetch(API_ENDPOINT);
      if (!response.ok) {
        throw new Error(`API error ${response.status}`);
      }
      return response.json();
    } catch (err) {
      console.warn('[smartYardApi] Failed to load live data, falling back to mock snapshot.', err);
    }
  }

  return getMockSnapshot();
}

export function transformSnapshot(snapshot) {
  const normalized = normalizeSnapshot(snapshot);
  if (!normalized.cameras.length) {
    return {
      cameras: [],
      tracks: [],
      statistics: {
        activeTrains: 0,
        maintenanceTrains: 0,
        availableTrains: 0,
        availableTracks: 6,
        averageTraffic: 0,
      },
      trafficData: { labels: [], values: [] },
      trackUtilization: { labels: [], values: [] },
      tracksHistory: {},
      previousDayDwell: [],
      lastUpdated: null,
    };
  }

  const cameras = normalized.cameras;
  const isMockSnapshot = Boolean(normalized.__mock || normalized.mock || normalized.mockSnapshot);

  const parsedLastUpdated = normalized.last_updated ? new Date(normalized.last_updated) : null;
  const referenceTime = parsedLastUpdated && !Number.isNaN(parsedLastUpdated.getTime())
    ? parsedLastUpdated
    : new Date();
  const referenceTs = referenceTime.getTime();

  const trackMeta = new Map();
  const trackEvents = new Map();

  cameras.forEach(cam => {
    const labelMap = new Map();
    (cam.occupancy?.tracks || []).forEach(track => {
      if (!track || !track.global_index) {
        return;
      }
      labelMap.set((track.label || '').toLowerCase(), track.global_index);
      trackMeta.set(track.global_index, {
        id: track.global_index,
        label: track.global_label || `Voie ${track.global_index}`,
        totalDurationSec: track.total_duration_sec || 0,
        count: track.count || 0,
        uniqueTrains: track.unique_trains || [],
        lastEvent: track.last_event || null,
        cameraFolder: cam.folder,
        cameraLabel: cam.camera_label,
        videoDurationSec: cam.video_duration_sec || 0,
      });
    });

    (cam.occupancy?.occupancy_events || []).forEach(evt => {
      const keyLabel = (evt.track_label || `track_${evt.track_id || ''}`).toLowerCase();
      const globalIndex = labelMap.get(keyLabel);
      if (!globalIndex) return;
      const list = trackEvents.get(globalIndex) || [];
      list.push(evt);
      trackEvents.set(globalIndex, list);
    });
  });

  const tracks = Array.from(trackMeta.values())
    .sort((a, b) => a.id - b.id)
    .map(meta => {
      const events = (trackEvents.get(meta.id) || []).sort((a, b) => {
        const timeA = a.generated_at ? new Date(a.generated_at).getTime() : 0;
        const timeB = b.generated_at ? new Date(b.generated_at).getTime() : 0;
        return timeA - timeB;
      });

      const latestEvent = meta.lastEvent || events[events.length - 1] || null;
      const latestTrain = latestEvent?.train_number || meta.uniqueTrains.slice(-1)[0] || null;
      const timestamp = latestEvent?.generated_at || null;
      const eventTime = timestamp ? new Date(timestamp).getTime() : 0;
      const ageMs = eventTime ? Math.max(0, referenceTs - eventTime) : Infinity;
      const status = ageMs > 60 * 60 * 1000 ? 'free' : events.length > 0 ? 'occupied' : 'free';
      const history = events.slice(-12).map(evt => toHours(evt.duration_sec || 0));
      if (history.length === 0) {
        history.push(toHours(meta.totalDurationSec));
      }

      const utilizationPercent = meta.videoDurationSec
        ? Math.min(100, Math.round(((meta.totalDurationSec || 0) / meta.videoDurationSec) * 100))
        : 0;

      return {
        id: meta.id,
        label: meta.label,
        status,
        trainId: latestTrain,
        timestamp,
        totalDurationSec: meta.totalDurationSec,
        count: meta.count,
        uniqueTrains: meta.uniqueTrains,
        cameraFolder: meta.cameraFolder,
        cameraLabel: meta.cameraLabel,
        videoDurationSec: meta.videoDurationSec,
        history,
        events,
        utilizationPercent,
      };
    });

  if (isMockSnapshot) {
    applyMockCycleAdjustments(tracks, referenceTs);
  }

  const events = cameras.flatMap(cam => (cam.occupancy?.occupancy_events || []).map(evt => ({
    ...evt,
    camera_label: cam.camera_label,
    camera_folder: cam.folder,
    voie_index: cam.voie_index,
  })));

  events.sort((a, b) => {
    const timeA = a.generated_at ? new Date(a.generated_at).getTime() : 0;
    const timeB = b.generated_at ? new Date(b.generated_at).getTime() : 0;
    return timeB - timeA;
  });

  const occupiedTracks = tracks.filter(track => track.status === 'occupied');
  const occupiedTrainIds = new Set(occupiedTracks.flatMap(track => {
    if (Array.isArray(track.uniqueTrains) && track.uniqueTrains.length) {
      return track.uniqueTrains;
    }
    return track.trainId ? [track.trainId] : [];
  }));

  let activeTrainsCount = occupiedTrainIds.size;
  if (!activeTrainsCount) {
    const trainsWithNumber = new Set(events.filter(evt => evt.train_number).map(evt => evt.train_number));
    const fallbackTrainIds = new Set(events.map(evt => `${evt.camera_folder || 'cam'}-${evt.track_id || evt.track_label || 'x'}`));
    activeTrainsCount = trainsWithNumber.size || fallbackTrainIds.size || occupiedTracks.length;
  }

  const maintenanceThresholdHours = 4;
  const maintenanceTrainsCount = tracks.filter(track => {
    const totalHours = toHours(track.totalDurationSec);
    return totalHours >= maintenanceThresholdHours;
  }).length;

  const availableTracksCount = Math.max(0, 6 - occupiedTracks.length);

  const hourlyBuckets = new Map();
  for (let i = 23; i >= 0; i--) {
    const bucketDate = new Date(referenceTs - i * 60 * 60 * 1000);
    const label = `${String(bucketDate.getHours()).padStart(2, '0')}h`;
    hourlyBuckets.set(label, 0);
  }

  events.forEach(evt => {
    if (!evt.generated_at) return;
    const d = new Date(evt.generated_at);
    if (Number.isNaN(d.getTime())) return;
    const diffHours = Math.floor((referenceTs - d.getTime()) / (60 * 60 * 1000));
    if (diffHours < 24) {
      const label = `${String(d.getHours()).padStart(2, '0')}h`;
      if (hourlyBuckets.has(label)) {
        hourlyBuckets.set(label, (hourlyBuckets.get(label) || 0) + 1);
      }
    }
  });

  const trackUtilization = {
    labels: tracks.map(t => t.label),
    values: tracks.map(t => {
      if (typeof t.utilizationPercent === 'number') {
        return Math.max(0, Math.min(100, Math.round(t.utilizationPercent)));
      }
      if (!t.videoDurationSec) return 0;
      const ratio = (t.totalDurationSec / t.videoDurationSec) * 100;
      return Math.min(100, Math.round(ratio));
    }),
  };

  const tracksHistory = tracks.reduce((acc, track) => {
    acc[track.id] = track.history;
    return acc;
  }, {});

  const previousDayDwell = tracks.map(track => ({
    id: track.id,
    hours: Number(toHours(track.totalDurationSec).toFixed(2)),
  }));

  const statistics = {
    activeTrains: activeTrainsCount,
    maintenanceTrains: maintenanceTrainsCount,
    availableTrains: Math.max(0, activeTrainsCount - maintenanceTrainsCount),
    availableTracks: availableTracksCount,
    averageTraffic: Math.round(events.length / Math.max(1, occupiedTracks.length)),
  };

  const trafficLabels = Array.from(hourlyBuckets.keys());
  const trafficValues = trafficLabels.map(label => hourlyBuckets.get(label) || 0);
  const trafficData = {
    labels: trafficLabels,
    values: trafficValues,
  };

  return {
    cameras,
    tracks,
    statistics,
    trafficData,
    trackUtilization,
    tracksHistory,
    previousDayDwell,
    lastUpdated: parsedLastUpdated && !Number.isNaN(parsedLastUpdated.getTime()) ? referenceTime : null,
    events,
  };
}
