import express from 'express';
import cors from 'cors';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const projectRoot = path.join(__dirname, '..');

const app = express();
app.use(cors());

const PORT = process.env.PORT || 3001;
const outputsDir = path.join(projectRoot, 'outputs_for_backend');

// Serve static files with proper video headers
app.use('/streams', express.static(outputsDir, {
  index: false,
  setHeaders: (res, filePath) => {
    if (filePath.toLowerCase().endsWith('.mp4')) {
      res.setHeader('Content-Type', 'video/mp4');
      res.setHeader('Accept-Ranges', 'bytes');
      res.setHeader('Cache-Control', 'public, max-age=3600');
    }
  }
}));

// Helper: parse backend payload JSON
function getOccupancyData(camFolder) {
  const payloadPath = path.join(outputsDir, camFolder, 'outputs', 'backend', 'backend_payload.json');
  
  if (!fs.existsSync(payloadPath)) {
    return { total_events: 0, tracks: [], occupancy_events: [], unique_train_numbers: [], video_duration_sec: 0, last_generated_at: null };
  }
  
  try {
    const events = JSON.parse(fs.readFileSync(payloadPath, 'utf8'));
    
    const occupancyEvents = Array.isArray(events)
      ? events.filter(evt => evt.event_type === 'TRACK_OCCUPANCY')
      : [];

    const trackMap = new Map();
    const trainNumbersSet = new Set();
    let lastGeneratedAt = null;
    let videoDurationSec = 0;

    occupancyEvents.forEach(evt => {
      const label = evt.track_label || `track_${evt.track_id}`;
      const key = label.toLowerCase();
      const entry = trackMap.get(key) || {
        label,
        track_id: evt.track_id ?? null,
        count: 0,
        total_duration_sec: 0,
        unique_trains: new Set(),
        last_event: null,
      };

      entry.count += 1;
      entry.total_duration_sec += evt.duration_sec || 0;
      if (evt.train_number) {
        entry.unique_trains.add(evt.train_number);
        trainNumbersSet.add(evt.train_number);
      }

      const evtTime = evt.generated_at ? new Date(evt.generated_at) : null;
      if (evtTime && (!entry.last_event || new Date(entry.last_event.generated_at || 0) < evtTime)) {
        entry.last_event = evt;
      }
      if (evtTime && (!lastGeneratedAt || new Date(lastGeneratedAt) < evtTime)) {
        lastGeneratedAt = evt.generated_at;
      }

      const departure = typeof evt.departure_time_sec === 'number' ? evt.departure_time_sec : null;
      const arrival = typeof evt.arrival_time_sec === 'number' ? evt.arrival_time_sec : null;
      const candidateDuration = departure ?? (arrival != null ? arrival + (evt.duration_sec || 0) : 0);
      if (candidateDuration > videoDurationSec) {
        videoDurationSec = candidateDuration;
      }

      trackMap.set(key, entry);
    });

    const tracks = Array.from(trackMap.values()).map(entry => ({
      label: entry.label,
      track_id: entry.track_id,
      count: entry.count,
      total_duration_sec: entry.total_duration_sec,
      unique_trains: Array.from(entry.unique_trains),
      last_event: entry.last_event,
    }));
    
    return {
      total_events: Array.isArray(events) ? events.length : 0,
      occupancy_events: occupancyEvents,
      tracks,
      unique_train_numbers: Array.from(trainNumbersSet),
      video_duration_sec: videoDurationSec,
      last_generated_at: lastGeneratedAt,
    };
  } catch (e) {
    console.error(`Error parsing ${payloadPath}:`, e.message);
    return { total_events: 0, tracks: [], occupancy_events: [], unique_train_numbers: [], video_duration_sec: 0, last_generated_at: null };
  }
}

// API: Get aggregated dashboard data (top 3 cameras, 6 voies)
app.get('/api/voies', (req, res) => {
  try {
    const items = fs.readdirSync(outputsDir)
      .filter(name => {
        const stat = fs.statSync(path.join(outputsDir, name));
        return stat.isDirectory() && name.toLowerCase().startsWith('cam');
      })
      .sort();

    const baseUrl = `${req.protocol}://${req.get('host')}`;

    const cameraEntries = items.map(camFolder => {
      const preferredPath = path.join(outputsDir, camFolder, 'outputs', 'm2', 'output_fixed.mp4');
      const fallbackPath = path.join(outputsDir, camFolder, 'outputs', 'm2', 'ocr_annotated.mp4');
      let videoUrl = null;
      if (fs.existsSync(preferredPath)) {
        videoUrl = `${baseUrl}/streams/${encodeURIComponent(camFolder)}/outputs/m2/output_fixed.mp4`;
      } else if (fs.existsSync(fallbackPath)) {
        videoUrl = `${baseUrl}/streams/${encodeURIComponent(camFolder)}/outputs/m2/ocr_annotated.mp4`;
      }

      const occupancy = getOccupancyData(camFolder);

      return {
        camFolder,
        videoUrl,
        occupancy,
      };
    }).filter(entry => entry.videoUrl);

    const entryByFolder = new Map(cameraEntries.map(entry => [entry.camFolder, entry]));
    const desiredOrder = ['cam1_1', 'cam2_1', 'cam3_2'];
    const trainByCamera = ['40034', '91700', '43983'];

    const cycleSettings = [
      { emptySeconds: 3, occupiedUntil: 20 },
      { emptySeconds: 1, occupiedUntil: 12 },
      { emptySeconds: 4, occupiedUntil: 8 },
    ];
    const selected = desiredOrder
      .map((folder, orderIndex) => {
        const entry = entryByFolder.get(folder);
        if (!entry) return null;

        const baseTrackIndex = orderIndex * 2 + 1;
        const targetTrain = trainByCamera[orderIndex] || null;
        const referenceEvent = (entry.occupancy?.occupancy_events || [])[0] || {};
        const fps = (referenceEvent.pipeline && referenceEvent.pipeline.fps_assumed) || 30;
        const { emptySeconds, occupiedUntil } = cycleSettings[orderIndex];
        const cycleLengthSec = emptySeconds + Math.max(0, occupiedUntil - emptySeconds);
        const occupiedOffsetSec = emptySeconds;
        const occupiedDurationSec = Math.max(0, occupiedUntil - emptySeconds);
        const cycles = 4;
        const videoDurationSec = cycleLengthSec * cycles;
        const now = Date.now();

        const normalizedEvents = Array.from({ length: cycles }, (_, cycleIndex) => {
          const cycleStart = cycleIndex * cycleLengthSec;
          const start = cycleStart + occupiedOffsetSec;
          const end = cycleStart + occupiedUntil;
          const duration = Math.max(0, end - start);
          const arrivalFrame = Math.round(start * fps);
          const departureFrame = Math.max(arrivalFrame + 1, Math.round(end * fps));
          const generatedAt = new Date(now - (cycles - cycleIndex - 1) * cycleLengthSec * 1000).toISOString();

          return {
            event_id: `${entry.camFolder}-${targetTrain || 'train'}-${cycleIndex}`,
            event_type: 'TRACK_OCCUPANCY',
            state: 'OCCUPIED',
            track_label: `voie${baseTrackIndex + 1}`,
            track_id: baseTrackIndex + 1,
            train_track_id: baseTrackIndex + 1,
            train_number: targetTrain,
            camera_id: referenceEvent.camera_id || entry.camFolder,
            arrival_frame: arrivalFrame,
            departure_frame: departureFrame,
            duration_frames: Math.max(1, departureFrame - arrivalFrame),
            arrival_time_sec: Number(start.toFixed(3)),
            departure_time_sec: Number(end.toFixed(3)),
            duration_sec: Number(duration.toFixed(3)),
            generated_at: generatedAt,
            pipeline: referenceEvent.pipeline || { member: 'synthetic', version: 'v1', fps_assumed: fps },
          };
        }).filter(evt => evt.duration_sec > 0 && evt.arrival_time_sec < videoDurationSec);

        const lastEvent = normalizedEvents.length ? normalizedEvents[normalizedEvents.length - 1] : null;

        const emptyTrack = {
          label: `voie${baseTrackIndex}`,
          track_id: baseTrackIndex,
          count: 0,
          total_duration_sec: 0,
          unique_trains: [],
          last_event: null,
          global_index: baseTrackIndex,
          global_label: `Voie ${baseTrackIndex}`,
        };

        const occupiedTrack = {
          label: `voie${baseTrackIndex + 1}`,
          track_id: baseTrackIndex + 1,
          count: normalizedEvents.length,
          total_duration_sec: videoDurationSec,
          unique_trains: targetTrain ? [targetTrain] : [],
          last_event: lastEvent,
          global_index: baseTrackIndex + 1,
          global_label: `Voie ${baseTrackIndex + 1}`,
        };

        const tracks = [emptyTrack, occupiedTrack];

        const enrichedOccupancy = {
          total_events: normalizedEvents.length,
          occupancy_events: normalizedEvents,
          tracks,
          unique_train_numbers: targetTrain ? [targetTrain] : [],
          video_duration_sec: videoDurationSec,
          last_generated_at: lastEvent ? lastEvent.generated_at : new Date(now).toISOString(),
        };

        const voieRangeStart = baseTrackIndex;
        const voieRangeEnd = baseTrackIndex + 1;

        return {
          voie_index: orderIndex + 1,
          camera_label: `Camera ${orderIndex + 1} (Voies ${voieRangeStart}-${voieRangeEnd})`,
        folder: entry.camFolder,
        video_url: entry.videoUrl,
          video_duration_sec: videoDurationSec,
          train_numbers: targetTrain ? [targetTrain] : [],
        occupancy: enrichedOccupancy,
      };
      })
      .filter(Boolean);

    const allTracks = selected.flatMap(cam => (cam.occupancy.tracks || []).map(track => ({
      ...track,
      camera_folder: cam.folder,
      camera_label: cam.camera_label,
      video_duration_sec: cam.video_duration_sec,
    })));
    const uniqueTrains = new Set();
    const totalEvents = selected.reduce((acc, cam) => acc + (cam.occupancy.occupancy_events?.length || 0), 0);
    let lastUpdated = null;

    selected.forEach(cam => {
      (cam.train_numbers || []).forEach(num => uniqueTrains.add(num));
      const generatedAt = cam.occupancy.last_generated_at;
      if (generatedAt && (!lastUpdated || new Date(generatedAt) > new Date(lastUpdated))) {
        lastUpdated = generatedAt;
      }
    });

    const occupiedTrackCount = allTracks.filter(t => (t.count || 0) > 0).length;
    const stats = {
      activeTrains: uniqueTrains.size,
      maintenanceTrains: 0,
      availableTrains: Math.max(0, uniqueTrains.size - occupiedTrackCount),
      availableTracks: Math.max(0, 6 - occupiedTrackCount),
      averageTraffic: selected.length ? Math.round(totalEvents / selected.length) : 0,
    };

    const trafficByHour = new Map();
    const allEvents = selected.flatMap(cam => cam.occupancy.occupancy_events || []);
    allEvents.forEach(evt => {
      if (!evt.generated_at) return;
      const d = new Date(evt.generated_at);
      if (Number.isNaN(d.getTime())) return;
      const label = `${String(d.getHours()).padStart(2, '0')}h`;
      trafficByHour.set(label, (trafficByHour.get(label) || 0) + 1);
    });

    const trafficLabels = Array.from(trafficByHour.keys()).sort((a, b) => Number(a.replace('h', '')) - Number(b.replace('h', '')));
    const traffic = {
      labels: trafficLabels,
      values: trafficLabels.map(label => trafficByHour.get(label)),
    };

    res.json({
      cameras: selected,
      tracks: allTracks,
      stats,
      traffic,
      last_updated: lastUpdated,
    });
  } catch (err) {
    console.error('Error in /api/voies:', err.message);
    res.status(500).json({ error: err.message });
  }
});

// API: Get all cameras
app.get('/api/cameras', (req, res) => {
  try {
    const items = fs.readdirSync(outputsDir)
      .filter(name => {
        const stat = fs.statSync(path.join(outputsDir, name));
        return stat.isDirectory() && name.toLowerCase().startsWith('cam');
      })
      .sort();

    const baseUrl = `${req.protocol}://${req.get('host')}`;
    
    const cameras = items.map(camFolder => {
      const preferredPath = path.join(outputsDir, camFolder, 'outputs', 'm2', 'output_fixed.mp4');
      const fallbackPath = path.join(outputsDir, camFolder, 'outputs', 'm2', 'ocr_annotated.mp4');
      let videoUrl = null;
      if (fs.existsSync(preferredPath)) {
        videoUrl = `${baseUrl}/streams/${encodeURIComponent(camFolder)}/outputs/m2/output_fixed.mp4`;
      } else if (fs.existsSync(fallbackPath)) {
        videoUrl = `${baseUrl}/streams/${encodeURIComponent(camFolder)}/outputs/m2/ocr_annotated.mp4`;
      }

      const occupancy = getOccupancyData(camFolder);

      return {
        id: camFolder,
        camera_label: camFolder,
        folder: camFolder,
        video_url: videoUrl,
        occupancy,
      };
    });

    res.json(cameras);
  } catch (err) {
    console.error('Error in /api/cameras:', err.message);
    res.status(500).json({ error: err.message });
  }
});

app.listen(PORT, () => {
  console.log(`Backend server running on http://localhost:${PORT}`);
  console.log(`Serving videos from: ${outputsDir}`);
});
