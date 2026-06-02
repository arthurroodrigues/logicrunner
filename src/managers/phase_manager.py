from src.data.phases import PHASES


class PhaseManager:
    def __init__(self, unlocked_phase: int = 1) -> None:
        self.current_phase = 1
        self.unlocked_phase = max(1, min(10, unlocked_phase))
        self.phase_correct_count = 0

    @property
    def config(self) -> dict:
        return PHASES[self.current_phase]

    @property
    def required_correct_count(self) -> int:
        return self.config["required_correct"]

    @property
    def speed(self) -> float:
        return self.config["speed"]

    def start_phase(self, phase: int) -> None:
        self.current_phase = max(1, min(10, phase))
        self.phase_correct_count = 0

    def register_correct(self) -> bool:
        self.phase_correct_count += 1
        return self.phase_correct_count >= self.required_correct_count

    def complete_current(self) -> None:
        self.unlocked_phase = max(self.unlocked_phase, min(10, self.current_phase + 1))
