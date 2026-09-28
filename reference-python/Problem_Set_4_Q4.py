"""
Problem Set 4, Question 4 -- solution code.

The RBC model of Lecture 8:

    max E sum beta^t [ log C + theta (1-N)^(1-eta)/(1-eta) ]
    s.t. C + K' = Z K^alpha N^(1-alpha) + (1-delta) K,
         log Z' = rho log Z + sigma eps'.

Solve it numerically for the policy function g(K, Z), simulate it for the
business-cycle moments, and then put the numerical policy and the log-linear
rule of Question 3(f) side by side: feed both the SAME realised sequence of
productivity and compare the capital paths they generate.

Run:  python Problem_Set_4_Q4.py        (about a minute)
"""

import numpy as np
from scipy.stats import norm
from scipy.interpolate import CubicSpline
import scipy.sparse as sp
import scipy.sparse.linalg as spla
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

# ----------------------------------------------------------------------
# Calibration -- Question 3(g)
# ----------------------------------------------------------------------
BETA, ALPHA, DELTA, ETA = 0.99, 0.36, 0.025, 1.0
NBAR = 0.20
RHO, SIGMA = 0.95, 0.007

rk = 1 / BETA - 1 + DELTA
KY = ALPHA / rk
KBAR = KY ** (1 / (1 - ALPHA)) * NBAR
YBAR = KBAR**ALPHA * NBAR ** (1 - ALPHA)
CBAR = YBAR - DELTA * KBAR
WBAR = (1 - ALPHA) * YBAR / NBAR
THETA = WBAR * (1 - NBAR) ** ETA / CBAR       # from theta C (1-N)^-eta = w
EPS_F = (1 - NBAR) / (ETA * NBAR)             # Frisch elasticity

print("Steady state (Question 3(g))")
print(f"    K/Y = {KY:.4f}   I/Y = {DELTA*KY:.4f}   C/Y = {CBAR/YBAR:.4f}")
print(f"    K   = {KBAR:.4f}   Y = {YBAR:.5f}   C = {CBAR:.5f}   w = {WBAR:.5f}")
print(f"    theta = {THETA:.4f}   Frisch elasticity = {EPS_F:.2f}")
print()


# ----------------------------------------------------------------------
# The log-linear solution -- Question 3(f), solved explicitly
# ----------------------------------------------------------------------
# The three log-linearised conditions, in the notation of Question 3(e):
#
#   k' = (1/beta) k - mu c + y z + (1-alpha) y n
#   A n = alpha k + z - c,          A = alpha + 1/eps_F
#   c = E c' - lam ( E z' + (1-alpha) E n' - (1-alpha) k' ),  lam = 1-beta(1-delta)
#
# Substituting k' = a_k k + a_z z, c = b_k k + b_z z, n = d_k k + d_z z and
# matching coefficients reduces to a quadratic in a_k.
MU, YK = CBAR / KBAR, YBAR / KBAR
LAM = 1 - BETA * (1 - DELTA)
A = ALPHA + 1 / EPS_F
L = LAM * (1 - ALPHA) / A
M = MU + (1 - ALPHA) * YK / A
B = 1 / BETA + (1 - ALPHA) * YK * ALPHA / A

qa, qb, qc = 1 + L, -(B * (1 + L) + 1 + M * L / EPS_F), B
disc = qb**2 - 4 * qa * qc
roots = np.array([(-qb - np.sqrt(disc)) / (2 * qa), (-qb + np.sqrt(disc)) / (2 * qa)])
stable = roots[np.abs(roots) < 1]
assert len(stable) == 1, f"expected exactly one stable root, got {roots}"
a_k = float(stable[0])
b_k = (B - a_k) / M
d_k = (ALPHA - b_k) / A

D = YK * (1 + (1 - ALPHA) / A)
E1 = b_k - LAM * (1 - ALPHA) * d_k + LAM * (1 - ALPHA)
E2 = LAM * RHO + LAM * (1 - ALPHA) * RHO / A
E3 = (1 - RHO) - LAM * (1 - ALPHA) * RHO / A
b_z = (E1 * D - E2) / (E3 + E1 * M)
a_z = D - M * b_z
d_z = (1 - b_z) / A

print("Log-linear solution (Question 3(f))")
print(f"    roots of the quadratic: {roots[0]:.6f}, {roots[1]:.6f}")
print("    the unstable root is discarded -- it violates transversality")
print(f"    k' = {a_k:.6f} k + {a_z:.6f} z")
print(f"    c  = {b_k:.6f} k + {b_z:.6f} z")
print(f"    n  = {d_k:.6f} k + {d_z:.6f} z")

r1k = a_k - (1 / BETA - MU * b_k + (1 - ALPHA) * YK * d_k)
r1z = a_z - (-MU * b_z + YK + (1 - ALPHA) * YK * d_z)
r2k = A * d_k - (ALPHA - b_k)
r2z = A * d_z - (1 - b_z)
r3k = b_k - (b_k * a_k - LAM * (1 - ALPHA) * a_k * (d_k - 1))
r3z = b_z - (
    b_k * a_z + b_z * RHO
    - LAM * (RHO + (1 - ALPHA) * (d_k * a_z + d_z * RHO) - (1 - ALPHA) * a_z)
)
print(f"    residuals in the three conditions: "
      f"{max(abs(x) for x in (r1k, r1z, r2k, r2z, r3k, r3z)):.2e}")
print()


# ----------------------------------------------------------------------
# (b) Grids
# ----------------------------------------------------------------------
def tauchen(rho, sigma, n, m):
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
    return z, P


# The productivity grid does two jobs. For the moments in (c) it need only cover
# the ergodic range, about +/- 3 unconditional standard deviations (+/- 0.067 in
# logs). For the paths in (e) it must also contain log Z = 0.20. So it is much
# wider than usual -- but the SPACING stays well below sigma, which is what keeps
# the chain a faithful representation of the AR(1).
N_Z, Z_RANGE = 161, 0.22
SD_Z = SIGMA / np.sqrt(1 - RHO**2)
logz, P = tauchen(RHO, SIGMA, N_Z, Z_RANGE / SD_Z)
Z = np.exp(logz)

# A curved capital grid: dense near the steady state, wide enough for the
# largest path in (e).
N_K = 300
u = np.linspace(-1, 1, N_K)
K = KBAR * (1 + 0.9 * np.sign(u) * u**2)

print(f"(b) productivity grid: {N_Z} nodes, log Z in "
      f"[{logz[0]:+.3f}, {logz[-1]:+.3f}], spacing {(logz[1]-logz[0])/SIGMA:.2f} sigma")
print(f"    capital grid: {N_K} nodes on [{K[0]:.2f}, {K[-1]:.2f}]")


# ----------------------------------------------------------------------
# (b) Solving for the policy function by time iteration
# ----------------------------------------------------------------------
# Guess a policy, use it to work out what marginal utility will be tomorrow,
# solve today's Euler equation for today's choice, and repeat until the policy
# stops moving.
#
# One trick makes this cheap. Rather than searching over K', search over N: the
# intratemporal condition
#       theta C (1-N)^(-eta) = (1-alpha) Z K^alpha N^(-alpha)
# then gives C in closed form, and the resource constraint gives K'. So each
# candidate N delivers (C, K') with no nested solve. The Euler residual is
# increasing in N, so a bisection finds the root.
Kg = K[:, None]
Zg = Z[None, :]
COL = np.broadcast_to(np.arange(N_Z), (N_K, N_Z))


def from_hours(N):
    """Consumption and next-period capital implied by choosing N at each (K, Z)."""
    C = (1 - ALPHA) * Zg * Kg**ALPHA * N ** (-ALPHA) * (1 - N) ** ETA / THETA
    Kp = Zg * Kg**ALPHA * N ** (1 - ALPHA) + (1 - DELTA) * Kg - C
    return C, Kp


def hours_at(Kc, Zc, Kn, iters=55):
    """Invert the intratemporal condition for N given (K, Z, K')."""
    lo = np.full(np.shape(Kn), 1e-10)
    hi = np.full(np.shape(Kn), 1 - 1e-10)
    for _ in range(iters):
        mid = 0.5 * (lo + hi)
        C = Zc * Kc**ALPHA * mid ** (1 - ALPHA) + (1 - DELTA) * Kc - Kn
        too_low = THETA * C * (1 - mid) ** (-ETA) < (1 - ALPHA) * Zc * Kc**ALPHA * mid ** (-ALPHA)
        lo = np.where(too_low, mid, lo)
        hi = np.where(too_low, hi, mid)
    return 0.5 * (lo + hi)


def solve_policy(tol=1e-12, maxit=3000):
    g = np.broadcast_to(Kg, (N_K, N_Z)).copy()      # start from K' = K
    for it in range(maxit):
        # marginal utility and gross return on the grid, under the current policy
        Ng = hours_at(Kg, Zg, g)
        Cg = Zg * Kg**ALPHA * Ng ** (1 - ALPHA) + (1 - DELTA) * Kg - g
        Rg = ALPHA * Zg * Kg ** (ALPHA - 1) * Ng ** (1 - ALPHA) + 1 - DELTA
        EE = (Rg / Cg) @ P.T                         # EE[i, j] = E[R'/C' | z_j] at K' = K_i

        lo = np.full((N_K, N_Z), 1e-6)
        hi = np.full((N_K, N_Z), 1 - 1e-6)
        for _ in range(48):
            N = 0.5 * (lo + hi)
            C, Kp = from_hours(N)
            Kc = np.clip(Kp, K[0], K[-1])
            idx = np.clip(np.searchsorted(K, Kc) - 1, 0, N_K - 2)
            w = (Kc - K[idx]) / (K[idx + 1] - K[idx])
            ee = (1 - w) * EE[idx, COL] + w * EE[idx + 1, COL]
            up = 1 / C - BETA * ee < 0               # residual rises in N
            lo = np.where(up, N, lo)
            hi = np.where(up, hi, N)
        N = 0.5 * (lo + hi)
        C, Kp = from_hours(N)
        gap = np.max(np.abs(Kp - g))
        g, Npol = Kp, N
        if gap < tol:
            break
    return g, Npol, it + 1, gap


print("    solving by time iteration...")
policy, Npolicy, iters, gap = solve_policy()
print(f"    converged in {iters} iterations, final change {gap:.1e}")
print()


# ----------------------------------------------------------------------
# (c) Simulation and business-cycle moments
# ----------------------------------------------------------------------
def hp_filter(y, lam=1600.0):
    """Hodrick-Prescott trend by a direct sparse solve; returns the cyclical part."""
    T = len(y)
    d = np.ones(T - 2)
    Dm = sp.diags([d, -2 * d, d], [0, 1, 2], shape=(T - 2, T), format="csc")
    trend = spla.spsolve((sp.identity(T, format="csc") + lam * Dm.T @ Dm).tocsc(), y)
    return y - trend


gspl = [CubicSpline(K, policy[:, j]) for j in range(N_Z)]
nspl = [CubicSpline(K, Npolicy[:, j]) for j in range(N_Z)]


def simulate(T=20_000, burn=1_000, seed=0):
    rng = np.random.default_rng(seed)
    cum = P.cumsum(axis=1)
    j = N_Z // 2
    k = KBAR
    out = np.empty((T, 5))                            # Y, C, I, N, w
    for t in range(T):
        kn = float(gspl[j](k))
        n = float(nspl[j](k))
        y = Z[j] * k**ALPHA * n ** (1 - ALPHA)
        out[t] = (y, y + (1 - DELTA) * k - kn, kn - (1 - DELTA) * k, n,
                  (1 - ALPHA) * y / n)
        k = kn
        j = int(np.searchsorted(cum[j], rng.random()))
    return out[burn:]


print("(c) simulating...")
sim = simulate()
labels = ["Y", "C", "I", "N", "w"]
cyc = np.column_stack([hp_filter(np.log(sim[:, i])) for i in range(5)])
sd = cyc.std(axis=0) * 100
corr = [np.corrcoef(cyc[:, i], cyc[:, 0])[0, 1] for i in range(5)]
data_sd = [1.79, 1.12, 8.20, 1.76, 0.81]
data_corr = [None, 0.88, 0.87, 0.87, 0.14]

print("                      model            data")
print("             sd(%)  corr(Y)    sd(%)  corr(Y)")
for i, lab in enumerate(labels):
    cm = "  ---  " if i == 0 else f"{corr[i]:+.2f}  "
    cd = "  ---  " if i == 0 else f"{data_corr[i]:+.2f}  "
    print(f"  {lab:>3}   {sd[i]:6.2f}   {cm}   {data_sd[i]:6.2f}   {cd}")
print()
print(f"    output volatility, model / data = {sd[0]/data_sd[0]:.2f}")
print(f"    hours relative to output:  model {sd[3]/sd[0]:.2f}   data {data_sd[3]/data_sd[0]:.2f}")
print()
print("    What it gets right: the ranking and the rough magnitudes. Consumption")
print("    is much smoother than output, investment several times more volatile,")
print("    both strongly procyclical, and output volatility is around four-fifths")
print("    of the data. (Lecture 8 quotes two-thirds to three-quarters, from a")
print("    slightly different calibration; the difference is eta, which is 1 here.)")
print()
print("    What it misses is the labour market, in exactly the way Lecture 8 §6")
print("    said it would. Hours are only about three-fifths as volatile as output,")
print("    against nearly one-for-one in the data. And the real wage is almost")
print("    perfectly correlated with output. That second failure is structural,")
print("    not a matter of calibration: with a single shock and a Cobb-Douglas")
print("    technology both w and Y are essentially Z, so they cannot help but move")
print("    together. No choice of parameters repairs it; only a second shock would.")
print()


# ----------------------------------------------------------------------
# (d)-(e) The two decision rules, fed the same productivity path
# ----------------------------------------------------------------------
# Pick a sequence for productivity: one innovation at date 0, then none, so
# log Z_t = rho^t eps0. Feed that same realised sequence through each decision
# rule and compare the capital paths. Both economies face the same shocks; the
# only difference between them is which rule the household is following.
T_PATH = 80
SHOCKS = [0.01, 0.05, 0.10, 0.20]


def path_loglinear(eps0, T=T_PATH):
    zhat = eps0 * RHO ** np.arange(T + 1)
    khat = np.zeros(T + 1)
    for t in range(T):
        khat[t + 1] = a_k * khat[t] + a_z * zhat[t]
    return KBAR * np.exp(khat)


def path_numerical(eps0, T=T_PATH):
    zhat = eps0 * RHO ** np.arange(T + 1)
    k = np.empty(T + 1)
    k[0] = KBAR
    for t in range(T):
        j = int(np.clip(np.searchsorted(logz, zhat[t]) - 1, 0, N_Z - 2))
        w = (zhat[t] - logz[j]) / (logz[j + 1] - logz[j])
        k[t + 1] = (1 - w) * float(gspl[j](k[t])) + w * float(gspl[j + 1](k[t]))
    return k


print("(e) the log-linear rule against the numerical policy, same shock sequence")
print("      shock    in sd      max gap     peak: log-linear / numerical")
fig, axes = plt.subplots(2, 2, figsize=(11, 7.5))
gaps = []
for ax, eps0 in zip(axes.ravel(), SHOCKS):
    kl, kn = path_loglinear(eps0), path_numerical(eps0)
    g_ = np.max(np.abs(kn - kl) / kl) * 100
    gaps.append(g_)
    print(f"      {eps0:5.2f}   {eps0/SIGMA:6.1f}    {g_:8.4f}%      "
          f"{np.max(kl/KBAR-1)*100:6.3f}% / {np.max(kn/KBAR-1)*100:6.3f}%")
    ax.plot(100 * (kl / KBAR - 1), lw=2, label="log-linear")
    ax.plot(100 * (kn / KBAR - 1), lw=2, ls="--", label="numerical")
    ax.set_title(f"eps_0 = {eps0:.2f}   (gap {g_:.3f}%)")
    ax.set_xlabel("quarters")
    ax.set_ylabel("$K$, % from steady state")
    ax.legend(frameon=False)
fig.tight_layout()
fig.savefig("PS4_Q4_paths.png", dpi=150)

print()
print(f"    At one standard deviation the two paths differ by {gaps[0]:.4f}% of the")
print("    capital stock -- on the plot they are a single line. The log-linear")
print("    rule is not approximately right here; for any purpose the model is put")
print("    to, it is right.")
print()
print("    The error then grows fast, and faster than proportionally: roughly")
print("    fourfold for every doubling of the shock, which is what an error of")
print("    second order in the deviation looks like. By eps0 = 0.20 -- some")
print(f"    twenty-eight standard deviations, a shock this model would never")
print(f"    generate -- it is {gaps[3]:.2f}% and the two paths are visibly apart.")
print()
print("(f) what the first-order solution discards")
print("    (i) Curvature. It replaces the true policy function by its tangent at")
print("        the steady state. The true policy is concave, so far from the")
print("        steady state the linear rule misstates the response; and being")
print("        symmetric by construction it cannot capture the asymmetry between")
print("        large positive and large negative shocks. Near the steady state a")
print("        tangent is an excellent description of a smooth function, which is")
print("        why the error is invisible at eps0 = 0.01 and obvious at 0.20.")
print("    (ii) Uncertainty itself. A first-order solution is certainty")
print("        equivalent: its coefficients contain no sigma, so the household")
print("        behaves exactly as it would if it knew future shocks would equal")
print("        their means. Precautionary saving, risk premia and option values")
print("        are absent by construction -- the same point as Question 2(b),")
print("        that one may not pull E through a nonlinear function. Note this")
print("        error does NOT shrink with the shock size: it is there even at")
print("        eps0 = 0, and seeing it needs a second-order solution.")
print()
print("(g) is it adequate?")
print("    For Lecture 8's purpose, comfortably. With sigma = 0.007 the economy")
print("    never leaves a neighbourhood a couple of per cent wide, and there the")
print("    two solutions agree to four decimal places.")
print()
print("    But 'adequate' is doing real work in that sentence. The approximation")
print("    would NOT be adequate for questions that turn on precisely what it")
print("    discards: welfare comparisons across regimes with different amounts of")
print("    risk, asset pricing, the effect of uncertainty on investment, or any")
print("    experiment involving large or rare shocks. The adequacy of an")
print("    approximation is a property of the question, not of the model.")
print()
print("    wrote PS4_Q4_paths.png")
