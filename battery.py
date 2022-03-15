from abc import ABC
from dataclasses import dataclass
from random import choice
from typing import Final

CAPACITY_CONST: Final[int] = 24 * 60 * 60
AVERAGE_PER_SECOND_USE = 1
INTERVAL = 15
AVERAGE_PER_INTERVAL_USE = AVERAGE_PER_SECOND_USE * 15


@dataclass
class Battery(ABC):
    per_second_use: int
    level: int
    minimum: float

    def is_full(self):
        return self.level == CAPACITY_CONST

    def level_normalized(self):
        return self.level / CAPACITY_CONST

    def set_level(self, level):
        self.level = level * CAPACITY_CONST

    def charge(self, ratio_of_per_second_use, n_seconds=INTERVAL):
        self.level += ratio_of_per_second_use * self.per_second_use * n_seconds

    def deplete(self, ratio_of_per_second_use, n_seconds=INTERVAL):
        self.level -= ratio_of_per_second_use * self.per_second_use * n_seconds

    def is_empty(self):
        return self.level == 0.0


@dataclass
class NormalBattery(Battery):
    def __init__(self):
        super(NormalBattery, self).__init__(
            AVERAGE_PER_SECOND_USE, 0, choice([0.75, 0.5, 0.25])
        )


@dataclass
class MicrogridBattery(Battery):
    def __init__(self):
        super(MicrogridBattery, self).__init__(
            AVERAGE_PER_SECOND_USE * (1 / 2), 0, 0.5
        )  # lasts twice as long as normal battery


@dataclass
class CriticalMicrogridBattery(Battery):
    def __init__(self):
        super(CriticalMicrogridBattery, self).__init__(
            AVERAGE_PER_SECOND_USE * (1 / 2), 0, 0.75
        )


@dataclass
class CentralUtilityBattery(Battery):
    def __init__(self):
        super(CentralUtilityBattery, self).__init__(
            AVERAGE_PER_SECOND_USE * (1 / 12 * 8000), 0, 0
        )
