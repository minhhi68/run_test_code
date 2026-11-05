"""
Prototype resolver with priority scheduling for random subdomain attacks.

Runs as a caching forwarder in front of an authoritative server:
    clients -> [this resolver] -> authoritative

Modes:
    fifo      baseline: one FIFO queue (behaves like a plain resolver)
    priority  proposed: known names -> high queue, unseen names -> low queue
              (low queue ordered by client history score)
"""
import argparse
import asyncio
import heapq
import itertools
import time
from collections import deque

import dns.asyncquery
import dns.exception
import dns.message
import dns.rcode

# ---------------- Parameters (initial values, tuned by experiments) ----------
KNOWN_MIN_CLIENTS = 2        # name is "known" after NOERROR from >= 2 clients
KNOWN_EXPIRE = 24 * 3600     # forget a name not queried for 24 h
CLIENT_WINDOW = 600          # client score recomputed every 10 min
NEW_CLIENT_SCORE = 0.5       # score of a client with no history
DETECT_WINDOW = 2.0          # attack detector window (s)
TIMEOUT_THRESHOLD = 0.2      # attack ON if timeout ratio > 20 %
CALM_WINDOWS = 5             # attack OFF after 5 calm windows in a row
HIGH_WEIGHT, LOW_WEIGHT = 4, 1   # 80 / 20 split, work-conserving
UPSTREAM_TIMEOUT = 1.0       # upstream query timeout (s)
MAX_INFLIGHT = 50            # max outstanding upstream queries
MAX_QUEUE = 1000             # per-queue size; full -> SERVFAIL


def now():
    return time.monotonic()


class KnownNames:
    """Names resolved with NOERROR, asked by >= KNOWN_MIN_CLIENTS clients."""

    def __init__(self):
        self.names = {}  # name -> [set(client_ip), last_seen]

    def is_known(self, name):
        e = self.names.get(name)
        return e is not None and len(e[0]) >= KNOWN_MIN_CLIENTS

    def learn(self, name, client):
        e = self.names.setdefault(name, [set(), now()])
        if len(e[0]) < KNOWN_MIN_CLIENTS:
            e[0].add(client)
        e[1] = now()

    def cleanup(self):
        limit = now() - KNOWN_EXPIRE
        for n in [n for n, e in self.names.items() if e[1] < limit]:
            del self.names[n]


class ClientHistory:
    """Score = successful / total queries in the last finished window."""

    def __init__(self):
        self.count = {}   # client -> [ok, total]
        self.score_of = {}

    def record(self, client, ok):
        c = self.count.setdefault(client, [0, 0])
        c[0] += ok
        c[1] += 1

    def score(self, client):
        return self.score_of.get(client, NEW_CLIENT_SCORE)

    def roll_window(self):
        for client, (ok, total) in self.count.items():
            if total:
                self.score_of[client] = ok / total
        self.count = {}


class AttackDetector:
    """Attack ON when upstream timeout ratio > threshold in a window."""

    def __init__(self):
        self.attack = False
        self.sent = self.timeouts = self.calm = 0

    def record(self, timed_out):
        self.sent += 1
        self.timeouts += timed_out

    def tick(self):
        ratio = self.timeouts / self.sent if self.sent else 0.0
        if ratio > TIMEOUT_THRESHOLD:
            self.attack, self.calm = True, 0
        elif self.attack:
            self.calm += 1
            if self.calm >= CALM_WINDOWS:
                self.attack = False
        self.sent = self.timeouts = 0
        return ratio


class Scheduler:
    def __init__(self, mode):
        self.mode = mode
        self.high = deque()
        self.low = []                 # heap of (-score, seq, item)
        self.seq = itertools.count()
        self.turn = 0                 # position in the 4:1 pattern
        self.ready = asyncio.Event()

    def put(self, item, known, score):
        if self.mode == "fifo" or known:
            if len(self.high) >= MAX_QUEUE:
                return False
            self.high.append(item)
        else:
            if len(self.low) >= MAX_QUEUE:
                return False
            heapq.heappush(self.low, (-score, next(self.seq), item))
        self.ready.set()
        return True

    def get(self):
        """Weighted 4:1 round, work-conserving. None if both empty."""
        want_high = self.turn < HIGH_WEIGHT
        self.turn = (self.turn + 1) % (HIGH_WEIGHT + LOW_WEIGHT)
        if (want_high and self.high) or not self.low:
            return self.high.popleft() if self.high else None
        return heapq.heappop(self.low)[2]


class Resolver(asyncio.DatagramProtocol):
    def __init__(self, upstream, mode):
        self.upstream = upstream      # (ip, port)
        self.known = KnownNames()
        self.history = ClientHistory()
        self.detector = AttackDetector()
        self.sched = Scheduler(mode)
        self.cache = {}               # (qname, qtype) -> (response, expiry)
        self.inflight = asyncio.Semaphore(MAX_INFLIGHT)

    # ---- client side ----
    def connection_made(self, transport):
        self.transport = transport

    def datagram_received(self, data, addr):
        asyncio.ensure_future(self.handle(data, addr))

    async def handle(self, data, addr):
        try:
            q = dns.message.from_wire(data)
        except dns.exception.DNSException:
            return
        client = addr[0]
        name = q.question[0].name.to_text().lower()
        key = (name, q.question[0].rdtype)

        hit = self.cache.get(key)
        if hit and hit[1] > now():
            resp = dns.message.from_wire(hit[0])
            ok = True
        else:
            fut = asyncio.get_running_loop().create_future()
            known = self.known.is_known(name)
            if self.sched.put((q, fut), known, self.history.score(client)):
                resp = await fut
            else:
                resp = None
            if resp is not None and resp.rcode() == dns.rcode.NOERROR and resp.answer:
                ok = True
                ttl = min(r.ttl for r in resp.answer)
                self.cache[key] = (resp.to_wire(), now() + ttl)
            else:
                ok = False

        # learning only outside attack mode
        if not self.detector.attack:
            self.history.record(client, ok)
            if ok:
                self.known.learn(name, client)

        if resp is None:
            resp = dns.message.make_response(q)
            resp.set_rcode(dns.rcode.SERVFAIL)
        resp.id = q.id
        self.transport.sendto(resp.to_wire(), addr)

    # ---- upstream side ----
    async def dispatcher(self):
        while True:
            await self.inflight.acquire()
            item = self.sched.get()
            while item is None:
                self.sched.ready.clear()
                await self.sched.ready.wait()
                item = self.sched.get()
            asyncio.ensure_future(self.send_upstream(*item))

    async def send_upstream(self, q, fut):
        try:
            resp = await dns.asyncquery.udp(
                q, self.upstream[0], port=self.upstream[1],
                timeout=UPSTREAM_TIMEOUT, ignore_unexpected=True)
            self.detector.record(False)
        except (dns.exception.DNSException, OSError):
            resp = None
            self.detector.record(True)
        finally:
            self.inflight.release()
        if not fut.done():
            fut.set_result(resp)

    async def housekeeping(self, log):
        t_window = now()
        while True:
            await asyncio.sleep(DETECT_WINDOW)
            ratio = self.detector.tick()
            if now() - t_window >= CLIENT_WINDOW:
                self.history.roll_window()
                self.known.cleanup()
                t_window = now()
            if log:
                print(f"[{time.strftime('%H:%M:%S')}] attack={self.detector.attack} "
                      f"timeout_ratio={ratio:.2f} high_q={len(self.sched.high)} "
                      f"low_q={len(self.sched.low)} known={sum(self.known.is_known(n) for n in self.known.names)}",
                      flush=True)


async def main():
    global CLIENT_WINDOW
    p = argparse.ArgumentParser()
    p.add_argument("--listen", default="127.0.0.1:5300")
    p.add_argument("--upstream", default="127.0.0.1:5301")
    p.add_argument("--mode", choices=["fifo", "priority"], default="priority")
    p.add_argument("--client-window", type=float, default=CLIENT_WINDOW,
                   help="client score window in seconds (shorten for tests)")
    p.add_argument("--log", action="store_true")
    a = p.parse_args()
    CLIENT_WINDOW = a.client_window

    lip, lport = a.listen.split(":")
    uip, uport = a.upstream.split(":")
    r = Resolver((uip, int(uport)), a.mode)
    loop = asyncio.get_running_loop()
    await loop.create_datagram_endpoint(lambda: r, local_addr=(lip, int(lport)))
    print(f"resolver mode={a.mode} on {a.listen} -> {a.upstream}", flush=True)
    await asyncio.gather(r.dispatcher(), r.housekeeping(a.log))


if __name__ == "__main__":
    asyncio.run(main())
