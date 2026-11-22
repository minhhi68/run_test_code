"""Generate slides 2-6 of the 6th progress report in the style of the 5th report."""
from xml.sax.saxutils import escape

EMU = 914400
NAVY, TEAL, DARK, GREY, MID = "333399", "008B8B", "1F1F1F", "595959", "808080"
TINT, TEAL_TINT, CARD = "EEEEF7", "E6F4F4", "F2F2F2"
L, W = 0.45, 9.1          # content left edge and width (inches)

HEAD = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
        '<p:sld xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" '
        'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" '
        'xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main"><p:cSld><p:spTree>'
        '<p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr>'
        '<p:grpSpPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="0" cy="0"/><a:chOff x="0" y="0"/>'
        '<a:chExt cx="0" cy="0"/></a:xfrm></p:grpSpPr>')
TAIL = ('</p:spTree></p:cSld><p:clrMapOvr><a:masterClrMapping/></p:clrMapOvr></p:sld>')
STYLE = ('<p:style><a:lnRef idx="1"><a:schemeClr val="accent1"/></a:lnRef><a:fillRef idx="3">'
         '<a:schemeClr val="accent1"/></a:fillRef><a:effectRef idx="2"><a:schemeClr val="accent1"/>'
         '</a:effectRef><a:fontRef idx="minor"><a:schemeClr val="lt1"/></a:fontRef></p:style>')


def e(v):
    return int(round(v * EMU))


class Slide:
    def __init__(self, title, num, lead):
        self.n = 3
        self.parts = [
            '<p:sp><p:nvSpPr><p:cNvPr id="2" name="Title"/><p:cNvSpPr><a:spLocks noGrp="1"/></p:cNvSpPr>'
            '<p:nvPr><p:ph type="title"/></p:nvPr></p:nvSpPr><p:spPr/><p:txBody><a:bodyPr/><a:lstStyle/>'
            f'<a:p><a:r><a:rPr lang="en-US" altLang="ja-JP" dirty="0"/><a:t>{escape(title)}</a:t></a:r></a:p></p:txBody></p:sp>',
            '<p:sp><p:nvSpPr><p:cNvPr id="3" name="Slide number"/><p:cNvSpPr><a:spLocks noGrp="1"/></p:cNvSpPr>'
            '<p:nvPr><p:ph type="sldNum" sz="quarter" idx="11"/></p:nvPr></p:nvSpPr><p:spPr/><p:txBody><a:bodyPr/>'
            '<a:lstStyle/><a:p><a:fld id="{77CF89B9-20DF-48C4-93EE-BEB19D29513E}" type="slidenum">'
            f'<a:rPr lang="en-US" altLang="ja-JP"/><a:t>{num}</a:t></a:fld><a:endParaRPr lang="en-US" altLang="ja-JP"/></a:p></p:txBody></p:sp>',
        ]
        self.text(L, 0.95, W, 0.4, [[(lead, 16, NAVY, "b")]], name="Lead")

    def _id(self):
        self.n += 1
        return self.n

    @staticmethod
    def paras(ps, align="l", space=300):
        out = []
        for p in ps:
            bullet = False
            if isinstance(p, dict):
                bullet, p = p.get("bullet", False), p["runs"]
            ppr = (f'<a:pPr marL="171450" indent="-171450" algn="{align}"><a:spcAft><a:spcPts val="{space}"/></a:spcAft>'
                   '<a:buFont typeface="Arial"/><a:buChar char="&#8226;"/></a:pPr>' if bullet else
                   f'<a:pPr algn="{align}"><a:spcAft><a:spcPts val="{space}"/></a:spcAft><a:buNone/></a:pPr>')
            runs = ""
            for text, sz, color, fmt in p:
                runs += (f'<a:r><a:rPr lang="en-US" sz="{sz * 100}" b="{1 if "b" in fmt else 0}" i="{1 if "i" in fmt else 0}" dirty="0">'
                         f'<a:solidFill><a:srgbClr val="{color}"/></a:solidFill><a:latin typeface="Arial"/>'
                         f'<a:cs typeface="Arial"/></a:rPr><a:t xml:space="preserve">{escape(text)}</a:t></a:r>')
            out.append(f'<a:p>{ppr}{runs}</a:p>')
        return "".join(out)

    def text(self, x, y, w, h, ps, name="Text", align="l", anchor="t", space=300):
        i = self._id()
        self.parts.append(
            f'<p:sp><p:nvSpPr><p:cNvPr id="{i}" name="{escape(name)}"/><p:cNvSpPr txBox="1"/><p:nvPr/></p:nvSpPr>'
            f'<p:spPr><a:xfrm><a:off x="{e(x)}" y="{e(y)}"/><a:ext cx="{e(w)}" cy="{e(h)}"/></a:xfrm>'
            '<a:prstGeom prst="rect"><a:avLst/></a:prstGeom><a:noFill/></p:spPr>'
            f'<p:txBody><a:bodyPr wrap="square" lIns="0" tIns="0" rIns="0" bIns="0" anchor="{anchor}"><a:noAutofit/></a:bodyPr>'
            f'<a:lstStyle/>{self.paras(ps, align, space)}</p:txBody></p:sp>')

    def box(self, x, y, w, h, fill=None, line=None, geom="roundRect", ps=None, name="Box",
            lw=15875, align="ctr", anchor="ctr", inset=0.08):
        i = self._id()
        fill_x = f'<a:solidFill><a:srgbClr val="{fill}"/></a:solidFill>' if fill else '<a:noFill/>'
        line_x = (f'<a:ln w="{lw}"><a:solidFill><a:srgbClr val="{line}"/></a:solidFill></a:ln>' if line
                  else '<a:ln><a:noFill/></a:ln>')
        adj = '<a:gd name="adj" fmla="val 8000"/>' if geom == "roundRect" else ""
        body = self.paras(ps, align) if ps else '<a:p><a:endParaRPr lang="en-US"/></a:p>'
        ins = e(inset)
        self.parts.append(
            f'<p:sp><p:nvSpPr><p:cNvPr id="{i}" name="{escape(name)}"/><p:cNvSpPr/><p:nvPr/></p:nvSpPr>'
            f'<p:spPr><a:xfrm><a:off x="{e(x)}" y="{e(y)}"/><a:ext cx="{e(w)}" cy="{e(h)}"/></a:xfrm>'
            f'<a:prstGeom prst="{geom}"><a:avLst>{adj}</a:avLst></a:prstGeom>{fill_x}{line_x}<a:effectLst/></p:spPr>{STYLE}'
            f'<p:txBody><a:bodyPr wrap="square" lIns="{ins}" tIns="{ins}" rIns="{ins}" bIns="{ins}" rtlCol="0" anchor="{anchor}"/>'
            f'<a:lstStyle/>{body}</p:txBody></p:sp>')

    def badge(self, x, y, label, color=NAVY, d=0.36, sz=12):
        self.box(x, y, d, d, fill=color, geom="ellipse", inset=0, name=f"Badge {label}",
                 ps=[[(label, sz, "FFFFFF", "b")]])

    def arrow(self, x1, y1, x2, y2, name="Arrow"):
        i = self._id()
        flip = (' flipH="1"' if x2 < x1 else "") + (' flipV="1"' if y2 < y1 else "")
        self.parts.append(
            f'<p:cxnSp><p:nvCxnSpPr><p:cNvPr id="{i}" name="{name}"/><p:cNvCxnSpPr/><p:nvPr/></p:nvCxnSpPr>'
            f'<p:spPr><a:xfrm{flip}><a:off x="{e(min(x1, x2))}" y="{e(min(y1, y2))}"/>'
            f'<a:ext cx="{e(abs(x2 - x1))}" cy="{e(abs(y2 - y1))}"/></a:xfrm><a:prstGeom prst="line"><a:avLst/></a:prstGeom>'
            f'<a:ln w="19050"><a:solidFill><a:srgbClr val="{MID}"/></a:solidFill><a:tailEnd type="triangle" w="med" len="med"/>'
            '</a:ln></p:spPr></p:cxnSp>')

    def xml(self):
        return HEAD + "".join(self.parts) + TAIL


def R(text, sz=13, color=DARK, fmt=""):
    return (text, sz, color, fmt)


def B(*runs):
    return {"bullet": True, "runs": list(runs)}


# ---------------------------------------------------------------- slide 2
def slide2():
    s = Slide("Answering Last Week's Question", 2,
              "Each queue needs two concrete algorithms: one to schedule, one to drop")
    # question card
    s.box(L, 1.5, W, 0.78, fill=CARD, name="Question card")
    s.text(L + 0.25, 1.62, W - 0.5, 0.65, [
        [R("Sensei's question (11/17)", 11, GREY, "b")],
        [R("“Consider the concrete algorithms for each queue, and the possible candidates for each.”", 14, DARK, "i")],
    ], name="Question text", space=200)

    # pipeline: Query -> {High, Low} -> Dispatcher -> Authoritative
    y0 = 2.75
    s.box(L, y0 + 0.55, 1.45, 0.7, line=MID, name="Query", ps=[[R("Query", 12, DARK, "b")], [R("cache miss", 10)]])
    s.box(2.55, y0, 2.6, 0.8, fill=TEAL_TINT, line=TEAL, name="High queue",
          ps=[[R("High queue", 12, TEAL, "b"), R("  known names", 10)],
              [R("① scheduling   ② drop policy", 10, DARK)]])
    s.box(2.55, y0 + 1.0, 2.6, 0.8, fill=TINT, line=NAVY, name="Low queue",
          ps=[[R("Low queue", 12, NAVY, "b"), R("  unknown names", 10)],
              [R("① scheduling   ② drop policy", 10, DARK)]])
    s.box(5.75, y0 + 0.55, 1.5, 0.7, line=MID, name="Dispatcher", ps=[[R("Dispatcher", 12, DARK, "b")], [R("4 : 1 (kept)", 10)]])
    s.box(7.85, y0 + 0.55, 1.7, 0.7, line=MID, name="Authoritative", ps=[[R("Authoritative", 12, DARK, "b")], [R("100 qps", 10)]])
    s.arrow(L + 1.45, y0 + 0.9, 2.55, y0 + 0.4, "Arrow q-high")
    s.arrow(L + 1.45, y0 + 0.9, 2.55, y0 + 1.4, "Arrow q-low")
    s.arrow(5.15, y0 + 0.4, 5.75, y0 + 0.9, "Arrow high-d")
    s.arrow(5.15, y0 + 1.4, 5.75, y0 + 0.9, "Arrow low-d")
    s.arrow(7.25, y0 + 0.9, 7.85, y0 + 0.9, "Arrow d-auth")

    # two decision cards
    y1, cw = 4.85, (W - 0.3) / 2
    for k, (badge, head, q, rules) in enumerate([
        ("①", "Scheduling", "Which waiting query goes upstream next?",
         "Last week: rule 3 (prevent starvation)"),
        ("②", "Drop policy (queue management)", "Which query is dropped: when full, or when too old?",
         "Last week: rule 1 (evict) and rule 2 (drop stale)"),
    ]):
        x = L + k * (cw + 0.3)
        s.box(x, y1, cw, 1.3, fill=TINT, name=f"Decision {k + 1}")
        s.text(x + 0.25, y1 + 0.15, cw - 0.4, 1.05, [
            [R(badge + " " + head, 14, NAVY, "b")],
            [R(q, 12)],
            [R(rules, 10, GREY, "i")],
        ], name=f"Decision {k + 1} text", space=300)
    s.text(L, 6.3, W, 0.3, [[R("Last week's three rules were these two decisions mixed together; "
                                "next slides give two candidates for each queue", 11, GREY)]], name="Note")
    return s


# ---------------------------------------------------------------- comparison slide helper
def compare(s, y, rows, a_title, b_title, h_row=0.62, label_w=1.55):
    """rows: list of (label, A text runs-list, B text runs-list)."""
    col = (W - label_w - 0.3) / 2
    xa, xb = L + label_w + 0.15, L + label_w + 0.3 + col
    n = len(rows)
    total = 0.5 + n * h_row + 0.1
    s.box(xa, y, col, total, fill=CARD, name="Column A")
    s.box(xb, y, col, total, fill=TINT, line=NAVY, name="Column B")
    s.text(xa + 0.2, y + 0.12, col - 0.3, 0.35, [[R(a_title, 13, GREY, "b")]], name="A title")
    s.text(xb + 0.2, y + 0.12, col - 0.3, 0.35, [[R(b_title, 13, NAVY, "b")]], name="B title")
    for k, (label, a, b) in enumerate(rows):
        ry = y + 0.5 + k * h_row
        s.text(L, ry + 0.06, label_w, h_row - 0.06, [[R(label, 12, DARK, "b")]], name=f"Row {k + 1} label")
        s.text(xa + 0.2, ry + 0.06, col - 0.35, h_row - 0.06, a, name=f"Row {k + 1} A", space=100)
        s.text(xb + 0.2, ry + 0.06, col - 0.35, h_row - 0.06, b, name=f"Row {k + 1} B", space=100)
    return y + total


# ---------------------------------------------------------------- slide 3
def slide3():
    s = Slide("High Queue: Candidates", 3,
              "Known names, trusted traffic, short queue: keep it simple, add only a time limit")
    s.badge(L, 1.55, "H", TEAL)
    s.text(L + 0.5, 1.58, W - 0.5, 0.35, [[R("High queue = names already resolved by ≥ 2 clients", 13, DARK)]],
           name="Scope")
    end = compare(s, 2.1, [
        ("① Scheduling", [[R("FIFO", 13, DARK, "b")], [R("first come, first served", 11, GREY)]],
         [[R("FIFO", 13, DARK, "b")], [R("unchanged", 11, GREY)]]),
        ("② Drop policy", [[R("Tail drop", 13, DARK, "b")], [R("reject new queries when full", 11, GREY)]],
         [[R("Tail drop + sojourn-time drop", 13, DARK, "b")],
          [R("drop if waited > 2 s (client timeout), CoDel-style", 11, GREY)]]),
    ], "Candidate A (current)", "Candidate B (to test)", h_row=0.8)

    y = end + 0.3
    s.box(L, y, W, 1.3, fill=CARD, name="Why card")
    s.text(L + 0.25, y + 0.15, W - 0.5, 1.3, [
        [R("Why keep FIFO here", 13, NAVY, "b")],
        B(R("Measured: during the attack the high queue held at most 32 queries; the low queue sat at its 1000 limit", 12)),
        B(R("So the order inside the high queue barely matters; a time limit only removes queries the client already gave up", 12)),
        B(R("Option kept in reserve: per-client round robin (DRR), if bots start asking known names", 12)),
    ], name="Why text", space=300)
    s.text(L, 6.35, W, 0.3, [[R("CoDel: Nichols et al., RFC 8289 (2018).  DRR: Shreedhar & Varghese, SIGCOMM 1995.  "
                                 "Queue sizes: priority-mode logs, 3 runs", 10, GREY)]], name="Refs")
    return s


# ---------------------------------------------------------------- slide 4
def slide4():
    s = Slide("Low Queue: Candidates", 4,
              "Attack and new legitimate names share this queue: the real choice is here")
    end = compare(s, 1.6, [
        ("① Scheduling",
         [[R("Strict priority by score", 13, DARK, "b")], [R("highest client score always first", 11, GREY)]],
         [[R("Score-weighted fair queueing", 13, DARK, "b")],
          [R("weighted DRR: share ∝ client score", 11, GREY)]]),
        ("② Drop when full",
         [[R("Push-out (evict)", 13, DARK, "b")], [R("higher score replaces lowest score", 11, GREY)]],
         [[R("Per-client quota", 13, DARK, "b")], [R("each client holds ≤ N queries", 11, GREY)]]),
        ("② Drop when old",
         [[R("Deadline drop", 13, DARK, "b")], [R("waited > 2 s → not sent upstream", 11, GREY)]],
         [[R("Deadline drop", 13, DARK, "b")], [R("same as A", 11, GREY)]]),
    ], "Candidate A (rules 1 + 2)", "Candidate B (to test)", h_row=0.68)

    y, cw = end + 0.3, (W - 0.3) / 2
    s.box(L, y, cw, 1.4, fill=CARD, name="A note")
    s.text(L + 0.22, y + 0.15, cw - 0.4, 1.5, [
        [R("A: already tested (3 runs)", 13, NAVY, "b")],
        B(R("New legitimate names: 39 % → 98 % success with push-out", 12)),
        B(R("Risk: low-score clients can starve", 12)),
    ], name="A note text", space=300)
    s.box(L + cw + 0.3, y, cw, 1.4, fill=TINT, name="B note")
    s.text(L + cw + 0.52, y + 0.15, cw - 0.4, 1.5, [
        [R("B: why it is worth testing", 13, NAVY, "b")],
        B(R("Every client keeps a share → no starvation, no need for rule 3", 12)),
        B(R("Quota caps a bot even if it earned a good score", 12)),
    ], name="B note text", space=300)
    s.text(L, 6.35, W, 0.3, [[R("Fair queueing: Demers et al., SIGCOMM 1989.  DRR: Shreedhar & Varghese, 1995.  "
                                 "Push-out: Kesselman et al., SIAM J. Comput. 2004", 10, GREY)]], name="Refs")
    return s


# ---------------------------------------------------------------- slide 5
def slide5():
    s = Slide("Related Work", 5,
              "Closest work filters by name; mine ranks queries by name and client history")
    rows = [
        ("Hasegawa et al., IEEE TNSM 2023", "FQDN allowlist at cache servers; non-listed names are dropped during an attack",
         "Mine lowers priority instead of dropping, so new legitimate names can still succeed", True),
        ("Takeuchi et al., IPSJ JIP 2016, 2017", "Detect and filter by features of the subdomain name",
         "Under a wildcard zone, attack names look like real ones; mine uses history, not name shape", False),
        ("ISC BIND fetch limits", "fetches-per-zone / fetches-per-server cap how many queries go upstream",
         "Limits how many, not which ones; mine decides which queries use the capacity", False),
    ]
    y = 1.5
    for k, (who, what, diff, hl) in enumerate(rows):
        s.box(L, y, W, 1.15, fill=TINT if hl else CARD, line=NAVY if hl else None, name=f"Work {k + 1}")
        s.text(L + 0.25, y + 0.14, 2.6, 0.95, [[R(who, 13, NAVY, "b")]], name=f"Work {k + 1} name")
        s.text(L + 3.05, y + 0.14, W - 3.3, 0.95, [
            [R(what, 12)],
            [R("→ " + diff, 12, NAVY, "b")],
        ], name=f"Work {k + 1} text", space=400)
        y += 1.3
    s.box(L, y + 0.05, W, 0.75, fill=CARD, name="Algorithms card")
    s.text(L + 0.25, y + 0.15, W - 0.5, 0.6, [
        [R("Queue algorithms I build on", 12, NAVY, "b")],
        [R("Fair queueing [Demers 1989], DRR [Shreedhar 1995], RED [Floyd 1993], CoDel [RFC 8289], push-out [Kesselman 2004]", 11)],
    ], name="Algorithms text", space=200)
    s.text(L, 6.4, W, 0.3, [[R("In my search so far, I have not found a resolver that ranks queries by both name history "
                                "and client history", 10, GREY, "i")]], name="Novelty note")
    return s


# ---------------------------------------------------------------- slide 6
def slide6():
    s = Slide("Next Week and Questions", 6,
              "Implement candidate B and compare A vs B for each queue on the same testbed")
    lw = 5.0
    steps = [
        ("1", "Deadline drop in both queues", "shared by A and B; also counts wasted upstream queries"),
        ("2", "Low queue B: weighted DRR + quota", "share ∝ client score; quota N to be tuned"),
        ("3", "Run A vs B, 10 runs each", "attack 2×–16× capacity; bots with good history"),
    ]
    y = 1.5
    for num, head, sub in steps:
        s.box(L, y, lw, 0.95, fill=TINT, name=f"Step {num}")
        s.badge(L + 0.2, y + 0.29, num)
        s.text(L + 0.75, y, lw - 0.9, 0.95, [[R(head, 13, DARK, "b")], [R(sub, 11, GREY)]],
               name=f"Step {num} text", space=200, anchor="ctr")
        y += 1.1
    s.box(L, y, lw, 1.0, fill=CARD, name="Metrics")
    s.text(L + 0.25, y + 0.12, lw - 0.4, 0.8, [
        [R("Metrics", 12, NAVY, "b")],
        [R("Success ratio (popular / new names), SERVFAIL rate, waiting time, wasted upstream queries", 11)],
    ], name="Metrics text", space=200)

    qx, qw = L + lw + 0.3, W - lw - 0.3
    s.box(qx, 1.5, qw, 4.3, fill=CARD, line=NAVY, name="Questions")
    s.text(qx + 0.25, 1.65, qw - 0.45, 4.0, [
        [R("Questions for your advice", 13, NAVY, "b")],
        [R("1. Is “scheduling + drop policy” per queue the right level of detail?", 13)],
        [R("2. For the low queue, is weighted fair queueing a good second candidate, or is there one you prefer?", 13)],
        [R("3. Should I also compare dispatcher ratios (4:1 vs strict priority), or keep 4:1 fixed for now?", 13)],
    ], name="Questions text", space=1800)
    return s


if __name__ == "__main__":
    import sys
    out = sys.argv[1]
    for n, f in [(2, slide2), (3, slide3), (4, slide4), (5, slide5), (6, slide6)]:
        with open(f"{out}/ppt/slides/slide{n}.xml", "w", encoding="utf-8") as fh:
            fh.write(f().xml())
    p = f"{out}/ppt/slides/slide1.xml"
    x = open(p, encoding="utf-8").read()
    x = x.replace("<a:t>Progress Report (5</a:t>", "<a:t>Progress Report (6</a:t>").replace(
        "<a:t>2026.11.17</a:t>", "<a:t>2026.11.23</a:t>")
    open(p, "w", encoding="utf-8").write(x)
