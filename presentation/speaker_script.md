# 6th Progress Report: speaker script

About 8 minutes in total. The **bold** parts are the key sentences: if you forget everything else, say those.

---

## Slide 1: Title (15 s)

> Good afternoon. This is my sixth progress report. Today I will answer the question from the last meeting.

---

## Slide 2: Answering Last Week's Question (1.5 min)

> Last week, sensei asked me to consider the concrete algorithm for each queue, and the possible candidates.
>
> **I realised that each queue needs two separate algorithms.**
> The first is **scheduling**: which waiting query goes upstream next.
> The second is the **drop policy**, also called queue management: which query is dropped, either when the queue is full or when the query is too old.
>
> In the diagram, both the high queue and the low queue have these two decisions. The dispatcher between them stays at four to one for now.
>
> Last week I showed three rules. Looking back, they were these two decisions mixed together. Rule 3, preventing starvation, is a scheduling decision. Rules 1 and 2, evict and drop stale queries, are drop policies.
>
> On the next two slides, I give two candidates for each queue.

---

## Slide 3: High Queue: Candidates (1.5 min)

> First, the high queue. It holds names already resolved by at least two clients, so the traffic is trusted.
>
> **Candidate A** is the current one: FIFO scheduling, and tail drop, which means new queries are rejected when the queue is full.
> **Candidate B** keeps FIFO, but adds a **sojourn-time drop**: if a query waited longer than the client timeout of two seconds, it is not sent upstream. This idea comes from CoDel, RFC 8289.
>
> Why keep FIFO? In my logs, during the attack the high queue held **at most 32 queries**, while the low queue was always at its limit of 1000. So the order inside the high queue barely matters. The time limit only removes queries the client has already given up on.
>
> If bots start asking known names in the future, I keep per-client round robin, DRR, as a reserve option.

---

## Slide 4: Low Queue: Candidates (2 min)

> The low queue is where the real choice is, because attack names and new legitimate names are in the same queue.
>
> **Candidate A** is rules 1 and 2 from last week: strict priority by client score, push-out when the queue is full, and a deadline drop for old queries.
> I already tested push-out in three runs: for new legitimate names, the success ratio went from **39 percent to 98 percent**. But strict priority has a risk: clients with a low score can starve.
>
> **Candidate B** is **score-weighted fair queueing**, implemented as weighted deficit round robin. Each client gets a share of the service proportional to its score. So a good client gets more, but nobody gets zero. This removes starvation by design, so rule 3 is not needed.
> When the queue is full, B uses a **per-client quota**: each client can hold at most N queries in the queue. This limits a bot even if it earned a good score during warm-up.
> Both candidates keep the same deadline drop.
>
> These algorithms come from fair queueing by Demers and others, DRR by Shreedhar and Varghese, and push-out buffer management by Kesselman and others.

---

## Slide 5: Related Work (1.5 min)

> Here is related work, to show how my method differs.
>
> The closest work is **Hasegawa et al., IEEE TNSM 2023**. Cache servers keep an allowlist of names and drop other names during an attack. My method is similar in using known names, but **I lower the priority instead of dropping**, so new legitimate names can still succeed.
>
> **Takeuchi et al.** detect the attack from features of the subdomain name. But under a wildcard zone, attack names look like real names, so my method uses history instead of the shape of the name.
>
> BIND already has fetch limits. They limit *how many* queries go upstream, but not *which* ones. My method decides which queries use the capacity.
>
> In my search so far, I have not found a resolver that ranks queries by both name history and client history.

---

## Slide 6: Next Week and Questions (1 min, then discussion)

> Next week, I will implement candidate B and compare A and B on the same testbed.
> First, the deadline drop in both queues. Second, weighted DRR with a quota in the low queue. Third, ten runs for each, with attacks from two to sixteen times the capacity, including bots with good history.
> I will measure the success ratio, SERVFAIL rate, waiting time and wasted upstream queries.
>
> I have three questions for your advice. *(Read them from the slide.)*
>
> Thank you.

---

## Likely follow-up questions

| Question | Short answer |
|---|---|
| Why not just rate-limit each client? | Rate limiting caps every client equally, all the time, including good ones. Fair queueing only limits clients when the queue is busy, and still gives more to trusted clients. |
| What is N for the quota? | Not fixed yet. I will start around queue size ÷ number of active clients, and tune it in the experiments. |
| How does weighted DRR work? | Each client has its own small queue and a "deficit" counter. Every round, the counter grows by the client's weight (score), and the client sends queries while the counter is large enough. It's O(1) per query. |
| What if a bot gets a high score? | That is the bots-with-good-history scenario. The quota limits how much of the queue it can hold, and its score drops once its queries start failing. |
| Why drop at 2 s? | It's the client timeout in my testbed. After 2 s, the client has already given up, so the answer is wasted upstream capacity. |
| Is 39 % → 98 % reliable? | Only 3 runs, on one testbed. That's why next week's plan has 10 runs per setting. |

## Before you cite: things to verify

- Open **Hasegawa et al. 2023** and check the one-line summary. The earlier search only read the abstract.
- The "at most 32 queries" and "39 % → 98 %" numbers come from `results/` in the repo (3 runs, priority and evict modes).
