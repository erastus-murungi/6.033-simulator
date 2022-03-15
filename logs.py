from dataclasses import dataclass, field
from enum import Enum
from itertools import count
from typing import ClassVar

RECORD_SIZES = {
    "record_type": 8,
    "lossy_aggregation": 8,
    "record_id": 64,
    "meter_id": 64,
    "account_number": 16,
    "start_time": 32,
    "end_time": 32,
    "reading": 64,
    "previous_state": 16,
    "new_state": 16,
    "time": 32,
}

BYTES_PER_BIT = 8


def record_size(field_name: str):
    """
    >>> record_size('record_type')
    8
    """
    return RECORD_SIZES[field_name]


class RecordType(Enum):
    POWER_GENERATION = 0
    POWER_STORED = 1
    POWER_THROUGH = 2


class State(Enum):
    DISCONNECTED_FROM_POWER_NET = 0
    RUNNING_ON_POWER_NET = 1
    SHUTDOWN = 2
    INITIALIZED = 3
    AGGREGATING_DATA = 4
    NOT_AGGREGATING_DATA = 5


@dataclass
class HistoryLog:
    record_type: RecordType
    lossy_aggregation: bool
    meter_id: int
    account_number: int
    start_time: int
    end_time: int
    reading: int
    id_gen: ClassVar = count(0)
    record_id: int = field(default_factory=id_gen.__next__)

    @staticmethod
    def size():
        """
        >>> HistoryLog.size() == 36
        True
        """
        return (
            sum(RECORD_SIZES[attr] for attr in HistoryLog.__annotations__.keys())
            // BYTES_PER_BIT
        )


@dataclass
class EventLog:
    previous_state: State
    new_state: State
    meter_id: int
    time: int
    id_gen: ClassVar = count(0)
    record_id: int = field(default_factory=id_gen.__next__)

    @staticmethod
    def size():
        """
        >>> EventLog.size() == 24
        True
        """
        return (
            sum(RECORD_SIZES[attr] for attr in EventLog.__annotations__.keys())
            // BYTES_PER_BIT
        )


if __name__ == "__main__":
    import doctest

    doctest.testmod()
