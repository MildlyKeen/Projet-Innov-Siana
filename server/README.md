Backend server for serving pipeline outputs and simple APIs

Run (from project root):

```bash
npm install
npm run serve:backend
# or: node server/index.js
```

Endpoints:
- `GET /api/cameras` — list all camera folders found in `outputs_for_backend` with `video_url` (if overlay mp4 found) and `occupied_tracks` (if present in backend payloads).
- `GET /api/voies` — returns exactly 6 voie-mapped camera entries labeled `Camera Voie 1..6` (picks first 6 cam* folders alphabetically).
- `GET /api/backend/:cam/payload` — returns nearest `backend_payload.json` for a given camera folder.
- Static: `/streams/...` serves the `outputs_for_backend` tree; `/input_videos/...` serves `M1_M2_M3/inputs/videos`.

Notes on video playback issues:
- Browsers expect MP4s with H.264/AAC and the `moov` atom at the start (faststart). If a video does not play in the browser, try remuxing with ffmpeg:

```
ffmpeg -i in.mp4 -c copy -movflags +faststart out_fixed.mp4
```

If remuxing fails, re-encode to H.264/AAC:

```
ffmpeg -i in.mp4 -c:v libx264 -crf 23 -preset medium -c:a aac -b:a 128k -movflags +faststart out_fixed.mp4
```

If you need the server to do range requests or advanced streaming handling, we can enhance `server/index.js` accordingly.
