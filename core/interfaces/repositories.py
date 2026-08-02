from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Tuple


class IRepository(ABC):
    """اینترفیس پایه برای ریپازیتوری‌ها"""

    @abstractmethod
    async def execute_query(self, query: str) -> List[Tuple]:
        """اجرای کوئری دلخواه"""
        pass

    @abstractmethod
    async def get_count(self) -> int:
        """دریافت تعداد کل رکوردها"""
        pass


class IEventRepository(IRepository):
    """اینترفیس ریپازیتوری رویدادها"""

    @abstractmethod
    async def get_sample(self, limit: int = 10) -> List[Dict]:
        """دریافت نمونه رویدادها"""
        pass

    @abstractmethod
    async def get_user_events(self, user_id: int, limit: int = 20) -> List[Dict]:
        """دریافت رویدادهای یک کاربر"""
        pass

    @abstractmethod
    async def get_user_stats(self, user_id: int) -> Dict:
        """دریافت آمار یک کاربر"""
        pass

    @abstractmethod
    async def search_events(self, query: str, limit: int = 50) -> List[Dict]:
        """جستجوی رویدادها"""
        pass