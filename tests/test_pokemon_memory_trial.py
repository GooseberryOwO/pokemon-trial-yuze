import json

import pytest

from altruagent.runner import DecisionContext, DecisionError, run_game
from examples.llm.providers import ProviderError
from examples.pokemon_memory_agent import GAME, MemoryAgent
from scripts.pokemon_memory_demo import DemoGame, DemoProvider, simulate


def play(root, stage, pos, match, provider=None):
    game = DemoGame(stage, pos)
    a = MemoryAgent(provider or DemoProvider(), root, "test", str(stage))
    return a.run_recorded_match(game, DecisionContext(game.session_id, None, GAME, "x", pos), match, run_game)


def test_complete_private_history_on_every_decision(tmp_path):
    folder = simulate(tmp_path)
    for seat in ("P01", "P02"):
        events = [json.loads(s) for s in (folder / seat / "game2.jsonl").read_text().splitlines()]
        assert events[0]["previous"]["bytes"] == (folder / seat / "game1.jsonl").stat().st_size
        assert events[-1]["event"] == "end"


def test_wrong_match_missing_peer_overwrite_and_tampering(tmp_path):
    play(tmp_path, 1, 0, "a")
    with pytest.raises(FileExistsError):
        play(tmp_path, 1, 0, "a")
    with pytest.raises(ValueError, match="different match"):
        play(tmp_path, 1, 1, "b")
    with pytest.raises(ValueError, match="two completed"):
        play(tmp_path, 2, 0, "b")
    play(tmp_path, 1, 1, "a")
    with pytest.raises(ValueError, match="new match ID"):
        play(tmp_path, 2, 0, "a")
    path = tmp_path / "trial-test" / "P01" / "game1.jsonl"
    with path.open("ab") as f:
        f.write(b"modified")
    with pytest.raises(ValueError, match="digest mismatch"):
        play(tmp_path, 2, 0, "b")


def test_context_rejected_no_fallback_or_completion(tmp_path):
    class Reject(DemoProvider):
        def complete_structured(self, *a, **kw):
            raise ProviderError("input too long")
    for seat in (0, 1):
        play(tmp_path, 1, seat, "a")
    with pytest.raises(DecisionError, match="full model request failed"):
        play(tmp_path, 2, 0, "b", Reject())
    folder = tmp_path / "trial-test" / "P01"
    assert (folder / "game2.jsonl").exists()
    assert not (folder / "game2.done.json").exists()
    assert '"tool":"play_action"' not in (folder / "game2.jsonl").read_text()
