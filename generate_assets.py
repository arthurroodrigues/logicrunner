import math
import os
import random
from pathlib import Path

import pygame


ROOT = Path("assets/generated")

CYAN = (0, 255, 255)
PURPLE = (170, 80, 255)
GREEN = (0, 255, 120)
RED = (255, 80, 80)
YELLOW = (255, 220, 0)
BG = (5, 10, 25)
WHITE = (240, 248, 255)
METAL = (18, 28, 48)
METAL_2 = (30, 42, 68)


def ensure_dirs() -> None:
    for folder in [
        "floor",
        "walls",
        "ceiling",
        "gates",
        "obstacles",
        "decorations",
        "signs",
        "collectibles",
        "player",
        "effects",
    ]:
        (ROOT / folder).mkdir(parents=True, exist_ok=True)


def save(surface: pygame.Surface, folder: str, filename: str) -> None:
    pygame.image.save(surface, ROOT / folder / filename)


def surf(size: tuple[int, int]) -> pygame.Surface:
    return pygame.Surface(size, pygame.SRCALPHA)


def add_glow(surface: pygame.Surface, shape_drawer, color: tuple[int, int, int], passes: int = 5) -> None:
    for index in range(passes, 0, -1):
        alpha = int(28 / index)
        shape_drawer((*color, alpha), index * 7)


def draw_text(
    surface: pygame.Surface,
    text: str,
    size: int,
    color: tuple[int, int, int],
    center: tuple[int, int],
    bold: bool = True,
) -> None:
    font = pygame.font.SysFont("consolas", size, bold=bold)
    rendered = font.render(text, True, color)
    surface.blit(rendered, rendered.get_rect(center=center))


def draw_neon_rect(surface: pygame.Surface, rect: pygame.Rect, color: tuple[int, int, int], width: int = 3, radius: int = 12) -> None:
    for expand, alpha in [(30, 22), (20, 32), (10, 48)]:
        pygame.draw.rect(surface, (*color, alpha), rect.inflate(expand, expand), width, border_radius=radius)
    pygame.draw.rect(surface, color, rect, width, border_radius=radius)


def draw_gradient_rect(surface: pygame.Surface, rect: pygame.Rect, top: tuple[int, int, int], bottom: tuple[int, int, int]) -> None:
    for y in range(rect.height):
        t = y / max(1, rect.height - 1)
        color = tuple(int(top[i] * (1 - t) + bottom[i] * t) for i in range(3))
        pygame.draw.line(surface, color, (rect.x, rect.y + y), (rect.right, rect.y + y))


def make_floor(index: int) -> pygame.Surface:
    s = surf((512, 512))
    draw_gradient_rect(s, pygame.Rect(0, 0, 512, 512), (8, 14, 32), (16, 28, 52))
    accent = [CYAN, PURPLE, GREEN, YELLOW, (50, 160, 255)][index % 5]
    for x in range(0, 513, 64):
        pygame.draw.line(s, (20, 45, 70), (x, 0), (x, 512), 1)
    for y in range(0, 513, 64):
        pygame.draw.line(s, (20, 45, 70), (0, y), (512, y), 1)
    for x in [128, 256, 384]:
        pygame.draw.line(s, (*accent, 150), (x, 0), (x, 512), 5)
        pygame.draw.line(s, (*accent, 60), (x - 8, 0), (x - 8, 512), 2)
        pygame.draw.line(s, (*accent, 60), (x + 8, 0), (x + 8, 512), 2)
    for y in [96, 224, 352, 480]:
        pygame.draw.line(s, (*accent, 120), (0, y), (512, y), 3)
    pygame.draw.rect(s, (*WHITE, 24), (8, 8, 496, 496), 2)
    return s


def make_wall(side: str, index: int) -> pygame.Surface:
    s = surf((512, 512))
    draw_gradient_rect(s, pygame.Rect(0, 0, 512, 512), (7, 12, 28), (18, 22, 46))
    accent = [CYAN, PURPLE, GREEN][index % 3]
    mirror = -1 if side == "right" else 1
    pygame.draw.rect(s, METAL_2, (36, 76, 170, 322), border_radius=12)
    draw_neon_rect(s, pygame.Rect(36, 76, 170, 322), accent, 3, 12)
    draw_text(s, "ROOM", 28, WHITE, (121, 110))
    for i in range(4):
        x = 260 + i * 42
        pygame.draw.rect(s, METAL, (x, 286, 30, 110), border_radius=5)
        pygame.draw.line(s, accent, (x + 4, 306), (x + 26, 306), 2)
    panel = pygame.Rect(250, 92, 188, 82)
    pygame.draw.rect(s, (8, 18, 34), panel, border_radius=10)
    draw_neon_rect(s, panel, accent, 2, 10)
    draw_text(s, ["AI LAB", "LOGIC", "MATH"][index % 3], 26, accent, panel.center)
    for y in range(0, 512, 64):
        start = (512, y) if mirror < 0 else (0, y)
        end = (0, y + 70) if mirror < 0 else (512, y + 70)
        pygame.draw.line(s, (*accent, 65), start, end, 1)
    return s


def make_ceiling(index: int) -> pygame.Surface:
    s = surf((512, 512))
    draw_gradient_rect(s, pygame.Rect(0, 0, 512, 512), (4, 7, 18), (18, 20, 36))
    accent = [CYAN, PURPLE, YELLOW][index % 3]
    for x in range(40, 512, 120):
        pygame.draw.rect(s, METAL_2, (x, 80, 58, 360), border_radius=16)
        pygame.draw.line(s, accent, (x + 29, 100), (x + 29, 420), 5)
    for y in [96, 256, 416]:
        pygame.draw.line(s, (45, 55, 78), (0, y), (512, y), 8)
        pygame.draw.line(s, (*accent, 130), (0, y), (512, y), 2)
    return s


def make_gate(symbol: str, color: tuple[int, int, int]) -> pygame.Surface:
    s = surf((512, 512))
    rect = pygame.Rect(124, 62, 264, 378)
    for expand, alpha in [(80, 25), (52, 38), (28, 65)]:
        pygame.draw.rect(s, (*color, alpha), rect.inflate(expand, expand), 8, border_radius=42)
    pygame.draw.rect(s, (6, 16, 30, 210), rect, border_radius=36)
    pygame.draw.rect(s, color, rect, 12, border_radius=36)
    pygame.draw.rect(s, (*WHITE, 180), rect.inflate(-34, -34), 3, border_radius=28)
    pygame.draw.rect(s, (*color, 120), (154, 438, 208, 32), border_radius=16)
    for _ in range(28):
        x = random.randint(80, 430)
        y = random.randint(40, 470)
        pygame.draw.circle(s, (*color, random.randint(80, 180)), (x, y), random.randint(1, 4))
    draw_text(s, symbol, 210, color, (256, 245))
    draw_text(s, symbol, 190, WHITE, (256, 245))
    return s


def make_low_obstacle(kind: str) -> pygame.Surface:
    s = surf((256, 256))
    accent = YELLOW
    if kind == "chair":
        pygame.draw.rect(s, (40, 48, 70), (70, 96, 110, 38), border_radius=8)
        pygame.draw.rect(s, (30, 36, 56), (86, 54, 78, 92), border_radius=12)
        pygame.draw.line(s, accent, (82, 94), (168, 94), 4)
        for x in [82, 164]:
            pygame.draw.line(s, WHITE, (x, 134), (x - 20, 210), 5)
            pygame.draw.line(s, WHITE, (x + 10, 134), (x + 30, 210), 5)
    elif kind == "desk":
        pygame.draw.rect(s, (46, 36, 42), (42, 92, 172, 50), border_radius=10)
        pygame.draw.line(s, accent, (50, 92), (206, 92), 5)
        for x in [58, 196]:
            pygame.draw.line(s, WHITE, (x, 142), (x - 20, 218), 6)
    elif kind == "books":
        colors = [CYAN, PURPLE, YELLOW, GREEN]
        for i in range(5):
            rect = pygame.Rect(58 + i * 8, 160 - i * 24, 142, 26)
            pygame.draw.rect(s, colors[i % 4], rect, border_radius=5)
            pygame.draw.rect(s, (10, 14, 28), rect.inflate(-12, -8), border_radius=3)
    elif kind == "backpack":
        pygame.draw.rect(s, (28, 34, 58), (72, 62, 112, 160), border_radius=34)
        pygame.draw.rect(s, PURPLE, (88, 116, 80, 70), 5, border_radius=18)
        pygame.draw.line(s, CYAN, (84, 74), (66, 148), 5)
        pygame.draw.line(s, CYAN, (172, 74), (190, 148), 5)
    else:
        pygame.draw.rect(s, (34, 42, 55), (72, 74, 112, 150), border_radius=20)
        pygame.draw.rect(s, CYAN, (62, 58, 132, 34), border_radius=10)
        pygame.draw.line(s, RED, (90, 118), (166, 190), 5)
    draw_neon_rect(s, pygame.Rect(44, 44, 168, 184), accent, 2, 18)
    return s


def make_high_obstacle(kind: str) -> pygame.Surface:
    s = surf((256, 256))
    accent = random.choice([CYAN, PURPLE, RED, GREEN])
    if kind == "locker":
        for x in [48, 92, 136]:
            pygame.draw.rect(s, (28, 36, 58), (x, 28, 42, 198), border_radius=8)
            pygame.draw.line(s, CYAN, (x + 8, 62), (x + 34, 62), 2)
            pygame.draw.circle(s, YELLOW, (x + 32, 118), 3)
    elif kind == "library_cart":
        pygame.draw.rect(s, (32, 38, 54), (44, 70, 168, 120), border_radius=12)
        for y in [96, 132, 166]:
            pygame.draw.line(s, YELLOW, (56, y), (200, y), 5)
        for x in [76, 176]:
            pygame.draw.circle(s, WHITE, (x, 210), 16, 4)
    elif kind == "projector":
        pygame.draw.rect(s, (34, 40, 60), (58, 82, 140, 86), border_radius=16)
        pygame.draw.circle(s, CYAN, (154, 125), 28, 5)
        pygame.draw.polygon(s, (*CYAN, 70), [(182, 112), (236, 78), (236, 166)])
    elif kind == "server_rack":
        pygame.draw.rect(s, (18, 26, 42), (62, 28, 132, 210), border_radius=12)
        for y in range(48, 214, 32):
            pygame.draw.rect(s, (34, 48, 74), (76, y, 104, 20), border_radius=4)
            pygame.draw.circle(s, GREEN, (166, y + 10), 3)
    else:
        pygame.draw.rect(s, (30, 28, 46), (60, 28, 136, 210), border_radius=18)
        pygame.draw.rect(s, CYAN, (78, 52, 100, 44), border_radius=8)
        draw_text(s, "VEND", 24, WHITE, (128, 74))
        pygame.draw.rect(s, (12, 18, 34), (84, 112, 88, 72), border_radius=8)
    draw_neon_rect(s, pygame.Rect(42, 20, 172, 224), accent, 2, 16)
    return s


def make_decoration(name: str) -> pygame.Surface:
    s = surf((512, 512))
    if name == "bench":
        pygame.draw.rect(s, (38, 35, 48), (94, 230, 324, 54), border_radius=14)
        pygame.draw.rect(s, (42, 38, 54), (120, 164, 272, 70), border_radius=16)
        for x in [142, 370]:
            pygame.draw.line(s, CYAN, (x, 284), (x - 34, 392), 8)
            pygame.draw.line(s, CYAN, (x + 20, 284), (x + 54, 392), 8)
    elif name == "plant":
        pygame.draw.rect(s, (46, 38, 46), (184, 312, 144, 92), border_radius=18)
        for angle in range(0, 360, 35):
            end = (256 + int(math.cos(math.radians(angle)) * 105), 250 + int(math.sin(math.radians(angle)) * 90))
            pygame.draw.line(s, GREEN, (256, 310), end, 12)
    elif name.startswith("poster"):
        color = {"poster_logic": CYAN, "poster_math": YELLOW, "poster_ai": PURPLE}[name]
        rect = pygame.Rect(112, 92, 288, 328)
        pygame.draw.rect(s, (8, 16, 34), rect, border_radius=16)
        draw_neon_rect(s, rect, color, 4, 16)
        if name == "poster_logic":
            draw_text(s, "P", 64, color, (190, 250))
            draw_text(s, "Q", 64, color, (322, 250))
            pygame.draw.line(s, color, (234, 276), (256, 220), 8)
            pygame.draw.line(s, color, (278, 276), (256, 220), 8)
        else:
            label = {"poster_math": "SUM", "poster_ai": "AI"}[name]
            draw_text(s, label, 64, color, rect.center)
    elif name == "clock":
        pygame.draw.circle(s, (8, 16, 34), (256, 256), 128)
        pygame.draw.circle(s, CYAN, (256, 256), 128, 8)
        pygame.draw.line(s, WHITE, (256, 256), (256, 160), 7)
        pygame.draw.line(s, WHITE, (256, 256), (326, 280), 7)
    elif name == "fire_extinguisher":
        pygame.draw.rect(s, RED, (196, 132, 116, 270), border_radius=42)
        pygame.draw.rect(s, WHITE, (216, 194, 76, 48), border_radius=8)
        pygame.draw.line(s, CYAN, (256, 132), (316, 70), 8)
    else:
        pygame.draw.rect(s, (8, 18, 34), (80, 90, 352, 280), border_radius=18)
        draw_neon_rect(s, pygame.Rect(80, 90, 352, 280), CYAN, 5, 18)
        pygame.draw.line(s, CYAN, (256, 90), (256, 370), 4)
        pygame.draw.line(s, CYAN, (80, 230), (432, 230), 4)
    return s


def make_sign(label: str) -> pygame.Surface:
    s = surf((512, 512))
    rect = pygame.Rect(70, 170, 372, 142)
    pygame.draw.rect(s, (8, 16, 34, 220), rect, border_radius=22)
    draw_neon_rect(s, rect, CYAN, 5, 22)
    draw_text(s, label.upper(), 44 if len(label) < 10 else 34, WHITE, rect.center)
    pygame.draw.line(s, PURPLE, (108, 324), (404, 324), 5)
    return s


def make_collectible(kind: str) -> pygame.Surface:
    s = surf((128, 128))
    if kind == "logic_coin":
        pygame.draw.circle(s, YELLOW, (64, 64), 46)
        pygame.draw.circle(s, (90, 65, 0), (64, 64), 34)
        pygame.draw.line(s, WHITE, (43, 82), (64, 38), 7)
        pygame.draw.line(s, WHITE, (85, 82), (64, 38), 7)
    elif kind == "knowledge_crystal":
        points = [(64, 8), (102, 52), (84, 112), (28, 112), (10, 52)]
        pygame.draw.polygon(s, CYAN, points)
        pygame.draw.polygon(s, WHITE, points, 3)
    else:
        pygame.draw.circle(s, (*PURPLE, 75), (64, 64), 54)
        pygame.draw.circle(s, PURPLE, (64, 64), 34, 5)
        pygame.draw.circle(s, WHITE, (64, 64), 12)
    return s


def make_player(frame: str) -> pygame.Surface:
    s = surf((512, 512))
    body_y = 166
    if frame == "jump":
        body_y = 124
    elif frame == "slide":
        body_y = 248
    elif frame == "hit":
        body_y = 178
    run_offset = 0
    if frame.startswith("run_"):
        run_offset = int(math.sin(int(frame[-2:]) * math.pi / 3) * 22)
    body = pygame.Rect(190, body_y, 132, 228 if frame != "slide" else 104)
    color = RED if frame == "hit" else CYAN
    pygame.draw.ellipse(s, (*color, 70), body.inflate(62, 54), 4)
    pygame.draw.rect(s, color, body, border_radius=44)
    pygame.draw.rect(s, (8, 16, 34), body.inflate(-28, -34), border_radius=30)
    pygame.draw.rect(s, PURPLE, (210, body.y + 28, 92, 32), border_radius=16)
    backpack = pygame.Rect(168, body.y + 48, 52, 126 if frame != "slide" else 64)
    pygame.draw.rect(s, (28, 34, 58), backpack, border_radius=22)
    pygame.draw.line(s, WHITE, (216, body.bottom - 18), (178, body.bottom + 64 + run_offset), 10)
    pygame.draw.line(s, WHITE, (296, body.bottom - 18), (334, body.bottom + 64 - run_offset), 10)
    pygame.draw.line(s, color, (202, body.y + 92), (144, body.y + 138 - run_offset), 9)
    pygame.draw.line(s, color, (310, body.y + 92), (368, body.y + 138 + run_offset), 9)
    draw_text(s, "LR", 34, WHITE, body.center)
    return s


def make_particle(color: tuple[int, int, int]) -> pygame.Surface:
    s = surf((128, 128))
    for radius, alpha in [(58, 25), (40, 55), (24, 120), (10, 255)]:
        pygame.draw.circle(s, (*color, alpha), (64, 64), radius)
    return s


def make_effect(name: str) -> pygame.Surface:
    s = surf((512, 512))
    if name == "speed_line":
        pygame.draw.line(s, (*CYAN, 230), (256, 20), (256, 492), 10)
        pygame.draw.line(s, (*CYAN, 70), (236, 20), (236, 492), 3)
        pygame.draw.line(s, (*CYAN, 70), (276, 20), (276, 492), 3)
    elif name == "jump_trail":
        for i in range(9):
            pygame.draw.circle(s, (*CYAN, 160 - i * 14), (256, 420 - i * 42), 42 - i * 3)
    elif name == "glow_circle":
        for radius in range(230, 20, -28):
            pygame.draw.circle(s, (*PURPLE, max(10, 110 - radius // 3)), (256, 256), radius, 5)
    elif name == "impact_flash":
        for angle in range(0, 360, 20):
            end = (256 + int(math.cos(math.radians(angle)) * 220), 256 + int(math.sin(math.radians(angle)) * 220))
            pygame.draw.line(s, (*YELLOW, 220), (256, 256), end, 8)
    else:
        for y in range(40, 472, 34):
            color = random.choice([CYAN, PURPLE, RED, GREEN])
            pygame.draw.rect(s, (*color, 160), (random.randint(20, 120), y, random.randint(160, 420), 8))
    return s


def generate() -> None:
    ensure_dirs()
    for i in range(5):
        save(make_floor(i), "floor", f"floor_tile_{i + 1:02}.png")
    for side in ["left", "right"]:
        for i in range(3):
            save(make_wall(side, i), "walls", f"wall_{side}_{i + 1:02}.png")
    for i in range(3):
        save(make_ceiling(i), "ceiling", f"ceiling_{i + 1:02}.png")
    save(make_gate("V", GREEN), "gates", "gate_true.png")
    save(make_gate("F", RED), "gates", "gate_false.png")
    save(make_gate("?", YELLOW), "gates", "gate_unknown.png")
    for name in ["chair", "desk", "books", "backpack", "trashcan"]:
        save(make_low_obstacle(name), "obstacles", f"{name}_obstacle.png")
    for name in ["locker", "library_cart", "projector", "server_rack", "vending_machine"]:
        save(make_high_obstacle(name), "obstacles", f"{name}_obstacle.png")
    for name in ["bench", "plant", "poster_logic", "poster_math", "poster_ai", "clock", "fire_extinguisher", "window"]:
        save(make_decoration(name), "decorations", f"{name}.png")
    for name, label in [
        ("sign_library", "Biblioteca"),
        ("sign_lab", "Laboratorio"),
        ("sign_auditorium", "Auditorio"),
        ("sign_cafeteria", "Cafeteria"),
        ("sign_exit", "Saida"),
    ]:
        save(make_sign(label), "signs", f"{name}.png")
    for name in ["logic_coin", "knowledge_crystal", "energy_orb"]:
        save(make_collectible(name), "collectibles", f"{name}.png")
    save(make_player("idle"), "player", "runner_idle.png")
    for i in range(1, 7):
        save(make_player(f"run_{i:02}"), "player", f"runner_run_{i:02}.png")
    for name in ["jump", "slide", "hit"]:
        save(make_player(name), "player", f"runner_{name}.png")
    for name, color in [
        ("particle_green", GREEN),
        ("particle_red", RED),
        ("particle_yellow", YELLOW),
        ("particle_cyan", CYAN),
        ("particle_purple", PURPLE),
    ]:
        save(make_particle(color), "effects", f"{name}.png")
    for name in ["speed_line", "jump_trail", "glow_circle", "impact_flash", "screen_glitch"]:
        save(make_effect(name), "effects", f"{name}.png")


if __name__ == "__main__":
    os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
    pygame.init()
    pygame.font.init()
    random.seed(42)
    generate()
    pygame.quit()
    print(f"Generated assets in {ROOT}")
