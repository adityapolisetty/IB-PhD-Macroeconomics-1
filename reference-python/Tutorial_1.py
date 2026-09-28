"""
Tutorial 1 -- Simulating the Solow model.

For the TA to walk through, and to hand out afterwards.

Students arrive having done the pre-work: they can write a loop, write a
function, make a plot, and run a script from a terminal. This session adds two
things and no more --- numpy arrays, and stepping a differential equation
forward --- and ends where Problem Set 1, Question 1(g) begins.

The model, from Lecture 1 and PS1 Q1(a):

    kdot = s f(k) - (delta + n) k,      f(k) = A k^alpha

Run:  python Tutorial_1.py
"""

import numpy as np
import matplotlib.pyplot as plt

# ======================================================================
# STEP 1.  Parameters and functions
# ----------------------------------------------------------------------
# Named variables, not numbers buried in the formulas. When you want to know
# what a higher saving rate does, you change one line and re-run.
# ======================================================================

ALPHA = 1 / 3
A = 1.0
S = 0.20
DELTA = 0.05
N = 0.01


def f(k):
    """Output per worker."""
    return A * k**ALPHA


def g(k):
    """
    The law of motion: how fast capital per worker is changing.

    This is the whole model. Everything below is a way of looking at it.
    """
    return S * f(k) - (DELTA + N) * k


# The steady state, from PS1 Q1(c). We know it in closed form here, which is
# convenient but unusual -- most of the models later in the course do not
# oblige, and we will have to find their steady states numerically.
k_star = (S * A / (DELTA + N)) ** (1 / (1 - ALPHA))
print(f"steady state:  k* = {k_star:.4f}")


# ======================================================================
# STEP 2.  Arrays, and the diagram from Q1(d)
# ----------------------------------------------------------------------
# np.linspace(a, b, n) gives n evenly spaced numbers from a to b, as an array.
# Arithmetic on an array applies to every element, so f(k_grid) evaluates the
# production function at all 400 points at once. That is the only new idea in
# this step -- if you prefer to write a loop instead, nothing here breaks.
# ======================================================================

k_grid = np.linspace(0.01, 2.5 * k_star, 400)

fig, axes = plt.subplots(1, 2, figsize=(11, 4.2))

# Left panel: the two curves whose crossing is the steady state.
axes[0].plot(k_grid, S * f(k_grid), lw=2, label=r"$s f(k)$")
axes[0].plot(k_grid, (DELTA + N) * k_grid, lw=2, label=r"$(\delta + n)k$")
axes[0].plot([k_star], [S * f(k_star)], "ko", ms=5, zorder=5)
axes[0].set_title("Saving against depreciation")

# Right panel: the same information as a phase line. Where g is positive,
# capital is rising; where negative, falling. The arrows in your sketch are
# just the sign of this curve.
axes[1].plot(k_grid, g(k_grid), lw=2, color="C3", label=r"$\dot k = g(k)$")
axes[1].axhline(0, color="0.5", lw=0.9)
axes[1].plot([k_star], [0], "ko", ms=5, zorder=5)
axes[1].set_title("The phase line")

for ax in axes:
    ax.axvline(k_star, color="0.6", lw=0.8, ls=":")
    ax.set_xlabel("$k$")
    ax.legend(frameon=False)
    ax.set_xlim(0, 2.5 * k_star)

fig.tight_layout()
fig.savefig("tutorial1_diagram.png", dpi=150)
print("wrote tutorial1_diagram.png")


# ======================================================================
# STEP 3.  Stepping the model forward
# ----------------------------------------------------------------------
# kdot = g(k) says capital changes by g(k) per unit of time. So over a short
# interval dt it changes by about dt * g(k):
#
#     k(t + dt) = k(t) + dt * g(k(t))
#
# That is the pre-work loop with a different line inside it.
# ======================================================================


def simulate(k0, T=200.0, dt=0.01):
    """Return the time grid and the path of k starting from k0."""
    t = np.arange(0.0, T + dt, dt)
    path = np.empty_like(t)
    k = k0
    for i in range(len(t)):
        path[i] = k
        k = k + dt * g(k)
    return t, path


t, path = simulate(k_star / 4)
print(f"from k0 = k*/4:  k(200) = {path[-1]:.4f}   (k* = {k_star:.4f})")


# ======================================================================
# STEP 4.  Convergence from anywhere, and choosing dt
# ======================================================================

fig, ax = plt.subplots(figsize=(6.6, 4.4))
for k0 in (0.1 * k_star, 0.5 * k_star, 1.5 * k_star, 2.2 * k_star):
    t, path = simulate(k0)
    ax.plot(t, path, lw=1.8, label=f"$k_0 = {k0 / k_star:.1f}\\,k^*$")
ax.axhline(k_star, color="0.4", lw=1.0, ls="--")
ax.text(2, k_star * 1.03, "$k^*$", color="0.3")
ax.set_xlabel("years")
ax.set_ylabel("$k$")
ax.set_title("Convergence from any starting point")
ax.legend(frameon=False)
fig.tight_layout()
fig.savefig("tutorial1_convergence.png", dpi=150)
print("wrote tutorial1_convergence.png")

# How do you know dt is small enough? You do not, in the abstract. You halve it
# and see whether the answer moves. When it stops moving, it is small enough.
print("\nk(50) starting from k*/4, as the step shrinks:")
previous = None
for dt in (2.0, 1.0, 0.5, 0.1, 0.01, 0.001):
    t, path = simulate(k_star / 4, T=50.0, dt=dt)
    moved = "" if previous is None else f"   (moved {abs(path[-1] - previous):.4f})"
    print(f"   dt = {dt:<6} -> {path[-1]:.4f}{moved}")
    previous = path[-1]
print("Each cut in dt moves the answer less than the last one did, and by the end")
print("it is barely moving at all. That is the only test you have, and it is enough.")

# ======================================================================
# Where this goes next
# ----------------------------------------------------------------------
# PS1 Q1(g) asks you to run this from k0 = k*/4 and k0 = 4k*, and compare the
# path against the linear approximation from Q1(f). You now have everything you
# need: simulate() gives the true path, and the approximation is one line.
# ======================================================================
