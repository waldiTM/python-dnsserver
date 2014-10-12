import asyncio
import collections
import dns.message


class DnsDatagramReader:
    def __init__(self, limit=None, loop=None):
        self._limit = limit
        if loop is None:
            loop = asyncio.get_event_loop()
        self._loop = loop
        self._buffer = collections.deque()
        self._waiter = None  # A future.

    def _create_waiter(self, func_name):
        # StreamReader uses a future to link the protocol feed_data() method
        # to a read coroutine. Running two read coroutines at the same time
        # would have an unexpected behaviour. It would not possible to know
        # which coroutine would get the next data.
        if self._waiter is not None:
            raise RuntimeError('%s() called while another coroutine is '
                               'already waiting for incoming data' % func_name)
        return asyncio.Future(loop=self._loop)

    def feed_data(self, data, addr):
        if not data:
            return

        self._buffer.appendleft((data, addr))

        waiter = self._waiter
        if waiter is not None:
            self._waiter = None
            if not waiter.cancelled():
                waiter.set_result(False)

    @asyncio.coroutine
    def read(self):
        if not len(self._buffer):
            self._waiter = self._create_waiter('read')
            try:
                yield from self._waiter
            finally:
                self._waiter = None

        data, addr = self._buffer.pop()
        mesg = dns.message.from_wire(data)
        return mesg, addr


class DnsDatagramWriter:
    def __init__(self, transport):
        self._transport = transport

    def write(self, mesg, addr=None):
        self._transport.sendto(mesg.to_wire(), addr)


class DnsDatagramProtocol(asyncio.DatagramProtocol):
    def __init__(self, reader):
        self._reader = reader
        self._writer = None

    def datagram_received(self, data, addr):
        self._reader.feed_data(data, addr)

    def error_received(self, exc):
        print(exc)


@asyncio.coroutine
def start_dns_datagram_server(client_cb, host=None, port=53, *, loop=None, limit=None, **kwds):
    if loop is None:
        loop = asyncio.get_event_loop()

    reader = DnsDatagramReader(limit=limit, loop=loop)
    protocol = DnsDatagramProtocol(reader)

    transport, protocol = yield from loop.create_datagram_endpoint(lambda: protocol, local_addr=(host, port), **kwds)

    writer = DnsDatagramWriter(transport)

    return transport, asyncio.async(client_cb(reader, writer))
