import random
from dataclasses import dataclass, field

from src import config
from src.data.biomes import BIOMES, RARE_EVENTS


@dataclass
class Chunk:
    z: float
    biome_key: str
    event: str | None = None
    decorations: list[dict] = field(default_factory=list)

    @property
    def biome(self) -> dict:
        return BIOMES[self.biome_key]


class ChunkManager:
    def __init__(self) -> None:
        self.chunks: list[Chunk] = []
        self.last_biomes: list[str] = []

    def reset(self) -> None:
        self.chunks = []
        self.last_biomes = []
        for index in range(config.CHUNK_POOL_SIZE):
            self.chunks.append(self.create_chunk(index * config.CHUNK_LENGTH))

    def update(self, dz: float, difficulty: float) -> None:
        for chunk in self.chunks:
            chunk.z -= dz
        while self.chunks and self.chunks[0].z + config.CHUNK_LENGTH < config.TRACK_NEAR_Z:
            self.chunks.pop(0)
        while len(self.chunks) < config.CHUNK_POOL_SIZE:
            next_z = self.chunks[-1].z + config.CHUNK_LENGTH if self.chunks else config.TRACK_NEAR_Z
            self.chunks.append(self.create_chunk(next_z, difficulty))

    def current_biome_key(self) -> str:
        visible = [chunk for chunk in self.chunks if chunk.z <= 18 <= chunk.z + config.CHUNK_LENGTH]
        if visible:
            return visible[0].biome_key
        return self.chunks[0].biome_key if self.chunks else "academic"

    def create_chunk(self, z: float, difficulty: float = 0.0) -> Chunk:
        biome_key = self.pick_biome(difficulty)
        event = self.pick_event(difficulty)
        decorations = self.create_decorations(biome_key, event)
        self.last_biomes = (self.last_biomes + [biome_key])[-3:]
        return Chunk(z=z, biome_key=biome_key, event=event, decorations=decorations)

    def pick_biome(self, difficulty: float) -> str:
        options = list(BIOMES)
        if len(set(self.last_biomes[-2:])) == 1 and self.last_biomes:
            options = [item for item in options if item != self.last_biomes[-1]]
        if difficulty < 0.35 and "secret" in options:
            options.remove("secret")
        return random.choice(options)

    def pick_event(self, difficulty: float) -> str | None:
        chance = 0.035 + difficulty * 0.045
        return random.choice(RARE_EVENTS) if random.random() < chance else None

    def create_decorations(self, biome_key: str, event: str | None) -> list[dict]:
        biome = BIOMES[biome_key]
        count = random.randint(2, 5)
        decorations = []
        for index in range(count):
            side = random.choice([-1, 1])
            decorations.append(
                {
                    "x": side * random.uniform(4.25, 4.8),
                    "y": random.uniform(1.15, 2.65),
                    "z": random.uniform(1.4, config.CHUNK_LENGTH - 1.2),
                    "label": random.choice(biome["decor"]),
                    "side": side,
                }
            )
        if event:
            decorations.append({"x": 0.0, "y": 3.25, "z": config.CHUNK_LENGTH * 0.52, "label": event.upper(), "side": 0})
        return decorations
