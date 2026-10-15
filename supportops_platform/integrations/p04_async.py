"""P04 0.1.1 package adapter for local SQLite and in-memory broker integration tests."""

from supportops_async.api import create_app
from supportops_async.queue.memory import InMemoryBroker
from supportops_async.store.sqlite import SQLiteTaskStore
from supportops_async.worker.runner import Worker


def create_p04_local_components():
    store = SQLiteTaskStore(":memory:")
    broker = InMemoryBroker()
    app = create_app(store, broker)
    worker = Worker(store, broker)
    return app, store, broker, worker
