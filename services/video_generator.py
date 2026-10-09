from __future__ import annotations

import os
import subprocess
from pathlib import Path

from config.settings import get_settings

settings = get_settings()


class VideoGenerator:
    def __init__(self, ffmpeg_bin: str = "ffmpeg") -> None:
        self.ffmpeg_bin = ffmpeg_bin

    def create_subtitle_file(self, subtitle_path: str | Path, lines: list[str]) -> Path:
        path = Path(subtitle_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        content = []
        for index, text in enumerate(lines, start=1):
            content.append(f"{index}\n00:00:{index:02}.000 --> 00:00:{index + 1:02}.000\n{text}\n")
        path.write_text("\n".join(content), encoding="utf-8")
        return path

    def build_slideshow_video(
        self,
        image_files: list[str | Path],
        output_path: str | Path,
        duration_per_image: float = 3.0,
        resolution: str = "1280:720",
        fps: int = 24,
    ) -> Path:
        image_list = [str(Path(p)) for p in image_files]
        if not image_list:
            raise ValueError("At least one image is required for a slideshow.")

        concat_list = Path(output_path).parent / "slideshow_concat.txt"
        concat_list.write_text("\n".join(f"file '{p}'" for p in image_list), encoding="utf-8")

        cmd = [
            self.ffmpeg_bin,
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            str(concat_list),
            "-vf",
            f"fps={fps},scale={resolution},format=yuv420p",
            "-y",
            str(output_path),
        ]
        subprocess.run(cmd, check=True)
        return Path(output_path)

    def render_video_from_images(
        self,
        image_files: list[str | Path],
        output_path: str | Path,
        text_overlays: list[str] | None = None,
        subtitle_file: str | Path | None = None,
        resolution: str = "1280:720",
    ) -> Path:
        video_path = Path(output_path)
        video_path.parent.mkdir(parents=True, exist_ok=True)

        if not image_files:
            raise ValueError("No images provided to render a video.")

        first_image = str(Path(image_files[0]))
        cmd = [self.ffmpeg_bin, "-loop", "1", "-i", first_image, "-t", str(settings.max_video_duration), "-vf", f"scale={resolution},format=yuv420p", "-y", str(video_path)]
        subprocess.run(cmd, check=True)

        if subtitle_file is not None:
            subtitle_path = Path(subtitle_file)
            if subtitle_path.exists():
                cmd = [
                    self.ffmpeg_bin,
                    "-i",
                    str(video_path),
                    "-vf",
                    f"subtitles={subtitle_path}",
                    "-y",
                    str(video_path.with_suffix(".final.mp4")),
                ]
                subprocess.run(cmd, check=True)
                return video_path.with_suffix(".final.mp4")

        return video_path


video_generator = VideoGenerator()

__all__ = ["VideoGenerator", "video_generator"]
