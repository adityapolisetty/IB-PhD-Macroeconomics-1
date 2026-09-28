"""Precompute economic policy curves for the class intuition visual."""

import ast
import json
import math
import re
import sys
from pathlib import Path
from types import SimpleNamespace
import numpy as np

HERE = Path(__file__).resolve().parent
SOURCE = HERE.parent / "reference-python"
OUT = HERE.parent / "src" / "data" / "model-data.json"
# Read reference scripts; write only the model-data file inside this project.
NORM = SimpleNamespace(cdf=lambda x: .5 * (1 + math.erf(float(x) / math.sqrt(2))))


def definitions(path, names, env):
    content = path.read_text(encoding="utf-8")
    for node in ast.parse(content).body:
        if isinstance(node, ast.FunctionDef) and node.name in names:
            exec(ast.get_source_segment(content, node), env)


def segment(path, start, stop, env):
    exec("\n".join(path.read_text(encoding="utf-8").splitlines()[start - 1:stop]), env)


data = {}
prior = json.loads(OUT.read_text()) if OUT.exists() else {}


def save_data():
    OUT.write_text(json.dumps(data, separators=(",", ":")), encoding="utf-8")


extract = dict(np=np, norm=NORM, BETA=.95, RHO=.8, SIGMA=.1,
               N_P=7, N_S=200, N_Q=180)
expath = SOURCE / "Problem_Set_4_Q2.py"
definitions(expath, {"tauchen", "solve"}, extract)
# The physical boundary is V(0,p)=0. Include that anchor rather than clamp
# continuation at the lowest positive stock node.
solve_node = next(n for n in ast.parse(expath.read_text()).body if isinstance(n, ast.FunctionDef) and n.name == "solve")
solve_code = ast.get_source_segment(expath.read_text(), solve_node)
solve_code = solve_code.replace("np.interp(S_next, S, EV[:, i])", "np.interp(S_next, np.r_[0.0, S], np.r_[0.0, EV[:, i]])")
exec(solve_code, extract)
extract["p"], extract["P"] = extract["tauchen"](.8, .1, 7, mu=math.log(2))
extract["S"] = np.exp(np.linspace(math.log(.001), math.log(5), 200))
extract["frac"] = np.linspace(0, .99, 180)
excurves = {}
for kappa in (0., .1, .5):
    V, Q, iterations, gap = extract["solve"](kappa)
    assert gap < 1e-8
    mask = extract["S"] >= .05
    excurves[str(kappa)] = {
        str(j): np.round(100 * Q[mask, j] / extract["S"][mask], 6).tolist()
        for j in (1, 3, 5)
    }
    print("Extraction", kappa, iterations, gap, flush=True)
data["extraction"] = dict(stock=np.round(extract["S"][mask], 6).tolist(),
                          prices=np.round(extract["p"], 6).tolist(), curves=excurves)

firm = dict(np=np, norm=NORM, BETA=.96, DELTA=.1, NU=.6, RHO=.7,
            SIGMA=.3, F_COST=.05, P_SELL=.95, N_K=250, N_Z=11)
fpath = SOURCE / "Problem_Set_5_Q3.py"
definitions(fpath, {"tauchen"}, firm)
firm["Z"], firm["P"] = firm["tauchen"](.7, .3, 11)
segment(fpath, 62, 70, firm)
definitions(fpath, {"solve"}, firm)
target = float(firm["KSTAR"][5])
maskf = (firm["K"] >= .25 * target) & (firm["K"] <= 8.0 * target)
firmcurves = {}
for fixed in (0., .05, .1):
    for resale in (.8, .95, 1.):
        cost = np.where(firm["_GAP"] >= 0, firm["_GAP"], resale * firm["_GAP"])
        V, adjust, policy, iterations, gap = firm["solve"](f=fixed, cost=cost)
        assert gap < 2e-8
        rate = (policy[:, 5] - .9 * firm["K"]) / firm["K"]
        band = np.where(~adjust[:, 5])[0]
        firmcurves[f"{fixed:.2f}:{resale:.2f}"] = dict(
            rate=np.round(100 * rate[maskf], 6).tolist(),
            band=[round(float(firm["K"][band[0]] / target), 6),
                  round(float(firm["K"][band[-1]] / target), 6)] if len(band) else None)
        print("Investment", fixed, resale, iterations, gap, flush=True)
data["investment"] = dict(capital=np.round(firm["K"][maskf] / target, 6).tolist(),
                          curves=firmcurves)

if "--reuse-rbc" in sys.argv and "rbc" in prior:
    data["rbc"] = prior["rbc"]
    save_data()
    print("Data complete; verified RBC policy reused", flush=True)
    raise SystemExit(0)

rbc = dict(np=np, norm=NORM)
rpath = SOURCE / "Problem_Set_4_Q4.py"
segment(rpath, 31, 42, rbc)
segment(rpath, 62, 84, rbc)
definitions(rpath, {"tauchen", "from_hours", "hours_at", "solve_policy"}, rbc)
rbc["N_Z"], rbc["N_K"] = 161, 300
sd = rbc["SIGMA"] / np.sqrt(1 - rbc["RHO"] ** 2)
rbc["logz"], rbc["P"] = rbc["tauchen"](.95, .007, 161, .22 / sd)
rbc["Z"] = np.exp(rbc["logz"])
u = np.linspace(-1, 1, 300)
rbc["K"] = rbc["KBAR"] * (1 + .9 * np.sign(u) * u ** 2)
rbc["Kg"], rbc["Zg"] = rbc["K"][:, None], rbc["Z"][None, :]
rbc["COL"] = np.broadcast_to(np.arange(161), (300, 161))
policy, hours, iterations, gap = rbc["solve_policy"](tol=1e-10)
assert gap < 2e-10 and np.all((hours > 0) & (hours < 1))
print("RBC policy", iterations, gap, flush=True)

# Natural cubic interpolation of the numerical capital rule, separately by Z.
K = rbc["K"]
h = np.diff(K)
rhs = 3 * (np.diff(policy, axis=0)[1:] / h[1:, None]
           - np.diff(policy, axis=0)[:-1] / h[:-1, None])
l = np.ones(len(K)); mu = np.zeros(len(K)); zz = np.zeros_like(policy)
for i in range(1, len(K) - 1):
    l[i] = 2 * (K[i + 1] - K[i - 1]) - h[i - 1] * mu[i - 1]
    mu[i] = h[i] / l[i]
    zz[i] = (rhs[i - 1] - h[i - 1] * zz[i - 1]) / l[i]
c = np.zeros_like(policy)
for i in range(len(K) - 2, -1, -1):
    c[i] = zz[i] - mu[i] * c[i + 1]
b = np.diff(policy, axis=0) / h[:, None] - h[:, None] * (c[1:] + 2 * c[:-1]) / 3
d = (c[1:] - c[:-1]) / (3 * h[:, None])


def spline(k, j):
    i = int(np.clip(np.searchsorted(K, k) - 1, 0, len(K) - 2))
    dx = k - K[i]
    return policy[i, j] + b[i, j] * dx + c[i, j] * dx ** 2 + d[i, j] * dx ** 3


paths = {}
for shock in (.01, .05, .1, .2):
    num = [rbc["KBAR"]]; lin = [0.]
    for t in range(80):
        zhat = shock * .95 ** t
        lin.append(rbc["a_k"] * lin[-1] + rbc["a_z"] * zhat)
        j = int(np.clip(np.searchsorted(rbc["logz"], zhat) - 1, 0, 159))
        weight = (zhat - rbc["logz"][j]) / (rbc["logz"][j + 1] - rbc["logz"][j])
        num.append((1 - weight) * spline(num[-1], j) + weight * spline(num[-1], j + 1))
    lin = rbc["KBAR"] * np.exp(lin)
    num = np.array(num)
    assert np.isfinite(num).all() and np.all((num > K[0]) & (num < K[-1]))
    paths[f"{shock:.2f}"] = dict(
        linear=np.round(100 * (lin / rbc["KBAR"] - 1), 7).tolist(),
        numerical=np.round(100 * (num / rbc["KBAR"] - 1), 7).tolist(),
        gap=round(float(np.max(np.abs(num - lin) / lin) * 100), 7))
    print("RBC shock", shock, "max gap", paths[f"{shock:.2f}"]["gap"], flush=True)
data["rbc"] = dict(paths=paths)
save_data()
print("Data complete", flush=True)
