import random

from src import config
from src.data.biomes import BIOMES
from src.entities.collectible import Collectible
from src.entities.obstacle import Obstacle
from src.entities.powerup import PowerUp


class RunnerSpawnManager:
    def __init__(self) -> None:
        self.obstacle_timer = 0.0
        self.powerup_timer = 6.0
        self.collectible_timer = 1.4
        self.last_lane: int | None = None
        self.last_kind: str | None = None

    def reset(self) -> None:
        self.obstacle_timer = 0.8
        self.powerup_timer = 4.0
        self.collectible_timer = 1.0
        self.last_lane = None
        self.last_kind = None

    def update(self, dt: float, phase: int, speed: float, biome_key: str = "academic") -> tuple[list[Obstacle], list[PowerUp], list[Collectible]]:
        self.obstacle_timer -= dt
        self.powerup_timer -= dt
        self.collectible_timer -= dt
        obstacles: list[Obstacle] = []
        powerups: list[PowerUp] = []
        collectibles: list[Collectible] = []
        difficulty = min(1.0, phase / 10)
        biome = BIOMES.get(biome_key, BIOMES["academic"])

        if self.obstacle_timer <= 0:
            count = 1 if random.random() > 0.18 + difficulty * 0.22 else 2
            lanes = random.sample([0, 1, 2], count)
            if count == 2 and self.last_lane in lanes:
                lanes = random.sample([0, 1, 2], count)
            for lane in lanes:
                kind_choices = list(biome["obstacles"])
                if self.last_kind in kind_choices and len(kind_choices) > 1:
                    kind_choices.remove(self.last_kind)
                kind = random.choice(kind_choices)
                obstacles.append(Obstacle(lane, kind, speed, biome_key=biome_key))
                self.last_lane = lane
                self.last_kind = kind
            self.obstacle_timer = max(0.95, 1.95 - difficulty * 0.5 + random.uniform(-0.12, 0.28))

        if self.powerup_timer <= 0:
            kind = random.choice(["boost", "magnet", "slowmo", "shield", "multiplier"])
            powerups.append(PowerUp(random.randrange(3), kind, speed))
            self.powerup_timer = random.uniform(7.0, 12.0)

        if self.collectible_timer <= 0:
            lane = random.randrange(3)
            kind = random.choice(["coin", "coin", "chip", "page", "data"])
            for offset in range(random.randint(2, 4)):
                collectibles.append(Collectible(lane, kind, speed, config.POWERUP_SPAWN_Z + offset * 2.0))
            self.collectible_timer = random.uniform(1.0, 2.2)

        return obstacles, powerups, collectibles
