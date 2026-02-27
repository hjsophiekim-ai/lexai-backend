"""두 버전 간 diff 계산 후 reverse_index 엔트리 생성."""

import difflib
from typing import List, Tuple
from sqlalchemy.orm import Session

from models import Version, VersionSegment, ReverseIndexEntry


def _lines_with_offsets(content: str) -> List[Tuple[int, int, str]]:
    """(start_offset, end_offset, line_text) per line. 1-based line numbers implied by index."""
    lines = content.splitlines(keepends=True)
    result = []
    offset = 0
    for line in lines:
        start = offset
        end = offset + len(line)
        result.append((start, end, line.rstrip("\n\r") or line))
        offset = end
    return result


def _make_summary(kind: str, old_snippet: str, new_snippet: str) -> str:
    if kind == "added":
        return f"추가됨: {new_snippet[:80]}{'...' if len(new_snippet) > 80 else ''}"
    if kind == "removed":
        return f"삭제됨: {old_snippet[:80]}{'...' if len(old_snippet) > 80 else ''}"
    if kind == "changed":
        return f"변경됨 (이전): {old_snippet[:40]}... → (이후): {new_snippet[:40]}..."
    return "변경됨"


def compute_and_store_reverse_index(
    db: Session,
    document_id: int,
    base_version_id: int,
    target_version_id: int,
) -> int:
    """
    base_version vs target_version 라인 단위 diff 계산 후,
    target_version 기준으로 reverse_index 엔트리 저장.
    Returns count of stored entries.
    """
    base = db.query(Version).filter(Version.id == base_version_id).first()
    target = db.query(Version).filter(Version.id == target_version_id).first()
    if not base or not target or base.document_id != document_id or target.document_id != document_id:
        return 0

    base_lines = base.content.splitlines()
    target_lines = target.content.splitlines()
    target_offsets = _lines_with_offsets(target.content)

    matcher = difflib.SequenceMatcher(None, base_lines, target_lines)
    count = 0
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "equal":
            continue
        # target 쪽 라인 인덱스 j1..j2 (0-based) → line_start/line_end (1-based)
        line_start = j1 + 1
        line_end = j2
        if line_end < line_start:
            line_end = line_start
        start_offset = target_offsets[j1][0] if j1 < len(target_offsets) else 0
        end_offset = target_offsets[j2 - 1][1] if j2 > 0 and j2 - 1 < len(target_offsets) else start_offset
        if j2 <= len(target_offsets):
            end_offset = target_offsets[j2 - 1][1]

        if tag == "replace":
            kind = "changed"
            old_snippet = "\n".join(base_lines[i1:i2]) if i2 > i1 else ""
            new_snippet = "\n".join(target_lines[j1:j2]) if j2 > j1 else ""
        elif tag == "insert":
            kind = "added"
            old_snippet = ""
            new_snippet = "\n".join(target_lines[j1:j2]) if j2 > j1 else ""
        elif tag == "delete":
            kind = "removed"
            old_snippet = "\n".join(base_lines[i1:i2]) if i2 > i1 else ""
            new_snippet = ""
        else:
            kind = "changed"
            old_snippet = "\n".join(base_lines[i1:i2]) if i2 > i1 else ""
            new_snippet = "\n".join(target_lines[j1:j2]) if j2 > j1 else ""

        summary = _make_summary(kind, old_snippet, new_snippet)
        evidence = []
        for k in range(j1, j2):
            if k < len(target_offsets):
                s, e, txt = target_offsets[k]
                evidence.append({"line_start": k + 1, "line_end": k + 1, "snippet": txt[:200]})

        entry = ReverseIndexEntry(
            version_id=target_version_id,
            start_offset=start_offset,
            end_offset=end_offset,
            line_start=line_start,
            line_end=line_end,
            kind=kind,
            summary=summary,
            evidence=evidence,
        )
        db.add(entry)
        count += 1

    db.commit()
    return count
