"""The briefs we give Gemma. Kept in one place so they are easy to tune."""

READ_BOARD = """This is a photo of a whiteboard, blackboard, lecture slide or page of handwritten notes.

Write out everything on it as clean Markdown in {language}:
- Keep the original wording. Do not summarise, explain or add anything that is not there.
- Use `##` for a heading written on the board, `-` for bullet points, and keep numbered lists numbered.
- Maths goes in LaTeX between $ signs, for example $x^2 + y^2 = r^2$.
- Code goes in a fenced code block with the language name.
- Tables become Markdown tables.
- If part of the handwriting is genuinely unreadable, write [unclear] there rather than guessing.
- Ignore anything that is not part of the board: hands, the room, reflections, the edge of the frame.

If the photo has a diagram, flowchart or graph, describe it in one short paragraph{mermaid_note}.

If the photo contains no readable writing at all, reply with exactly: BLANK

Reply with the Markdown only. No preamble, no closing remark."""

MERMAID_NOTE = (
    ", then redraw it as a Mermaid diagram inside a ```mermaid fenced block "
    "(use `flowchart TD` for boxes and arrows, `graph LR` for left-to-right flows)"
)

SUGGEST_TITLE = """Here are notes taken from a lecture or meeting:

{sample}

Give a title for them: at most seven words in {language}, naming the actual subject.
Reply with the title only, no quotes and no full stop."""


def read_board_prompt(language: str, with_mermaid: bool) -> str:
    return READ_BOARD.format(language=language, mermaid_note=MERMAID_NOTE if with_mermaid else "")


def title_prompt(sample: str, language: str) -> str:
    return SUGGEST_TITLE.format(sample=sample[:1500], language=language)
