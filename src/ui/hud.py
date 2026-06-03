import pygame

from src import config
from src.core.utils import draw_text


class Hud:
    def draw(self, surface: pygame.Surface, fonts: dict, game: object) -> None:
        panel = pygame.Rect(28, 20, config.SCREEN_WIDTH - 56, 118)
        pygame.draw.rect(surface, (8, 14, 32), panel, border_radius=8)
        pygame.draw.rect(surface, config.CYAN, panel, 2, border_radius=8)
        phase = game.phase_manager.current_phase
        score = game.score_manager.score
        lives = "♥" * game.lives
        top = f"Fase {phase}: {game.phase_manager.config['name']}    Score: {score}    Vidas: {lives}"
        draw_text(surface, top, fonts["small"], config.WHITE, topleft=(48, 34), max_width=config.SCREEN_WIDTH - 110)
        combo = f"Combo: x{game.score_manager.current_combo}"
        progress = game.phase_manager.phase_correct_count / game.phase_manager.required_correct_count
        draw_text(surface, combo, fonts["small"], config.CYAN, topleft=(48, 64))
        bar = pygame.Rect(240, 67, 400, 16)
        pygame.draw.rect(surface, (22, 30, 55), bar, border_radius=8)
        pygame.draw.rect(surface, config.GREEN, (bar.x, bar.y, int(bar.w * progress), bar.h), border_radius=8)
        pygame.draw.rect(surface, config.WHITE, bar, 1, border_radius=8)
        speed_rect = pygame.Rect(710, 67, 190, 16)
        pygame.draw.rect(surface, (22, 30, 55), speed_rect, border_radius=8)
        pygame.draw.rect(surface, config.PURPLE, (speed_rect.x, speed_rect.y, int(speed_rect.w * game.speed_ratio), speed_rect.h), border_radius=8)
        pygame.draw.rect(surface, config.WHITE, speed_rect, 1, border_radius=8)
        draw_text(surface, "VEL", fonts["tiny"], config.MUTED, topleft=(910, 65))
        draw_text(surface, game.current_challenge["question"], fonts["medium"], config.WHITE, topleft=(48, 94), max_width=config.SCREEN_WIDTH - 110)
