import random

from src.core.utils import clamp


class RunnerCamera:
    def __init__(self) -> None:
        self.offset_x = 0.0
        self.offset_y = 0.0
        self.shake = 0.0
        self.fov_scale = 1.0
        self.tilt = 0.0
        self.world_x = 0.0
        self.world_y = 3.15

    def reset(self) -> None:
        self.offset_x = 0.0
        self.offset_y = 0.0
        self.shake = 0.0
        self.fov_scale = 1.0
        self.tilt = 0.0
        self.world_x = 0.0
        self.world_y = 3.15

    def add_shake(self, amount: float) -> None:
        self.shake = max(self.shake, amount)

    def update(self, dt: float, player_x: float, speed_ratio: float, lean: float) -> None:
        target_x = (player_x - 500) * -0.035
        target_y = -18 * speed_ratio
        self.offset_x += (target_x - self.offset_x) * min(1, dt * 5.5)
        self.offset_y += (target_y - self.offset_y) * min(1, dt * 4.0)
        self.fov_scale += ((1.0 + speed_ratio * 0.13) - self.fov_scale) * min(1, dt * 3.5)
        self.tilt += (lean * 0.35 - self.tilt) * min(1, dt * 8.0)
        self.world_x += ((player_x * 0.24) - self.world_x) * min(1, dt * 4.2)
        self.world_y += ((3.15 + speed_ratio * 0.35) - self.world_y) * min(1, dt * 2.5)
        self.shake = max(0.0, self.shake - dt * 18)

    @property
    def render_offset(self) -> tuple[int, int]:
        if self.shake <= 0:
            return int(self.offset_x), int(self.offset_y)
        jitter = clamp(self.shake, 0, 12)
        return (
            int(self.offset_x + random.uniform(-jitter, jitter)),
            int(self.offset_y + random.uniform(-jitter, jitter)),
        )
