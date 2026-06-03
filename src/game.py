import math
import random

import pygame

from src import config
from src.core import states
from src.core.camera import RunnerCamera
from src.core.projection import Projection
from src.core.utils import draw_text, pulse
from src.entities.door import ANSWER_STYLES, Door, classify_answer
from src.entities.particle import Particle
from src.entities.player import Player
from src.entities.powerup import POWERUPS
from src.managers.audio_manager import AudioManager
from src.managers.challenge_manager import ChallengeManager
from src.managers.chunk_manager import ChunkManager
from src.managers.phase_manager import PhaseManager
from src.managers.save_manager import SaveManager
from src.managers.score_manager import ScoreManager
from src.managers.spawn_manager import RunnerSpawnManager
from src.core.floor_renderer import ScanlineFloorRenderer
from src.ui.button import Button
from src.ui.hud import Hud


class Game:
    def __init__(self) -> None:
        pygame.init()
        pygame.display.set_caption("Logic Runner")
        self.screen = pygame.display.set_mode((config.SCREEN_WIDTH, config.SCREEN_HEIGHT))
        self.clock = pygame.time.Clock()
        self.running = True
        self.state = states.SPLASH

        raw_cover = pygame.image.load("assets/capa.png").convert()
        self._cover = pygame.transform.smoothscale(raw_cover, (config.SCREEN_WIDTH, config.SCREEN_HEIGHT))
        self._floor_renderer = ScanlineFloorRenderer(config.SCREEN_WIDTH, config.SCREEN_HEIGHT, config.HORIZON_Y)


        self.fonts = {
            "title": pygame.font.SysFont("consolas", 66, bold=True),
            "large": pygame.font.SysFont("consolas", 38, bold=True),
            "medium": pygame.font.SysFont("consolas", 24, bold=True),
            "small": pygame.font.SysFont("consolas", 18),
            "tiny": pygame.font.SysFont("consolas", 15),
        }

        self.save_manager = SaveManager()
        self.phase_manager = PhaseManager(self.save_manager.data["max_unlocked_phase"])
        self.challenge_manager = ChallengeManager()
        self.chunk_manager = ChunkManager()
        self.spawn_manager = RunnerSpawnManager()
        self.score_manager = ScoreManager()
        self.audio = AudioManager()
        self.camera = RunnerCamera()
        self.projection = Projection(self.camera)
        self.player = Player()
        self.hud = Hud()

        self.lives = config.MAX_LIVES
        self.current_challenge = self.challenge_manager.next_challenge(1)
        self.doors: list[Door] = []
        self.obstacles = []
        self.powerups = []
        self.collectibles = []
        self.active_powerups: dict[str, float] = {}
        self.particles: list[Particle] = []
        self.speed_lines: list[tuple[float, float, float, float]] = []
        self.chunk_manager.reset()

        self.menu_index = 0
        self.phase_index = 0
        self.pause_index = 0
        self.settings_index = 0
        self.confirm_reset = False

        self.feedback_timer = 0.0
        self.feedback_title = ""
        self.feedback_correct = ""
        self.feedback_explanation = ""
        self.last_question = ""
        self.last_correct = ""
        self.flash_timer = 0.0
        self.track_offset = 0.0
        self.distance = 0.0
        self.combo_pop_timer = 0.0
        self.answer_flash_timer = 0.0
        self.correct_lane: int | None = None

    @property
    def run_speed(self) -> float:
        phase_speed = self.phase_manager.speed
        distance_boost = min(110, self.distance * 0.018)
        base = config.BASE_RUN_SPEED + phase_speed * 32 + distance_boost
        if "boost" in self.active_powerups:
            base *= 1.22
        if "slowmo" in self.active_powerups:
            base *= 0.68
        return min(config.MAX_RUN_SPEED, base)

    @property
    def speed_ratio(self) -> float:
        return min(1.0, self.run_speed / config.MAX_RUN_SPEED)

    @property
    def score_multiplier(self) -> int:
        return 2 if "multiplier" in self.active_powerups else 1

    @property
    def world_speed(self) -> float:
        return self.run_speed / 20.0

    def run(self) -> None:
        while self.running:
            dt = self.clock.tick(config.FPS) / 1000
            self.handle_events()
            self.update(dt)
            self.draw()
        pygame.quit()

    def handle_events(self) -> None:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                self.handle_key(event.key)

    def handle_key(self, key: int) -> None:
        if self.state == states.SPLASH:
            if key in (pygame.K_RETURN, pygame.K_SPACE):
                self.state = states.MAIN_MENU
        elif self.state == states.MAIN_MENU:
            self.handle_vertical_menu(key, 5)
            if key in (pygame.K_RETURN, pygame.K_SPACE):
                self.activate_main_menu()
        elif self.state == states.PHASE_SELECT:
            self.handle_phase_select(key)
        elif self.state == states.HOW_TO_PLAY:
            if key in (pygame.K_ESCAPE, pygame.K_RETURN, pygame.K_SPACE):
                self.state = states.MAIN_MENU
        elif self.state == states.SETTINGS:
            self.handle_settings(key)
        elif self.state == states.PLAYING:
            if key in (pygame.K_LEFT, pygame.K_a):
                self.player.move_left()
            elif key in (pygame.K_RIGHT, pygame.K_d):
                self.player.move_right()
            elif key in (pygame.K_SPACE, pygame.K_w, pygame.K_UP):
                if self.player.jump():
                    self.camera.add_shake(2.0)
            elif key in (pygame.K_s, pygame.K_DOWN, pygame.K_LCTRL, pygame.K_RCTRL):
                if self.player.slide():
                    self.spawn_slide_particles()
            elif key in (pygame.K_p, pygame.K_ESCAPE):
                self.state = states.PAUSED
        elif self.state == states.PAUSED:
            self.handle_vertical_menu(key, 4, attr="pause_index")
            if key in (pygame.K_RETURN, pygame.K_SPACE):
                self.activate_pause_menu()
            elif key == pygame.K_ESCAPE:
                self.state = states.PLAYING
        elif self.state == states.FEEDBACK:
            if key == pygame.K_SPACE:
                self.next_round()
        elif self.state == states.PHASE_COMPLETE:
            if key in (pygame.K_RETURN, pygame.K_SPACE):
                self.start_phase(self.phase_manager.current_phase + 1, keep_score=True)
            elif key == pygame.K_ESCAPE:
                self.state = states.MAIN_MENU
        elif self.state in (states.GAME_OVER, states.VICTORY):
            if key in (pygame.K_RETURN, pygame.K_SPACE):
                self.start_run(1)
            elif key == pygame.K_ESCAPE:
                self.state = states.MAIN_MENU

    def handle_vertical_menu(self, key: int, count: int, attr: str = "menu_index") -> None:
        index = getattr(self, attr)
        if key in (pygame.K_UP, pygame.K_w):
            setattr(self, attr, (index - 1) % count)
        elif key in (pygame.K_DOWN, pygame.K_s):
            setattr(self, attr, (index + 1) % count)

    def activate_main_menu(self) -> None:
        if self.menu_index == 0:
            self.start_run(1)
        elif self.menu_index == 1:
            self.state = states.PHASE_SELECT
        elif self.menu_index == 2:
            self.state = states.HOW_TO_PLAY
        elif self.menu_index == 3:
            self.state = states.SETTINGS
        elif self.menu_index == 4:
            self.running = False

    def handle_phase_select(self, key: int) -> None:
        if key == pygame.K_ESCAPE:
            self.state = states.MAIN_MENU
        elif key in (pygame.K_LEFT, pygame.K_a):
            self.phase_index = max(0, self.phase_index - 1)
        elif key in (pygame.K_RIGHT, pygame.K_d):
            self.phase_index = min(9, self.phase_index + 1)
        elif key in (pygame.K_UP, pygame.K_w):
            self.phase_index = max(0, self.phase_index - 2)
        elif key in (pygame.K_DOWN, pygame.K_s):
            self.phase_index = min(9, self.phase_index + 2)
        elif key in (pygame.K_RETURN, pygame.K_SPACE):
            phase = self.phase_index + 1
            if phase <= self.phase_manager.unlocked_phase:
                self.start_run(phase)

    def handle_settings(self, key: int) -> None:
        settings = self.save_manager.data["settings"]
        if key == pygame.K_ESCAPE:
            self.confirm_reset = False
            self.state = states.MAIN_MENU
        elif key in (pygame.K_UP, pygame.K_w):
            self.settings_index = (self.settings_index - 1) % 4
        elif key in (pygame.K_DOWN, pygame.K_s):
            self.settings_index = (self.settings_index + 1) % 4
        elif key in (pygame.K_LEFT, pygame.K_a, pygame.K_RIGHT, pygame.K_d):
            delta = 0.1 if key in (pygame.K_RIGHT, pygame.K_d) else -0.1
            if self.settings_index == 0:
                settings["music_volume"] = round(max(0, min(1, settings["music_volume"] + delta)), 1)
            elif self.settings_index == 1:
                settings["sfx_volume"] = round(max(0, min(1, settings["sfx_volume"] + delta)), 1)
            elif self.settings_index == 2:
                settings["fullscreen"] = not settings["fullscreen"]
            self.save_manager.save()
        elif key in (pygame.K_RETURN, pygame.K_SPACE):
            if self.settings_index == 2:
                settings["fullscreen"] = not settings["fullscreen"]
                self.save_manager.save()
            elif self.settings_index == 3:
                if self.confirm_reset:
                    self.save_manager.reset_progress()
                    self.phase_manager.unlocked_phase = 1
                    self.confirm_reset = False
                else:
                    self.confirm_reset = True

    def start_run(self, phase: int) -> None:
        self.score_manager.reset()
        self.lives = config.MAX_LIVES
        self.distance = 0.0
        self.active_powerups.clear()
        self.start_phase(phase, keep_score=True)

    def start_phase(self, phase: int, keep_score: bool = True) -> None:
        if not keep_score:
            self.score_manager.reset()
        self.phase_manager.start_phase(phase)
        self.player.reset()
        self.camera.reset()
        self.spawn_manager.reset()
        self.chunk_manager.reset()
        self.obstacles = []
        self.powerups = []
        self.collectibles = []
        self.particles = []
        self.next_round()
        self.state = states.PLAYING

    def next_round(self) -> None:
        self.current_challenge = self.challenge_manager.next_challenge(self.phase_manager.current_phase)
        speed = self.world_speed
        options = self.current_challenge["options"]
        correct_answer = self.current_challenge["correct_answer"]
        try:
            self.correct_lane = options.index(correct_answer)
        except ValueError:
            self.correct_lane = None

        # Remove obstacles that would block the path to the correct door
        if self.correct_lane is not None:
            self.obstacles = [
                obs for obs in self.obstacles
                if not (obs.lane == self.correct_lane and obs.z < config.ANSWER_GATE_Z + 12)
            ]

        self.doors = [
            Door(index, option, option == correct_answer, speed)
            for index, option in enumerate(options)
        ]
        self.answer_flash_timer = 1.25
        self.feedback_timer = 0
        self.state = states.PLAYING

    def update(self, dt: float) -> None:
        self.update_effect_timers(dt)
        self.particles = [particle for particle in self.particles if particle.update()]

        if self.state == states.PLAYING:
            self.distance += self.world_speed * dt
            self.track_offset = (self.track_offset + self.world_speed * dt) % 12
            self.score_manager.update_survival(dt)
            landed = self.player.update(dt)
            if landed:
                self.camera.add_shake(2.8)
                self.spawn_landing_particles()

            self.camera.update(dt, self.player.x, self.speed_ratio, self.player.lean)
            difficulty = min(1.0, self.distance / 900)
            self.chunk_manager.update(self.world_speed * dt, difficulty)
            biome_key = self.chunk_manager.current_biome_key()
            new_obstacles, new_powerups, new_collectibles = self.spawn_manager.update(
                dt, self.phase_manager.current_phase, self.world_speed, biome_key,
                correct_lane=self.correct_lane if self.doors else None,
            )
            self.obstacles.extend(new_obstacles)
            self.powerups.extend(new_powerups)
            self.collectibles.extend(new_collectibles)
            self.update_world_objects(dt)
        elif self.state == states.FEEDBACK:
            self.feedback_timer -= dt
            if self.feedback_timer <= 0:
                self.next_round()

    def update_effect_timers(self, dt: float) -> None:
        if self.flash_timer > 0:
            self.flash_timer = max(0, self.flash_timer - dt)
        if self.combo_pop_timer > 0:
            self.combo_pop_timer = max(0, self.combo_pop_timer - dt)
        if self.answer_flash_timer > 0:
            self.answer_flash_timer = max(0, self.answer_flash_timer - dt)
        expired = [name for name, timer in self.active_powerups.items() if timer - dt <= 0]
        for name in expired:
            self.active_powerups.pop(name, None)
        for name in list(self.active_powerups):
            self.active_powerups[name] -= dt

    def update_world_objects(self, dt: float) -> None:
        speed_multiplier = 1.0
        for door in self.doors:
            door.speed = self.world_speed
            door.update(dt, speed_multiplier)
            if door.collides_with(self.player):
                self.resolve_door(door)
                return
        self.doors = [door for door in self.doors if not door.is_offscreen()]
        if not self.doors:
            self.next_round()
            return

        for obstacle in self.obstacles:
            obstacle.speed = self.world_speed
            obstacle.update(dt, speed_multiplier)
            if obstacle.collides_with(self.player):
                self.resolve_obstacle_collision(obstacle)
                return
        self.obstacles = [obstacle for obstacle in self.obstacles if not obstacle.is_offscreen()]

        for powerup in self.powerups:
            powerup.speed = self.world_speed
            powerup.update(dt, speed_multiplier)
            if powerup.collides_with(self.player):
                self.collect_powerup(powerup)
        self.powerups = [powerup for powerup in self.powerups if not powerup.is_offscreen() and not powerup.collides_with(self.player)]

        for collectible in self.collectibles:
            collectible.speed = self.world_speed
            collectible.update(dt, speed_multiplier)
            if collectible.collides_with(self.player):
                self.collect_item(collectible)
        self.collectibles = [
            collectible
            for collectible in self.collectibles
            if not collectible.is_offscreen() and not collectible.collides_with(self.player)
        ]

        if random.random() < 0.22 * self.speed_ratio:
            x = random.choice([-3.8, -2.8, 2.8, 3.8])
            y = random.choice([0.08, 1.2, 2.4])
            z = random.uniform(38.0, config.WORLD_FAR_Z)
            length = random.uniform(5.0, 12.0)
            self.speed_lines.append((x, y, z, length))
        self.speed_lines = [
            (x, y, z - self.world_speed * dt * 1.9, length)
            for x, y, z, length in self.speed_lines
            if z > config.TRACK_NEAR_Z
        ]

    def resolve_door(self, door: Door) -> None:
        self.last_question = self.current_challenge["question"]
        self.last_correct = self.current_challenge["correct_answer"]
        color = config.GREEN if door.is_correct else config.RED
        px, py, _ = self.projection.project(door.x, 0.8, max(door.z, config.WORLD_NEAR_Z))
        self.particles.extend(Particle(px, py, color) for _ in range(36))
        self.doors = []
        if door.is_correct:
            self.score_manager.correct(self.score_multiplier)
            self.combo_pop_timer = 0.55
            self.camera.add_shake(1.8)
            if self.phase_manager.register_correct():
                self.complete_phase()
            else:
                self.next_round()
        else:
            self.apply_damage(show_feedback=True)

    def resolve_obstacle_collision(self, obstacle: object) -> None:
        self.obstacles.remove(obstacle)
        if "shield" in self.active_powerups:
            self.active_powerups.pop("shield", None)
            self.camera.add_shake(6.0)
            px, py, _ = self.projection.project(obstacle.x, 0.8, max(obstacle.z, config.WORLD_NEAR_Z))
            self.particles.extend(Particle(px, py, config.GREEN) for _ in range(42))
            return
        self.apply_damage(show_feedback=False)

    def apply_damage(self, show_feedback: bool) -> None:
        self.score_manager.wrong()
        self.lives -= 1
        self.flash_timer = 0.42
        self.camera.add_shake(11.0)
        self.player.stumble()
        if self.lives <= 0:
            self.save_manager.record_run(self.score_manager.score, self.phase_manager.unlocked_phase)
            self.state = states.GAME_OVER
            return
        if show_feedback:
            self.feedback_title = "Resposta incorreta!"
            self.feedback_correct = self.current_challenge["correct_answer"]
            self.feedback_explanation = self.current_challenge["explanation"]
            self.feedback_timer = 2.6
            self.state = states.FEEDBACK

    def collect_powerup(self, powerup: object) -> None:
        self.active_powerups[powerup.kind] = POWERUPS[powerup.kind]["duration"]
        self.score_manager.score += 75
        self.camera.add_shake(3.0)
        px, py, _ = self.projection.project(powerup.x, 1.0, max(powerup.z, config.WORLD_NEAR_Z))
        self.particles.extend(Particle(px, py, powerup.data["color"]) for _ in range(28))

    def collect_item(self, collectible: object) -> None:
        self.score_manager.score += collectible.data["points"] * self.score_multiplier
        px, py, _ = self.projection.project(collectible.x, 1.0, max(collectible.z, config.WORLD_NEAR_Z))
        self.particles.extend(Particle(px, py, collectible.data["color"]) for _ in range(14))

    def complete_phase(self) -> None:
        phase = self.phase_manager.current_phase
        self.score_manager.phase_bonus()
        if phase == 10:
            self.score_manager.final_bonus()
        self.phase_manager.complete_current()
        self.lives = min(config.MAX_LIVES, self.lives + 1)
        self.save_manager.record_run(self.score_manager.score, self.phase_manager.unlocked_phase, phase)
        self.state = states.PHASE_COMPLETE if phase < 10 else states.VICTORY

    def activate_pause_menu(self) -> None:
        if self.pause_index == 0:
            self.state = states.PLAYING
        elif self.pause_index == 1:
            self.start_phase(self.phase_manager.current_phase, keep_score=True)
        elif self.pause_index == 2:
            self.state = states.MAIN_MENU
        elif self.pause_index == 3:
            self.running = False

    def spawn_landing_particles(self) -> None:
        for _ in range(18):
            px, py, _ = self.projection.project(self.player.x, 0, config.PLAYER_RENDER_Z)
            self.particles.append(Particle(px + random.randint(-22, 22), py, config.CYAN))

    def spawn_slide_particles(self) -> None:
        for _ in range(10):
            px, py, _ = self.projection.project(self.player.x, 0, config.PLAYER_RENDER_Z)
            self.particles.append(Particle(px + random.randint(-26, 26), py, config.PURPLE))

    def draw(self) -> None:
        if self.state in (states.SPLASH, states.MAIN_MENU):
            self.screen.blit(self._cover, (0, 0))
        else:
            self.draw_background()
        if self.state == states.SPLASH:
            self.draw_splash()
        elif self.state == states.MAIN_MENU:
            self.draw_main_menu()
        elif self.state == states.PHASE_SELECT:
            self.draw_phase_select()
        elif self.state == states.HOW_TO_PLAY:
            self.draw_how_to_play()
        elif self.state == states.SETTINGS:
            self.draw_settings()
        elif self.state in (states.PLAYING, states.PAUSED, states.FEEDBACK):
            self.draw_playing()
            if self.state == states.PAUSED:
                self.draw_pause()
            elif self.state == states.FEEDBACK:
                self.draw_feedback()
        elif self.state == states.PHASE_COMPLETE:
            self.draw_phase_complete()
        elif self.state == states.GAME_OVER:
            self.draw_end_screen("GAME OVER", config.RED)
        elif self.state == states.VICTORY:
            self.draw_end_screen("VOCE CONCLUIU O LOGIC RUNNER!", config.GREEN)

        if self.flash_timer > 0:
            overlay = pygame.Surface((config.SCREEN_WIDTH, config.SCREEN_HEIGHT), pygame.SRCALPHA)
            overlay.fill((255, 20, 60, int(120 * min(1, self.flash_timer / 0.42))))
            self.screen.blit(overlay, (0, 0))
        pygame.display.flip()

    def draw_background(self) -> None:
        self.screen.fill((8, 10, 16))
        self._floor_renderer.draw(self.screen, self.track_offset)

        projection = self.projection
        for x, y, z, length in self.speed_lines:
            start = projection.project(x, y, z)[0:2]
            end = projection.project(x, y, max(config.TRACK_NEAR_Z, z - length))[0:2]
            pygame.draw.line(self.screen, (60, 210, 255), start, end, 2)

        if self.speed_ratio > 0.74:
            overlay = pygame.Surface((config.SCREEN_WIDTH, config.SCREEN_HEIGHT), pygame.SRCALPHA)
            alpha = int((self.speed_ratio - 0.74) * 110)
            pygame.draw.rect(overlay, (0, 220, 255, alpha), (0, 0, 16, config.SCREEN_HEIGHT))
            pygame.draw.rect(overlay, (0, 220, 255, alpha), (config.SCREEN_WIDTH - 16, 0, 16, config.SCREEN_HEIGHT))
            self.screen.blit(overlay, (0, 0))

    def draw_title(self, subtitle: str | None = None) -> None:
        cx = config.SCREEN_WIDTH // 2
        glow = pulse(80, 180, 0.004, pygame.time.get_ticks())
        title = self.fonts["title"].render("LOGIC RUNNER", True, config.CYAN)
        shadow = self.fonts["title"].render("LOGIC RUNNER", True, config.PURPLE)
        self.screen.blit(shadow, shadow.get_rect(center=(cx + 4, 104)))
        self.screen.blit(title, title.get_rect(center=(cx, 100)))
        if subtitle:
            surf = self.fonts["medium"].render(subtitle, True, config.WHITE)
            surf.set_alpha(glow)
            self.screen.blit(surf, surf.get_rect(center=(cx, 158)))

    def draw_splash(self) -> None:
        glow = pulse(140, 255, 0.004, pygame.time.get_ticks())
        hint = self.fonts["medium"].render("Pressione ENTER para continuar", True, config.WHITE)
        hint.set_alpha(glow)
        self.screen.blit(hint, hint.get_rect(center=(config.SCREEN_WIDTH // 2, 662)))

    def draw_main_menu(self) -> None:
        overlay = pygame.Surface((config.SCREEN_WIDTH, 340), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 172))
        self.screen.blit(overlay, (0, config.SCREEN_HEIGHT - 340))
        labels = ["INICIAR JOGO", "SELECIONAR FASE", "COMO JOGAR", "CONFIGURACOES", "SAIR"]
        self.draw_button_list(labels, self.menu_index, 382)
        info = f"Melhor pontuacao: {self.save_manager.data['high_score']}   Fase maxima: {self.phase_manager.unlocked_phase}"
        draw_text(self.screen, info, self.fonts["small"], config.MUTED, center=(config.SCREEN_WIDTH // 2, 668))

    def draw_button_list(self, labels: list[str], selected: int, start_y: int) -> None:
        cx = config.SCREEN_WIDTH // 2
        for index, label in enumerate(labels):
            rect = pygame.Rect(cx - 170, start_y + index * 58, 340, 42)
            Button(rect, label).draw(self.screen, self.fonts["small"], selected == index)

    def draw_phase_select(self) -> None:
        from src.data.phases import PHASES

        cx = config.SCREEN_WIDTH // 2
        draw_text(self.screen, "SELECIONE A FASE", self.fonts["large"], config.CYAN, center=(cx, 90))
        completed = set(self.save_manager.data["completed_phases"])
        for index in range(10):
            phase = index + 1
            col = index % 2
            row = index // 2
            rect = pygame.Rect(cx - 330 + col * 390, 155 + row * 78, 320, 52)
            locked = phase > self.phase_manager.unlocked_phase
            done = phase in completed
            text = f"{phase}. {PHASES[phase]['name']}"
            if locked:
                text = f"{phase}. BLOQUEADA"
            elif done:
                text = f"{text} OK"
            Button(rect, text).draw(self.screen, self.fonts["tiny"], self.phase_index == index, locked)
        draw_text(self.screen, "Setas para navegar, ENTER para jogar, ESC para voltar", self.fonts["small"], config.MUTED, center=(cx, 610))

    def draw_how_to_play(self) -> None:
        cx = config.SCREEN_WIDTH // 2
        draw_text(self.screen, "COMO JOGAR", self.fonts["large"], config.CYAN, center=(cx, 82))
        lines = [
            "A/D ou esquerda/direita trocam de faixa com movimento suave.",
            "SPACE, W ou seta para cima fazem o personagem pular.",
            "S, CTRL ou seta para baixo ativam slide/agachar.",
            "Pule caixas e cones pulando ou desviando. Desvie de bloqueios.",
            "Desvie de bloqueios laterais trocando de faixa.",
            "Ao mesmo tempo, escolha a porta com a resposta logica correta.",
            "Powerups: boost, slow motion, escudo e multiplicador.",
        ]
        for index, line in enumerate(lines):
            draw_text(self.screen, line, self.fonts["medium"], config.WHITE, center=(cx, 165 + index * 48), max_width=1100)
        draw_text(self.screen, "ENTER ou ESC para voltar", self.fonts["small"], config.MUTED, center=(cx, 610))

    def draw_settings(self) -> None:
        settings = self.save_manager.data["settings"]
        cx = config.SCREEN_WIDTH // 2
        draw_text(self.screen, "CONFIGURACOES", self.fonts["large"], config.CYAN, center=(cx, 90))
        labels = [
            f"Volume musica: {settings['music_volume']:.1f}",
            f"Volume efeitos: {settings['sfx_volume']:.1f}",
            f"Tela cheia: {'Ligada' if settings['fullscreen'] else 'Desligada'}",
            "Confirmar reset" if self.confirm_reset else "Resetar progresso",
        ]
        self.draw_button_list(labels, self.settings_index, 210)
        draw_text(self.screen, "Use esquerda/direita para ajustar. ESC volta.", self.fonts["small"], config.MUTED, center=(cx, 570))

    def draw_playing(self) -> None:
        draw_order = []
        draw_order.extend((door.z, door) for door in self.doors)
        draw_order.extend((obstacle.z, obstacle) for obstacle in self.obstacles)
        draw_order.extend((powerup.z, powerup) for powerup in self.powerups)
        draw_order.extend((collectible.z, collectible) for collectible in self.collectibles)
        for _, entity in sorted(draw_order, key=lambda item: item[0], reverse=True):
            entity.draw(self.screen, self.fonts["small"], self.projection)
        self.player.draw(self.screen, self.fonts["small"], self.projection)
        for particle in self.particles:
            particle.draw(self.screen)
        self.draw_powerup_ui()
        self.draw_answer_flash()
        if self.combo_pop_timer > 0:
            scale = 1 + self.combo_pop_timer
            draw_text(self.screen, f"COMBO x{self.score_manager.current_combo}", self.fonts["medium"], config.GREEN, center=(config.SCREEN_WIDTH // 2, int(162 - 10 * scale)))
        self.hud.draw(self.screen, self.fonts, self)

    def draw_answer_flash(self) -> None:
        if self.answer_flash_timer <= 0:
            return
        alpha = int(210 * min(1, self.answer_flash_timer / 0.55))
        seen = []
        for option in self.current_challenge["options"]:
            kind = classify_answer(option)
            if kind not in seen:
                seen.append(kind)
        total_width = len(seen) * 122
        start_x = config.SCREEN_WIDTH // 2 - total_width // 2
        overlay = pygame.Surface((config.SCREEN_WIDTH, config.SCREEN_HEIGHT), pygame.SRCALPHA)
        for index, kind in enumerate(seen):
            style = ANSWER_STYLES[kind]
            rect = pygame.Rect(start_x + index * 122, 145, 108, 34)
            color = style["color"]
            pygame.draw.rect(overlay, (*style["dark"], alpha), rect, border_radius=8)
            pygame.draw.rect(overlay, (*color, alpha), rect, 2, border_radius=8)
            symbol_font = pygame.font.SysFont("consolas", 24, bold=True)
            symbol = symbol_font.render(style["symbol"], True, config.WHITE)
            symbol.set_alpha(alpha)
            overlay.blit(symbol, symbol.get_rect(center=(rect.x + 23, rect.centery)))
            label = self.fonts["tiny"].render(style["label"], True, config.WHITE)
            label.set_alpha(alpha)
            overlay.blit(label, label.get_rect(midleft=(rect.x + 42, rect.centery)))
        self.screen.blit(overlay, (0, 0))

    def draw_powerup_ui(self) -> None:
        x = config.SCREEN_WIDTH - 210
        y = 146
        for name, timer in self.active_powerups.items():
            data = POWERUPS[name]
            rect = pygame.Rect(x, y, 190, 24)
            pygame.draw.rect(self.screen, (9, 15, 34), rect, border_radius=6)
            pygame.draw.rect(self.screen, data["color"], rect, 1, border_radius=6)
            fill = rect.inflate(-4, -8)
            fill.w = int((rect.w - 4) * (timer / data["duration"]))
            pygame.draw.rect(self.screen, data["color"], fill, border_radius=4)
            draw_text(self.screen, data["label"], self.fonts["tiny"], config.WHITE, center=rect.center, max_width=180)
            y += 30

    def draw_pause(self) -> None:
        self.draw_modal("JOGO PAUSADO")
        cx = config.SCREEN_WIDTH // 2
        labels = ["CONTINUAR", "REINICIAR FASE", "VOLTAR AO MENU", "SAIR"]
        for index, label in enumerate(labels):
            rect = pygame.Rect(cx - 150, 265 + index * 55, 300, 40)
            Button(rect, label).draw(self.screen, self.fonts["small"], self.pause_index == index)

    def draw_feedback(self) -> None:
        self.draw_modal(self.feedback_title)
        cx = config.SCREEN_WIDTH // 2
        draw_text(self.screen, f"Resposta correta: {self.feedback_correct}", self.fonts["medium"], config.GREEN, center=(cx, 310), max_width=850)
        draw_text(self.screen, self.feedback_explanation, self.fonts["small"], config.WHITE, center=(cx, 380), max_width=900)
        draw_text(self.screen, "ESPACO para continuar", self.fonts["tiny"], config.MUTED, center=(cx, 470))

    def draw_phase_complete(self) -> None:
        self.draw_modal("FASE CONCLUIDA!")
        phase = self.phase_manager.current_phase
        lines = [
            f"Fase {phase}: {self.phase_manager.config['name']}",
            f"Pontuacao atual: {self.score_manager.score}",
            f"Acertos na fase: {self.phase_manager.phase_correct_count}",
            f"Erros totais: {self.score_manager.wrong_answers}",
            f"Maior combo: {self.score_manager.max_combo}",
            "ENTER para proxima fase ou ESC para menu",
        ]
        cx = config.SCREEN_WIDTH // 2
        for index, line in enumerate(lines):
            draw_text(self.screen, line, self.fonts["small"], config.WHITE if index < 5 else config.MUTED, center=(cx, 255 + index * 38), max_width=900)

    def draw_end_screen(self, title: str, color: tuple[int, int, int]) -> None:
        self.draw_modal(title, color)
        lines = [
            f"Pontuacao final: {self.score_manager.score}",
            f"Fase alcancada: {self.phase_manager.current_phase}",
            f"Portas corretas: {self.score_manager.correct_answers}",
            f"Erros: {self.score_manager.wrong_answers}",
            f"Maior combo: {self.score_manager.max_combo}",
        ]
        if self.state == states.GAME_OVER and self.last_question:
            lines.extend([f"Ultima questao: {self.last_question}", f"Resposta correta: {self.last_correct}"])
        elif self.state == states.VICTORY:
            lines.append("Voce dominou os principais conceitos de logica proposicional.")
        lines.append("ENTER para jogar novamente ou ESC para menu")
        cx = config.SCREEN_WIDTH // 2
        for index, line in enumerate(lines):
            draw_text(self.screen, line, self.fonts["small"], config.WHITE if index < len(lines) - 1 else config.MUTED, center=(cx, 230 + index * 38), max_width=960)

    def draw_modal(self, title: str, color: tuple[int, int, int] = config.CYAN) -> None:
        overlay = pygame.Surface((config.SCREEN_WIDTH, config.SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 145))
        self.screen.blit(overlay, (0, 0))
        cx = config.SCREEN_WIDTH // 2
        rect = pygame.Rect(cx - 440, 155, 880, 390)
        pygame.draw.rect(self.screen, (10, 14, 32), rect, border_radius=8)
        pygame.draw.rect(self.screen, color, rect, 3, border_radius=8)
        draw_text(self.screen, title, self.fonts["large"], color, center=(cx, 205), max_width=820)
