import math
import pygame

from src import config
from src.core.utils import draw_text


POWERUPS = {
    "boost": {"label": "BOOST", "color": (255, 225, 80), "duration": 4.0},
    "magnet": {"label": "IMA", "color": (80, 220, 255), "duration": 7.0},
    "slowmo": {"label": "SLOW", "color": (180, 130, 255), "duration": 4.5},
    "shield": {"label": "ESCUDO", "color": (80, 255, 150), "duration": 8.0},
    "multiplier": {"label": "x2", "color": (255, 110, 210), "duration": 8.0},
}


class PowerUp:
    def __init__(self, lane: int, kind: str, speed: float) -> None:
        self.lane = lane
        self.kind = kind
        self.x = config.WORLD_LANE_POSITIONS[lane]
        self.z = config.POWERUP_SPAWN_Z
        self.speed = speed
        self.radius = 0.42
        self.phase = 0.0
        self.data = POWERUPS[kind]

    @property
    def y(self) -> float:
        return self.z

    @property
    def rect(self) -> pygame.Rect:
        return pygame.Rect(config.LANE_POSITIONS[self.lane] - 28, int(config.PLAYER_Y - self.z), 56, 56)

    def update(self, dt: float, speed_multiplier: float) -> None:
        self.z -= self.speed * speed_multiplier * dt
        self.phase += dt * 7

    def is_offscreen(self) -> bool:
        return self.z < -4.0

    def collides_with(self, player: object) -> bool:
        return self.lane == player.lane and self.z <= config.COLLISION_Z

    def draw(self, surface: pygame.Surface, font: pygame.font.Font, projection: object) -> None:
        y = 1.1 + math.sin(self.phase) * 0.18
        sx, sy, scale = projection.project(self.x, y, self.z)
        radius = max(3, int(self.radius * scale))
        if sy < config.HORIZON_Y - 30 or sy > config.SCREEN_HEIGHT + 30:
            return
        color = self.data["color"]
        gx, gy, ground_scale = projection.project(self.x, 0.0, self.z)
        shadow = pygame.Rect(0, 0, max(3, int(0.72 * ground_scale)), max(2, int(0.16 * ground_scale)))
        shadow.center = (gx, gy)
        pygame.draw.ellipse(surface, (0, 0, 0), shadow)
        pygame.draw.circle(surface, color, (sx, sy), radius, max(1, radius // 9))
        pygame.draw.circle(surface, (15, 22, 44), (sx, sy), max(1, radius - 5))
        if radius > 16:
            draw_text(surface, self.data["label"], font, config.WHITE, center=(sx, sy), max_width=radius * 2)
