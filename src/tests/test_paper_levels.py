import pytest

from src.core import ImageInstanceOps
from src.defaults.config import CONFIG_DEFAULTS

PAGE_THRESHOLD = 200.0
BLANK_ROW = [229.2, 225.2, 228.0, 225.0]
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


def read_block(ops, strips):
    paper_levels = ops.get_paper_levels(strips, [(0, len(strips))])
    readings = []
    for strip, paper_level in zip(strips, paper_levels):
        readable_vals, fallback_thr, is_faint = ops.read_strip_against_paper(
            strip, paper_level, PAGE_THRESHOLD
        )
        no_outliers = max(strip) - min(strip) < 30
        threshold = ops.get_local_threshold(readable_vals, fallback_thr, no_outliers)
        readings.append(([value < threshold for value in strip], is_faint))
    return readings


def test_blank_rows_on_paper_darkening_down_the_page_read_blank(ops):
    strips = [
        [level + 3.0, level, level + 1.0, level - 2.0]
        for level in (228.0 - 2.0 * row for row in range(15))
    ]
    for marks, _ in read_block(ops, strips):
        assert not any(marks)


def test_traced_darkened_blank_rows_read_blank(ops):
    strips = DARKENED_BLANK_ROWS * 3
    for marks, _ in read_block(ops, strips):
        assert not any(marks)


def test_grey_pencil_mark_reads_without_a_flag(ops):
    strips = [BLANK_ROW] * 5 + [GREY_MARK_ROW] + [BLANK_ROW] * 5
    marks, is_faint = read_block(ops, strips)[5]
    assert marks == [False, False, True, False]
    assert not is_faint


def test_three_mark_rows_in_a_multi_correct_section_read(ops):
    multi_row = [110.0, 105.0, 108.0, 230.0]
    strips = [multi_row] * 6 + [BLANK_ROW] * 5
    for marks, _ in read_block(ops, strips)[:6]:
        assert marks == [True, True, True, False]


def test_whitener_bubble_does_not_make_the_rest_read_marked(ops):
    whitener_row = [228.0, 252.0, 226.0, 227.0]
    strips = [BLANK_ROW] * 5 + [whitener_row] + [BLANK_ROW] * 5
    marks, _ = read_block(ops, strips)[5]
    assert not any(marks)


def test_clipped_white_bubble_does_not_flood_a_digit_column(ops):
    digit_column = [217.0, 220.3, 217.4, 218.6, 218.3, 224.3, 221.2, 222.8, 224.2, 226.2, 222.1, 222.3, 255.0]
    strips = [digit_column] * 5
    for marks, _ in read_block(ops, strips):
        assert not any(marks)


def test_white_paper_keeps_dark_marks(ops):
    white_blank = [236.2, 251.2, 251.9, 249.8]
    marked_row = [236.2, 111.9, 251.2, 251.9]
    strips = [white_blank, marked_row] * 5
    for marks, _ in read_block(ops, strips)[1::2]:
        assert marks == [False, True, False, False]


def test_faint_mark_is_flagged(ops):
    faint_row = [229.2, 225.2, 203.0, 225.0]
    strips = [BLANK_ROW] * 5 + [faint_row] + [BLANK_ROW] * 5
    _, is_faint = read_block(ops, strips)[5]
    assert is_faint


def test_long_digit_columns_are_not_flagged(ops):
    column = [230.0] * 5 + [205.0] * 5
    readable_vals, fallback_thr, is_faint = ops.read_strip_against_paper(column, 230.0, PAGE_THRESHOLD)
    assert not is_faint


def test_short_strips_have_no_paper_level_and_keep_the_page_threshold(ops):
    strips = [[230.0, 120.0], [225.0], BLANK_ROW]
    paper_levels = ops.get_paper_levels(strips, [(0, 3)])
    assert paper_levels[:2] == [None, None]
    assert ops.read_strip_against_paper(strips[0], None, PAGE_THRESHOLD)[1] == PAGE_THRESHOLD


def test_short_strips_do_not_pull_down_their_neighbours_paper_level(ops):
    strips = [[90.0, 85.0], [88.0], BLANK_ROW]
    paper_levels = ops.get_paper_levels(strips, [(0, 3)])
    assert paper_levels[2] > 220


@pytest.mark.parametrize("marked_rows", [5, 6, 8, 11])
def test_dense_multi_correct_rows_with_varied_shading_read_at_the_block_start(ops, marked_rows):
    multi_row = [110.0, 95.0, 130.0, 230.0]
    strips = [multi_row] * marked_rows + [BLANK_ROW] * (11 - marked_rows)
    for marks, _ in read_block(ops, strips)[:marked_rows]:
        assert marks == [True, True, True, False]


def test_blank_rows_on_a_grey_blurry_sheet_read_blank(ops):
    grey_blank_rows = [
        [193.8, 180.8, 186.0, 184.0],
        [192.6, 182.3, 175.1, 185.7],
        [190.2, 184.4, 181.0, 187.3],
    ]
    for marks, _ in read_block(ops, grey_blank_rows * 4):
        assert not any(marks)
