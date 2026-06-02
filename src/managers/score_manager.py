class ScoreManager:
    def __init__(self) -> None:
        self.reset()

    def reset(self) -> None:
        self.score = 0
        self.current_combo = 0
        self.max_combo = 0
        self.correct_answers = 0
        self.wrong_answers = 0
        self._survival_accumulator = 0.0

    def update_survival(self, dt: float) -> None:
        self._survival_accumulator += dt
        while self._survival_accumulator >= 1.0:
            self.score += 10
            self._survival_accumulator -= 1.0

    def correct(self, multiplier: int = 1) -> None:
        self.correct_answers += 1
        self.current_combo += 1
        self.max_combo = max(self.max_combo, self.current_combo)
        self.score += 100 * multiplier
        if self.current_combo % 10 == 0:
            self.score += 250 * multiplier
        elif self.current_combo % 5 == 0:
            self.score += 100 * multiplier
        elif self.current_combo % 3 == 0:
            self.score += 50 * multiplier

    def wrong(self) -> None:
        self.wrong_answers += 1
        self.current_combo = 0
        self.score = max(0, self.score - 50)

    def phase_bonus(self) -> None:
        self.score += 300

    def final_bonus(self) -> None:
        self.score += 1000
