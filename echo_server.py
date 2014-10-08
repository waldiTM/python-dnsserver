import asyncio
import dns.flags, dns.message

from dnsserver.transport.datagram import start_dns_datagram_server
from dnsserver.transport.stream import start_dns_server


@asyncio.coroutine
def accept_client(client_reader, client_writer):
    task = asyncio.Task(handle_client(client_reader, client_writer))


@asyncio.coroutine
def handle_client(client_reader, client_writer):
    while True:
        query, addr = yield from client_reader.read()

        response = dns.message.Message(query.id)
        response.flags = dns.flags.QR | (query.flags & dns.flags.RD)
        response.set_opcode(query.opcode())
        response.question = list(query.question)
        if query.edns >= 0:
            response.use_edns(0, 0, 8192, query.payload)

        client_writer.write(response, addr)


loop = asyncio.get_event_loop()
f = start_dns_datagram_server(handle_client, host=None, port=2991)
loop.run_until_complete(f)
f = start_dns_server(accept_client, host=None, port=2991)
loop.run_until_complete(f)
loop.run_forever()
