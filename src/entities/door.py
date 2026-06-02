import pygame

from src import config
from src.core.utils import draw_text


ANSWER_STYLES = {
    "true": {"symbol": "V", "color": config.GREEN, "dark": (7, 38, 28), "label": "VERDADEIRO"},
    "false": {"symbol": "F", "color": config.RED, "dark": (44, 8, 18), "label": "FALSO"},
    "unknown": {"symbol": "?", "color": config.YELLOW, "dark": (42, 33, 8), "label": "INDEFINIDO"},
    "equivalence": {"symbol": "≡", "color": config.PURPLE, "dark": (31, 14, 48), "label": "EQUIV."},
}


def classify_answer(text: str) -> str:
    normalized = text.strip().lower()
    if normalized == "verdadeiro":
        return "true"
    if normalized == "falso":
        return "false"
    if normalized in {"indefinido", "nao se aplica", "não se aplica", "contradicao", "contradição", "tautologia"}:
        return "unknown"
    return "equivalence"


class Door:
    def __init__(self, lane: int, text: str, is_correct: bool, speed: float) -> None:
        self.lane = lane
        self.x = config.WORLD_LANE_POSITIONS[lane]
        self.z = config.ANSWER_GATE_Z
        self.width = 1.92
        self.height = 2.72
        self.text = text
        self.is_correct = is_correct
        self.speed = speed
        self.answer_kind = classify_answer(text)
        self.style = ANSWER_STYLES[self.answer_kind]
        self.pulse = 0.0

    @property
    def y(self) -> float:
        return self.z

    @y.setter
    def y(self, value: float) -> None:
        self.z = abs(value) if value < 0 else value

    @property
    def rect(self) -> pygame.Rect:
        return pygame.Rect(config.LANE_POSITIONS[self.lane] - 84, int(config.PLAYER_Y - self.z), 168, 92)

    def update(self, dt: float, speed_multiplier: float = 1.0) -> None:
        self.z -= self.speed * speed_multiplier * dt
        self.pulse += dt * (6.0 if self.answer_kind == "false" else 3.5)

    def collides_with(self, player: object) -> bool:
        return self.lane == player.lane and self.z <= config.COLLISION_Z

    def is_offscreen(self) -> bool:
        return self.z < -3.0

    def draw(self, surface: pygame.Surface, font: pygame.font.Font, projection: object) -> None:
        rect = projection.world_rect(self.x, 0.2, self.z, self.width, self.height)
        if rect.bottom < config.HORIZON_Y - 20 or rect.top > config.SCREEN_HEIGHT:
            return
        color = self.style["color"]
        dark = self.style["dark"]
        pulse_size = int((1 + pygame.math.Vector2(1, 0).rotate(self.pulse * 40).x) * max(1, rect.w // 24))
        ground_x, ground_y, scale = projection.project(self.x, 0.0, self.z)
        shadow = pygame.Rect(0, 0, max(4, int(self.width * scale * 0.9)), max(2, int(0.22 * scale)))
        shadow.center = (ground_x, ground_y)
        pygame.draw.ellipse(surface, (0, 0, 0), shadow)
        glow = rect.inflate(max(8, rect.w // 4) + pulse_size, max(10, rect.h // 5) + pulse_size)
        pygame.draw.rect(surface, dark, rect, border_radius=8)
        pygame.draw.rect(surface, color, glow, max(1, rect.w // 60), border_radius=10)
        pygame.draw.rect(surface, color, rect.inflate(max(2, rect.w // 12), max(3, rect.h // 12)), 1, border_radius=10)
        pygame.draw.rect(surface, color, rect, max(2, rect.w // 18), border_radius=8)
        base = pygame.Rect(rect.left, ground_y - max(2, rect.h // 18), rect.width, max(3, rect.h // 12))
        pygame.draw.rect(surface, color, base, border_radius=4)
        reflection = pygame.Rect(rect.left + rect.w // 6, ground_y + max(2, rect.h // 28), rect.w * 2 // 3, max(2, rect.h // 18))
        pygame.draw.rect(surface, color, reflection, border_radius=6)
        pygame.draw.line(surface, config.WHITE, (rect.left + 8, rect.top + max(8, rect.h // 7)), (rect.right - 8, rect.top + max(8, rect.h // 7)), max(1, rect.w // 60))

        if rect.w > 24:
            sparkle_radius = max(1, rect.w // 35)
            for index, side in enumerate([-1, 1, -1, 1]):
                offset_y = rect.h * (0.18 + index * 0.17)
                wobble = int(pulse_size * side * 0.5)
                x = rect.centerx + side * (rect.w // 2 + max(4, rect.w // 10)) + wobble
                y = rect.top + int(offset_y)
                pygame.draw.circle(surface, color, (x, y), sparkle_radius)

        symbol_size = max(18, min(96, int(rect.h * 0.68)))
        symbol_font = pygame.font.SysFont("consolas", symbol_size, bold=True)
        symbol = symbol_font.render(self.style["symbol"], True, config.WHITE)
        outline = symbol_font.render(self.style["symbol"], True, color)
        symbol_center = (rect.centerx, rect.centery - max(0, rect.h // 12))
        for dx, dy in [(-2, 0), (2, 0), (0, -2), (0, 2)]:
            surface.blit(outline, outline.get_rect(center=(symbol_center[0] + dx, symbol_center[1] + dy)))
        surface.blit(symbol, symbol.get_rect(center=symbol_center))

        if rect.w > 78:
            label = self.text if rect.w > 116 else self.style["label"]
            label_font = pygame.font.SysFont("consolas", max(13, min(24, rect.w // 7)), bold=True)
            y = rect.bottom - max(15, rect.h // 7)
            draw_text(surface, label, label_font, config.WHITE, center=(rect.centerx, y), max_width=rect.width - 10)

        if self.answer_kind == "unknown" and rect.w > 32:
            for index in range(3):
                y = rect.top + 8 + index * max(5, rect.h // 5)
                pygame.draw.line(surface, color, (rect.left + 7, y), (rect.left + max(10, rect.w // 3), y), 1)
