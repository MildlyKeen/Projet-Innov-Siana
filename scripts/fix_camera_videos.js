import { spawnSync } from 'node:child_process';
import { copyFileSync, existsSync, mkdirSync } from 'node:fs';
import path from 'node:path';
import ffmpegPath from 'ffmpeg-static';

const CAMS = ['cam1_1', 'cam1_2', 'cam2_1', 'cam2_2', 'cam3_1', 'cam3_2'];
const ROOT = path.resolve('outputs_for_backend');
const DEST_ROOT = path.resolve('M1_M2_M3', 'inputs', 'videos');

if (!ffmpegPath) {
  console.error('ffmpeg-static did not provide a binary path.');
  process.exit(1);
}

mkdirSync(DEST_ROOT, { recursive: true });

function transcodeCamera(cam) {
  const inputPath = path.join(ROOT, cam, 'outputs', 'm2', 'ocr_annotated.mp4');
  const outputPath = path.join(ROOT, cam, 'outputs', 'm2', 'output_fixed.mp4');

  if (!existsSync(inputPath)) {
    console.warn(`Skipping ${cam}: missing ${inputPath}`);
    return;
  }

  console.log(`\n▶ Processing ${cam}`);
  console.log(`   Input : ${inputPath}`);
  console.log(`   Output: ${outputPath}`);

  const ffmpegArgs = [
    '-y',
    '-i', inputPath,
    '-c:v', 'libx264',
    '-crf', '23',
    '-preset', 'medium',
    '-c:a', 'aac',
    '-b:a', '128k',
    '-movflags', '+faststart',
    outputPath,
  ];

  const result = spawnSync(ffmpegPath, ffmpegArgs, { stdio: 'inherit' });

  if (result.status !== 0) {
    throw new Error(`ffmpeg failed for ${cam}`);
  }

  const destPath = path.join(DEST_ROOT, `${cam}_output_fixed.mp4`);
  copyFileSync(outputPath, destPath);
  console.log(`✅ Copied to ${destPath}`);
}

try {
  CAMS.forEach(transcodeCamera);
  console.log('\nAll camera videos processed successfully.');
} catch (err) {
  console.error(`\n✗ Error: ${err.message}`);
  process.exit(1);
}
