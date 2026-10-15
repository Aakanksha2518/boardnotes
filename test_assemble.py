"""Tests for the parts that need no model: ordering, repeat shots, assembly."""

from pathlib import Path

from boardnotes.assemble import (
    BoardReading,
    build_document,
    collect_photos,
    drop_repeat_shots,
    natural_order,
    overlap,
)

PART_WAY = "## Binary Search Trees\n- left subtree < node < right subtree\n- search is O(h)"
FULLER = PART_WAY + "\n- balanced gives h = log n\n- worst case gives h = n"
DIFFERENT = "## Traversals\n- inorder gives sorted order\n- preorder copies the tree"


def reading(name: str, markdown: str) -> BoardReading:
    return BoardReading(photo=Path(name), markdown=markdown)


def test_photos_sort_the_way_a_person_counts():
    names = [Path("IMG_10.png"), Path("IMG_2.png"), Path("IMG_1.png")]
    assert [photo.name for photo in sorted(names, key=natural_order)] == ["IMG_1.png", "IMG_2.png", "IMG_10.png"]


def test_collect_photos_ignores_other_files(tmp_path):
    (tmp_path / "IMG_1.png").write_bytes(b"x")
    (tmp_path / "notes.md").write_text("not a photo")
    (tmp_path / "IMG_2.jpg").write_bytes(b"x")
    assert [photo.name for photo in collect_photos(tmp_path)] == ["IMG_1.png", "IMG_2.jpg"]


def test_overlap_is_high_for_the_same_board_and_low_for_different_ones():
    assert overlap(PART_WAY, FULLER) > 0.72
    assert overlap(PART_WAY, DIFFERENT) < 0.5


def test_repeat_shot_is_merged_and_the_fuller_one_wins():
    kept = drop_repeat_shots([reading("IMG_1.png", PART_WAY), reading("IMG_2.png", FULLER)])
    assert len(kept) == 1
    assert kept[0].photo.name == "IMG_2.png"
    assert [photo.name for photo in kept[0].replaced] == ["IMG_1.png"]


def test_fuller_shot_wins_even_when_it_came_first():
    kept = drop_repeat_shots([reading("IMG_1.png", FULLER), reading("IMG_2.png", PART_WAY)])
    assert len(kept) == 1
    assert kept[0].photo.name == "IMG_1.png"


def test_different_boards_are_both_kept():
    kept = drop_repeat_shots([reading("IMG_1.png", FULLER), reading("IMG_10.png", DIFFERENT)])
    assert len(kept) == 2


def test_blank_photos_are_dropped():
    kept = drop_repeat_shots([reading("IMG_1.png", "BLANK"), reading("IMG_2.png", FULLER)])
    assert len(kept) == 1
    assert kept[0].photo.name == "IMG_2.png"


def test_keeping_repeats_is_possible_with_a_high_threshold():
    kept = drop_repeat_shots([reading("IMG_1.png", PART_WAY), reading("IMG_2.png", FULLER)], threshold=0.99)
    assert len(kept) == 2


def test_document_has_a_title_numbered_sections_and_photo_credits():
    kept = drop_repeat_shots([reading("IMG_1.png", PART_WAY), reading("IMG_2.png", FULLER), reading("IMG_10.png", DIFFERENT)])
    document = build_document(kept, title="Trees lecture")

    assert document.startswith("# Trees lecture")
    assert "## Board 1" in document and "## Board 2" in document
    assert "<!-- from IMG_2.png, IMG_1.png -->" in document
    assert "h = log n" in document


def test_credits_can_be_turned_off():
    document = build_document([reading("IMG_1.png", DIFFERENT)], title="T", credit_photos=False)
    assert "<!--" not in document


def test_section_label_is_configurable():
    document = build_document([reading("IMG_1.png", DIFFERENT)], title="T", section_label="Slide")
    assert "## Slide 1" in document
