from typing import Sequence

from fuzzer.utils.power_schedule import PowerSchedule

from fuzzer.utils.seed import Seed


class AFLFastSchedule(PowerSchedule):
    """Exponential power schedule as implemented in AFL"""

    def __init__(self, exponent: float) -> None:
        self.exponent = exponent

    def assignEnergy(self, population: Sequence[Seed]) -> None:
        """Assign exponential energy inversely proportional to path frequency"""
        for seed in population:
            seed.energy = 1 / (self.path_frequency[seed.path_id] ** self.exponent)
