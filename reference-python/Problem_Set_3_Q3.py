"""
Problem Set 3, Question 3(d)-(g) -- solution code.

The discrete-time neoclassical growth model with log utility,

    V(k) = max_{k'} { log( A k^alpha + (1-delta) k - k' ) + beta V(k') }.

With delta = 1 this has a closed form (Question 1). With delta < 1 it does not,
which is the whole reason for solving it on a grid.

Run:  python Problem_Set_3_Q3.py
"""

import numpy as np
import matplotlib

matplotlib.use("Agg")  # write files rather than open a window; drop this line if you want a window
import matplotlib.pyplot as plt

# ----------------------------------------------------------------------
# Parameters
# ----------------------------------------------------------------------
A = 1.0
BETA = 0.90
DELTA = 0.10
ALPHA = 0.30

N_GRID = 500
TOL = 1e-6


def k_bar(alpha, A=A, beta=BETA, delta=DELTA):
    """
    Steady-state capital, part (c).

    The Euler equation at a steady state reads 1 = beta[alpha A k^(alpha-1) + 1 - delta],
    so alpha A k^(alpha-1) = 1/beta - (1 - delta), which inverts directly.
    """
    return (alpha * A / (1 / beta - (1 - delta))) ** (1 / (1 - alpha))


# ----------------------------------------------------------------------
# (d) Value function iteration
# ----------------------------------------------------------------------
def solve(alpha, n=N_GRID, tol=TOL, A=A, beta=BETA, delta=DELTA):
    """
    Value function iteration on a grid.

    The whole method is three lines of arithmetic. Everything else is bookkeeping.
    Build the matrix of period payoffs once, outside the loop -- it does not depend
    on the value function, so recomputing it every iteration is pure waste.
    """
    kb = k_bar(alpha, A, beta, delta)
    grid = np.linspace(1e-3, 2 * kb, n)

    # resources[i, j] = what is left to consume at k_i after choosing k' = k_j
    resources = A * grid[:, None] ** alpha + (1 - delta) * grid[:, None] - grid[None, :]
    feasible = resources > 0
    # -inf on infeasible choices, so the maximiser never selects them
    payoff = np.where(feasible, np.log(np.where(feasible, resources, 1.0)), -np.inf)

    V = np.zeros(n)
    for iteration in range(20_000):
        M = payoff + beta * V[None, :]        # value of every (k, k') pair
        choice = M.argmax(axis=1)             # best k' for each k
        V_new = M[np.arange(n), choice]
        gap = np.max(np.abs(V_new - V))
        V = V_new
        if gap < tol:
            break

    policy = grid[choice]
    consumption = A * grid**alpha + (1 - delta) * grid - policy
    return grid, V, policy, consumption, iteration + 1, gap, kb


grid, V, policy, consumption, iters, gap, kb = solve(ALPHA)
print(f"(c)  steady state, analytically:  k_bar = {kb:.4f}")
print(f"(d)  converged in {iters} iterations, final change {gap:.2e}")

# What the stopping rule actually guarantees -- Question 2(d).
print(f"     the change between iterates is below {TOL:g}, so by the bound in Q2(d)")
print(f"     the distance to the true V is below {TOL/(1-BETA):.1e}, which is {1/(1-BETA):.0f}x larger")


# ----------------------------------------------------------------------
# (e) The policy function against the 45-degree line
# ----------------------------------------------------------------------
fig, ax = plt.subplots(figsize=(6.2, 4.6))
ax.plot(grid, policy, lw=2, label=r"$k'(k)$")
ax.plot(grid, grid, lw=1.2, ls="--", color="0.45", label=r"$45^\circ$")
ax.axvline(kb, color="C3", lw=0.9, ls=":")
ax.text(kb, 0.05 * grid[-1], r" $\bar k$", color="C3")
ax.set_xlabel("$k$")
ax.set_ylabel("$k'$")
ax.set_title("Policy function and the 45-degree line")
ax.legend(frameon=False)
fig.tight_layout()
fig.savefig("PS3_Q3_policy.png", dpi=150)

# where the policy actually crosses the 45-degree line
d = policy - grid
crossings = [i for i in np.where(np.sign(d[:-1]) != np.sign(d[1:]))[0] if grid[i] > 0.1 * kb]
k_cross = grid[crossings[0]] if crossings else np.nan
print(f"(e)  policy crosses 45 degrees at k = {k_cross:.4f} against k_bar = {kb:.4f}")
print(f"     grid spacing is {grid[1]-grid[0]:.4f}, so the gap is about one grid point --")
print(f"     the error is discretisation, not a mistake. A finer grid shrinks it.")


# ----------------------------------------------------------------------
# (f) Simulate from k0 = 0.5 k_bar
# ----------------------------------------------------------------------
def simulate(grid, policy, k0, T=50):
    """Iterate the policy forward, interpolating between grid points."""
    path = np.empty(T + 1)
    path[0] = k0
    for t in range(T):
        path[t + 1] = np.interp(path[t], grid, policy)
    return path


k_path = simulate(grid, policy, 0.5 * kb)
c_path = A * k_path**ALPHA + (1 - DELTA) * k_path - np.r_[k_path[1:], k_path[-1]]

fig, axes = plt.subplots(1, 2, figsize=(11, 4.2))
axes[0].plot(k_path, lw=2)
axes[0].axhline(kb, color="0.45", lw=1.0, ls="--")
axes[0].set_ylabel("$k_t$")
axes[0].set_title("Capital")
axes[1].plot(c_path, lw=2, color="C1")
axes[1].axhline(A * kb**ALPHA - DELTA * kb, color="0.45", lw=1.0, ls="--")
axes[1].set_ylabel("$c_t$")
axes[1].set_title("Consumption")
for ax in axes:
    ax.set_xlabel("period")
fig.tight_layout()
fig.savefig("PS3_Q3_simulation.png", dpi=150)
print(f"(f)  from k0 = {0.5*kb:.4f}, k(50) = {k_path[-1]:.4f}, k_bar = {kb:.4f}")


# ----------------------------------------------------------------------
# (g) How the capital share changes the speed of convergence
# ----------------------------------------------------------------------
fig, ax = plt.subplots(figsize=(6.6, 4.4))
print("\n(g)  periods for |k - k_bar| / k_bar to fall below 10%:")
for alpha, colour in [(0.10, "C0"), (0.30, "C1"), (0.60, "C3")]:
    g, _, pol, _, _, _, kba = solve(alpha)
    path = simulate(g, pol, 0.5 * kba)
    gap_frac = np.abs(path - kba) / kba
    ax.plot(gap_frac, lw=2, color=colour, label=rf"$\alpha = {alpha:.2f}$")
    below = np.where(gap_frac < 0.10)[0]
    print(f"     alpha = {alpha:.2f}: {below[0]} periods")

ax.set_xlabel("period")
ax.set_ylabel(r"$|k_t - \bar k| / \bar k$")
ax.set_title("Distance from steady state")
ax.legend(frameon=False)
fig.tight_layout()
fig.savefig("PS3_Q3_convergence.png", dpi=150)

print()
print("     Convergence is slower the larger is alpha. Diminishing returns are what")
print("     pull capital back to the steady state: a low alpha means the marginal")
print("     product falls away sharply as capital accumulates, so the gap closes fast.")
print("     As alpha rises the returns flatten and convergence slows -- and in the")
print("     limit alpha -> 1 the model becomes AK and never converges at all.")
print("     Compare the continuous-time rate (1-alpha)(delta+n) from PS1 Q1(f).")
print()
print("     wrote PS3_Q3_policy.png, PS3_Q3_simulation.png, PS3_Q3_convergence.png")
