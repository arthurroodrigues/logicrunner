import random

from src import config
from src.data.biomes import BIOMES
from src.entities.collectible import Collectible
from src.entities.obstacle import Obstacle
from src.entities.powerup import PowerUp


class RunnerSpawnManager:
    def __init__(self) -> None:
        self.obstacle_timer = 0.0
        self.powerup_timer = 5.0
        self.collectible_timer = 0.8
        self.last_lane: int | None = None
        self.last_kind: str | None = None

    def reset(self) -> None:
        self.obstacle_timer = 0.6
        self.powerup_timer = 3.5
        self.collectible_timer = 0.6
        self.last_lane = None
        self.last_kind = None

    def update(self, dt: float, phase: int, speed: float, biome_key: str = "academic", correct_lane: int | None = None) -> tuple[list[Obstacle], list[PowerUp], list[Collectible]]:
        self.obstacle_timer -= dt
        self.powerup_timer -= dt
        self.collectible_timer -= dt
        obstacles: list[Obstacle] = []
        powerups: list[PowerUp] = []
        collectibles: list[Collectible] = []
        difficulty = min(1.0, phase / 10)
        biome = BIOMES.get(biome_key, BIOMES["academic"])

        if self.obstacle_timer <= 0:
            available_lanes = [lane for lane in [0, 1, 2] if lane != correct_lane]
            count = 1 if random.random() > 0.18 + difficulty * 0.22 else 2
            count = min(count, len(available_lanes))
            if count > 0:
                lanes = random.sample(available_lanes, count)
                if count == 2 and self.last_lane in lanes:
                    lanes = random.sample(available_lanes, count)
                for lane in lanes:
                    kind_choices = list(biome["obstacles"])
                    if self.last_kind in kind_choices and len(kind_choices) > 1:
                        kind_choices.remove(self.last_kind)
                    kind = random.choice(kind_choices)
                    obstacles.append(Obstacle(lane, kind, speed, biome_key=biome_key))
                    self.last_lane = lane
                    self.last_kind = kind
            self.obstacle_timer = max(0.70, 1.55 - difficulty * 0.5 + random.uniform(-0.10, 0.20))

        if self.powerup_timer <= 0:
            kind = random.choice(["boost", "slowmo", "shield", "multiplier"])
            powerups.append(PowerUp(random.randrange(3), kind, speed))
            self.powerup_timer = random.uniform(7.0, 12.0)

        if self.collectible_timer <= 0:
            lane = random.randrange(3)
            kind = "coin"
            for offset in range(random.randint(3, 5)):
                collectibles.append(Collectible(lane, kind, speed, config.POWERUP_SPAWN_Z + offset * 2.0))
            self.collectible_timer = random.uniform(0.7, 1.6)

        return obstacles, powerups, collectibles
