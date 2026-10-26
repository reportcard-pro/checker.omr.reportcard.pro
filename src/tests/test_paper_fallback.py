import pytest

from src.core import ImageInstanceOps
from src.defaults.config import CONFIG_DEFAULTS

PAGE_THRESHOLD = 200.0
BLANK_ROW_TOP = [229.2, 225.2, 228.0, 225.0]
GREY_MARK_ROW = [229.2, 225.2, 180.6, 225.0]
DARKENED_BLANK_ROWS = [
    [203.6, 200.5, 201.4, 200.2],
    [198.8, 200.5, 196.5, 198.4],
    [201.1, 200.2, 200.8, 198.3],
    [198.2, 197.9, 197.1, 196.8],
]


@pytest.fixture
def ops():
    return ImageInstanceOps(CONFIG_DEFAULTS)


def marked(ops, strip, fallback):
    threshold = ops.get_local_threshold(strip, fallback, True)
    return [value < threshold for value in strip]


def test_darkened_blank_rows_read_blank(ops):
    strips = [BLANK_ROW_TOP] * 3 + DARKENED_BLANK_ROWS * 3
    fallbacks = ops.get_paper_fallback_thresholds(strips, [(0, len(strips))])
    for strip, fallback in zip(strips, fallbacks):
        assert not any(marked(ops, strip, min(PAGE_THRESHOLD, fallback)))


def test_darkened_blank_rows_read_as_marks_with_page_threshold_alone(ops):
    assert any(
        any(marked(ops, strip, PAGE_THRESHOLD)) for strip in DARKENED_BLANK_ROWS
    )


def test_grey_pencil_mark_still_reads(ops):
    strips = [BLANK_ROW_TOP] * 5 + [GREY_MARK_ROW] + [BLANK_ROW_TOP] * 5
    fallbacks = ops.get_paper_fallback_thresholds(strips, [(0, len(strips))])
    assert marked(ops, GREY_MARK_ROW, min(PAGE_THRESHOLD, fallbacks[5])) == [
        False,
        False,
        True,
        False,
    ]


def test_fully_marked_row_among_blank_rows_reads_all_marked(ops):
    full_row = [82.0, 80.5, 79.9, 81.2]
    strips = [BLANK_ROW_TOP] * 5 + [full_row] + [BLANK_ROW_TOP] * 5
    fallbacks = ops.get_paper_fallback_thresholds(strips, [(0, len(strips))])
    assert all(marked(ops, full_row, min(PAGE_THRESHOLD, fallbacks[5])))


def test_fallback_follows_each_blocks_own_paper_level(ops):
    strips = [BLANK_ROW_TOP] * 4 + DARKENED_BLANK_ROWS
    fallbacks = ops.get_paper_fallback_thresholds(strips, [(0, 4), (4, 8)])
    assert fallbacks[0] == pytest.approx(229.2 - 25)
    assert fallbacks[4] == pytest.approx(200.8 - 25)


def test_short_strips_keep_the_page_threshold(ops):
    strips = [[230.0, 120.0], [225.0], [229.0, 228.0, 120.0, 227.0]]
    fallbacks = ops.get_paper_fallback_thresholds(strips, [(0, 3)])
    assert fallbacks[0] == float("inf")
    assert fallbacks[1] == float("inf")
    assert min(PAGE_THRESHOLD, fallbacks[0]) == PAGE_THRESHOLD
