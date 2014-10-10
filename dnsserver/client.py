import asyncio

from .protocol import DnsDatagramProtocol, DnsStreamProtocol


class Client:
    def __init__(self, transport, protocol, reader):
        self._transport, self._protocol, self._reader = transport, protocol, reader

    def __call__(self, query):
        id = query.id
        assert id not in self._reader._requests

        self._protocol.write(self._transport, query)
        f = asyncio.Future()
        self._reader._requests[id] = f

        return f


class ClientReader:
    def __init__(self):
        self._requests = {}

    def feed(self, response):
        f = self._requests.pop(response.id, None)
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
