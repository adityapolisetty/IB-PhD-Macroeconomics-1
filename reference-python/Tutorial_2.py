"""
Tutorial 2 -- From hand-stepping to scipy, and from one equation to two.

For the TA to walk through, and to hand out afterwards.

Three steps:
  1. the Solow model again, this time handed to scipy, agreeing with last week;
  2. the household of PS1 Q3 written as a system of two equations;
  3. what goes wrong when the initial consumption is not the optimal one, and
     how to make the solver stop when it does.

Everything here is what PS1 Q3(f) asks for, so the session ends with the tools
in hand rather than the answer.

Run:  python Tutorial_2.py
"""

import numpy as np
from scipy.integrate import solve_ivp
import matplotlib.pyplot as plt

# ======================================================================
# STEP 1.  The same ODE, handed to a library
# ----------------------------------------------------------------------
# Last week: k <- k + dt * g(k), with dt chosen by us and checked by halving.
# scipy does the same job, but picks its own steps and controls the error.
#
# The signature is the only awkward part. solve_ivp wants a function of
# (t, y) even when t does not appear, and it hands back y as a 2-D array
# with one row per variable -- hence the [0] below.
# ======================================================================

ALPHA, A, S, DELTA, N = 1 / 3, 1.0, 0.20, 0.05, 0.01
k_star = (S * A / (DELTA + N)) ** (1 / (1 - ALPHA))


def solow(t, y):
    k = y[0]
    return [S * A * k**ALPHA - (DELTA + N) * k]


sol = solve_ivp(solow, [0.0, 200.0], [k_star / 4], dense_output=True)
print(f"STEP 1   k* = {k_star:.4f}")
print(f"         scipy:      k(50) = {sol.sol(50)[0]:.4f}")

# By hand, exactly as last week, for comparison.
k, dt = k_star / 4, 0.01
for _ in range(int(50 / dt)):
    k = k + dt * (S * A * k**ALPHA - (DELTA + N) * k)
print(f"         by hand:    k(50) = {k:.4f}")
print("         Same answer. From here on we let scipy do the stepping.")


# ======================================================================
# STEP 2.  Two equations instead of one
# ----------------------------------------------------------------------
# The household of PS1 Q3:
#
#     adot = r a + w - c        wealth accumulates what is not consumed
#     cdot = g c                the Euler equation, with g = (r - rho)/sigma
#
# Nothing changes structurally: the state is now a pair, so the function
# returns a pair. Order matters and is yours to choose -- fix it once and
# stay consistent, because every index below depends on it.
# ======================================================================

R, RHO, SIGMA, W, A0 = 0.05, 0.03, 2.0, 1.0, 1.0
G = (R - RHO) / SIGMA


def household(t, y):
    a, c = y
    return [R * a + W - c, G * c]


# Part (d) of Q3 gives the optimal initial consumption in closed form.
c0_star = (R - G) * (A0 + W / R)
print(f"\nSTEP 2   g = {G:.4f},  optimal c0 = {c0_star:.4f}")

sol = solve_ivp(household, [0.0, 200.0], [A0, c0_star], dense_output=True)
print(f"         {'t':>5}{'a(t)':>12}{'exp(-rt) a(t)':>16}")
for t_check in (0, 50, 100, 200):
    a_t = sol.sol(t_check)[0]
    print(f"         {t_check:>5}{a_t:>12.3f}{np.exp(-R * t_check) * a_t:>16.4f}")
print("         Assets grow by a factor of 135. Discounted assets go to zero.")
print("         Transversality is the second column, not the first.")


# ======================================================================
# STEP 3.  Getting c0 wrong, and stopping when it shows
# ----------------------------------------------------------------------
# An event is a function of (t, y) that solve_ivp watches for a sign change.
# Marking it terminal tells the solver to stop there. Here we watch for the
# household running out of wealth.
# ======================================================================


def assets_exhausted(t, y):
    return y[0]


assets_exhausted.terminal = True
assets_exhausted.direction = -1  # only on the way down, not on the way up

print("\nSTEP 3   perturbing c0 by one per cent:")
fig, ax = plt.subplots(figsize=(6.8, 4.4))

for label, c0, colour in [("1% too low", 0.99 * c0_star, "C0"),
                          ("optimal", c0_star, "k"),
                          ("1% too high", 1.01 * c0_star, "C3")]:
    # Tighter than the default. A path that grows exponentially magnifies
    # integration error along with everything else: at the default tolerance
    # the too-low path finishes about 1.5% away from the exact answer.
    s = solve_ivp(household, [0.0, 200.0], [A0, c0],
                  events=[assets_exhausted], dense_output=True,
                  rtol=1e-10, atol=1e-12)
    if s.t_events[0].size:
        print(f"         {label:<12} exhausted at t = {s.t_events[0][0]:.1f}")
    else:
        print(f"         {label:<12} a(200) = {s.y[0, -1]:>10,.1f}")
    t_grid = np.linspace(0.0, s.t[-1], 800)
    ax.plot(t_grid, s.sol(t_grid)[0], color=colour, lw=1.9, label=label)

ax.set_xlim(0, 200)
ax.set_ylim(-20, 200)
ax.set_xlabel("years")
ax.set_ylabel("$a(t)$")
ax.set_title("One per cent either way")
ax.legend(frameon=False)
fig.tight_layout()
fig.savefig("tutorial2_household.png", dpi=150)
print("         wrote tutorial2_household.png")

print()
print("         Notice the asymmetry. Too much consumption crosses zero, and a")
print("         crossing is something the solver can catch. Too little just")
print("         grows -- there is nothing to cross, so catching it means picking")
print("         a threshold yourself. Q3(f)(iii) asks why that matters.")

# ======================================================================
# Where this goes next
# ----------------------------------------------------------------------
# You now have everything PS1 Q3(f) needs. Next week the same three pieces --
# a system, an event, and a wrong initial guess -- become the shooting method,
# which finds the right guess when there is no closed form to tell you.
# ======================================================================
