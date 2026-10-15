"""Put the pieces together: photo order, repeat shots, and the final document."""

import re
from dataclasses import dataclass, field
from difflib import SequenceMatcher
from pathlib import Path

from .gemma import IMAGE_SUFFIXES

BLANK_MARKER = "BLANK"


@dataclass
class BoardReading:
    """What one photo turned out to contain."""

    photo: Path
    markdown: str
    replaced: list[Path] = field(default_factory=list)  # earlier shots of this same board

    @property
    def is_blank(self) -> bool:
        return self.markdown.strip().upper().startswith(BLANK_MARKER) or not self.markdown.strip()


def natural_order(photo: Path) -> tuple:
    """Sort IMG_2.jpg before IMG_10.jpg, the way a person would expect."""
    pieces = re.split(r"(\d+)", photo.name.lower())
    return tuple(int(piece) if piece.isdigit() else piece for piece in pieces)


def collect_photos(folder: Path) -> list[Path]:
    if folder.is_file():
        return [folder] if folder.suffix.lower() in IMAGE_SUFFIXES else []
    photos = [path for path in folder.iterdir() if path.is_file() and path.suffix.lower() in IMAGE_SUFFIXES]
    return sorted(photos, key=natural_order)


def _comparable(markdown: str) -> str:
    """Strip formatting so two readings of the same board compare fairly."""
    plain = re.sub(r"```.*?```", " ", markdown, flags=re.DOTALL)
    plain = re.sub(r"[#*`\-_>|$\\]", " ", plain)
    return " ".join(plain.lower().split())


def overlap(first: str, second: str) -> float:
    """How much two readings have in common, from 0 to 1."""
    left, right = _comparable(first), _comparable(second)
    if not left or not right:
        return 0.0
    return SequenceMatcher(None, left, right).ratio()


def drop_repeat_shots(readings: list[BoardReading], threshold: float = 0.72) -> list[BoardReading]:
    """People photograph the same board several times as it fills up. Keep the
    fullest version of each board and remember which shots it replaced."""
    kept: list[BoardReading] = []
    for reading in readings:
        if reading.is_blank:
            continue
        if kept and overlap(kept[-1].markdown, reading.markdown) >= threshold:
            previous = kept[-1]
            fuller, replaced = (
                (reading, previous) if len(_comparable(reading.markdown)) >= len(_comparable(previous.markdown))
                else (previous, reading)
            )
            fuller.replaced = previous.replaced + [replaced.photo]
            kept[-1] = fuller
        else:
            kept.append(reading)
    return kept


def build_document(
    readings: list[BoardReading],
    title: str,
    section_label: str = "Board",
    credit_photos: bool = True,
) -> str:
    """One Markdown file out of all the kept readings."""
    lines = [f"# {title}", ""]
    for number, reading in enumerate(readings, start=1):
        lines.append(f"## {section_label} {number}")
        if credit_photos:
            sources = ", ".join([reading.photo.name] + [photo.name for photo in reading.replaced])
            lines.append(f"<!-- from {sources} -->")
        lines.append("")
        lines.append(reading.markdown.strip())
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"
