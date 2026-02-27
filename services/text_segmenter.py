"""텍스트를 라인 단위로 분해하여 구조적 위치(start/end, line_start/line_end) 생성."""

from typing import List, Tuple


def segment_text(content: str) -> List[Tuple[int, int, int, int, str]]:
    """
    Returns list of (line_start, line_end, start_offset, end_offset, content).
    Line numbers are 1-based.
    """
    lines = content.splitlines(keepends=True)
    segments = []
    offset = 0
    for i, line in enumerate(lines):
        line_num = i + 1
        start = offset
        end = offset + len(line)
        segments.append((line_num, line_num, start, end, line.rstrip("\n\r") or line))
        offset = end
    if not segments and content:
        segments.append((1, 1, 0, len(content), content))
    elif not segments:
        segments.append((1, 1, 0, 0, ""))
    return segments
