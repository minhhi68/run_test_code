"""
Test authoritative server for example.test with a wildcard record.

Every *.example.test A query gets NOERROR (like a wildcard zone), so attack
names cannot be told apart by the answer. Capacity is limited by a token
bucket: queries above --qps are silently dropped (a rate-limited channel).
"""
import argparse
import asyncio
import time

import dns.message
import dns.rcode
import dns.rrset


class Auth(asyncio.DatagramProtocol):
    def __init__(self, qps, ttl):
        self.qps, self.ttl = qps, ttl
        self.tokens, self.last = qps, time.monotonic()
        self.answered = self.dropped = 0

    def connection_made(self, transport):
        self.transport = transport

    def datagram_received(self, data, addr):
        t = time.monotonic()
        self.tokens = min(self.qps, self.tokens + (t - self.last) * self.qps)
        self.last = t
        if self.tokens < 1:
            self.dropped += 1
            return
        self.tokens -= 1
        q = dns.message.from_wire(data)
        r = dns.message.make_response(q)
        name = q.question[0].name
        if name.to_text().lower().endswith("example.test."):
            r.answer.append(dns.rrset.from_text(name, self.ttl, "IN", "A", "192.0.2.1"))
        else:
            r.set_rcode(dns.rcode.REFUSED)
        self.answered += 1
        self.transport.sendto(r.to_wire(), addr)


async def main():
    p = argparse.ArgumentParser()
    p.add_argument("--listen", default="127.0.0.1:5301")
    p.add_argument("--qps", type=float, default=100)
    p.add_argument("--ttl", type=int, default=1)
    a = p.parse_args()
    ip, port = a.listen.split(":")
    auth = Auth(a.qps, a.ttl)
    await asyncio.get_running_loop().create_datagram_endpoint(
        lambda: auth, local_addr=(ip, int(port)))
    print(f"auth on {a.listen} qps={a.qps} ttl={a.ttl}", flush=True)
    while True:
        await asyncio.sleep(3600)


if __name__ == "__main__":
    asyncio.run(main())
