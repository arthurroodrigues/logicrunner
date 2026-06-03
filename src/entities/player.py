import math
import os

import pygame

from src import config


# ── Sprite sheet loading ──────────────────────────────────────────────────────

_FRAMES: dict[str, pygame.Surface] | None = None
_CACHE: dict[tuple[str, int], pygame.Surface] = {}


def _load_frames() -> dict[str, pygame.Surface]:
    global _FRAMES
    if _FRAMES is not None:
        return _FRAMES
    sheet = pygame.image.load(os.path.join("assets", "player.png")).convert_alpha()

    # Image: 666x375, transparent background.
    # Row 1 (y=0, h=187): 4 running frames; x dividers at gap midpoints.
    # Row 2 (y=187, h=188): 3 crouch frames (left) + 3 jump frames (right).
    ry1, rh1 = 0,   187
    ry2, rh2 = 187, 188
    run_xs    = [107, 213, 317, 422, 527]
    crouch_xs = [92,  172, 248, 321]
    jump_xs   = [321, 407, 489, 573]

    frames: dict[str, pygame.Surface] = {}
    for i in range(4):
        frames[f"run_{i}"] = sheet.subsurface(run_xs[i], ry1, run_xs[i+1] - run_xs[i], rh1)
    for i in range(3):
        frames[f"crouch_{i}"] = sheet.subsurface(crouch_xs[i], ry2, crouch_xs[i+1] - crouch_xs[i], rh2)
        frames[f"jump_{i}"]   = sheet.subsurface(jump_xs[i],   ry2, jump_xs[i+1]   - jump_xs[i],   rh2)
    _FRAMES = frames
    return frames


def _get_scaled(frames: dict, key: str, target_h: int) -> pygame.Surface:
    cache_key = (key, target_h)
    if cache_key not in _CACHE:
        src = frames[key]
        w = max(1, int(src.get_width() * target_h / src.get_height()))
        _CACHE[cache_key] = pygame.transform.smoothscale(src, (w, target_h))
    return _CACHE[cache_key]


# ── Player class ──────────────────────────────────────────────────────────────

class Player:
    def __init__(self) -> None:
        self.lane = config.PLAYER_START_LANE
        self.x = float(config.WORLD_LANE_POSITIONS[self.lane])
        self.y = float(config.GROUND_Y)
        self.world_y = 0.0
        self.target_x = self.x
        self.vx = 0.0
        self.vy = 0.0
        self.width = 0.74
        self.standing_height = 1.55
        self.slide_height = 0.82
        self.slide_timer = 0.0
        self.run_time = 0.0
        self.lean = 0.0
        self.stumble_timer = 0.0
        self.landing_timer = 0.0

    @property
    def is_airborne(self) -> bool:
        return self.world_y > 0.04 or self.vy > 0

    @property
    def is_sliding(self) -> bool:
        return self.slide_timer > 0

    @property
    def height(self) -> float:
        return self.slide_height if self.is_sliding else self.standing_height

    @property
    def hitbox(self) -> pygame.Rect:
        screen_x = config.LANE_POSITIONS[self.lane]
        screen_y = config.PLAYER_Y - int(self.world_y * 120)
        width = 58
        height = 46 if self.is_sliding else 86
        return pygame.Rect(
            int(screen_x - width // 2),
            int(screen_y - height),
            width,
            height,
        )

    @property
    def rect(self) -> pygame.Rect:
        return self.hitbox

    def move_left(self) -> None:
        if self.lane > 0:
            self.lane -= 1
            self.target_x = float(config.WORLD_LANE_POSITIONS[self.lane])
            self.lean = -1.0

    def move_right(self) -> None:
        if self.lane < len(config.LANE_POSITIONS) - 1:
            self.lane += 1
            self.target_x = float(config.WORLD_LANE_POSITIONS[self.lane])
            self.lean = 1.0

    def jump(self) -> bool:
        if not self.is_airborne and not self.is_sliding:
            self.vy = 8.6
            self.landing_timer = 0
            return True
        return False

    def slide(self) -> bool:
        if not self.is_airborne:
            self.slide_timer = config.SLIDE_DURATION
            return True
        return False

    def stumble(self) -> None:
        self.stumble_timer = 0.45

    def reset(self) -> None:
        self.lane = config.PLAYER_START_LANE
        self.x = float(config.WORLD_LANE_POSITIONS[self.lane])
        self.target_x = self.x
        self.y = float(config.GROUND_Y)
        self.world_y = 0.0
        self.vx = 0.0
        self.vy = 0.0
        self.slide_timer = 0.0
        self.lean = 0.0
        self.stumble_timer = 0.0
        self.landing_timer = 0.0

    def update(self, dt: float) -> bool:
        self.run_time += dt
        old_airborne = self.is_airborne
        stiffness = 54.0
        damping = 14.5
        force = (self.target_x - self.x) * stiffness - self.vx * damping
        self.vx += force * dt
        self.x += self.vx * dt
        self.lean += ((self.vx / 520) - self.lean) * min(1, dt * 8)

        self.vy -= 22.0 * dt
        self.world_y += self.vy * dt
        landed = False
        if self.world_y <= 0:
            if old_airborne and self.vy < -2:
                landed = True
                self.landing_timer = 0.18
            self.world_y = 0.0
            self.vy = 0.0

        if self.slide_timer > 0:
            self.slide_timer = max(0.0, self.slide_timer - dt)
        if self.stumble_timer > 0:
            self.stumble_timer = max(0.0, self.stumble_timer - dt)
        if self.landing_timer > 0:
            self.landing_timer = max(0.0, self.landing_timer - dt)
        return landed

    def _frame_key(self) -> str:
        if self.is_sliding:
            return f"crouch_{int(self.run_time * 7) % 3}"
        if self.is_airborne:
            if self.vy > 2:
                return "jump_0"
            if self.vy >= -2:
                return "jump_1"
            return "jump_2"
        return f"run_{int(self.run_time * 9) % 4}"

    def draw(self, surface: pygame.Surface, font: pygame.font.Font, projection: object | None = None) -> None:
        if projection:
            rect = projection.world_rect(self.x, self.world_y, config.PLAYER_RENDER_Z, self.width, self.standing_height)
            rect.y += 28
        else:
            rect = self.hitbox

        lean_px = int(self.lean * 12)
        run_bob = 0 if self.is_airborne else int(math.sin(self.run_time * 18) * 4)
        if self.is_sliding:
            rect.y += 10

        # Shadow ellipse on the ground
        shadow_w = rect.width + 24
        pygame.draw.ellipse(surface, (0, 0, 0), pygame.Rect(rect.centerx - shadow_w // 2, config.GROUND_Y + 6, shadow_w, 12))

        frames = _load_frames()
        key = self._frame_key()
        target_h = max(10, rect.height)
        img = _get_scaled(frames, key, target_h)

        blit_x = rect.centerx - img.get_width() // 2 + lean_px
        blit_y = rect.bottom - img.get_height() + run_bob
        surface.blit(img, (blit_x, blit_y))

        # Red tint overlay when hit
        if self.stumble_timer > 0:
            tint = pygame.Surface(img.get_size(), pygame.SRCALPHA)
            tint.fill((255, 40, 40, 110))
            surface.blit(tint, (blit_x, blit_y))
