from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional


class IEventService(ABC):
    """اینترفیس سرویس رویدادها"""

    @abstractmethod
    async def get_count(self) -> int:
        pass

    @abstractmethod
    async def get_sample(self, limit: int = 10) -> List[Dict]:
        pass

    @abstractmethod
    async def get_user_data(self, user_id: int, limit: int = 20, include_stats: bool = False) -> Dict[str, Any]:
        pass


class IAnalyticsService(ABC):
    """اینترفیس سرویس تحلیل‌ها"""

    @abstractmethod
    async def get_top_apps(self, limit: int = 10) -> List[Dict]:
        pass

    @abstractmethod
    async def get_network_quality(self) -> List[Dict]:
        pass

    @abstractmethod
    async def get_hourly_heatmap(self, days: int = 7) -> List[Dict]:
        pass


class IPartitionService(ABC):
    """اینترفیس سرویس پارتیشن‌ها"""

    @abstractmethod
    async def get_partition_status(self) -> List[Dict]:
        pass

    @abstractmethod
    async def drop_partition(self, year_month: str) -> Dict:
        pass

    @abstractmethod
    async def clean_old_partitions(self, months: int) -> Dict:
        pass