import asyncio
import dns.flags, dns.message, dns.rdatatype
import sys

from dnsserver.client import open_dns_datagram_client


@asyncio.coroutine
def client(name, server='localhost'):
    client = yield from open_dns_datagram_client(server)

    results = set()
    query = dns.message.make_query(name, dns.rdatatype.A, use_edns=0)
    f1 = client(query)
    query = dns.message.make_query(name, dns.rdatatype.AAAA, use_edns=0)
    f2 = client(query)
    done, pending = yield from asyncio.wait((f1, f2), timeout=3)
    for f in done:
        print(f.result())
    for f in pending:
        f.cancel()


loop = asyncio.get_event_loop()
task = asyncio.async(client(*sys.argv[1:]))
loop.run_until_complete(task)
loop.close()
