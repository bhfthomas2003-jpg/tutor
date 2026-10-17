"""Manim template 'steps': title, math lines revealed one by one, timed subtitles. Driven by a JSON spec (env MANIM_SPEC)."""
import json, os, textwrap
from manim import *

spec = json.load(open(os.environ["MANIM_SPEC"]))

class StepsScene(Scene):
    def construct(self):
        self.camera.background_color = "#0e162d"
        W, H = config.frame_width, config.frame_height
        wrap = 52 if W > H else 28
        d = float(spec["duration"]); lead = 0.8
        title = Text(spec["title"], font_size=40, color="#ffc107")
        if title.width > W - 1: title.scale_to_fit_width(W - 1)
        title.to_edge(UP)
        self.play(Write(title), run_time=lead)
        lines = [Text(l, font_size=34, color="#f0f4ff") for l in spec["math"]]
        grp = VGroup(*lines).arrange(DOWN, aligned_edge=LEFT, buff=0.35)
        if lines:
            if grp.width > W - 1: grp.scale_to_fit_width(W - 1)
            grp.next_to(title, DOWN, buff=0.6).to_edge(LEFT, buff=0.5)
        chunks = spec["chunks"] or [""]
        total_w = sum(max(len(c.split()), 1) for c in chunks)
        budget = max(d - lead, 0.5) + 0.3
        cap = None
        for i, c in enumerate(chunks):
            dur = budget * max(len(c.split()), 1) / total_w
            if cap: self.remove(cap)
            if c:
                cap = Text(textwrap.fill(c, wrap), font_size=26, color=WHITE).to_edge(DOWN, buff=0.4)
                if cap.width > W - 0.6: cap.scale_to_fit_width(W - 0.6)
                cap.add_background_rectangle(color=BLACK, opacity=0.85, buff=0.12)
                self.add(cap)
            used = 0
            if lines:  # reveal the next share of math lines at each chunk
                upto = -(-(i + 1) * len(lines) // len(chunks)); prev = -(-i * len(lines) // len(chunks))
                for ln in lines[prev:upto]:
                    self.play(FadeIn(ln, shift=RIGHT * 0.2), run_time=0.5); used += 0.5
            self.wait(max(dur - used, 0.05))
