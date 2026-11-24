"""High-Resolution Video Rendering Engine.
Pipes procedural in-memory PIL frames directly into bundled FFmpeg with zero disk intermediate clutter.
Supports optional multiplexed voiceover audio tracks.
"""

import ast
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Generator, Dict, Any, Optional, List
from PIL import Image

import imageio_ffmpeg
from core.preview import load_script_module, get_scene_names

PROJECT_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_DIR = PROJECT_ROOT / "scripts"
OUTPUT_DIR.mkdir(exist_ok=True)


def render_video_stream(
    script_code: str,
    duration_per_scene: float = 4.0,
    fps: int = 30,
    voiceover_audio_path: Optional[str] = None,
    output_filename: str = "",
) -> Generator[Dict[str, Any], None, None]:
    """Renders all procedural scenes into a 1080x1920 MP4 video and streams frame progress."""
    scenes = get_scene_names(script_code)
    if not scenes:
        yield {
            "status": "error",
            "error": "No 'def scene_N()' functions found in script to render.",
        }
        return

    # Load compiled module
    try:
        mod = load_script_module(script_code)
    except Exception as e:
        yield {
            "status": "error",
            "error": f"Failed to compile script: {str(e)}",
        }
        return

    num_scenes = len(scenes)
    frames_per_scene = max(1, int(round(duration_per_scene * fps)))
    total_frames = num_scenes * frames_per_scene
    total_duration_sec = total_frames / fps

    # Setup output filename
    ts = int(time.time())
    if not output_filename:
        output_filename = f"rendered_short_{ts}.mp4"
    if not output_filename.endswith(".mp4"):
        output_filename += ".mp4"

    out_file = OUTPUT_DIR / output_filename
    temp_video_file = OUTPUT_DIR / f"temp_{ts}_{output_filename}"

    ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()

    # Determine audio presence
    has_audio = bool(
        voiceover_audio_path
        and os.path.exists(voiceover_audio_path)
        and os.path.getsize(voiceover_audio_path) > 1000
    )

    target_video_out = str(temp_video_file if has_audio else out_file)

    cmd = [
        ffmpeg_exe,
        "-y",
        "-f", "rawvideo",
        "-vcodec", "rawvideo",
        "-s", "1080x1920",
        "-pix_fmt", "rgba",
        "-r", str(fps),
        "-i", "-",
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-preset", "fast",
        "-crf", "18",
        target_video_out,
    ]

    try:
        proc = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except Exception as e:
        yield {
            "status": "error",
            "error": f"Could not start FFmpeg encoder: {str(e)}",
        }
        return

    t0 = time.time()
    last_yield = 0.0
    global_frame = 0

    import inspect

    yield {
        "status": "rendering",
        "current_frame": 0,
        "total_frames": total_frames,
        "progress_pct": 0,
        "fps_rate": 0.0,
        "elapsed": 0.0,
        "message": f"Starting render: {num_scenes} scenes, {total_frames} frames @ {fps} FPS...",
    }

    try:
        for scene_idx, scene_name in enumerate(scenes):
            scene_func = getattr(mod, scene_name, None)
            if not callable(scene_func):
                continue

            sig = inspect.signature(scene_func)
            param_count = len(sig.parameters)

            for f_idx in range(frames_per_scene):
                p = f_idx / max(1, frames_per_scene - 1)
                time_s = global_frame / fps

                # Call scene function
                if param_count >= 2:
                    frame = scene_func(float(p), float(time_s))
                elif param_count == 1:
                    frame = scene_func(float(p))
                else:
                    frame = scene_func()

                if not isinstance(frame, Image.Image):
                    frame = Image.new("RGBA", (1080, 1920), (15, 23, 42, 255))
                elif frame.size != (1080, 1920):
                    frame = frame.resize((1080, 1920), Image.Resampling.BILINEAR)

                # Ensure RGBA
                if frame.mode != "RGBA":
                    frame = frame.convert("RGBA")

                # Pipe directly to FFmpeg
                proc.stdin.write(frame.tobytes())
                global_frame += 1

                now = time.time()
                if now - last_yield > 0.4 or global_frame == total_frames:
                    last_yield = now
                    elapsed = now - t0
                    fps_rate = global_frame / max(0.01, elapsed)
                    pct = int(round((global_frame / total_frames) * 100))

                    yield {
                        "status": "rendering",
                        "current_frame": global_frame,
                        "total_frames": total_frames,
                        "progress_pct": pct,
                        "fps_rate": fps_rate,
                        "elapsed": elapsed,
                        "message": f"Scene {scene_idx+1}/{num_scenes} ({scene_name}) • Frame {global_frame}/{total_frames} ({pct}%) • {fps_rate:.1f} FPS",
                    }

        proc.stdin.close()
        proc.wait()

    except Exception as e:
        if proc.poll() is None:
            proc.kill()
        yield {
            "status": "error",
            "error": f"Rendering interrupted: {str(e)}",
        }
        return

    # If voiceover audio is supplied, mux it with the video using FFmpeg
    if has_audio:
        yield {
            "status": "rendering",
            "current_frame": total_frames,
            "total_frames": total_frames,
            "progress_pct": 98,
            "fps_rate": 0.0,
            "elapsed": time.time() - t0,
            "message": "Multiplexing recorded voiceover audio track...",
        }

        mux_cmd = [
            ffmpeg_exe,
            "-y",
            "-i", str(temp_video_file),
            "-i", str(voiceover_audio_path),
            "-c:v", "copy",
            "-c:a", "aac",
            "-b:a", "192k",
            "-shortest",
            str(out_file),
        ]
        try:
            mux_proc = subprocess.run(mux_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            if temp_video_file.exists():
                temp_video_file.unlink()
        except Exception:
            # Fallback to silent video
            if temp_video_file.exists():
                shutil.move(str(temp_video_file), str(out_file))

    total_time = time.time() - t0
    final_size_mb = out_file.stat().st_size / (1024 * 1024) if out_file.exists() else 0.0

    yield {
        "status": "complete",
        "video_path": str(out_file.resolve()),
        "filename": out_file.name,
        "total_frames": total_frames,
        "duration_sec": total_duration_sec,
        "render_time": total_time,
        "file_size_mb": final_size_mb,
        "has_audio": has_audio,
        "message": f"✔ Video rendered in {total_time:.1f}s ({final_size_mb:.2f} MB)",
    }
