import math
import pygame

from src import config
from src.core.utils import draw_text, get_sprite_scaled


POWERUPS = {
    "boost":      {"label": "BOOST",  "color": (255, 225, 80),  "duration": 4.0,  "sprite": "boost.png"},
    "slowmo":     {"label": "SLOW",   "color": (180, 130, 255), "duration": 4.5,  "sprite": "slow.png"},
    "shield":     {"label": "ESCUDO", "color": (80, 255, 150),  "duration": 8.0,  "sprite": "escudo.png"},
    "multiplier": {"label": "x2",     "color": (255, 110, 210), "duration": 8.0,  "sprite": "mutiplicador.png"},
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
        return self.z <= config.COLLISION_Z and abs(player.x - self.x) <= config.LANE_WIDTH_WORLD * 0.85

    def draw(self, surface: pygame.Surface, font: pygame.font.Font, projection: object) -> None:
        y_world = 1.1 + math.sin(self.phase) * 0.18
        sx, sy, scale = projection.project(self.x, y_world, self.z)
        radius = max(3, int(self.radius * scale))
        if sy < config.HORIZON_Y - 30 or sy > config.SCREEN_HEIGHT + 30:
            return

        # Ground shadow
        gx, gy, gs = projection.project(self.x, 0.0, self.z)
        shadow = pygame.Rect(0, 0, max(3, int(0.72 * gs)), max(2, int(0.16 * gs)))
        shadow.center = (gx, gy)
        pygame.draw.ellipse(surface, (0, 0, 0), shadow)

        sprite_file = self.data["sprite"]
        if sprite_file:
            size = radius * 2
            img = get_sprite_scaled(sprite_file, size, size)
            surface.blit(img, (sx - radius, sy - radius))
        else:
            color = self.data["color"]
            pygame.draw.circle(surface, color, (sx, sy), radius, max(1, radius // 9))
            pygame.draw.circle(surface, (15, 22, 44), (sx, sy), max(1, radius - 5))
            if radius > 16:
                draw_text(surface, self.data["label"], font, config.WHITE, center=(sx, sy), max_width=radius * 2)
