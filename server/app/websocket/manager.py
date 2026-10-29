import asyncio
from collections import defaultdict

from fastapi import WebSocket


class ConnectionManager:
    def __init__(self):
        self._connections: dict[int, set[WebSocket]] = defaultdict(set)
        self._lock = asyncio.Lock()

    async def connect(self, user_id: int, socket: WebSocket):
        await socket.accept()
        async with self._lock:
            self._connections[user_id].add(socket)

    async def disconnect(self, user_id: int, socket: WebSocket):
        async with self._lock:
            self._connections[user_id].discard(socket)
            if not self._connections[user_id]:
                self._connections.pop(user_id, None)

    async def send_user(self, user_id: int, payload: dict):
        dead: list[WebSocket] = []
        for socket in tuple(self._connections.get(user_id, ())):
            try:
                await socket.send_json(payload)
            except Exception:
                dead.append(socket)
        for socket in dead:
            await self.disconnect(user_id, socket)

    async def broadcast(self, payload: dict):
        for user_id in tuple(self._connections):
            await self.send_user(user_id, payload)

    def connected_user_ids(self) -> list[int]:
        return sorted(self._connections)

    def connection_counts(self) -> dict[int, int]:
        return {
            user_id: len(sockets)
            for user_id, sockets in sorted(self._connections.items())
            if sockets
        }


manager = ConnectionManager()
