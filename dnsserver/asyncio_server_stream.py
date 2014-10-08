import asyncio
import collections
import dns.message
import struct


class DnsServerStreamReader:
    def __init__(self, inner):
        self._inner = inner

    @asyncio.coroutine
    def read(self):
        ldata = yield from self._inner.read(2)
        (l,) = struct.unpack("!H", ldata)
        data = yield from self._inner.read(l)
        mesg = dns.message.from_wire(data)
        return mesg, None


class DnsServerStreamWriter:
    def __init__(self, inner):
        self._inner = inner

    def write(self, mesg, addr=None):
        data = mesg.to_wire()
        ldata = struct.pack("!H", len(data))
        self._inner.write(ldata)
        self._inner.write(data)


@asyncio.coroutine
def start_server(client_connected_cb, host=None, port=None, **kwds):
    @asyncio.coroutine
    def cb(client_reader, client_writer):
        client_reader = DnsServerStreamReader(client_reader)
        client_writer = DnsServerStreamWriter(client_writer)
        return client_connected_cb(client_reader, client_writer)

    return asyncio.start_server(cb, host, port, **kwds)
