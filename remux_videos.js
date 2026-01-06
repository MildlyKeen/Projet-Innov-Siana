#!/usr/bin/env node
/**
 * Remux MP4 files to add faststart (moov atom at beginning) for browser streaming.
 * Uses ffmpeg-static if available, otherwise looks for system ffmpeg.
 */

const fs = require('fs');
const path = require('path');
const { execSync, spawnSync } = require('child_process');

const outputsDir = 'outputs_for_backend';

function findMp4Files() {
  const mp4Files = [];
  
  function walk(dir) {
    const files = fs.readdirSync(dir);
    files.forEach(file => {
      const filePath = path.join(dir, file);
      const stat = fs.statSync(filePath);
      if (stat.isDirectory()) {
        walk(filePath);
      } else if (file.toLowerCase().endsWith('.mp4')) {
        mp4Files.push(filePath);
      }
    });
  }
  
  walk(outputsDir);
  return mp4Files;
}

function getFfmpegPath() {
  // Try to use ffmpeg-static first
  try {
    const ffmpegStatic = require('ffmpeg-static');
    if (ffmpegStatic && fs.existsSync(ffmpegStatic)) {
      console.log(`Using ffmpeg-static from: ${ffmpegStatic}\n`);
      return ffmpegStatic;
    }
  } catch (e) {
    // ffmpeg-static not available
  }
  
  // Fall back to system ffmpeg
  try {
    execSync('ffmpeg -version', { stdio: 'ignore' });
    return 'ffmpeg';
  } catch (e) {
    return null;
  }
}

function remuxWithFfmpeg(ffmpegPath) {
  const mp4Files = findMp4Files();
  
  if (mp4Files.length === 0) {
    console.log('No MP4 files found in outputs_for_backend');
    process.exit(0);
  }
  
  console.log(`Found ${mp4Files.length} MP4 files to remux`);
  console.log('Remuxing with ffmpeg (fast, non-destructive)...\n');
  
  let successCount = 0;
  let failCount = 0;
  
  mp4Files.forEach((file, idx) => {
    console.log(`[${idx + 1}/${mp4Files.length}] Processing: ${file}`);
    
    try {
      const tempFile = file + '.temp.mp4';
      
      // Use ffmpeg to remux with faststart (copy codec = no re-encoding)
      const result = spawnSync(ffmpegPath, [
        '-i', file,
        '-c', 'copy',
        '-movflags', '+faststart',
        tempFile,
        '-y'
      ], { stdio: 'pipe', encoding: 'utf8' });
      
      if (result.status !== 0) {
        throw new Error(result.stderr || 'ffmpeg failed');
      }
      
      // Replace original
      fs.unlinkSync(file);
      fs.renameSync(tempFile, file);
      
      console.log(`✓ Fixed: ${file}\n`);
      successCount++;
    } catch (e) {
      console.error(`✗ Error: ${e.message}\n`);
      const tempFile = file + '.temp.mp4';
      if (fs.existsSync(tempFile)) {
        try {
          fs.unlinkSync(tempFile);
        } catch (unlinkErr) {
          // ignore cleanup errors
        }
      }
      failCount++;
    }
  });
  
  console.log(`\nDone! ${successCount} files fixed, ${failCount} failed.`);
}

function main() {
  if (!fs.existsSync(outputsDir)) {
    console.error(`Error: ${outputsDir} directory not found`);
    process.exit(1);
  }
  
  const ffmpegPath = getFfmpegPath();
  
  if (ffmpegPath) {
    remuxWithFfmpeg(ffmpegPath);
  } else {
    console.log('ffmpeg not found in PATH.');
    console.log('');
    console.log('Options:');
    console.log('1. Try installing ffmpeg-static again:');
    console.log('   npm install --save-dev ffmpeg-static');
    console.log('   node remux_videos.js');
    console.log('');
    console.log('2. Or download ffmpeg portable manually:');
    console.log('   - Go to: https://ffmpeg.org/download.html');
    console.log('   - Download Windows build');
    console.log('   - Extract and add to PATH');
    console.log('');
    console.log('3. Alternative: Use Python with moviepy:');
    console.log('   pip install moviepy');
    console.log('   python remux_videos.py');
    process.exit(1);
  }
}

main();
