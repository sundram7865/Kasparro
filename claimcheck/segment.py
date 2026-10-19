"""Deterministic sentence segmentation with exact code-point offsets.

The model never counts characters: it selects sentence IDs and Python maps
them back to [start_char, end_char) spans in the untouched ai_answer.
"""
from __future__ import annotations

from dataclasses import dataclass

TERMINATORS = ".!?"
CLOSERS = "\"')]”’"


@dataclass(frozen=True)
class Sentence:
    sentence_id: str
    start: int
    end: int
    text: str


def split_sentences(text: str) -> list[Sentence]:
    """Split on . ! ? followed by whitespace or end of text.

    A terminator followed by a non-space character (``1.5``, ``0.35``) is not a
    boundary. Trailing text without a terminator becomes its own sentence, so
    every non-whitespace character belongs to exactly one sentence.
    """
    spans: list[tuple[int, int]] = []
    n = len(text)
    i = 0
    start: int | None = None
    while i < n:
        ch = text[i]
        if start is None:
            if ch.isspace():
                i += 1
                continue
            start = i
        if ch in TERMINATORS:
            end = i + 1
            while end < n and text[end] in CLOSERS:
                end += 1
            if end == n or text[end].isspace():
                spans.append((start, end))
                start = None
                i = end
                continue
        i += 1
    if start is not None:
        end = n
        while end > start and text[end - 1].isspace():
            end -= 1
        spans.append((start, end))
    return [Sentence(f"S{k}", s, e, text[s:e]) for k, (s, e) in enumerate(spans, start=1)]
