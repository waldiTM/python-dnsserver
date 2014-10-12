import asyncio
import collections
import dns.message
import struct


class DnsStreamReader:
    def __init__(self, inner):
        self._inner = inner

    @asyncio.coroutine
    def read(self):
        ldata = yield from self._inner.read(2)
        if not ldata:
            return None, None

        (l,) = struct.unpack("!H", ldata)
        data = yield from self._inner.read(l)
        mesg = dns.message.from_wire(data)
        return mesg, None


class DnsStreamWriter:
    def __init__(self, inner):
        self._inner = inner

    def close(self):
        self._inner.close()

    def write(self, mesg, addr=None):
        data = mesg.to_wire()
        ldata = struct.pack("!H", len(data))
        self._inner.write(ldata)
        self._inner.write(data)


def _wrap(reader, writer):
    return DnsStreamReader(reader), DnsStreamWriter(writer)

@asyncio.coroutine
def start_dns_server(client_connected_cb, host=None, port=None, **kwds):
    @asyncio.coroutine
    def cb(*args):
        return client_connected_cb(*_wrap(*args))

    return asyncio.start_server(cb, host, port, **kwds)
