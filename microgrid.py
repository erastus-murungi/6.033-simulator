from abc import ABC
from dataclasses import dataclass, field
from enum import Enum

from battery import MicrogridBattery, CriticalMicrogridBattery
from house import House, Building


class UnitType(Enum):
    HOSPITAL = 0
    FIRE_STATION = 1
    POLICE_STATION = 2

    def __repr__(self):
        return self.name


@dataclass
class Critical:
    type: UnitType


class MicrogridType(Enum):
    HOUSES = 1
    BUILDINGS = 2
    CRITICAL = 3

    def __repr__(self):
        return self.name


@dataclass
class LocalLoop:
    flowing: int = 0

    def consume(self, how_much: int):
        self.flowing -= how_much

    def add(self, how_much: int):
        self.flowing += how_much

    def has_extra_power(self):
        return self.flowing > 0


@dataclass
class Microgrid(ABC):
    type: MicrogridType


@dataclass
class HousesMicrogrid(Microgrid):
    houses: tuple[
        House, House, House, House, House, House, House, House, House, House
    ]  # 10 houses

    def __init__(self, houses):
        super(HousesMicrogrid, self).__init__(MicrogridType.HOUSES)
        self.houses = houses
        self.battery = MicrogridBattery()
        self.local_loop = LocalLoop()

    def __repr__(self):
        return f"<{tuple([getattr(house, 'id') for house in self.houses])}>"


@dataclass
class BuildingsMicrogrid(Microgrid):
    buildings: tuple[Building, Building, Building] = field(
        default_factory=lambda: (Building(), Building(), Building())
    )  # 3 buildings

    def __init__(self):
        super(BuildingsMicrogrid, self).__init__(MicrogridType.BUILDINGS)
        self.buildings = (Building(), Building(), Building())
        self.battery = MicrogridBattery()
        self.local_loop = LocalLoop()

    def __repr__(self):
        return (
            f"BuildingsMicrogrid<{tuple(building.id for building in self.buildings)}>"
        )


@dataclass
class CriticalMicrogrid(Microgrid):
    members: tuple[Critical, Critical, Critical]

    def __init__(self):
        super(CriticalMicrogrid, self).__init__(MicrogridType.CRITICAL)
        self.members = (
            Critical(UnitType.HOSPITAL),
            Critical(UnitType.FIRE_STATION),
            Critical(UnitType.POLICE_STATION),
        )
        self.battery = CriticalMicrogridBattery()
        self.local_loop = LocalLoop()
