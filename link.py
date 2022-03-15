from dataclasses import dataclass

from house import House, Building, Apartment
from microgrid import Microgrid


@dataclass
class MicrogridToOutMeter:
    microgrid: Microgrid
    house: House


@dataclass
class MicrogridToInMeter:
    microgrid: Microgrid
    house: House


@dataclass
class MicrogridToApartmentMeter:
    microgrid: Microgrid
    building: Building
    apartment: Apartment
