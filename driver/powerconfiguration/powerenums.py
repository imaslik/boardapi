from __future__ import absolute_import
from enum import Enum


class CurrentMonitoringMethod(Enum):
    RES = 1
    PMBUS = 2
    VR = 3

    def __eq__(self, other):
        return self.value == other.value


class PowerManagementType(Enum):
    PMBUS = 0
    RDAC = 1

    def __eq__(self, other):
        return self.value == other.value


class ActionTypeFPGA(Enum):
    NOTHING = 0
    OPENCLOSE = 1
    OPEN = 2
    CLOSE = 3

    def __eq__(self, other):
        return self.value == other.value


class DelayTimeType(Enum):
    MILISECONDS = 0
    SECONDS = 1
    MINUTES = 2

    def __eq__(self, other):
        return self.value == other.value

