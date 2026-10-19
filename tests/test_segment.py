from claimcheck.segment import split_sentences


def test_every_gold_span_is_exactly_one_segment(answers_by_id, gold):
    spans = {
        (aid, s.start, s.end)
        for aid, answer in answers_by_id.items()
        for s in split_sentences(answer.ai_answer)
    }
    for g in gold:
        assert (g.answer_id, g.start_char, g.end_char) in spans, g.claim_id


def test_segments_cover_text_exactly_without_whitespace_edges(answers):
    for answer in answers:
        text = answer.ai_answer
        sentences = split_sentences(text)
        assert [s.sentence_id for s in sentences] == [f"S{i}" for i in range(1, len(sentences) + 1)]
        covered = "".join(s.text for s in sentences)
        assert "".join(covered.split()) == "".join(text.split())
        for s in sentences:
            assert s.text == text[s.start:s.end] == s.text.strip()


def test_decimal_numbers_do_not_end_sentences():
    text = "It lasts 1.5 years. It weighs 0.35 kilograms! Done?"
    assert [s.text for s in split_sentences(text)] == [
        "It lasts 1.5 years.",
        "It weighs 0.35 kilograms!",
        "Done?",
    ]


def test_trailing_text_without_terminator_is_kept():
    text = "First sentence.\n\n  trailing fragment  "
    sentences = split_sentences(text)
    assert [s.text for s in sentences] == ["First sentence.", "trailing fragment"]
    assert text[sentences[1].start:sentences[1].end] == "trailing fragment"
