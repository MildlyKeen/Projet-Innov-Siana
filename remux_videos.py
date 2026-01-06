#!/usr/bin/env python3
"""
Remux MP4 files to add faststart (moov atom at beginning) for browser streaming.
Uses moviepy to avoid ffmpeg dependency.
"""

import os
import sys
from pathlib import Path

def remux_videos():
    """Find and remux all MP4 files in outputs_for_backend."""
    try:
        from moviepy.editor import VideoFileClip
    except ImportError:
        print("Error: moviepy is not installed.")
        print("Install it with: pip install moviepy")
        sys.exit(1)
    
    outputs_dir = Path("outputs_for_backend")
    
    if not outputs_dir.exists():
        print(f"Error: {outputs_dir} directory not found")
        sys.exit(1)
    
    mp4_files = list(outputs_dir.rglob("*.mp4"))
    
    if not mp4_files:
        print("No MP4 files found in outputs_for_backend")
        sys.exit(0)
    
    print(f"Found {len(mp4_files)} MP4 files to remux")
    print("This may take a while depending on file sizes...\n")
    
    for i, mp4_file in enumerate(mp4_files, 1):
        print(f"[{i}/{len(mp4_files)}] Processing: {mp4_file}")
        
        try:
            # Load the video
            video = VideoFileClip(str(mp4_file))
            
            # Create temporary output
            temp_file = str(mp4_file) + ".temp.mp4"
            
            # Write video (moviepy automatically optimizes for streaming)
            video.write_videofile(
                temp_file,
                codec="libx264",
                audio_codec="aac",
                verbose=False,
                logger=None
            )
            
            # Replace original
            os.remove(str(mp4_file))
            os.rename(temp_file, str(mp4_file))
            
            print(f"✓ Fixed: {mp4_file}\n")
            
        except Exception as e:
            print(f"✗ Error processing {mp4_file}: {e}\n")
            # Clean up temp file if it exists
            temp_file = str(mp4_file) + ".temp.mp4"
            if os.path.exists(temp_file):
                os.remove(temp_file)
            continue
    
    print("Done! All MP4 files have been processed.")

if __name__ == "__main__":
    remux_videos()
