const FPS = 30;

const createOccupancyEvent = ({
  cameraId,
  cameraFolder,
  trainNumber,
  trackLabel,
  trackId,
  arrivalSec,
  departureSec,
  generatedAt,
  eventIndex,
}) => {
  const durationSec = Math.max(0, departureSec - arrivalSec);
  if (durationSec <= 0) {
    return null;
  }
  const arrivalFrame = Math.round(arrivalSec * FPS);
  const departureFrame = Math.max(arrivalFrame + 1, Math.round(departureSec * FPS));
  const durationFrames = departureFrame - arrivalFrame;
  return {
    event_id: `${cameraFolder}-${trainNumber}-${eventIndex}`,
    event_type: 'TRACK_OCCUPANCY',
    state: 'OCCUPIED',
    track_label: trackLabel,
    track_id: trackId,
    train_track_id: trackId,
    train_number: trainNumber,
    camera_id: cameraId,
    arrival_frame: arrivalFrame,
    departure_frame: departureFrame,
    duration_frames: durationFrames,
    arrival_time_sec: Number(arrivalSec.toFixed(3)),
    departure_time_sec: Number(departureSec.toFixed(3)),
    duration_sec: Number(durationSec.toFixed(3)),
    generated_at: generatedAt,
    pipeline: {
      member: 'mock_member',
      version: 'mock_v1',
      fps_assumed: FPS,
    },
  };
};

const buildTrackMeta = ({
  label,
  trackId,
  globalIndex,
  totalDuration,
  count,
  uniqueTrains,
  lastEvent,
}) => ({
  label,
  track_id: trackId,
  global_index: globalIndex,
  global_label: `Voie ${globalIndex}`,
  total_duration_sec: totalDuration,
  count,
  unique_trains: uniqueTrains,
  last_event: lastEvent,
});

const generateCycleEvents = ({
  cameraId,
  cameraFolder,
  trainNumber,
  trackLabel,
  trackId,
  emptySeconds,
  occupiedUntil,
  cycles,
  now,
}) => {
  const cycleLengthSec = occupiedUntil;
  const events = [];
  for (let cycleIndex = 0; cycleIndex < cycles; cycleIndex += 1) {
    const cycleStart = cycleIndex * cycleLengthSec;
    const arrivalSec = cycleStart + emptySeconds;
    const departureSec = cycleStart + occupiedUntil;
    const generatedAt = new Date(now - (cycles - cycleIndex) * cycleLengthSec * 1000).toISOString();
    const event = createOccupancyEvent({
      cameraId,
      cameraFolder,
      trainNumber,
      trackLabel,
      trackId,
      arrivalSec,
      departureSec,
      generatedAt,
      eventIndex: cycleIndex,
    });
    if (event) {
      events.push(event);
    }
  }
  return {
    events,
    cycleLengthSec,
    videoDurationSec: cycleLengthSec * cycles,
  };
};

export function getMockSnapshot() {
  const now = Date.now();

  const voie2Pattern = generateCycleEvents({
    cameraId: 'cam_01',
    cameraFolder: 'cam1_1',
    trainNumber: '40034',
    trackLabel: 'voie2',
    trackId: 2,
    emptySeconds: 3,
    occupiedUntil: 20,
    cycles: 4,
    now,
  });

  const voie4Pattern = generateCycleEvents({
    cameraId: 'cam_02',
    cameraFolder: 'cam2_1',
    trainNumber: '91700',
    trackLabel: 'voie4',
    trackId: 4,
    emptySeconds: 1,
    occupiedUntil: 12,
    cycles: 4,
    now,
  });

  const voie6Pattern = generateCycleEvents({
    cameraId: 'cam_03',
    cameraFolder: 'cam3_2',
    trainNumber: '43983',
    trackLabel: 'voie6',
    trackId: 6,
    emptySeconds: 4,
    occupiedUntil: 8,
    cycles: 4,
    now,
  });

  const cameras = [
    {
      voie_index: 1,
      camera_label: 'Camera 1 (Voies 1-2)',
      folder: 'cam1_1',
      video_url: 'http://localhost:3001/streams/cam1_1/outputs/m2/output_fixed.mp4',
      video_duration_sec: voie2Pattern.videoDurationSec,
      train_numbers: ['40034'],
      occupancy: {
        total_events: voie2Pattern.events.length,
        occupancy_events: voie2Pattern.events,
        tracks: [
          buildTrackMeta({
            label: 'voie1',
            trackId: 1,
            globalIndex: 1,
            totalDuration: voie2Pattern.videoDurationSec,
            count: 0,
            uniqueTrains: [],
            lastEvent: null,
          }),
          buildTrackMeta({
            label: 'voie2',
            trackId: 2,
            globalIndex: 2,
            totalDuration: voie2Pattern.videoDurationSec,
            count: voie2Pattern.events.length,
            uniqueTrains: ['40034'],
            lastEvent: voie2Pattern.events.length ? voie2Pattern.events[voie2Pattern.events.length - 1] : null,
          }),
        ],
        unique_train_numbers: ['40034'],
        video_duration_sec: voie2Pattern.videoDurationSec,
        last_generated_at: voie2Pattern.events.length ? voie2Pattern.events[voie2Pattern.events.length - 1].generated_at : new Date(now).toISOString(),
      },
    },
    {
      voie_index: 2,
      camera_label: 'Camera 2 (Voies 3-4)',
      folder: 'cam2_1',
      video_url: 'http://localhost:3001/streams/cam2_1/outputs/m2/output_fixed.mp4',
      video_duration_sec: voie4Pattern.videoDurationSec,
      train_numbers: ['31700'],
      occupancy: {
        total_events: voie4Pattern.events.length,
        occupancy_events: voie4Pattern.events,
        tracks: [
          buildTrackMeta({
            label: 'voie3',
            trackId: 3,
            globalIndex: 3,
            totalDuration: voie4Pattern.videoDurationSec,
            count: 0,
            uniqueTrains: [],
            lastEvent: null,
          }),
          buildTrackMeta({
            label: 'voie4',
            trackId: 4,
            globalIndex: 4,
            totalDuration: voie4Pattern.videoDurationSec,
            count: voie4Pattern.events.length,
            uniqueTrains: ['31700'],
            lastEvent: voie4Pattern.events.length ? voie4Pattern.events[voie4Pattern.events.length - 1] : null,
          }),
        ],
        unique_train_numbers: ['31700'],
        video_duration_sec: voie4Pattern.videoDurationSec,
        last_generated_at: voie4Pattern.events.length ? voie4Pattern.events[voie4Pattern.events.length - 1].generated_at : new Date(now).toISOString(),
      },
    },
    {
      voie_index: 3,
      camera_label: 'Camera 3 (Voies 5-6)',
      folder: 'cam3_2',
      video_url: 'http://localhost:3001/streams/cam3_2/outputs/m2/output_fixed.mp4',
      video_duration_sec: voie6Pattern.videoDurationSec,
      train_numbers: ['43983'],
      occupancy: {
        total_events: voie6Pattern.events.length,
        occupancy_events: voie6Pattern.events,
        tracks: [
          buildTrackMeta({
            label: 'voie5',
            trackId: 5,
            globalIndex: 5,
            totalDuration: voie6Pattern.videoDurationSec,
            count: 0,
            uniqueTrains: [],
            lastEvent: null,
          }),
          buildTrackMeta({
            label: 'voie6',
            trackId: 6,
            globalIndex: 6,
            totalDuration: voie6Pattern.videoDurationSec,
            count: voie6Pattern.events.length,
            uniqueTrains: ['43983'],
            lastEvent: voie6Pattern.events.length ? voie6Pattern.events[voie6Pattern.events.length - 1] : null,
          }),
        ],
        unique_train_numbers: ['43983'],
        video_duration_sec: voie6Pattern.videoDurationSec,
        last_generated_at: voie6Pattern.events.length ? voie6Pattern.events[voie6Pattern.events.length - 1].generated_at : new Date(now).toISOString(),
      },
    },
  ];

  const lastUpdated = new Date(now).toISOString();

  return {
    __mock: true,
    cameras,
    stats: {
      activeTrains: 3,
      maintenanceTrains: 0,
      availableTrains: 0,
      availableTracks: 3,
      averageTraffic: 3,
    },
    traffic: {
      labels: ['01h', '02h', '03h'],
      values: [4, 3, 2],
    },
    last_updated: lastUpdated,
  };
}

export default getMockSnapshot;
