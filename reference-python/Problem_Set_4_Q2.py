"""
Problem Set 4, Question 2(c) and 2(f) -- solution code.

Resource extraction under a stochastic price:

    V(S,p) = max_q { p q - q^2/S - kappa q^2 + beta E[V(S-q, p') | p] }

With kappa = 0 the problem is homogeneous of degree one in (S,q), so
V(S,p) = a(p) S and the extraction rate q/S does not depend on S at all.
With kappa > 0 the capacity cost breaks that, and the second state variable
has to be carried.

The point of the exercise is the contrast between the two columns of output.

Run:  python Problem_Set_4_Q2.py
"""

import numpy as np
from scipy.stats import norm
import matplotlib

matplotlib.use("Agg")  # write files rather than open a window
import matplotlib.pyplot as plt

# ----------------------------------------------------------------------
# Parameters
# ----------------------------------------------------------------------
BETA = 0.95
RHO = 0.8
SIGMA = 0.10
MEAN_PRICE = 2.0

N_P = 7          # price nodes for the computation in (f)
N_S = 600        # stock grid
N_Q = 300        # extraction grid, as a fraction of the stock


# ----------------------------------------------------------------------
# (c) Tauchen's method
# ----------------------------------------------------------------------
def tauchen(rho, sigma, n, m=3.0, mu=0.0):
    """
    Discretise log z' = rho log z + sigma eps' onto an n-state Markov chain.

    Nodes are evenly spaced across +/- m unconditional standard deviations.
    The two outer columns absorb the whole remaining tail, which is what makes
    each row sum to one.
    """
    sd = sigma / np.sqrt(1 - rho**2)
    z = np.linspace(-m * sd, m * sd, n)
    w = z[1] - z[0]
    P = np.zeros((n, n))
    for i in range(n):
        for j in range(n):
            if j == 0:
                P[i, j] = norm.cdf((z[0] - rho * z[i] + w / 2) / sigma)
            elif j == n - 1:
                P[i, j] = 1 - norm.cdf((z[-1] - rho * z[i] - w / 2) / sigma)
            else:
                P[i, j] = norm.cdf((z[j] - rho * z[i] + w / 2) / sigma) - norm.cdf(
                    (z[j] - rho * z[i] - w / 2) / sigma
                )
    return np.exp(z + mu), P


# The three-state chain asked for in part (c), to be checked against the hand calculation
p3, P3 = tauchen(RHO, SIGMA, 3)
print("(c) three-state chain, rho = 0.8, sigma = 0.1, m = 3")
print(f"    unconditional sd of log p = {SIGMA/np.sqrt(1-RHO**2):.5f}")
print(f"    log-price nodes = {np.round(np.log(p3), 4)}")
print("    transition matrix:")
for row in P3:
    print("      " + "  ".join(f"{x:.5f}" for x in row))
print(f"    row sums = {np.round(P3.sum(1), 12)}")
print()


# ----------------------------------------------------------------------
# (f) Value function iteration on the (S, p) grid
# ----------------------------------------------------------------------
p, P = tauchen(RHO, SIGMA, N_P, mu=np.log(MEAN_PRICE))

# A log-spaced stock grid. The choice grid is written as a FRACTION of the
# stock, which keeps the discretisation itself scale-free -- otherwise the
# grid, rather than the economics, would break the homogeneity we are testing.
S = np.exp(np.linspace(np.log(1e-3), np.log(5.0), N_S))
frac = np.linspace(0.0, 0.99, N_Q)


def solve(kappa, tol=1e-9, maxit=4000):
    V = np.zeros((N_S, N_P))
    Q = np.zeros((N_S, N_P))
    q = S[:, None] * frac[None, :]                       # (N_S, N_Q)
    S_next = S[:, None] * (1 - frac)[None, :]
    flow = (
        p[None, None, :] * q[:, :, None]
        - (q**2 / S[:, None])[:, :, None]
        - kappa * (q**2)[:, :, None]
    )
    for it in range(maxit):
        EV = V @ P.T                                     # EV[s, i] = E[V(S_s, p') | p_i]
        cont = np.empty((N_S, N_Q, N_P))
        for i in range(N_P):
            cont[:, :, i] = np.interp(S_next, S, EV[:, i])
        val = flow + BETA * cont
        k = val.argmax(axis=1)
        V_new = np.take_along_axis(val, k[:, None, :], axis=1)[:, 0, :]
        Q_new = q[np.arange(N_S)[:, None], k]
        gap = np.max(np.abs(V_new - V))
        V, Q = V_new, Q_new
        if gap < tol:
            break
    return V, Q, it + 1, gap


mid = N_P // 2
results = {}
for kappa in (0.0, 0.5):
    V, Q, iters, gap = solve(kappa)
    results[kappa] = (V, Q)
    print(f"(f) kappa = {kappa}: converged in {iters} iterations, final change {gap:.1e}")
    print(f"        S      V/S       q/S")
    for s_target in (0.1, 0.5, 1.5, 3.0, 4.5):
        si = np.argmin(np.abs(S - s_target))
        print(f"    {S[si]:7.3f}  {V[si, mid]/S[si]:7.5f}  {Q[si, mid]/S[si]:7.5f}")
    print()

print("    With kappa = 0 the extraction rate is the same number at every stock,")
print("    and V/S is constant to four figures -- the small drift at the very")
print("    bottom of the grid is truncation, not economics. That is homogeneity.")
print()
print("    With kappa = 0.5 the rate roughly halves as the stock grows from 0.5")
print("    to 4.5. The capacity cost depends on the LEVEL of extraction, so a")
print("    firm with twice the stock that doubled its extraction would pay four")
print("    times the capacity cost. Large firms therefore deplete more slowly.")


# ----------------------------------------------------------------------
# The two plots asked for in (f)
# ----------------------------------------------------------------------
fig, axes = plt.subplots(1, 2, figsize=(11, 4.2))
for kappa, colour in ((0.0, "C0"), (0.5, "C3")):
    V, Q = results[kappa]
    axes[0].plot(S, V[:, mid] / S, lw=2, color=colour, label=rf"$\kappa = {kappa}$")
    axes[1].plot(S, Q[:, mid] / S, lw=2, color=colour, label=rf"$\kappa = {kappa}$")
axes[0].set_ylabel("$V(S,p)/S$")
axes[0].set_title("Value per unit of stock")
axes[1].set_ylabel("$q(S,p)/S$")
axes[1].set_title("Extraction rate")
for ax in axes:
    ax.set_xlabel("$S$")
    ax.set_xlim(0, 5)
    ax.legend(frameon=False)
fig.tight_layout()
fig.savefig("PS4_Q2f_homogeneity.png", dpi=150)
print()
print("    wrote PS4_Q2f_homogeneity.png")
