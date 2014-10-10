import asyncio
import dns.message
import struct


class DnsDatagramProtocol(asyncio.DatagramProtocol):
    def __init__(self, reader):
        self._reader = reader

    def datagram_received(self, data, addr):
        mesg = dns.message.from_wire(data)
        self._reader.feed(mesg)

    def error_received(self, exc):
        print(exc)

    def write(self, transport, mesg):
        transport.sendto(mesg.to_wire())


class DnsStreamProtocol(asyncio.DatagramProtocol):
    def __init__(self, reader):
        self._reader = reader

    def data_received(self, data):
        (l,) = struct.unpack("!H", data[:2])
        # TODO
        mesg = dns.message.from_wire(data[2:l+2])
        self._reader.feed(mesg)

    def eof_received(self):
        print("eof")

    def write(self, transport, mesg):
        data = mesg.to_wire()
        ldata = struct.pack("!H", len(data))
        transport.write(ldata)
        transport.write(data)
