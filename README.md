# boardnotes

Point it at a folder of photos — whiteboards, lecture slides, handwritten pages — and get back one clean Markdown file. Powered by **Gemma 4** vision.

Everyone photographs the board during a lecture and never looks at those photos again, because 40 blurry images are not notes. `boardnotes` reads them, writes out the maths and the bullet points properly, redraws diagrams as Mermaid, and merges the three shots you took of the same board as it filled up.

```
$ boardnotes ~/photos/algorithms-lecture

Reading 3 photo(s) with gemma-4-31b-it:
  [1/3] IMG_1.png - 24 words (read)
  [2/3] IMG_2.png - 38 words (read)
  [3/3] IMG_10.png - 21 words (read)

Wrote ~/photos/algorithms-lecture/notes.md - 2 section(s), 1 repeat shot(s) merged.
```

The result:

```markdown
# Binary search trees

## Board 1
<!-- from IMG_2.png, IMG_1.png -->

## Binary Search Trees
- left subtree < node < right subtree
- search: $O(h)$, where $h$ is the height
- balanced $\Rightarrow h = \log n$
- worst case (sorted input) $\Rightarrow h = n$
```

## Why Gemma 4

Reading a board is a hard vision job: messy handwriting, glare, maths that plain OCR turns into gibberish, and diagrams that are not text at all. Gemma 4 is natively multimodal and strong at reading text inside images, so equations come out as LaTeX and flowcharts come back as Mermaid you can actually render.

The weights are Apache 2.0, which matters here more than usual — a semester of lecture photos, meeting whiteboards or a page of someone's private notes is not something you necessarily want to upload. Point `--base-url` at a local Gemma and nothing leaves your machine.

## Install

```bash
git clone https://github.com/Aakanksha2518/boardnotes
cd boardnotes
pip install -e .
```

Get a free key from [Google AI Studio](https://aistudio.google.com) and set it:

```bash
export GEMINI_API_KEY=your-key-here
```

## Use

```bash
boardnotes photos/                        # writes photos/notes.md
boardnotes photos/ -o lecture-03.md       # choose where it goes
boardnotes photos/ --title "Trees, week 4"
boardnotes photos/ --section-label Slide  # "## Slide 1" instead of "## Board 1"
boardnotes photo.jpg                      # a single photo works too
```

Try it on the bundled sample photos:

```bash
boardnotes examples/
```

### Run it entirely on your own machine

```bash
ollama run gemma4:31b
boardnotes photos/ --base-url http://localhost:11434/v1 --model gemma4:31b
```

Any OpenAI-compatible server works — Ollama, vLLM, llama.cpp.

### Options

| Flag | What it does |
| --- | --- |
| `-o, --output` | Where to write the notes (default: `notes.md` beside the photos) |
| `--title` | Your own title; otherwise the model suggests one from the content |
| `--section-label` | Word used in each heading, e.g. `Slide`, `Page` |
| `--language` | Write the notes in another language (Gemma 4 covers 140+) |
| `--keep-repeats` | One section per photo, no merging |
| `--repeat-threshold` | How alike two shots must be to count as the same board (default 0.72) |
| `--no-diagrams` | Skip the Mermaid redraw, just describe diagrams in words |
| `--no-credits` | Leave out the comment saying which photo each section came from |
| `--model` | Default `gemma-4-31b-it`; `gemma-4-26b-a4b-it` is faster |
| `--base-url` | Point at a local or third-party OpenAI-compatible server |

## How it works

1. **Order the photos** the way a person counts, so `IMG_2` comes before `IMG_10`.
2. **Read each one** with Gemma 4, asking for the board's own words — maths as LaTeX, code in fenced blocks, tables as tables, `[unclear]` where the handwriting genuinely isn't readable. Nothing is summarised or invented. A photo with no writing on it comes back `BLANK` and is dropped.
3. **Merge the repeat shots.** Photos of one board as it fills up read very similarly, so their text is compared and only the fullest version is kept — the others are noted in a comment rather than thrown away silently.
4. **Assemble** one Markdown file with a title the model suggests from the content.

Readings are cached by the photo's own hash in `.boardnotes-cache.json`, so re-running with a different `--title` or threshold costs nothing.

## Tests

```bash
pytest
```

19 tests, none of which need an API key — the model is swapped for a stand-in, so ordering, merging and assembly are tested on their own.

## Limits

- Handwriting quality is the ceiling. Bad glare or a very faint pencil will produce `[unclear]`.
- The merge threshold is a guess that works for lecture boards; `--keep-repeats` turns it off entirely if your photos are all distinct.
- Notes are a draft, not a transcript. Check anything you'll be examined on.

## License

MIT. See [LICENSE](LICENSE).
