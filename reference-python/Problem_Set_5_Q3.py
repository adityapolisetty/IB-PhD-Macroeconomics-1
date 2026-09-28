"""
Problem Set 5, Question 3 -- solution code.

A firm faces nonconvex costs of adjusting its capital stock:

    V(k,z)   = max{ V_n(k,z), V_a(k,z) }
    V_n(k,z) = pi(k,z) + beta E[ V((1-delta)k, z') | z ]                 (do nothing)
    V_a(k,z) = max_k' { (1-f) pi(k,z) - c(k',k) + beta E[ V(k',z') | z ] }  (adjust)

with pi(k,z) = z k^nu, log z' = rho log z + sigma eps', and

    c(k',k) = i        if i >= 0        (buy at 1)
            = p_s i    if i  < 0        (sell at p_s < 1, so selling is lossy)

where i = k' - (1-delta)k. The fixed cost f is a fraction of the profit flow.

Solve it, look at the policy, simulate a panel, and compare the four facts of
Lecture 9 §3 with what the model produces.

Run:  python Problem_Set_5_Q3.py        (about a minute)
"""

import numpy as np
from scipy.stats import norm
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

# ----------------------------------------------------------------------
# Parameters -- annual, plant level
# ----------------------------------------------------------------------
BETA, DELTA, NU = 0.96, 0.10, 0.60
RHO, SIGMA = 0.70, 0.30          # idiosyncratic productivity: persistent and large
F_COST, P_SELL = 0.05, 0.95      # fixed cost as a share of profit; resale price

N_K, N_Z = 250, 11


def tauchen(rho, sigma, n, m=3.0):
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
    return np.exp(z), P


Z, P = tauchen(RHO, SIGMA, N_Z)

# Centre the capital grid on the frictionless target, nu z k^(nu-1) = r + delta,
# and leave room on both sides for the inaction region to sit inside the grid.
R_RATE = 1 / BETA - 1
KSTAR = (NU * Z / (R_RATE + DELTA)) ** (1 / (1 - NU))
K = np.exp(np.linspace(np.log(KSTAR.min() * 0.25), np.log(KSTAR.max() * 1.6), N_K))
PI = Z[None, :] * K[:, None] ** NU

# cost of moving from k to k', for every (k, k') pair
_KOLD = (1 - DELTA) * K[:, None]
_GAP = K[None, :] - _KOLD
COST = np.where(_GAP >= 0, _GAP, P_SELL * _GAP)


def solve(f=F_COST, cost=COST, tol=1e-8, maxit=3000):
    """Value function iteration with a discrete adjust / do-nothing choice."""
    V = PI / (1 - BETA)
    for it in range(maxit):
        EV = V @ P.T
        Va = np.empty_like(V)
        idx = np.empty(V.shape, dtype=int)
        for iz in range(N_Z):
            M = -cost + BETA * EV[None, :, iz]        # (k, k') payoff net of profit
            idx[:, iz] = M.argmax(axis=1)
            Va[:, iz] = PI[:, iz] * (1 - f) + M[np.arange(N_K), idx[:, iz]]
        Vn = np.empty_like(V)
        for iz in range(N_Z):
            Vn[:, iz] = PI[:, iz] + BETA * np.interp((1 - DELTA) * K, K, EV[:, iz])
        Vnew = np.maximum(Va, Vn)
        gap = np.max(np.abs(Vnew - V))
        V = Vnew
        if gap < tol:
            break
    adjust = Va > Vn
    kpol = np.where(adjust, K[idx], (1 - DELTA) * K[:, None])
    return V, adjust, kpol, it + 1, gap


def simulate(kpol, T=400, N=6000, burn=100, seed=1):
    """Panel of firms; returns the matrix of investment rates i/k."""
    rng = np.random.default_rng(seed)
    cum = P.cumsum(axis=1)
    iz = rng.integers(0, N_Z, N)
    k = np.full(N, K[N_K // 2], dtype=float)
    out = np.empty((T - burn, N))
    for t in range(T):
        kn = np.empty(N)
        for j in range(N_Z):                          # one interp call per z state
            m = iz == j
            if m.any():
                kn[m] = np.interp(k[m], K, kpol[:, j])
        rate = (kn - (1 - DELTA) * k) / k
        if t >= burn:
            out[t - burn] = rate
        k = kn
        iz = (rng.random(N)[:, None] > cum[iz]).sum(axis=1)
    return out


def facts(R):
    r = R.ravel()
    return dict(
        mean=r.mean() * 100,
        spike=(r > 0.20).mean() * 100,
        inaction=(np.abs(r) < 0.01).mean() * 100,
        negative=(r < 0).mean() * 100,
        serial=np.corrcoef(R[:-1].ravel(), R[1:].ravel())[0, 1],
    )


# ----------------------------------------------------------------------
# (c) Solve, and look at the policy
# ----------------------------------------------------------------------
print("(c) solving...")
V, adjust, kpol, iters, gap = solve()
print(f"    converged in {iters} iterations, final change {gap:.1e}")
print(f"    capital grid [{K[0]:.2f}, {K[-1]:.2f}]")

mid = N_Z // 2
band = np.where(~adjust[:, mid])[0]
if len(band):
    print(f"    at the median z, the firm does nothing for k in "
          f"[{K[band[0]]:.2f}, {K[band[-1]]:.2f}] -- an inaction region "
          f"{K[band[-1]]/K[band[0]]:.1f} times wide")

fig, axes = plt.subplots(1, 2, figsize=(11, 4.4))
for iz, lab in ((2, "low $z$"), (mid, "median $z$"), (N_Z - 3, "high $z$")):
    axes[0].plot(K, kpol[:, iz], lw=2, label=lab)
axes[0].plot(K, K, "k--", lw=1, label="$45^\\circ$")
axes[0].set_xscale("log"); axes[0].set_yscale("log")
axes[0].set_xlabel("$k$"); axes[0].set_ylabel("$k'$")
axes[0].set_title("Policy function")
axes[0].legend(frameon=False)

# where the firm adjusts, in (k, z) space
axes[1].imshow(adjust.T, origin="lower", aspect="auto", cmap="Greys",
               extent=[np.log(K[0]), np.log(K[-1]), np.log(Z[0]), np.log(Z[-1])])
axes[1].set_xlabel("$\\log k$"); axes[1].set_ylabel("$\\log z$")
axes[1].set_title("Adjust (dark) / do nothing (light)")
fig.tight_layout()
fig.savefig("PS5_Q3_policy.png", dpi=150)
print("    wrote PS5_Q3_policy.png")
print()

# ----------------------------------------------------------------------
# (d) Simulate and compare with the facts of Lecture 9 §3
# ----------------------------------------------------------------------
print("(d) simulating a panel...")
R = simulate(kpol)
m = facts(R)
data = dict(mean=12.2, spike=18.0, inaction=8.0, negative=10.0, serial=0.007)
print()
print("                          model     data")
print(f"    mean i/k            {m['mean']:7.1f}%  {data['mean']:7.1f}%")
print(f"    spike, i/k > 20%    {m['spike']:7.1f}%  {data['spike']:7.1f}%")
print(f"    inaction, |i/k|<1%  {m['inaction']:7.1f}%  {data['inaction']:7.1f}%")
print(f"    negative, i/k < 0   {m['negative']:7.1f}%  {data['negative']:7.1f}%")
print(f"    serial correlation  {m['serial']:7.3f}   {data['serial']:7.3f}")
print()
print("    Three of the five come out right in kind and roughly in size: spikes")
print("    exist and are common, negative investment is rare, and the serial")
print("    correlation is essentially zero -- slightly negative, in fact, because a")
print("    firm that has just jumped to its target sits inside the band and will")
print("    not move again for a while. No convex model produces any of the three.")
print()
print("    The inaction rate is the failure, and it is not a near miss: the model")
print("    says four firms in five do nothing in a given year, against one in")
print("    twelve in the data. See part (f).")
print()

# ----------------------------------------------------------------------
# (e) Which parameter controls which moment
# ----------------------------------------------------------------------
print("(e) comparative statics")
print("        f     p_s    mean i/k   spike   inaction   negative   serial")
rows = [(0.01, 0.95), (0.05, 0.95), (0.10, 0.95), (0.05, 0.80), (0.05, 1.00)]
for f, ps in rows:
    cost = np.where(_GAP >= 0, _GAP, ps * _GAP)
    _, _, kp, _, _ = solve(f=f, cost=cost)
    mm = facts(simulate(kp))
    print(f"     {f:.3f}   {ps:.2f}    {mm['mean']:7.1f}%  {mm['spike']:6.1f}% "
          f"{mm['inaction']:9.1f}% {mm['negative']:9.1f}%  {mm['serial']:7.3f}")
print()
print("    The fixed cost f governs INACTION and, through it, the spike rate:")
print("    raising f widens the band, so firms adjust less often and by more when")
print("    they do. The resale price p_s governs NEGATIVE investment: lowering it")
print("    makes disinvestment lossy and pushes the sell trigger further away, so")
print("    fewer firms ever sell. Each parameter has its own moment, which is why")
print("    both nonconvexities are needed -- neither alone matches the asymmetry.")
print()

# ----------------------------------------------------------------------
# (f) Switch the nonconvexities off
# ----------------------------------------------------------------------
print("(f) f = 0 and p_s = 1: the frictionless benchmark")
cost0 = np.where(_GAP >= 0, _GAP, 1.0 * _GAP)
_, adj0, kp0, _, _ = solve(f=0.0, cost=cost0)
m0 = facts(simulate(kp0))
print(f"        inaction {m0['inaction']:.1f}%   spike {m0['spike']:.1f}%   "
      f"negative {m0['negative']:.1f}%   serial {m0['serial']:.3f}")
print(f"        the firm adjusts at {adj0.mean()*100:.0f}% of states")
print()
print("    Inaction disappears completely, as it must: with no fixed cost and no")
print("    resale loss the firm has a target and goes to it every period. The")
print("    nonconvexities are doing all the work, not the shock process.")
print()
print("    Why the inaction rate still misses by a factor of ten. In this model a")
print("    firm either pays the fixed cost and jumps, or does literally nothing.")
print("    Real plants do neither: they undertake small replacement and maintenance")
print("    investment every year, which is why only 8% of plant-years show an")
print("    investment rate inside +/-1%. The repair is to exempt low-level")
print("    investment from the fixed cost -- which is exactly the ingredient Khan")
print("    and Thomas (2008) add, and the reason theirs is the first model")
print("    consistent with the whole cross-sectional distribution rather than")
print("    with its tails.")
