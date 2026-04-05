from __future__ import annotations

from .generic import GenericEntityAdapter
from .goodwe import GoodWeAdapter
from .huawei import HuaweiSolarAdapter
from .solarman import SolarmanAdapter

ADAPTERS = {
    "generic": GenericEntityAdapter,
    "goodwe": GoodWeAdapter,
    "huawei": HuaweiSolarAdapter,
    "solarman": SolarmanAdapter,
}
