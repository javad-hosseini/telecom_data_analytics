# services/event_service.py
# Business logic for event-related operations. 
# This is where we process data before sending it to the API or CLI.

from typing import List, Dict, Any

from repositories.network_event_repository import NetworkEventRepository


class EventService:
    """
    Handles all event-related business logic.

    This service sits between the API layer and the repository layer.
    It gets raw data from the repository, processes it, and returns
    formatted data to the caller.
    """

    def __init__(self, repository: NetworkEventRepository):
        self.repo = repository

    async def get_count(self) -> int:
        """Get total number of events. Simple pass-through to repository."""
        return self.repo.count()

    async def get_sample(self, limit: int = 10) -> list[list[Any]]:
        """
        Get a random sample of events.

        Useful for quick data exploration or testing.
        Returns a list of dictionaries instead of raw tuples.
        """
        return self.repo.get_sample(limit)

    async def get_user_data(
            self,
            user_id: int,
            limit: int = 20,
            include_stats: bool = False
    ) -> Dict[str, Any]:
        """
        Get all data for a specific user.

        Returns:
            - Basic info: user_id and list of events
            - Optional: statistics if include_stats is True

        This is a good example of how services combine multiple
        repository calls into one meaningful response.
        """
        events = self.repo.get_by_user_id(user_id, limit)

        result = {
            "user_id": user_id,
            "events": events
        }

        # Only fetch stats if the caller asked for them
        if include_stats:
            stats = self.repo.get_stats_by_user(user_id)
            result["stats"] = stats

        return result

    async def search_events(self, query: str, limit: int = 50) -> List[Dict]:
        """
        Execute a custom search query with security checks.

        Important: This prevents dangerous SQL operations like DROP or DELETE.
        Also, automatically adds LIMIT if the user forgot to include it.

        This is the only way to run custom queries through the service layer.
        """
        # Security check - block destructive operations
        forbidden = ["DROP", "DELETE", "UPDATE", "INSERT", "ALTER"]
        if any(keyword in query.upper() for keyword in forbidden):
            raise ValueError("Query contains forbidden operations")

        # Make sure there's a limit to prevent huge result sets
        if "LIMIT" not in query.upper():
            query = f"{query} LIMIT {limit}"

        return self.repo.execute_query(query)
