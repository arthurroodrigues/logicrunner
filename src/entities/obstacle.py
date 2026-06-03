import pygame

from src import config
from src.core.utils import get_sprite_scaled


OBSTACLE_TYPES = {
    "jump": {"sprite": "caixa.png",     "requires": "jump",  "size": (1.15, 0.76)},
    "cone": {"sprite": "cone.png",      "requires": "jump",  "size": (1.10, 0.80)},
    "lane": {"sprite": "obstaculo.png", "requires": "dodge", "size": (1.28, 2.55)},
}


class Obstacle:
    def __init__(self, lane: int, kind: str, speed: float, biome_key: str = "academic") -> None:
        self.lane = lane
        self.kind = kind
        self.x = config.WORLD_LANE_POSITIONS[lane]
        self.z = config.OBSTACLE_SPAWN_Z
        self.speed = speed
        self.biome_key = biome_key
        self.passed = False
        data = OBSTACLE_TYPES[kind]
        self.width, self.height = data["size"]
        self.sprite_file = data["sprite"]

    @property
    def y(self) -> float:
        return self.z

    @property
    def rect(self) -> pygame.Rect:
        return pygame.Rect(config.LANE_POSITIONS[self.lane] - 70, int(config.PLAYER_Y - self.z), 140, 110)

    def update(self, dt: float, speed_multiplier: float) -> None:
        self.z -= self.speed * speed_multiplier * dt

    def is_offscreen(self) -> bool:
        return self.z < -4.0

    def collides_with(self, player: object) -> bool:
        if self.z > config.COLLISION_Z:
            return False
        if abs(player.x - self.x) > config.LANE_WIDTH_WORLD * 0.72:
            return False
        if self.kind in ("jump", "cone") and player.is_airborne:
            return False
        return True

    def draw(self, surface: pygame.Surface, font: pygame.font.Font, projection: object) -> None:
        rect = projection.world_rect(self.x, 0.0, self.z, self.width, self.height)
        if rect.bottom < config.HORIZON_Y - 20 or rect.top > config.SCREEN_HEIGHT:
            return

        # Shadow
        ground_x, ground_y, scale = projection.project(self.x, 0.0, self.z)
        shadow = pygame.Rect(0, 0, max(4, int(self.width * scale)), max(2, int(0.26 * scale)))
        shadow.center = (ground_x, ground_y)
        pygame.draw.ellipse(surface, (0, 0, 0), shadow)

        # Sprite
        w = max(1, rect.width)
        h = max(1, rect.height)
        img = get_sprite_scaled(self.sprite_file, w, h)
        surface.blit(img, (rect.x, rect.y))
