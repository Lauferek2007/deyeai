from __future__ import annotations

from .deye import DeyeAdapter
from .generic import GenericEntityAdapter
from .goodwe import GoodWeAdapter
from .huawei import HuaweiSolarAdapter
from .solarman import SolarmanAdapter

ADAPTERS = {
    "deye": DeyeAdapter,
    "generic": GenericEntityAdapter,
    "goodwe": GoodWeAdapter,
    "huawei": HuaweiSolarAdapter,
    "solarman": SolarmanAdapter,
}
