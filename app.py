"""Python server for HealCUT and its accurate local MP4 cutter.

The browser still handles YouTube playback and browser-authorized live capture.
This server provides a local FFmpeg endpoint for cutting a video file without
capturing the screen.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
from email import policy
from email.parser import BytesParser
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import quote


ROOT = Path(__file__).resolve().parent
MAX_UPLOAD_BYTES = 2 * 1024 * 1024 * 1024
MAX_CLIP_SECONDS = 4 * 60 * 60


class HealCUTHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def log_message(self, fmt: str, *args) -> None:
        print(f"[{self.log_date_time_string()}] {fmt % args}")

    def send_json(self, status: int, payload: dict) -> None:
        data = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self) -> None:
        if self.path == "/api/health":
            self.send_json(200, {
                "ok": True,
                "python": os.sys.version.split()[0],
                "ffmpeg_available": shutil.which("ffmpeg") is not None,
            })
            return
        if self.path == "/":
            self.path = "/index.html"
        super().do_GET()

    def do_POST(self) -> None:
        if self.path != "/api/clip":
            self.send_json(404, {"error": "Endpoint not found."})
            return
        ffmpeg = shutil.which("ffmpeg")
        if not ffmpeg:
            self.send_json(503, {"error": "FFmpeg is required. Install FFmpeg and add it to PATH, then restart HealCUT."})
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            self.send_json(400, {"error": "Invalid request size."})
            return
        if length <= 0 or length > MAX_UPLOAD_BYTES:
            self.send_json(413, {"error": "Choose a video file smaller than 2 GB."})
            return
        content_type = self.headers.get("Content-Type", "")
        if not content_type.lower().startswith("multipart/form-data;"):
            self.send_json(415, {"error": "Send the video as a multipart file upload."})
            return

        try:
            body = self.rfile.read(length)
            envelope = BytesParser(policy=policy.default).parsebytes(
                f"Content-Type: {content_type}\r\nMIME-Version: 1.0\r\n\r\n".encode("ascii") + body
            )
            fields: dict[str, str] = {}
            upload: tuple[str, bytes] | None = None
            for part in envelope.iter_parts():
                name = part.get_param("name", header="content-disposition")
                payload = part.get_payload(decode=True) or b""
                if name == "video" and part.get_filename():
                    upload = (Path(part.get_filename()).name, payload)
                elif name in {"start", "end"}:
                    fields[name] = payload.decode("utf-8", errors="strict").strip()

            if not upload or not upload[1]:
                self.send_json(400, {"error": "Choose a video file first."})
                return
            start = float(fields.get("start", ""))
            end = float(fields.get("end", ""))
            if start < 0 or end <= start or end - start > MAX_CLIP_SECONDS:
                self.send_json(400, {"error": "Enter valid start and end times. Clips can be up to four hours."})
                return

            with tempfile.TemporaryDirectory(prefix="healcut-") as temp_dir:
                source = Path(temp_dir) / "source-video"
                output = Path(temp_dir) / "HealCUT-clip.mp4"
                source.write_bytes(upload[1])
                command = [
                    ffmpeg, "-hide_banner", "-loglevel", "error", "-y",
                    "-i", str(source), "-ss", f"{start:.3f}", "-t", f"{end - start:.3f}",
                    "-map", "0:v:0", "-map", "0:a?",
                    "-vf", "scale=1920:1080:force_original_aspect_ratio=decrease:force_divisible_by=2,pad=1920:1080:(ow-iw)/2:(oh-ih)/2,setsar=1",
                    "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p",
                    "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", str(output),
                ]
                result = subprocess.run(command, capture_output=True, text=True, timeout=6 * 60 * 60)
                if result.returncode != 0 or not output.exists():
                    message = result.stderr[-1200:].strip() or "FFmpeg could not process this video."
                    self.send_json(422, {"error": message})
                    return
                clip = output.read_bytes()

            filename = f"HealCUT-{int(start)}-{int(end)}.mp4"
            self.send_response(200)
            self.send_header("Content-Type", "video/mp4")
            self.send_header("Content-Length", str(len(clip)))
            self.send_header("Content-Disposition", f"attachment; filename*=UTF-8''{quote(filename)}")
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(clip)
        except (ValueError, UnicodeDecodeError):
            self.send_json(400, {"error": "Start and end times must be valid seconds, such as 15 and 45."})
        except subprocess.TimeoutExpired:
            self.send_json(504, {"error": "FFmpeg took too long to process this file. Try a shorter clip."})
        except (BrokenPipeError, ConnectionResetError):
            return
        except Exception as exc:
            self.send_json(500, {"error": f"Could not create the clip: {exc}"})


if __name__ == "__main__":
    host = os.environ.get("HEALCUT_HOST", "127.0.0.1")
    port = int(os.environ.get("HEALCUT_PORT", "8765"))
    server = ThreadingHTTPServer((host, port), HealCUTHandler)
    print(f"HealCUT Python server: http://{host}:{port}")
    print(f"FFmpeg available: {'yes' if shutil.which('ffmpeg') else 'no (install FFmpeg for Python file cutting)'}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping HealCUT.")
        server.server_close()
