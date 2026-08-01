"""A6 — the OAuth `state` nonce is signed + time-bounded (CSRF on the connect flow)."""
from app.services import google_service as gs


def test_state_roundtrips():
    assert gs.verify_state(gs.make_state()) is True


def test_state_rejects_tampered_or_garbage():
    s = gs.make_state()
    assert gs.verify_state(s + "x") is False       # signature no longer matches
    assert gs.verify_state("a.b.c") is False        # wrong shape/sig
    assert gs.verify_state("garbage") is False      # not 3 parts
    assert gs.verify_state("") is False             # empty
    assert gs.verify_state(None) is False           # missing


def test_state_rejects_expired():
    # A freshly minted state is older than a 0-second (effectively negative) window.
    assert gs.verify_state(gs.make_state(), max_age_seconds=-1) is False
