import asyncio
import json
import time
from typing import Dict, Set
from fastapi import Request


class SSEManager:
    MAX_CLIENTS = 200

    def __init__(self):
        self._clients: Dict[str, asyncio.Queue] = {}
        self._subscriptions: Dict[str, Set[str]] = {}

    async def connect(self, client_id: str) -> asyncio.Queue:
        if len(self._clients) >= self.MAX_CLIENTS:
            import logging
            logger = logging.getLogger("app.sse")
            logger.warning("SSE 连接数已达上限 (%d), 拒绝新连接: client_id=%s", self.MAX_CLIENTS, client_id)
            raise ConnectionError(f"SSE 连接数已达上限 ({self.MAX_CLIENTS})")
        queue = asyncio.Queue(maxsize=100)
        self._clients[client_id] = queue
        return queue

    async def disconnect(self, client_id: str):
        self._clients.pop(client_id, None)
        for topic in list(self._subscriptions.keys()):
            subs = self._subscriptions.get(topic)
            if subs:
                subs.discard(client_id)
                if not subs:
                    del self._subscriptions[topic]

    def subscribe(self, client_id: str, topic: str):
        if topic not in self._subscriptions:
            self._subscriptions[topic] = set()
        self._subscriptions[topic].add(client_id)

    async def publish(self, topic: str, data: dict):
        if topic not in self._subscriptions:
            return
        message = json.dumps(data, ensure_ascii=False)
        dead = []
        for cid in self._subscriptions.get(topic, set()):
            queue = self._clients.get(cid)
            if queue is None:
                dead.append(cid)
                continue
            try:
                if queue.full():
                    await queue.get()
                await queue.put(message)
            except asyncio.QueueFull:
                pass
        for cid in dead:
            self._subscriptions[topic].discard(cid)

    async def broadcast(self, data: dict):
        """向所有连接的客户端广播消息"""
        message = json.dumps(data, ensure_ascii=False)
        dead = []
        for cid, queue in self._clients.items():
            try:
                if queue.full():
                    await queue.get()
                await queue.put(message)
            except asyncio.QueueFull:
                pass
            except Exception:
                dead.append(cid)
        for cid in dead:
            await self.disconnect(cid)

    async def event_generator(self, client_id: str, request: Request):
        queue = await self.connect(client_id)
        try:
            yield f"event: connected\ndata: {json.dumps({'client_id': client_id})}\n\n"
            while True:
                if await request.is_disconnected():
                    break
                try:
                    msg = await asyncio.wait_for(queue.get(), timeout=30.0)
                    yield f"data: {msg}\n\n"
                except asyncio.TimeoutError:
                    yield f"event: heartbeat\ndata: {json.dumps({'ts': int(time.time())})}\n\n"
        finally:
            await self.disconnect(client_id)
