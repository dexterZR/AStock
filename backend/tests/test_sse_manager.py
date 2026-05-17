import pytest
import asyncio
import json
from app.infrastructure.sse_manager import SSEManager


@pytest.fixture
def manager():
    return SSEManager()


class TestSSEManager:
    async def test_connect(self, manager):
        queue = await manager.connect("client1")
        assert isinstance(queue, asyncio.Queue)
        assert "client1" in manager._clients

    async def test_disconnect(self, manager):
        await manager.connect("client1")
        await manager.disconnect("client1")
        assert "client1" not in manager._clients

    async def test_disconnect_nonexistent(self, manager):
        await manager.disconnect("nonexistent")

    async def test_subscribe(self, manager):
        manager.subscribe("client1", "market")
        assert "client1" in manager._subscriptions["market"]

    async def test_subscribe_multiple_clients(self, manager):
        manager.subscribe("client1", "market")
        manager.subscribe("client2", "market")
        assert len(manager._subscriptions["market"]) == 2

    async def test_subscribe_multiple_topics(self, manager):
        manager.subscribe("client1", "market")
        manager.subscribe("client1", "news")
        assert "client1" in manager._subscriptions["market"]
        assert "client1" in manager._subscriptions["news"]

    async def test_publish_to_subscribers(self, manager):
        await manager.connect("client1")
        manager.subscribe("client1", "market")
        await manager.publish("market", {"event": "price_update", "ts_code": "000001.SZ"})
        queue = manager._clients["client1"]
        msg = queue.get_nowait()
        parsed = json.loads(msg)
        assert parsed["event"] == "price_update"

    async def test_publish_no_subscribers(self, manager):
        await manager.publish("nonexistent", {"data": "test"})

    async def test_publish_removes_dead_client(self, manager):
        manager.subscribe("ghost", "market")
        assert "ghost" in manager._subscriptions["market"]
        await manager.publish("market", {"data": "test"})
        assert "ghost" not in manager._subscriptions["market"]

    async def test_broadcast(self, manager):
        await manager.connect("client1")
        await manager.connect("client2")
        await manager.broadcast({"event": "system", "msg": "hello"})
        q1 = manager._clients["client1"]
        q2 = manager._clients["client2"]
        msg1 = json.loads(q1.get_nowait())
        msg2 = json.loads(q2.get_nowait())
        assert msg1["event"] == "system"
        assert msg2["msg"] == "hello"

    async def test_disconnect_cleans_subscriptions(self, manager):
        await manager.connect("client1")
        manager.subscribe("client1", "market")
        manager.subscribe("client1", "news")
        await manager.disconnect("client1")
        assert "client1" not in manager._clients
        assert "market" not in manager._subscriptions
        assert "news" not in manager._subscriptions

    async def test_queue_overflow_on_publish(self, manager):
        queue = await manager.connect("client1")
        manager.subscribe("client1", "market")
        for i in range(101):
            await manager.publish("market", {"i": i})
        assert not queue.empty()
