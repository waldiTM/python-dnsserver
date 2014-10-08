import asyncio
import dns.flags, dns.message, dns.rdatatype
import sys

from dnsserver.transport.stream import open_dns_connection


@asyncio.coroutine
def client(name, server='localhost'):
    reader, writer = yield from open_dns_connection(server)

    query = dns.message.make_query(name, dns.rdatatype.A, use_edns=0)
    writer.write(query)
    query = dns.message.make_query(name, dns.rdatatype.AAAA, use_edns=0)
    writer.write(query)

    while True:
        mesg, addr = yield from reader.read()
        if not mesg:
            break
        print(mesg)


loop = asyncio.get_event_loop()
task = asyncio.async(client(*sys.argv[1:]))
loop.run_until_complete(task)
loop.close()
