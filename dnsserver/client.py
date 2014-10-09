import asyncio


class Client:
    def __init__(self, reader, writer):
        self._writer = writer
        self._reader = asyncio.async(self.__reader_task(reader))
        self._requests = {}

    @asyncio.coroutine
    def __call__(self, query):
        id = query.id
        assert id not in self._requests

        self._writer.write(query)
        f = asyncio.Future()
        self._requests[id] = f

        return f

    @asyncio.coroutine
    def __reader_task(self, reader):
        try:
            while True:
                response, addr = yield from reader.read()
                if not response:
                    break

                f = self._requests.pop(response.id, None)
                if f:
                    f.set_result(response)
                else:
                    print("Unexpected response:", response)

        finally:
            for f in self._requests.values():
                f.cancel()
