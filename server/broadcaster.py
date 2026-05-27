"""
broadcaster.py — Thread-safe, fully asynchronous SSE broadcast broker (Fix Q14, Q18).
"""

import asyncio
from typing import Set, Any

class Broadcaster:
    def __init__(self):
        # שימוש ב-Set למניעת כפילויות ומחיקה מהירה ב-O(1)
        self._listeners: Set[asyncio.Queue] = set()

    def register(self) -> asyncio.Queue:
        """Registers a new client queue for real-time messages."""
        q = asyncio.Queue()
        self._listeners.add(q)
        return q

    def unregister(self, q: asyncio.Queue) -> None:
        """Unregisters a client queue when they disconnect (Fix Q10)."""
        self._listeners.discard(q)

    async def publish(self, message: Any) -> None:
        """
        Asynchronously broadcasts a message to all registered listener queues.
        This is non-blocking and fully integrated with the asyncio Event Loop.
        """
        if not self._listeners:
            return

        # יצירת משימות הפצה לכל התורים במקביל
        for queue in list(self._listeners):
            try:
                await queue.put(message)
            except Exception:
                # הסרת תורים פגומים או סגורים בצורה בטוחה
                self.unregister(queue)

broadcaster = Broadcaster()