"""Render a short Chapter 3 phase-plane film; browser code handles interaction."""
from pathlib import Path
import math
import os
import shutil

from manim import Axes, Arrow, Create, Dot, FadeIn, Line, MoveAlongPath, Scene, Text, VMobject, config, linear

ROOT = Path(__file__).resolve().parents[1]
MEDIA = Path(os.environ.get("MANIM_MEDIA_DIR", ROOT / ".cache" / "manim-media"))
config.media_dir = str(MEDIA)
config.pixel_width = 1280
config.pixel_height = 720
config.frame_rate = 30
config.background_color = "#FFFFFF"
config.disable_caching = True

ALPHA, DELTA, RHO, SIGMA = 1 / 3, .05, .03, 2
KS = (ALPHA / (DELTA + RHO)) ** (1 / (1 - ALPHA))
CS = KS ** ALPHA - DELTA * KS
FPP = ALPHA * (ALPHA - 1) * KS ** (ALPHA - 2)
NU = (RHO - math.sqrt(RHO * RHO - 4 * CS * FPP / SIGMA)) / 2
SLOPE = RHO - NU


def rhs(k, c):
    return k ** ALPHA - c - DELTA * k, c * (ALPHA * k ** (ALPHA - 1) - DELTA - RHO) / SIGMA


def rk4(k, c, h):
    a, b = rhs(k, c)
    d, e = rhs(k + h * a / 2, c + h * b / 2)
    f, g = rhs(k + h * d / 2, c + h * e / 2)
    j, l = rhs(k + h * f, c + h * g)
    return k + h * (a + 2*d + 2*f + j) / 6, c + h * (b + 2*e + 2*g + l) / 6


def stable_arm(sign):
    k, c = KS + sign * 1e-6, CS + sign * SLOPE * 1e-6
    points = [(k, c)]
    for _ in range(24000):
        k, c = rk4(k, c, -.02)
        if not (.1 < k < 19.5 and .02 < c < 2.55):
            break
        if len(points) % 7 == 0:
            points.append((k, c))
        else:
            points.append((k, c))
    return list(reversed(points[::5]))


class PhaseFilm(Scene):
    def construct(self):
        axes = Axes(x_range=[0, 19.5, 4], y_range=[0, 2.55, .5], x_length=11.5, y_length=5.5,
                    tips=False, axis_config={"color": "#8C98AA", "stroke_width": 2}).shift((0, -.25, 0))
        arrows = []
        for k in [1.2 + i * 1.25 for i in range(15)]:
            for c in [.25 + i * .32 for i in range(7)]:
                dk, dc = rhs(k, c)
                norm = math.hypot(dk / 19.5, dc / 2.55)
                x, y = dk / 19.5 / norm * .13, dc / 2.55 / norm * .13
                p = axes.c2p(k, c)
                arrows.append(Arrow(p - [x, y, 0], p + [x, y, 0], buff=0, stroke_width=1.3,
                                    max_tip_length_to_length_ratio=.25, color="#A8B3CD"))
        nullcline = axes.plot(lambda k: k ** ALPHA - DELTA * k, x_range=[0, 19.5, .06], color="#70879E", stroke_width=4)
        vertical = Line(axes.c2p(KS, 0), axes.c2p(KS, 2.55), color="#8495AD", stroke_width=3)
        vertical.set_stroke(opacity=.8)
        arms = []
        for sign in [-1, 1]:
            arm = VMobject(color="#0000CD", stroke_width=5)
            arm.set_points_smoothly([axes.c2p(k, c) for k, c in stable_arm(sign)])
            arms.append(arm)
        title = Text("One path reaches the steady state", font="Arial", font_size=33, color="#1D263C").to_edge((0, 1, 0), buff=.14)
        stable = Dot(axes.c2p(KS, CS), radius=.09, color="#0000CD")
        travel = VMobject()
        travel.set_points_smoothly([axes.c2p(k, c) for k, c in stable_arm(-1) if 4.25 <= k <= 8.45])
        economy = Dot(travel.get_start(), radius=.11, color="#111318")
        self.add(axes, *arrows)
        self.play(FadeIn(title), Create(nullcline), Create(vertical), run_time=1.2)
        self.play(Create(arms[0]), Create(arms[1]), FadeIn(stable), FadeIn(economy), run_time=1.2)
        self.play(MoveAlongPath(economy, travel), run_time=3.5, rate_func=linear)
        self.wait(.5)


if __name__ == "__main__":
    scene = PhaseFilm()
    scene.render()
    source = MEDIA / "videos" / "720p30" / "PhaseFilm.mp4"
    output = ROOT / "public" / "phase" / "saddle-path.mp4"
    output.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, output)
    print(output)
