import pygame

from src import config
from src.core.utils import draw_text


OBSTACLE_TYPES = {
    "jump": {"label": "CAIXA", "color": (255, 205, 80), "requires": "jump", "size": (1.55, 0.78)},
    "slide": {"label": "LASER", "color": (255, 65, 120), "requires": "slide", "size": (1.7, 1.9)},
    "lane": {"label": "BLOQ.", "color": (120, 145, 255), "requires": "dodge", "size": (1.7, 1.65)},
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
        self.color = data["color"]
        self.label = data["label"]

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
        if self.lane != player.lane or self.z > config.COLLISION_Z:
            return False
        if self.kind == "jump" and player.is_airborne:
            return False
        if self.kind == "slide" and player.is_sliding:
            return False
        return True

    def draw(self, surface: pygame.Surface, font: pygame.font.Font, projection: object) -> None:
        y_base = 1.15 if self.kind == "slide" else 0.0
        rect = projection.world_rect(self.x, y_base, self.z, self.width, self.height)
        if rect.bottom < config.HORIZON_Y - 20 or rect.top > config.SCREEN_HEIGHT:
            return
        ground_x, ground_y, scale = projection.project(self.x, 0.0, self.z)
        shadow = pygame.Rect(0, 0, max(4, int(self.width * scale)), max(2, int(0.26 * scale)))
        shadow.center = (ground_x, ground_y)
        pygame.draw.ellipse(surface, (0, 0, 0), shadow)
        if self.kind == "slide":
            post_w = max(2, rect.w // 12)
            pygame.draw.rect(surface, (25, 16, 36), (rect.left, ground_y - rect.h, post_w, rect.h), border_radius=3)
            pygame.draw.rect(surface, (25, 16, 36), (rect.right - post_w, ground_y - rect.h, post_w, rect.h), border_radius=3)
            pygame.draw.rect(surface, self.color, rect, border_radius=8)
            inner = rect.inflate(-max(4, rect.w // 10), -max(8, rect.h // 2))
            pygame.draw.rect(surface, (255, 235, 245), inner, border_radius=8)
        elif self.kind == "jump":
            pygame.draw.rect(surface, (55, 35, 22), rect, border_radius=8)
            pygame.draw.rect(surface, self.color, rect, max(1, rect.w // 28), border_radius=8)
        else:
            pygame.draw.rect(surface, (20, 26, 54), rect, border_radius=8)
            pygame.draw.rect(surface, self.color, rect, max(1, rect.w // 28), border_radius=8)
        if rect.w > 42:
            draw_text(surface, self.label, font, config.WHITE, center=rect.center, max_width=rect.width - 10)
