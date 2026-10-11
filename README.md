# HealCUT

HealCUT is a browser-based clipping studio with a small Python server. The web page handles YouTube playback and browser-authorized live capture; Python serves the app and provides an FFmpeg-powered cutter for saved video files.

## Run locally with Python

1. Install Python 3.10 or newer.
2. Install FFmpeg and make sure `ffmpeg` is available on your PATH.
3. From this folder, run `python app.py`.
4. Open [http://localhost:8765](http://localhost:8765).

The Python cutter lets you choose a local video and start/end times in seconds. It exports an MP4 at 1920×1080, preserving the source aspect ratio with padding when needed. The video is processed on the computer running HealCUT; the temporary upload and output are removed after download.

## Live YouTube clipping

Paste a public or unlisted YouTube Live link, load the stream, and use its rewind controls to select a section. The browser requires you to share the HealCUT tab with audio for live capture. YouTube does not expose its underlying video feed to an ordinary web page, so this live workflow uses browser tab capture and may require the app to stay open during the clip.

The Python FFmpeg cutter works on video files you already have. It does not bypass YouTube access controls or turn a YouTube URL into a source file.

## Notes

- The Python server uses only the Python standard library; FFmpeg is required for file cutting.
- File uploads are limited to 2 GB and clip duration to four hours.
- MP4 encoding can take time, depending on source size and computer speed.
- Use only videos you have permission to record and clip.
