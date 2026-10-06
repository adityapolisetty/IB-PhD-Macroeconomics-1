# Model data and numerical choices

All seven Python scripts in the tutorial plan are copied into `reference-python/`.

## Models calculated in the browser

- **Solow:** A = 1, α = 1/3, effective depreciation = 0.06. The Cobb–Douglas law of motion admits an exact path used as a comparison with explicit Euler stepping.
- **Household:** r = 0.05, consumption growth = 0.01, wage = 1, initial assets = 1. Wealth uses the analytical solution; zero-wealth events are located by bisection. The transversality comparison uses discounted assets.
- **Shooting:** A = 1, α = 1/3, δ = 0.05, ρ = 0.03, σ = 2; k₀ = 0.3k*. Positive adaptive RK4 steps of at most 0.04. The display horizon is 120 and the classification horizon is 400. Finite-horizon shooting is a numerical illustration of the stable initial choice, not proof of infinite-horizon convergence.
- **Bellman:** A = 1, α = 0.3, δ = 0.1, β = 0.9, with five nodes from 0.25 to 2.25. This deliberately coarse matrix illustrates the update. The class notebook solves on a finer grid.

## Extraction

Reference: `Problem_Set_4_Q2.py`. β = 0.95, ρ = 0.8, σ = 0.1, median price = 2. Seven price nodes, 200 stock nodes, 180 extraction fractions. κ ∈ {0, 0.1, 0.5}. Final Bellman changes below 1e-9.

The interpolation includes the physical boundary V(0,p) = 0. The reference script clamps continuation value at its lowest positive stock node; anchoring zero removes that small-stock truncation artifact. This is recorded explicitly because it makes the no-capacity-cost extraction fraction exactly flat on the plotted range. The plotted stocks run from approximately 0.05 to 5.

## Investment

Reference: `Problem_Set_5_Q3.py`. β = 0.96, δ = 0.10, ν = 0.60, ρ = 0.7, σ = 0.3. 250 capital nodes and 11 productivity nodes. Fixed cost f ∈ {0, 0.05, 0.10}; resale price ∈ {0.8, 0.95, 1}. Final Bellman changes below 2e-8.

The fixed cost is a fraction of the current profit flow. Curves show the investment rate at median productivity, including the zero-investment policy from the no-adjustment choice. Capital is normalised by the median-productivity user-cost benchmark. Inaction bounds are grid locations, not analytical thresholds.

## RBC

Reference: `Problem_Set_4_Q4.py`. β = 0.99, α = 0.36, δ = 0.025, η = 1, steady-state hours = 0.2, ρ = 0.95, σ = 0.007. The numerical policy uses 300 capital nodes and 161 productivity nodes, with a final policy change below 2e-10.

Capital interpolation uses natural cubic splines, implemented in NumPy, rather than SciPy's default not-a-knot spline in the reference. Productivity interpolation is linear. Initial log-productivity innovations are 0.01, 0.05, 0.10 and 0.20, and later innovations are zero. Each pair of rules faces an identical realised productivity path.

The reported gap is the maximum of |K_num − K_linear| / K_linear × 100 over the displayed path. This differs from the percentage-point distance between the two plotted deviations from steady state.

The numerical policy is stochastic. Comparing shock magnitudes mainly illustrates loss of local accuracy; it does not cleanly isolate curvature from risk effects or grid/interpolation error.
