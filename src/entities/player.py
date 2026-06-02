import math

import pygame

from src import config


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
    def height(self) -> int:
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

    def draw(self, surface: pygame.Surface, font: pygame.font.Font, projection: object | None = None) -> None:
        if projection:
            rect = projection.world_rect(self.x, self.world_y, config.PLAYER_RENDER_Z, self.width, self.height)
            rect.y += 28
        else:
            rect = self.hitbox
        lean_px = int(self.lean * 12)
        run_bob = 0 if self.is_airborne else int(math.sin(self.run_time * 18) * 4)
        if self.is_sliding:
            rect.y += 10

        glow = rect.inflate(32, 22)
        pygame.draw.ellipse(surface, (15, 105, 120), glow, 2)
        shadow = pygame.Rect(rect.x - 15, config.GROUND_Y + 8, rect.width + 30, 14)
        pygame.draw.ellipse(surface, (0, 0, 0), shadow)

        body = rect.move(lean_px, run_bob)
        color = config.RED if self.stumble_timer > 0 else config.CYAN
        pygame.draw.rect(surface, color, body, border_radius=14)
        pygame.draw.rect(surface, config.WHITE, body.inflate(-18, -22), 2, border_radius=10)

        visor = pygame.Rect(body.x + 12, body.y + 18, body.width - 24, 12)
        if self.is_sliding:
            visor.y = body.y + 11
        pygame.draw.rect(surface, config.PURPLE, visor, border_radius=6)

        foot_y = body.bottom + (0 if self.is_airborne else run_bob)
        pygame.draw.line(surface, config.WHITE, (body.centerx - 12, body.bottom - 4), (body.centerx - 28, foot_y), 3)
        pygame.draw.line(surface, config.WHITE, (body.centerx + 12, body.bottom - 4), (body.centerx + 28, foot_y), 3)
        label = font.render("BACK", True, config.BG)
        surface.blit(label, label.get_rect(center=body.center))
