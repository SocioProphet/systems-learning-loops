#!/usr/bin/env python3
"""
core_models — the "model count by domain" thesis, made concrete.

Claim under test (yours): a STEM domain isn't thousands of facts — it's a SMALL, FINITE
set of closed-form governing models. Once you know the form, the answer is COMPUTED, not
recalled; and the dynamical forms can be REDISCOVERED from data (symbolic regression /
SINDy) rather than looked up. The corpus/vectors are scaffolding to index and teach the
application of these few rules — they are the decidable core.

This is a CURATED catalog of the canonical governing models per domain (not every
textbook formula). Each carries: form, type, and discovery method:
  type  : algebraic | ode | pde | identity | definition | inequality
  by    : lookup (definitional)           — must be given/known
          symbolic-regression (sr)        — fit closed form to input→output samples
          sindy                           — discover the governing ODE/PDE from trajectories

Run:  python3 scripts/core_models.py            # counts by domain + discovery mix
      python3 scripts/core_models.py --list      # full catalog
      python3 scripts/core_models.py --json       # machine-readable
"""
import sys, json
from collections import Counter

# (name, form, type, discovery)
CATALOG = {
 'classical_mechanics': [
  ("Newton's 2nd law", "F = m·a", 'ode', 'sindy'),
  ("Kinematics (SUVAT)", "v = v0 + a·t ; x = x0 + v0·t + ½a·t²", 'algebraic', 'sr'),
  ("Work–energy", "W = ΔKE = ½m·v² − ½m·v0²", 'algebraic', 'sr'),
  ("Momentum conservation", "Σ m·v = const", 'algebraic', 'sindy'),
  ("Universal gravitation", "F = G·m1·m2 / r²", 'algebraic', 'sr'),
  ("Hooke's law", "F = −k·x", 'ode', 'sindy'),
  ("Simple harmonic motion", "ẍ = −ω²·x", 'ode', 'sindy'),
  ("Rotational analog", "τ = I·α ; L = I·ω", 'ode', 'sindy'),
  ("Energy conservation", "KE + PE = const", 'algebraic', 'sindy'),
  ("Lagrangian", "d/dt(∂L/∂q̇) − ∂L/∂q = 0", 'ode', 'lookup'),
 ],
 'electromagnetism': [
  ("Gauss (E)", "∮ E·dA = q/ε0", 'pde', 'lookup'),
  ("Gauss (B)", "∮ B·dA = 0", 'pde', 'lookup'),
  ("Faraday", "∮ E·dl = −dΦB/dt", 'pde', 'sindy'),
  ("Ampère–Maxwell", "∮ B·dl = μ0·I + μ0·ε0·dΦE/dt", 'pde', 'lookup'),
  ("Lorentz force", "F = q(E + v×B)", 'algebraic', 'sr'),
  ("Coulomb", "F = k·q1·q2 / r²", 'algebraic', 'sr'),
  ("Ohm", "V = I·R", 'algebraic', 'sr'),
  ("Biot–Savart", "dB = (μ0/4π)·I·dl×r̂ / r²", 'algebraic', 'lookup'),
 ],
 'thermodynamics': [
  ("0th law", "thermal equilibrium is transitive", 'definition', 'lookup'),
  ("1st law", "dU = δQ − δW", 'ode', 'sindy'),
  ("2nd law", "dS ≥ δQ/T", 'inequality', 'lookup'),
  ("3rd law", "S → 0 as T → 0", 'definition', 'lookup'),
  ("Ideal gas", "P·V = n·R·T", 'algebraic', 'sr'),
  ("Gibbs free energy", "G = H − T·S", 'algebraic', 'sr'),
  ("Clausius–Clapeyron", "dP/dT = L / (T·ΔV)", 'ode', 'sindy'),
  ("Maxwell relations", "(∂T/∂V)_S = −(∂P/∂S)_V", 'identity', 'lookup'),
 ],
 'calculus': [
  ("Power rule", "d/dx xⁿ = n·xⁿ⁻¹", 'identity', 'sr'),
  ("Product rule", "(f·g)' = f'·g + f·g'", 'identity', 'lookup'),
  ("Quotient rule", "(f/g)' = (f'·g − f·g')/g²", 'identity', 'lookup'),
  ("Chain rule", "(f∘g)' = f'(g)·g'", 'identity', 'lookup'),
  ("FTC", "∫ₐᵇ f' dx = f(b) − f(a)", 'identity', 'lookup'),
  ("Taylor series", "f(x) = Σ fⁿ(a)/n!·(x−a)ⁿ", 'identity', 'sr'),
  ("L'Hôpital", "lim f/g = lim f'/g'", 'identity', 'lookup'),
  ("Integration by parts", "∫ u dv = u·v − ∫ v du", 'identity', 'lookup'),
 ],
 'linear_algebra': [
  ("Matrix–vector product", "(A·x)_i = Σ_j A_ij·x_j", 'definition', 'lookup'),
  ("Determinant", "det(A) via cofactor/expansion", 'algebraic', 'sr'),
  ("Eigenproblem", "A·v = λ·v", 'algebraic', 'sr'),
  ("Rank–nullity", "rank(A) + nullity(A) = n", 'identity', 'lookup'),
  ("Gram–Schmidt / QR", "A = Q·R", 'algebraic', 'lookup'),
  ("SVD", "A = U·Σ·Vᵀ", 'algebraic', 'sr'),
  ("Least squares", "x̂ = (AᵀA)⁻¹·Aᵀ·b", 'algebraic', 'sr'),
 ],
 'chemistry': [
  ("Ideal gas", "P·V = n·R·T", 'algebraic', 'sr'),
  ("Equilibrium", "K = Π[products]/Π[reactants]", 'algebraic', 'sr'),
  ("Rate law", "rate = k·[A]^m·[B]^n", 'ode', 'sindy'),
  ("Arrhenius", "k = A·exp(−Ea/RT)", 'algebraic', 'sr'),
  ("Nernst", "E = E° − (RT/nF)·ln Q", 'algebraic', 'sr'),
  ("Beer–Lambert", "A = ε·l·c", 'algebraic', 'sr'),
  ("Henderson–Hasselbalch", "pH = pKa + log([A⁻]/[HA])", 'algebraic', 'sr'),
  ("Gibbs–reaction", "ΔG = ΔG° + RT·ln Q", 'algebraic', 'sr'),
 ],
 'probability_statistics': [
  ("Bayes", "P(A|B) = P(B|A)·P(A)/P(B)", 'identity', 'lookup'),
  ("Expectation/variance", "E[X]=Σx·p ; Var=E[X²]−E[X]²", 'definition', 'sr'),
  ("Binomial", "P(k) = C(n,k)·pᵏ·(1−p)ⁿ⁻ᵏ", 'algebraic', 'sr'),
  ("Normal", "f = (1/σ√2π)·exp(−(x−μ)²/2σ²)", 'algebraic', 'sr'),
  ("Poisson", "P(k) = λᵏ·e⁻λ / k!", 'algebraic', 'sr'),
  ("CLT", "X̄ → N(μ, σ²/n)", 'definition', 'lookup'),
  ("OLS regression", "β̂ = (XᵀX)⁻¹·Xᵀy", 'algebraic', 'sr'),
 ],
 'circuits_signals': [
  ("Ohm", "V = I·R", 'algebraic', 'sr'),
  ("Kirchhoff current", "Σ I_in = Σ I_out", 'algebraic', 'lookup'),
  ("Kirchhoff voltage", "Σ V_loop = 0", 'algebraic', 'lookup'),
  ("RC/RL transient", "τ = R·C  (or L/R)", 'ode', 'sindy'),
  ("Impedance", "Z_C = 1/jωC ; Z_L = jωL", 'algebraic', 'sr'),
  ("RLC resonance", "ω0 = 1/√(LC)", 'ode', 'sindy'),
  ("Convolution", "y(t) = (x∗h)(t)", 'definition', 'lookup'),
  ("Fourier", "X(ω) = ∫ x(t)·e⁻ʲωᵗ dt", 'definition', 'lookup'),
 ],
 'astronomy': [
  ("Kepler I–III", "ellipse ; equal areas ; T² ∝ a³", 'algebraic', 'sr'),
  ("Gravitation", "F = G·M·m / r²", 'algebraic', 'sr'),
  ("Stefan–Boltzmann", "L = 4π·R²·σ·T⁴", 'algebraic', 'sr'),
  ("Wien's law", "λ_max·T = b", 'algebraic', 'sr'),
  ("Hubble", "v = H0·d", 'algebraic', 'sr'),
  ("Hydrostatic equilibrium", "dP/dr = −ρ·g", 'ode', 'sindy'),
  ("Schwarzschild radius", "r_s = 2GM/c²", 'algebraic', 'sr'),
 ],
}


def main():
    flags = sys.argv[1:]
    if '--json' in flags:
        print(json.dumps({d: [dict(zip(('name','form','type','by'), m)) for m in ms] for d, ms in CATALOG.items()}, indent=2))
        return
    total = sum(len(v) for v in CATALOG.values())
    by_type, by_disc = Counter(), Counter()
    print(f"# CORE MODEL COUNT BY DOMAIN  (curated canonical governing models)\n")
    print(f"  {'domain':24} {'#models':>7}   discovery mix (lookup / sr / sindy)")
    print(f"  {'-'*24} {'-'*7}   {'-'*34}")
    for d, ms in CATALOG.items():
        disc = Counter(m[3] for m in ms)
        for m in ms:
            by_type[m[2]] += 1; by_disc[m[3]] += 1
        mix = f"{disc.get('lookup',0)} / {disc.get('sr',0)} / {disc.get('sindy',0)}"
        print(f"  {d:24} {len(ms):>7}   {mix}")
        if '--list' in flags:
            for name, form, typ, by in ms:
                print(f"        · {name:26} [{typ:10} {by:6}]  {form}")
    print(f"\n  {'TOTAL':24} {total:>7}   across {len(CATALOG)} domains  (~{total//len(CATALOG)}/domain)")
    sr_sindy = by_disc['sr'] + by_disc['sindy']
    print(f"\n# thesis check:")
    print(f"  · {sr_sindy}/{total} ({100*sr_sindy//total}%) are DISCOVERABLE from data — sr (closed-form fit) or SINDy (governing ODE/PDE).")
    print(f"  · {by_disc['lookup']}/{total} are definitional (must be given/known).")
    print(f"  · by type: " + " · ".join(f"{t}:{n}" for t, n in by_type.most_common()))
    print(f"\n  => a STEM domain ≈ {total//len(CATALOG)} closed-form models. The corpus indexes their")
    print(f"     APPLICATION; the models themselves are a small, decidable, computable core.")


if __name__ == '__main__':
    main()
