"""extract_json_object — tolerant JSON parsing so a raw LLM blob never leaks to users."""
from app.services.textutil import extract_json_object, strip_fences


def test_plain_json():
    assert extract_json_object('{"answer_md": "hi", "grounded": true}') == {
        "answer_md": "hi",
        "grounded": True,
    }


def test_fenced_json():
    raw = '```json\n{"answer_md": "hi", "grounded": true}\n```'
    assert extract_json_object(raw) == {"answer_md": "hi", "grounded": True}


def test_json_with_trailing_stray_fence():
    # The reported Scout bug: a `{...}` followed by a lone ``` (and a stray backtick).
    raw = '{ "answer_md": "The site is https://x.com/ [S1].", "grounded": true } ```\n`'
    obj = extract_json_object(raw)
    assert obj is not None
    assert obj["answer_md"] == "The site is https://x.com/ [S1]."
    assert obj["grounded"] is True


def test_prose_around_json():
    raw = 'Sure! {"answer_md": "ok", "grounded": false} hope that helps'
    assert extract_json_object(raw) == {"answer_md": "ok", "grounded": False}


def test_not_json_returns_none():
    assert extract_json_object("just some plain text answer") is None
    assert extract_json_object("") is None


def test_strip_fences_unchanged():
    assert strip_fences("```\nhello\n```") == "hello"
