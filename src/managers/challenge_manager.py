import random
from copy import deepcopy
from typing import Any

from src.data.challenges import CHALLENGES


class ChallengeManager:
    def __init__(self) -> None:
        self.last_id: str | None = None

    def next_challenge(self, phase: int) -> dict[str, Any]:
        pool = [item for item in CHALLENGES if item["phase"] == phase]
        if phase == 10:
            pool = CHALLENGES[:]
        if len(pool) > 1 and self.last_id:
            pool = [item for item in pool if item["id"] != self.last_id]
        challenge = deepcopy(random.choice(pool))
        random.shuffle(challenge["options"])
        self.last_id = challenge["id"]
        return challenge
