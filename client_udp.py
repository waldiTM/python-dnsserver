import asyncio
import dns.flags, dns.message, dns.rdatatype
import sys

from dnsserver.client import open_dns_datagram_client


@asyncio.coroutine
def client(name, server='localhost'):
    client = yield from open_dns_datagram_client(server)

    query = dns.message.make_query(name, dns.rdatatype.A, use_edns=0)
    response = yield from client(query)
    print(response)
    query = dns.message.make_query(name, dns.rdatatype.AAAA, use_edns=0)
    response = yield from client(query)
    print(response)


loop = asyncio.get_event_loop()
task = asyncio.async(client(*sys.argv[1:]))
loop.run_until_complete(task)
loop.close()
