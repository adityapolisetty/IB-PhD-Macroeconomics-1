"""Render the slider-controlled utility and AK films with Manim.

The five-second timeline is deliberately linear: the website maps a slider
position directly to the corresponding rendered frame. All output stays in AP.
"""

from __future__ import annotations

import math
import os
import subprocess
from pathlib import Path

from manim import (
    Axes, DashedLine, Dot, DOWN, LEFT, Line, Scene, Text, ValueTracker,
    always_redraw, config, linear,
)

ROOT = Path(__file__).resolve().parents[1]
MEDIA = Path(os.environ.get("MANIM_MEDIA_DIR", ROOT / ".cache" / "manim-media"))
OUTPUT = ROOT / "public" / "utility"
INK = "#262824"
MUTED = "#737782"
ACCENT = "#0000CD"
TANGENT = "#CB622D"
RUN_TIME = 5

config.media_dir = str(MEDIA)
config.pixel_width = 960
config.pixel_height = 540
config.frame_rate = 24
config.background_color = "#FFFFFF"
config.disable_caching = True
config.write_to_movie = True


def one_variable(family: str, c: float, parameter: float = 1) -> tuple[float, float]:
    if family == "linear":
        return c, 1
    if family == "log":
        return math.log(c), 1 / c
    if family == "crra":  # sigma = 2; normalised to u(1) = 0
        return 1 - 1 / c, 1 / c**2
    if family == "cara":  # a = 0.6
        return (1 - math.exp(-0.6 * c)) / 0.6, math.exp(-0.6 * c)
    if family == "quadratic":  # bliss point c = 1 / 0.35
        return c - 0.35 * c**2 / 2, 1 - 0.35 * c
    if family == "ak":
        return parameter * c, parameter
    raise ValueError(family)


class OneVariableSweep(Scene):
    family = "linear"
    parameter = 1

    def construct(self):
        limits = {
            "linear": (0, 8.5, 2),
            "log": (-2, 2.5, 1),
            "crra": (-3.5, 1.5, 1),
            "cara": (0, 2, 0.5),
            "quadratic": (-4, 2, 1),
            "ak": (0, 16.5, 4),
        }
        y0, y1, y_step = limits[self.family]
        axes = Axes(
            x_range=[0, 8, 2], y_range=[y0, y1, y_step],
            x_length=10.4, y_length=5.5, tips=False,
            axis_config={"color": MUTED, "stroke_width": 2},
        ).shift(LEFT * 0.25)
        curve = axes.plot(
            lambda x: one_variable(self.family, x, self.parameter)[0],
            x_range=[0.18 if self.family in {"log", "crra"} else 0, 8, 0.02],
            color=ACCENT, stroke_width=7, use_smoothing=False,
        )
        tracker = ValueTracker(0.5)

        def point():
            c = tracker.get_value()
            return axes.c2p(c, one_variable(self.family, c, self.parameter)[0])

        def tangent():
            c = tracker.get_value()
            u, mu = one_variable(self.family, c, self.parameter)
            half = 0.47
            return Line(axes.c2p(c - half, u - half * mu),
                        axes.c2p(c + half, u + half * mu),
                        color=TANGENT, stroke_width=5)

        guide = always_redraw(lambda: DashedLine(
            axes.c2p(tracker.get_value(), 0), point(),
            color=MUTED, dash_length=0.09, stroke_width=2,
        ))
        label_x = Text("capital  k" if self.family == "ak" else "consumption  c", font_size=25, color=INK).next_to(axes.x_axis, direction=DOWN, buff=0.55)
        label_y = Text("output  f(k)" if self.family == "ak" else "utility  u(c)", font_size=25, color=INK).rotate(math.pi / 2).next_to(axes.y_axis, direction=LEFT, buff=0.55)
        ticks = [Text(str(v), font_size=21, color=MUTED).next_to(axes.c2p(v, 0), DOWN, buff=0.13) for v in (0, 2, 4, 6, 8)]
        y_values = []
        candidate = math.ceil(y0 / y_step) * y_step
        while candidate <= y1:
            if abs(candidate) > 1e-9:
                y_values.append(round(candidate, 2))
            candidate += y_step
        y_ticks = [Text(f"{v:g}", font_size=21, color=MUTED).next_to(axes.c2p(0, v), LEFT, buff=0.13) for v in y_values]
        self.add(axes, *ticks, *y_ticks, curve, label_x, label_y, guide, always_redraw(tangent),
                 always_redraw(lambda: Dot(point(), radius=0.105, color=TANGENT)))
        self.play(tracker.animate.set_value(7.5), run_time=RUN_TIME, rate_func=linear)


def render(scene_class: type[Scene], name: str):
    scene_class.__name__ = name.replace("-", "_")
    scene = scene_class()
    scene.render()
    raw = Path(scene.renderer.file_writer.movie_file_path)
    OUTPUT.mkdir(parents=True, exist_ok=True)
    target = OUTPUT / f"{name}.mp4"
    # Frequent keyframes keep the slider responsive while seeking in the browser.
    subprocess.run([
        "ffmpeg", "-loglevel", "error", "-y", "-i", str(raw),
        "-an", "-c:v", "libx264", "-preset", "medium", "-crf", "24",
        "-g", "6", "-keyint_min", "6", "-sc_threshold", "0",
        "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(target),
    ], check=True)
    print(f"Rendered {target.name}: {target.stat().st_size:,} bytes")


if __name__ == "__main__":
    for family in ("linear", "log", "crra", "cara", "quadratic"):
        render(type(f"One_{family}", (OneVariableSweep,), {"family": family}), f"one-{family}")
    for step in range(2, 9):
        productivity = step / 4
        render(type(f"AK_{step}", (OneVariableSweep,), {"family": "ak", "parameter": productivity}),
               f"one-ak-{productivity:.2f}")
