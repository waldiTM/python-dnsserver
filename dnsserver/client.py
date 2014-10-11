import asyncio

from .protocol import DnsDatagramProtocol, DnsStreamProtocol


class Client:
    def __init__(self, transport, protocol, reader):
        self._transport, self._protocol, self._reader = transport, protocol, reader

    @asyncio.coroutine
    def __call__(self, query):
        id = query.id
        assert id not in self._reader.requests

        self._reader.requests[id] = f = asyncio.Future()
        try:
            self._protocol.write(self._transport, query)
            response = yield from f
        finally:
            self._reader.requests.pop(id)
        return response


class ClientReader:
    def __init__(self):
        self.requests = {}

    def feed(self, response):
        f = self.requests.get(response.id, None)
        if f:
            f.set_result(response)
        else:
            print("Unexpected response:", response)


@asyncio.coroutine
def open_dns_client(host=None, port=53, *, loop=None, **kwds):
    if loop is None:
        loop = asyncio.get_event_loop()

    reader = ClientReader()
    protocol = DnsStreamProtocol(reader)

    transport, protocol = yield from loop.create_connection(lambda: protocol, host, port, **kwds)

    return Client(transport, protocol, reader)

@asyncio.coroutine
def open_dns_datagram_client(host=None, port=53, *, loop=None, limit=None, **kwds):
    if loop is None:
        loop = asyncio.get_event_loop()

    reader = ClientReader()
    protocol = DnsDatagramProtocol(reader)

    transport, protocol = yield from loop.create_datagram_endpoint(lambda: protocol, remote_addr=(host, port), **kwds)

    return Client(transport, protocol, reader)
