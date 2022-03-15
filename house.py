import pickle
import random
from dataclasses import dataclass, field
from itertools import count
from pprint import pprint
from typing import ClassVar, Final, Callable
from k_means_constrained import KMeansConstrained
import numpy as np
import matplotlib.pyplot as plt

from battery import NormalBattery, AVERAGE_PER_SECOND_USE
from logs import HistoryLog, State, RecordType, EventLog

NUM_APARTMENTS_PER_BUILDING: Final[int] = 100
NUM_HOUSES_PER_MICROGRID: Final[int] = 10
NUM_HOUSES: Final[int] = 8000
NUM_MICROGRIDS: Final[int] = NUM_HOUSES // NUM_HOUSES_PER_MICROGRID
NUM_BUILDINGS: Final[int] = 3


@dataclass
class SmartMeter:
    id_gen: ClassVar = count(0)
    id: int = field(default_factory=id_gen.__next__)
    initialized: bool = True
    off: bool = True
    lossy: bool = False
    history_logs: list[HistoryLog] = field(default_factory=list)
    event_logs: list[EventLog] = field(default_factory=list)
    previous_state: State = State.SHUTDOWN

    power_through: int = 0

    def consume_from_time(self, use_per_second):
        self.power_through += use_per_second

    def record_history_log(
        self, record_type: RecordType, meter_id, time, reading, lossy_aggregation=False
    ):
        self.history_logs.append(
            HistoryLog(
                record_type, lossy_aggregation, meter_id, -1, time, time, reading
            )
        )

    def record_change_of_state(self, new_state: State, meter_id, time):
        self.event_logs.append(EventLog(self.previous_state, new_state, meter_id, time))
        self.previous_state = new_state

    def shutdown(self):
        pass

    def get(self, kwargs):
        pass

    def put(self):
        pass

    def isolate(self):
        pass

    def aggregate(self, lossy: bool):
        pass

    def de_aggregate(self):
        pass

    def share_power(self, on: bool):
        pass

    def acknowledge(self):
        pass


@dataclass(frozen=True)
class Location:
    """
    >>> Location(1.1, 1.2)
    Location(x=1.1, y=1.2)
    """

    x: float
    y: float


def random_location():
    return Location(random.random() * 100, random.random() * 100)


def new_smart_meter():
    return SmartMeter()


def new_normal_battery():
    return NormalBattery()


def _average_power_consumer(time):
    return AVERAGE_PER_SECOND_USE


def average_power_consumer():
    return _average_power_consumer


@dataclass
class House:
    location: Location
    id_gen: ClassVar = count(0)
    amps: int = 200
    id: int = field(default_factory=id_gen.__next__)
    smart_meter_out: SmartMeter = field(default_factory=new_smart_meter)
    smart_meter_in: SmartMeter = field(default_factory=new_smart_meter)
    battery: NormalBattery = field(default_factory=new_normal_battery)
    power_consumer: Callable[[int], float] = field(
        repr=False, default_factory=average_power_consumer
    )
    power_consumed: int = 0

    def generated_power(self, time) -> float:
        if time < (24 * 60 * 60) * 0.4:
            return self.battery.per_second_use * 0.5
        else:
            return 0.0

    def set_power_consumption_function(self, power_consumer: Callable[[int], float]):
        self.power_consumer = power_consumer

    def increment_power_consumed_by(self, power_consumed):
        self.power_consumed += power_consumed

    def consume_power(self, time, interval):
        return self.power_consumer(time) * interval


@dataclass
class Apartment:
    id_gen: ClassVar = count(0)

    amps: int = 100
    id: int = field(default_factory=id_gen.__next__)
    smart_meter: SmartMeter = field(default_factory=lambda: SmartMeter())
    battery: NormalBattery = field(default_factory=lambda: NormalBattery())


@dataclass
class Building:
    id_gen: ClassVar = count(0)
    id: int = field(default_factory=id_gen.__next__)
    apartments: tuple[Apartment, ...] = field(
        default_factory=lambda: tuple(
            Apartment() for _ in range(NUM_APARTMENTS_PER_BUILDING)
        )
    )


def plot_clusters(clusters: list[list[Location]]):
    for locs in clusters:
        locs_arr = np.array([[loc.x, loc.y] for loc in locs])
        plt.scatter(locs_arr[:, 0], locs_arr[:, 1], alpha=0.5, marker="p")
    plt.show()


def get_clustered_locations() -> list[list[Location]]:
    locs = np.random.normal(size=(NUM_HOUSES, 2))
    clf = KMeansConstrained(
        n_clusters=len(locs) // NUM_HOUSES_PER_MICROGRID,
        size_max=NUM_HOUSES_PER_MICROGRID,
        size_min=NUM_HOUSES_PER_MICROGRID,
        n_jobs=-1,
        verbose=True,
    )
    clf.fit_predict(locs)
    return [
        [Location(*loc) for loc in locs[np.where(clf.labels_ == i)[0]]]
        for i in range(clf.n_clusters)
    ]


def gen_and_pickle_locations(plot=False) -> list[list[Location]]:
    locations = get_clustered_locations()
    assert all(len(cluster) == 10 for cluster in locations)
    with open("houses.pickle", "wb") as hs_pickle:
        pickle.dump(locations, hs_pickle)
    if plot:
        plot_clusters(locations)
    return locations


def unpickle_clustered_locations():
    with open("houses.pickle", "rb") as hs_pickle:
        clusters = pickle.load(hs_pickle)
        return clusters


def get_houses(clusters) -> tuple[tuple[House, ...], ...]:
    return tuple(
        tuple(House(location) for location in locations) for locations in clusters
    )


def get_houses_direct():
    clustered_locs = unpickle_clustered_locations()
    return get_houses(clustered_locs)


if __name__ == "__main__":
    import doctest

    doctest.testmod()
