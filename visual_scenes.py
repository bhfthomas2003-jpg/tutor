"""Manim templates: PlotScene (graph), NumberLineScene, GeometryScene. Driven by JSON spec (env MANIM_SPEC)."""
import json, os, re, textwrap
import sympy as sp
from sympy.parsing.sympy_parser import parse_expr, standard_transformations, implicit_multiplication_application, convert_xor
from manim import *

spec = json.load(open(os.environ["MANIM_SPEC"])); V = spec.get("visual") or {}
_OK = re.compile(r"^[0-9A-Za-z+\-*/^().,\s]+$")
_X = sp.Symbol("x")

def fn(s):
    if not _OK.match(s) or len(s) > 200: raise ValueError("bad function")
    e = parse_expr(s, local_dict={"x": _X}, transformations=standard_transformations + (implicit_multiplication_application, convert_xor))
    f = sp.lambdify(_X, e, "numpy")
    return lambda t: float(f(t))

def ticks(line_pt, vals, direction):
    return [Text(f"{v:g}", font_size=16, color=GREY_B).next_to(line_pt(v), direction, buff=0.1) for v in vals]

class Base(Scene):
    def visual(self, aw, ah):
        return VGroup(), []

    def construct(self):
        self.camera.background_color = "#0e162d"
        W, H = config.frame_width, config.frame_height
        d = float(spec["duration"]); wrap = 52 if W > H else 28
        title = Text(spec["title"], font_size=40, color="#ffc107")
        if title.width > W - 1: title.scale_to_fit_width(W - 1)
        title.to_edge(UP); self.play(Write(title), run_time=0.8)
        aw, ah = W - 1, H - 4.4
        try: g, anims = self.visual(aw, ah)
        except Exception: g, anims = VGroup(), []
        r = 0
        if anims:
            if g.width > aw: g.scale_to_fit_width(aw)
            if g.height > ah: g.scale_to_fit_height(ah)
            g.next_to(title, DOWN, buff=0.3)
            r = min(2.5, d * 0.3); self.play(LaggedStart(*anims, lag_ratio=0.25), run_time=r)
        chunks = spec["chunks"] or [""]; tw = sum(max(len(c.split()), 1) for c in chunks)
        budget = max(d - 0.8 - r, 0.5) + 0.3; cap = None
        for c in chunks:
            if cap: self.remove(cap)
            if c:
                cap = Text(textwrap.fill(c, wrap), font_size=26, color=WHITE).to_edge(DOWN, buff=0.4)
                if cap.width > W - 0.6: cap.scale_to_fit_width(W - 0.6)
                cap.add_background_rectangle(color=BLACK, opacity=0.85, buff=0.12); self.add(cap)
            self.wait(budget * max(len(c.split()), 1) / tw)

class PlotScene(Base):
    def visual(self, aw, ah):
        xr, yr = V.get("x_range", [-5, 5]), V.get("y_range", [-5, 5])
        ax = Axes(x_range=[xr[0], xr[1], max(1, round((xr[1]-xr[0]) / 10))], y_range=[yr[0], yr[1], max(1, round((yr[1]-yr[0]) / 8))],
                  x_length=aw, y_length=ah, tips=False, axis_config={"color": GREY_B})
        grp = VGroup(ax); anims = [Create(ax)]
        xs = [v for v in range(int(xr[0]), int(xr[1]) + 1) if v != 0][:: max(1, round((xr[1]-xr[0]) / 10))]
        ys = [v for v in range(int(yr[0]), int(yr[1]) + 1) if v != 0][:: max(1, round((yr[1]-yr[0]) / 8))]
        grp.add(*ticks(lambda v: ax.c2p(v, 0), xs, DOWN), *ticks(lambda v: ax.c2p(0, v), ys, LEFT))
        cols = [YELLOW, GREEN, RED, BLUE]; leg = VGroup()
        for i, s in enumerate(V.get("functions", [])[:4]):
            try:
                gr = ax.plot(fn(s), x_range=[xr[0], xr[1]], color=cols[i], use_smoothing=False)
            except Exception: continue
            grp.add(gr); anims.append(Create(gr)); leg.add(Text("y = " + s, font_size=20, color=cols[i]))
        if len(leg):
            leg.arrange(DOWN, aligned_edge=LEFT, buff=0.1).move_to(ax.get_corner(UL), aligned_edge=UL).shift(DOWN * 0.1 + RIGHT * 0.1); grp.add(leg); anims.append(FadeIn(leg))
        for p in V.get("points", [])[:8]:
            dot = Dot(ax.c2p(p[0], p[1]), color=WHITE); lab = Text(f"({p[0]:g}, {p[1]:g})", font_size=18).next_to(dot, UR, buff=0.05)
            grp.add(dot, lab); anims.append(FadeIn(VGroup(dot, lab)))
        return grp, anims

class NumberLineScene(Base):
    def visual(self, aw, ah):
        a, b = V.get("range", [-5, 5]); step = 1 if b - a <= 14 else (b - a) // 10
        nl = NumberLine(x_range=[a, b, step], length=aw, include_numbers=False, color=GREY_B)
        grp = VGroup(nl, *ticks(nl.n2p, range(int(a), int(b) + 1, step), DOWN)); anims = [Create(nl)]
        cl = lambda v: min(max(float(v) if v is not None else a, a), b)
        for iv in V.get("intervals", [])[:4]:
            lo, hi = iv.get("a"), iv.get("b"); closed = iv.get("closed", [True, True])
            seg = Line(nl.n2p(cl(lo if lo is not None else a)), nl.n2p(cl(hi if hi is not None else b)), color=YELLOW, stroke_width=8)
            grp.add(seg); anims.append(Create(seg))
            for v, c in ((lo, closed[0]), (hi, closed[1])):
                if v is None: continue
                dt = Dot(nl.n2p(cl(v)), color=YELLOW, radius=0.1); 
                if not c: dt.set_fill(opacity=0).set_stroke(YELLOW, 3)
                grp.add(dt); anims.append(FadeIn(dt))
        for p in V.get("points", [])[:8]:
            dt = Dot(nl.n2p(cl(p["v"])), color=RED); lab = Text(str(p.get("label", p["v"])), font_size=20, color=RED).next_to(dt, UP, buff=0.15)
            grp.add(dt, lab); anims.append(FadeIn(VGroup(dt, lab)))
        return grp, anims

class GeometryScene(Base):
    def visual(self, aw, ah):
        P = {k: (float(v[0]), float(v[1])) for k, v in V.get("points", {}).items()}
        circs = []
        for c in V.get("circles", [])[:4]:
            o = P[c["center"]]; r = c["r"] if "r" in c else ((P[c["through"]][0]-o[0])**2 + (P[c["through"]][1]-o[1])**2) ** .5
            circs.append((o, float(r)))
        xs = [p[0] for p in P.values()] + [o[0] + s * r for o, r in circs for s in (-1, 1)]
        ys = [p[1] for p in P.values()] + [o[1] + s * r for o, r in circs for s in (-1, 1)]
        cx, cy = (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2
        sc = min(aw / max(max(xs) - min(xs), 1e-6), ah / max(max(ys) - min(ys), 1e-6))
        m = lambda p: np.array([(p[0] - cx) * sc, (p[1] - cy) * sc, 0])
        grp, dots, segs, cs = VGroup(), [], [], []
        mid = sum((m(p) for p in P.values()), np.zeros(3)) / max(len(P), 1)
        for k, p in P.items():
            v = m(p) - mid; v = v / (np.linalg.norm(v) or 1)
            dt = Dot(m(p), color=WHITE); lb = Text(k, font_size=24, color=YELLOW).move_to(m(p) + v * 0.35)
            dots.append(FadeIn(VGroup(dt, lb))); grp.add(dt, lb)
        for s in V.get("segments", [])[:20]:
            a, b = (s[0], s[1]) if isinstance(s, (list, str)) else (s[0], s[1])
            ln = Line(m(P[a]), m(P[b]), color=BLUE_B); grp.add(ln); segs.append(Create(ln))
        for o, r in circs:
            c = Circle(radius=r * sc, color=GREEN).move_to(m(o)); grp.add(c); cs.append(Create(c))
        return grp, dots + segs + cs
