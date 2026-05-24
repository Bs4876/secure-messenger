"""
Simple in-process broadcaster for Server-Sent Events (SSE).

This provides a tiny publish/subscribe mechanism used by Stage 2.
Each connected client gets an asyncio.Queue. When a message is published
it is pushed into every queue so connected clients receive events.

This is intentionally small and in-memory (suitable for a single-process
development server). For production you would use Redis/Channels/etc.
"""

from __future__ import annotations

import asyncio
from typing import Any, Iterable, Tuple


class Broadcaster:
    def __init__(self) -> None:
        # set of (asyncio.Queue, loop) tuples for each connected client
        self._subscribers: set[Tuple[asyncio.Queue, asyncio.AbstractEventLoop]] = set()

    def register(self) -> asyncio.Queue:
        """Register a new subscriber and return its asyncio.Queue.

        Must be called from an async context (so we can capture the
        current event loop). Returns the queue the caller should await on.
        """
        loop = asyncio.get_running_loop()
        q: asyncio.Queue = asyncio.Queue()
        self._subscribers.add((q, loop))
        return q

    def unregister(self, q: asyncio.Queue) -> None:
        # remove any subscriber entries that use this queue
        to_remove = [s for s in self._subscribers if s[0] is q]
        for s in to_remove:
            try:
                self._subscribers.remove(s)
            except KeyError:
                pass

    def publish(self, message: Any) -> None:
        """Publish a message to all registered subscriber queues.

        This method is safe to call from background threads. It uses
        loop.call_soon_threadsafe to schedule queue.put_nowait on each
        subscriber's loop.
        """
        # Snapshot to avoid mutation during iteration
        subs: Iterable[Tuple[asyncio.Queue, asyncio.AbstractEventLoop]] = list(self._subscribers)
        for q, loop in subs:
            try:
                loop.call_soon_threadsafe(q.put_nowait, message)
            except Exception:
                # ignore failures for individual subscribers
                continue


# Module-level singleton used by the app
broadcaster = Broadcaster()
