"""boardnotes - turn photos of whiteboards, slides and handwritten pages into one Markdown file."""

import argparse
import sys
from pathlib import Path

from .assemble import BoardReading, build_document, collect_photos, drop_repeat_shots
from .cache import ReadingCache
from .gemma import DEFAULT_MODEL, GemmaVision, ModelUnavailable, mime_type_for
from .prompts import read_board_prompt, title_prompt


def read_every_photo(photos: list[Path], model: GemmaVision, cache: ReadingCache, options) -> list[BoardReading]:
    brief = read_board_prompt(options.language, with_mermaid=not options.no_diagrams)
    readings: list[BoardReading] = []

    for position, photo in enumerate(photos, start=1):
        try:
            image_bytes = photo.read_bytes()
        except OSError as problem:
            print(f"  skip {photo.name}: {problem}", file=sys.stderr)
            continue

        key = ReadingCache.key_for(image_bytes, options.model, options.language, options.no_diagrams)
        markdown = cache.get(key)
        status = "cached"

        if markdown is None:
            try:
                markdown = model.read_photo(image_bytes, mime_type_for(photo), brief)
            except ModelUnavailable as problem:
                print(f"  skip {photo.name}: {problem}", file=sys.stderr)
                continue
            cache.put(key, markdown)
            status = "read"

        reading = BoardReading(photo=photo, markdown=markdown)
        word_count = len(markdown.split())
        label = "blank" if reading.is_blank else f"{word_count} words"
        print(f"  [{position}/{len(photos)}] {photo.name} - {label} ({status})")
        readings.append(reading)

    return readings


def choose_title(readings: list[BoardReading], model: GemmaVision, options) -> str:
    if options.title:
        return options.title
    sample = "\n\n".join(reading.markdown for reading in readings[:2])
    try:
        suggested = model.ask_text(title_prompt(sample, options.language))
    except ModelUnavailable:
        return "Notes"
    cleaned = " ".join(suggested.split()).strip().strip('"').strip(".")
    return cleaned or "Notes"


def command_build(options: argparse.Namespace) -> int:
    source = Path(options.path)
    if not source.exists():
        print(f"error: no such file or folder: {source}", file=sys.stderr)
        return 2

    photos = collect_photos(source)
    if not photos:
        print("error: no images found there.", file=sys.stderr)
        return 2

    try:
        model = GemmaVision(
            model=options.model, api_key=options.api_key, base_url=options.base_url, timeout=options.timeout
        )
    except ModelUnavailable as problem:
        print(f"error: {problem}", file=sys.stderr)
        return 2

    cache_folder = source if source.is_dir() else source.parent
    cache = ReadingCache(cache_folder, enabled=not options.no_cache)

    print(f"Reading {len(photos)} photo(s) with {options.model}:")
    readings = read_every_photo(photos, model, cache, options)
    cache.save()

    if not readings:
        print("error: nothing could be read from those photos.", file=sys.stderr)
        return 1

    kept = readings if options.keep_repeats else drop_repeat_shots(readings, threshold=options.repeat_threshold)
    dropped = sum(len(reading.replaced) for reading in kept)
    blanks = sum(1 for reading in readings if reading.is_blank)

    title = options.title or choose_title(kept, model, options)
    document = build_document(kept, title=title, section_label=options.section_label, credit_photos=not options.no_credits)

    destination = Path(options.output) if options.output else cache_folder / "notes.md"
    try:
        destination.write_text(document, encoding="utf-8")
    except OSError as problem:
        print(f"error: could not write {destination}: {problem}", file=sys.stderr)
        return 2

    summary = f"\nWrote {destination} - {len(kept)} section(s)"
    if dropped:
        summary += f", {dropped} repeat shot(s) merged"
    if blanks:
        summary += f", {blanks} blank photo(s) skipped"
    if cache.hits:
        summary += f", {cache.hits} reused from cache"
    print(summary + ".")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="boardnotes",
        description="Turn photos of whiteboards, slides and handwritten pages into one Markdown file, using Gemma 4.",
    )
    parser.add_argument("path", help="a folder of photos, or a single photo")
    parser.add_argument("-o", "--output", default=None, help="where to write the notes (default: notes.md beside the photos)")
    parser.add_argument("--title", default=None, help="title for the notes (default: the model suggests one)")
    parser.add_argument("--section-label", default="Board", help="word used for each section heading (default: Board)")
    parser.add_argument("--language", default="English", help="language to write the notes in (default: English)")
    parser.add_argument("--no-diagrams", action="store_true", help="do not redraw diagrams as Mermaid")
    parser.add_argument("--keep-repeats", action="store_true", help="keep every photo, even repeat shots of one board")
    parser.add_argument("--repeat-threshold", type=float, default=0.72, help="how alike two shots must be to count as the same board (0-1)")
    parser.add_argument("--no-credits", action="store_true", help="do not note which photo each section came from")
    parser.add_argument("--no-cache", action="store_true", help="read every photo again, ignoring the cache")
    parser.add_argument("--model", default=DEFAULT_MODEL, help=f"model name (default: {DEFAULT_MODEL})")
    parser.add_argument("--api-key", default=None, help="overrides GEMINI_API_KEY")
    parser.add_argument("--base-url", default=None, help="an OpenAI-compatible server instead of the Gemini API")
    parser.add_argument("--timeout", type=int, default=120, help="seconds to wait for the model")

    options = parser.parse_args(argv)
    return command_build(options)


if __name__ == "__main__":
    raise SystemExit(main())
