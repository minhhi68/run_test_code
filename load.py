"""
Traffic generator: legitimate clients + attacking bots (wildcard scenario).

Phase 1 (warm-up): legitimate traffic only, so the resolver can learn.
Phase 2 (attack):  bots send random names under example.test.

Legitimate queries are of two kinds:
    popular  - names from a small fixed set, shared by all clients
    new      - unique names never seen before (same shape as attack names)

Output: success ratio per kind during the attack phase.
"""
import argparse
import asyncio
import json
import random
import string
import time

import dns.asyncquery
import dns.exception
import dns.message
import dns.rcode

POPULAR = [f"www{i}.example.test" for i in range(30)]


def rand_label(n=12):
    return "".join(random.choices(string.ascii_lowercase + string.digits, k=n))


async def one_query(server, src, name, kind, results, t0, timeout):
    q = dns.message.make_query(name, "A")
    sent = time.monotonic() - t0
    try:
        r = await dns.asyncquery.udp(q, server[0], port=server[1],
                                     source=src, timeout=timeout,
                                     ignore_unexpected=True)
        ok = r.rcode() == dns.rcode.NOERROR and bool(r.answer)
    except (dns.exception.DNSException, OSError):
        ok = False
    results.append((sent, kind, ok))


async def sender(server, src, rate, start, stop, pick, results, t0, timeout):
    await asyncio.sleep(start)
    tasks, nxt = [], time.monotonic()
    end = t0 + stop
    while time.monotonic() < end:
        name, kind = pick()
        tasks.append(asyncio.ensure_future(
            one_query(server, src, name, kind, results, t0, timeout)))
        nxt += 1 / rate
        await asyncio.sleep(max(0, nxt - time.monotonic()))
    await asyncio.gather(*tasks)


def legit_pick(new_ratio):
    def pick():
        if random.random() < new_ratio:
            return f"{rand_label()}.example.test", "legit_new"
        return random.choice(POPULAR), "legit_popular"
    return pick


def bot_pick():
    return f"{rand_label()}.example.test", "attack"


async def main():
    p = argparse.ArgumentParser()
    p.add_argument("--server", default="127.0.0.1:5300")
    p.add_argument("--clients", type=int, default=5)
    p.add_argument("--client-qps", type=float, default=10)
    p.add_argument("--new-ratio", type=float, default=0.2)
    p.add_argument("--bots", type=int, default=4)
    p.add_argument("--bot-qps", type=float, default=100)
    p.add_argument("--warmup", type=float, default=15)
    p.add_argument("--attack", type=float, default=20)
    p.add_argument("--timeout", type=float, default=2.0)
    a = p.parse_args()

    ip, port = a.server.split(":")
    server = (ip, int(port))
    results, t0 = [], time.monotonic()
    total = a.warmup + a.attack
    jobs = [sender(server, f"127.0.0.{11 + i}", a.client_qps, 0, total,
                   legit_pick(a.new_ratio), results, t0, a.timeout)
            for i in range(a.clients)]
    jobs += [sender(server, f"127.0.0.{101 + i}", a.bot_qps, a.warmup, total,
                    bot_pick, results, t0, a.timeout)
             for i in range(a.bots)]
    await asyncio.gather(*jobs)

    summary = {}
    for kind in ("legit_popular", "legit_new", "attack"):
        sel = [ok for t, k, ok in results if k == kind and t >= a.warmup]
        summary[kind] = {"sent": len(sel),
                         "success_ratio": round(sum(sel) / len(sel), 3) if sel else None}
    print(json.dumps(summary))


if __name__ == "__main__":
    asyncio.run(main())
