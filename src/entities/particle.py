import random

import pygame


class Particle:
    def __init__(self, x: float, y: float, color: tuple[int, int, int]) -> None:
        self.x = x
        self.y = y
        self.vx = random.uniform(-3.5, 3.5)
        self.vy = random.uniform(-5.0, 2.0)
        self.life = random.randint(20, 42)
        self.color = color

    def update(self) -> bool:
        self.x += self.vx
        self.y += self.vy
        self.vy += 0.18
        self.life -= 1
        return self.life > 0

    def draw(self, surface: pygame.Surface) -> None:
        radius = max(1, self.life // 10)
        pygame.draw.circle(surface, self.color, (int(self.x), int(self.y)), radius)
