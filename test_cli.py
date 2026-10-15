"""Runs the whole command with a stand-in model, so no API key is needed."""

import shutil
from pathlib import Path

import boardnotes.cli as cli
from boardnotes.gemma import GemmaVision

PART_WAY = "## Binary Search Trees\n- left subtree < node < right subtree\n- search is O(h)"
FULLER = PART_WAY + "\n- balanced gives h = log n\n- worst case gives h = n"
TRAVERSALS = "## Traversals\n- inorder gives sorted order\n- preorder copies the tree"

BY_PHOTO = {"IMG_1.png": PART_WAY, "IMG_2.png": FULLER, "IMG_10.png": TRAVERSALS}


class StandInModel:
    """Answers like Gemma would, without the network."""

    def __init__(self):
        self.photos_read = 0
        self.text_questions = 0
        self._order = ["IMG_1.png", "IMG_2.png", "IMG_10.png"]

    def read_photo(self, image_bytes, mime_type, instruction):
        name = self._order[self.photos_read % len(self._order)]
        self.photos_read += 1
        return BY_PHOTO[name]

    def ask_text(self, instruction):
        self.text_questions += 1
        return "Binary search trees"


def run(tmp_path, monkeypatch, model=None, extra=()):
    model = model or StandInModel()
    shutil.copytree(Path(__file__).parent / "examples", tmp_path / "photos")
    monkeypatch.setattr(cli, "GemmaVision", lambda **settings: model)
    exit_code = cli.main([str(tmp_path / "photos"), *extra])
    return exit_code, tmp_path / "photos" / "notes.md", model


def test_notes_file_is_written_with_a_suggested_title(tmp_path, monkeypatch):
    exit_code, notes, model = run(tmp_path, monkeypatch)
    assert exit_code == 0
    text = notes.read_text(encoding="utf-8")
    assert text.startswith("# Binary search trees")
    assert model.text_questions == 1


def test_repeat_shot_of_the_same_board_becomes_one_section(tmp_path, monkeypatch):
    _exit_code, notes, _model = run(tmp_path, monkeypatch)
    text = notes.read_text(encoding="utf-8")
    assert "## Board 1" in text and "## Board 2" in text
    assert "## Board 3" not in text  # three photos, two boards
    assert "h = log n" in text       # the fuller shot is the one kept


def test_given_title_is_used_and_no_text_question_is_asked(tmp_path, monkeypatch):
    model = StandInModel()
    _exit_code, notes, _model = run(tmp_path, monkeypatch, model=model, extra=["--title", "Trees lecture"])
    assert notes.read_text(encoding="utf-8").startswith("# Trees lecture")
    assert model.text_questions == 0


def test_keep_repeats_gives_a_section_per_photo(tmp_path, monkeypatch):
    _exit_code, notes, _model = run(tmp_path, monkeypatch, extra=["--keep-repeats"])
    assert "## Board 3" in notes.read_text(encoding="utf-8")


def test_second_run_reads_nothing_again(tmp_path, monkeypatch):
    _exit_code, notes, _model = run(tmp_path, monkeypatch)
    second = StandInModel()
    monkeypatch.setattr(cli, "GemmaVision", lambda **settings: second)
    cli.main([str(notes.parent)])
    assert second.photos_read == 0  # every photo came from the cache


def test_output_path_is_respected(tmp_path, monkeypatch):
    destination = tmp_path / "lecture.md"
    shutil.copytree(Path(__file__).parent / "examples", tmp_path / "photos")
    monkeypatch.setattr(cli, "GemmaVision", lambda **settings: StandInModel())
    cli.main([str(tmp_path / "photos"), "-o", str(destination)])
    assert destination.is_file()


def test_missing_folder_is_reported(tmp_path, monkeypatch):
    assert cli.main([str(tmp_path / "nowhere")]) == 2


def test_no_api_key_gives_a_clear_message(tmp_path, monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    try:
        GemmaVision()
    except Exception as problem:
        assert "GEMINI_API_KEY" in str(problem)
    else:
        raise AssertionError("expected a complaint about the missing key")
