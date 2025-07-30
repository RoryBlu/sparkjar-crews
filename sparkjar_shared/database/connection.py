from contextlib import asynccontextmanager

EVENTS = []


class FakeAsyncSession:
    def __init__(self, store):
        self._store = store

    def add(self, obj):
        self._store.append(obj)

    async def commit(self):
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        pass


@asynccontextmanager
async def get_direct_session():
    session = FakeAsyncSession(EVENTS)
    try:
        yield session
    finally:
        pass
