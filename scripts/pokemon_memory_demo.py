"""Offline wiring check with synthetic Pokémon seat observations; no model/network calls."""
import json
import tempfile
from pathlib import Path

from altruagent.runner import DecisionContext, run_game
from examples.pokemon_memory_agent import GAME, ROOT, MemoryAgent, digest


class DemoGame:
    def __init__(self, stage, seat):
        self.session_id = f"offline-session-{stage}"
        self.tag = f"private-observation-game{stage}-P{seat+1:02}"
        self.turn = 0

    def _call(self, tool, args):
        state = dict(session_id=self.session_id, state_version=self.turn, phase="draft",
                     is_terminal=False, is_current_actor=True, status="in_progress",
                     observation=self.tag, legal_actions={"actions": [
                         {"action_id": "draft_pick:a", "label": "Draft A"},
                         {"action_id": "draft_pick:b", "label": "Draft B"}]})
        if tool == "get_game_state":
            return state
        if tool == "play_action":
            self.turn += 1
            return {"accepted": True, "state": {**state, "state_version": self.turn,
                    "is_terminal": self.turn == 2, "is_current_actor": self.turn < 2}}
        if tool == "get_result":
            return {"is_terminal": True, "status": "completed", "termination_reason": "offline fixture"}
        raise AssertionError(tool)


class DemoProvider:
    model = "offline-fixture"

    def __init__(self):
        self.calls = []

    def complete_structured(self, messages, schema_name, schema, *, timeout=None):
        self.calls.append(list(messages))
        return {"action_id": "draft_pick:a", "reasoning_summary": "Offline scripted choice."}


def simulate(root, trial="demo"):
    for stage in (1, 2):
        for pos in (0, 1):
            provider = DemoProvider()
            agent = MemoryAgent(provider, root, trial, str(stage))
            game = DemoGame(stage, pos)
            ctx = DecisionContext(game.session_id, None, GAME, "offline-agent", pos)
            agent.run_recorded_match(game, ctx, f"offline-match-{stage}", run_game)
            assert len(provider.calls) == 2
            seat = f"P{pos+1:02}"
            folder = agent.folder / seat
            if stage == 1:
                assert all(len(call) == 2 for call in provider.calls)
            else:
                original = (folder / "game1.jsonl").read_bytes()
                receipt = json.loads((folder / "game1.done.json").read_bytes())
                assert receipt["sha256"] == digest(original)
                for call in provider.calls:
                    assert call[1]["role"] == "user" and call[1]["content"].encode() == original
                    assert f"private-observation-game1-{seat}" in call[1]["content"]
                    assert f"private-observation-game1-P{2-pos:02}" not in call[1]["content"]
                assert b"get_result" in original and b"play_action" in original
                print(f"verified {seat}: {len(original)} bytes replayed exactly on both game-2 decisions")
    return Path(root) / ("trial-" + trial)


if __name__ == "__main__":
    ROOT.mkdir(exist_ok=True)
    print(simulate(Path(tempfile.mkdtemp(prefix="offline-", dir=ROOT))))
