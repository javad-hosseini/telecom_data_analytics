from typing import List, Dict, Any, Optional
from repositories.network_event_repository import NetworkEventRepository


class EventService:
    """سرویس مدیریت رویدادها"""

    def __init__(self, repository: NetworkEventRepository):
        self.repo = repository

    async def get_count(self) -> int:
        """دریافت تعداد کل رویدادها"""
        return self.repo.count()

    async def get_sample(self, limit: int = 10) -> List[Dict]:
        """دریافت نمونه رویدادها"""
        return self.repo.get_sample(limit)

    async def get_user_data(
            self,
            user_id: int,
            limit: int = 20,
            include_stats: bool = False
    ) -> Dict[str, Any]:
        """دریافت داده‌های یک کاربر"""
        events = self.repo.get_by_user_id(user_id, limit)

        result = {
            "user_id": user_id,
            "events": events
        }

        if include_stats:
            stats = self.repo.get_stats_by_user(user_id)
            result["stats"] = stats

        return result

    async def search_events(self, query: str, limit: int = 50) -> List[Dict]:
        """جستجوی رویدادها با کوئری دلخواه"""
        # اعتبارسنجی امنیتی
        forbidden = ["DROP", "DELETE", "UPDATE", "INSERT", "ALTER"]
        if any(keyword in query.upper() for keyword in forbidden):
            raise ValueError("Query contains forbidden operations")

        # محدود کردن کوئری
        if "LIMIT" not in query.upper():
            query = f"{query} LIMIT {limit}"

        return self.repo.execute_query(query)
