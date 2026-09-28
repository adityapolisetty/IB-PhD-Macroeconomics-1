"""
Tutorial 3 -- The phase diagram, and shooting for the saddle path.

For the TA to walk through, and to hand out afterwards.

Four steps:
  1. why this model is the tractable one -- both mistakes cross an axis;
  2. the two loci, plotted;
  3. one guess too high and one too low, and what stops each of them;
  4. bisecting between the two to land on the saddle path.

The neoclassical growth model of Lecture 3 and PS2 Q2:

    cdot / c = [ f'(k) - delta - rho ] / sigma
    kdot     = f(k) - c - delta k,        f(k) = A k^alpha

Run:  python Tutorial_3.py
"""

import numpy as np
from scipy.integrate import solve_ivp
import matplotlib.pyplot as plt

# ======================================================================
# STEP 1.  Why this model is the kind one
# ----------------------------------------------------------------------
# Last week the household could go wrong in two directions, but only one of
# them crossed anything: too much consumption drove assets to zero, while too
# little just grew, with no crossing to catch.
#
# Here both mistakes cross an axis. Consume too much and capital is driven to
# zero; consume too little and the economy over-accumulates, capital sails
# past k*, and with f'(k) below rho + delta consumption is driven to zero.
# Two detectable failures on opposite sides is exactly what a search needs.
# ======================================================================

ALPHA = 1 / 3
A = 1.0
DELTA = 0.05
RHO = 0.03
SIGMA = 2.0


def f(k):
    return A * k**ALPHA


def f_prime(k):
    return ALPHA * A * k ** (ALPHA - 1)


def ngm(t, y):
    """The two laws of motion. y = (k, c)."""
    k, c = y
    return [f(k) - c - DELTA * k, c * (f_prime(k) - DELTA - RHO) / SIGMA]


# cdot = 0 needs f'(k) = rho + delta; the golden rule maximises f(k) - delta k.
k_star = (ALPHA * A / (RHO + DELTA)) ** (1 / (1 - ALPHA))
c_star = f(k_star) - DELTA * k_star
k_gr = (ALPHA * A / DELTA) ** (1 / (1 - ALPHA))

print(f"STEP 1   k*   = {k_star:.4f}")
print(f"         c*   = {c_star:.4f}")
print(f"         k_gr = {k_gr:.4f}   -- and k* < k_gr, as PS2 Q2(a) claims")


# ======================================================================
# STEP 2.  The two loci
# ----------------------------------------------------------------------
# kdot = 0  is  c = f(k) - delta k : concave, peaking at the golden rule.
# cdot = 0  is  the vertical line at k*.
# Nothing here needs a solver -- these are just two curves.
# ======================================================================

k_grid = np.linspace(0.05, 1.6 * k_gr, 500)

fig, ax = plt.subplots(figsize=(6.6, 4.8))
ax.plot(k_grid, f(k_grid) - DELTA * k_grid, lw=1.9, label=r"$\dot k = 0$")
ax.axvline(k_star, lw=1.9, color="C1", label=r"$\dot c = 0$")
ax.axvline(k_gr, lw=0.9, ls=":", color="0.5")
ax.text(k_gr, 0.04, r" $k_{gr}$", color="0.4")
ax.plot([k_star], [c_star], "ko", ms=5, zorder=5)


# ======================================================================
# STEP 3.  Two wrong guesses
# ----------------------------------------------------------------------
# An event per failure. Both are terminal: once either variable reaches zero
# there is nothing left to integrate.
# ======================================================================


# "Zero" numerically means small enough that the model has stopped saying
# anything. Both variables are of order one at the steady state, so 1e-4 is
# six thousandths of a per cent of it -- gone, for every purpose we have.
FLOOR = 1e-4


def capital_gone(t, y):
    return y[0] - FLOOR


def consumption_gone(t, y):
    return y[1] - FLOOR


capital_gone.terminal = True
consumption_gone.terminal = True


def integrate(k0, c0, t_end=400.0):
    return solve_ivp(
        ngm, [0.0, t_end], [k0, c0],
        events=[capital_gone, consumption_gone], dense_output=True,
        rtol=1e-11, atol=1e-13,
    )


K0 = 0.3 * k_star
print(f"\nSTEP 3   starting from k0 = 0.3 k* = {K0:.4f}")
for label, c0 in [("too high", 1.10), ("too low ", 0.40)]:
    s = integrate(K0, c0)
    if s.t_events[0].size:
        print(f"         c0 = {c0:.2f}  {label}  -> capital gone at t = {s.t_events[0][0]:.1f}")
    elif s.t_events[1].size:
        print(f"         c0 = {c0:.2f}  {label}  -> consumption gone at t = {s.t_events[1][0]:.1f}")
    else:
        print(f"         c0 = {c0:.2f}  {label}  -> neither event fired")
print("         Two failures, on opposite sides, each announcing itself.")


# ======================================================================
# STEP 4.  Bisection
# ----------------------------------------------------------------------
# Everything above the saddle path runs out of capital; everything below runs
# out of consumption. So halve the interval, ask which failure happened, and
# keep the half that still contains the boundary. Fifty or so rounds takes it
# to the limit of double precision.
# ======================================================================


def runs_out_of_capital(k0, c0):
    """True if this guess is above the saddle path."""
    s = integrate(k0, c0)
    if s.t_events[0].size:
        return True
    if s.t_events[1].size:
        return False
    return s.y[0, -1] < k_star  # neither fired: fall back on which way k drifted


def shoot(k0, rounds=60):
    """Bisect on c0 until the trajectory from k0 stays on the saddle path."""
    low, high = 1e-10, f(k0)      # cannot consume more than output
    for _ in range(rounds):
        mid = 0.5 * (low + high)
        if runs_out_of_capital(k0, mid):
            high = mid
        else:
            low = mid
    return 0.5 * (low + high)


print("\nSTEP 4   bisecting:")
for k0 in (K0, 1.8 * k_star):
    c0 = shoot(k0)
    s = integrate(k0, c0)
    t_grid = np.linspace(0.0, min(s.t[-1], 250.0), 1500)
    path = s.sol(t_grid)
    ax.plot(path[0], path[1], color="C3", lw=1.6)
    print(f"         k0 = {k0:7.4f}  ->  c0 = {c0:.6f}")

ax.plot([], [], color="C3", lw=1.6, label="saddle path")
ax.set_xlim(0, 1.6 * k_gr)
ax.set_ylim(0, 1.3 * max(f(k_grid) - DELTA * k_grid))
ax.set_xlabel("$k$")
ax.set_ylabel("$c$")
ax.set_title("Phase diagram and saddle path")
ax.legend(frameon=False, loc="lower right")
fig.tight_layout()
fig.savefig("tutorial3_saddle.png", dpi=150)
print("         wrote tutorial3_saddle.png")

print()
print("         The saddle path is only ever numerically reachable: any error in")
print("         c0 is amplified along the way, so the trajectory leaves the path")
print("         eventually however carefully c0 is chosen. Bisecting to machine")
print("         precision buys a century or so of it, which is more than enough.")

# ======================================================================
# Where this goes next
# ----------------------------------------------------------------------
# PS2 Q2(f) asks you to use this to run two experiments: halve the capital
# stock, and raise rho from 0.03 to 0.06.
#
# The second one will not work with the code as written above, because RHO is
# read from the top of the file. Your first job is to rewrite ngm, the steady
# state, and shoot so that they take the parameters as arguments. That is a
# small change and worth making carefully -- every model from here on comes
# with experiments attached.
# ======================================================================
