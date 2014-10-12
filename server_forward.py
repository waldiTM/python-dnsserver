import asyncio
import dns.entropy, dns.flags, dns.message, dns.rcode
import logging

from dnsserver.client import open_dns_datagram_client
from dnsserver.server.datagram import start_dns_datagram_server
from dnsserver.server.stream import start_dns_server


@asyncio.coroutine
def accept_server(server_reader, server_writer):
    task = asyncio.Task(handle_server(server_reader, server_writer))


@asyncio.coroutine
def handle_server(server_reader, server_writer):
    while True:
        query, addr = yield from server_reader.read()
        if not query:
            break
        query_id = query.id

        response = dns.message.Message(query.id)
        response.flags = dns.flags.QR | (query.flags & dns.flags.RD)
        response.set_opcode(query.opcode())
        response.question = list(query.question)
        if query.edns >= 0:
            response.use_edns(0, 0, 8192, query.payload)

        client = yield from open_dns_datagram_client('8.8.8.8')

        query.id = dns.entropy.random_16()
        f = asyncio.async(asyncio.wait_for(client(query), timeout=3))
        f.add_done_callback(lambda f: handle_response(f, server_writer, response, addr))


def handle_response(future, writer, response, addr):
    try:
        r = future.result()
        r.id = response.id
        response = r

    except asyncio.TimeoutError:
        logging.info('Timeout waiting for upstream response')
        response.set_rcode(dns.rcode.SERVFAIL)

    except Exception:
        logging.exception('Failed to obtain answer from upstream server')
        response.set_rcode(dns.rcode.SERVFAIL)

    writer.write(response, addr)


logging.basicConfig(level=logging.INFO)

loop = asyncio.get_event_loop()
f = start_dns_datagram_server(handle_server, host=None, port=2991)
loop.run_until_complete(f)
f = start_dns_server(accept_server, host=None, port=2991)
loop.run_until_complete(f)
loop.run_forever()
