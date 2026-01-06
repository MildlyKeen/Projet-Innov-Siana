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

    const sortedByDuration = cameraEntries
      .sort((a, b) => (b.occupancy.video_duration_sec || 0) - (a.occupancy.video_duration_sec || 0));

    const selected = sortedByDuration.slice(0, 3).map((entry, index) => {
      const baseTrackIndex = index * 2 + 1;
      const normalizedTracks = (entry.occupancy.tracks || []).map((track, trackIdx) => {
        const match = /([0-9]+)/.exec(track.label || '');
        const localIndex = match ? Number(match[1]) : (trackIdx + 1);
        const globalIndex = baseTrackIndex + Math.max(0, localIndex - 1);
        return {
          ...track,
          global_index: globalIndex,
          global_label: `Voie ${globalIndex}`,
        };
      });

      const enrichedOccupancy = {
        ...entry.occupancy,
        tracks: normalizedTracks,
      };

      return {
        voie_index: index + 1,
        camera_label: `Caméra ${index + 1}`,
        folder: entry.camFolder,
        video_url: entry.videoUrl,
        video_duration_sec: entry.occupancy.video_duration_sec || 0,
        train_numbers: entry.occupancy.unique_train_numbers || [],
        occupancy: enrichedOccupancy,
      };
    });

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
