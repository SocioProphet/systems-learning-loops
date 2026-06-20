#!/usr/bin/env python3
"""
gen_exam — generate clean, parametric exam/practice problems with COMPUTED answers.

The insight (yours): an MIT problem is a template — a fixed operation over an
expression skeleton with swappable coefficients/exponents/units. So we can emit an
unbounded bank of fresh problems, each with a deterministically-computed answer
(sympy), which is then T1-gradeable end to end (cas_grade.py agrees by construction).
This is the "multiple sets of sampled training corpora and exam results" generator.

Each item: {id, template, topic, problem, answer, slots}. Clean by construction, so
the deterministic grader has ~100% coverage on this bank (unlike OCR'd PDFs).

Usage:  python3 scripts/gen_exam.py [N] [--seed S] [--topic derivative,integral,...]
        → JSONL on stdout, one problem per line.
"""
import sys, json, random
import sympy as sp

x = sp.Symbol('x')


def _poly(rng, terms=2, maxdeg=4, maxc=6):
    """A random polynomial-ish expression skeleton."""
    e = 0
    used = set()
    for _ in range(terms):
        n = rng.randint(1, maxdeg)
        if n in used:
            continue
        used.add(n)
        e += rng.randint(1, maxc) * x**n
    return e or x


def t_derivative(rng):
    forms = [
        lambda: rng.randint(2, 6) * x**rng.randint(2, 5),                       # power rule
        lambda: rng.randint(1, 4) * x * sp.exp(rng.randint(1, 3) * x),          # product+chain
        lambda: sp.sin(rng.randint(1, 4) * x) * x**rng.randint(1, 2),           # product
        lambda: _poly(rng, terms=3),                                            # polynomial
        lambda: sp.log(rng.randint(1, 3) * x**2 + 1),                           # chain
    ]
    f = rng.choice(forms)()
    return f"Compute the derivative of f(x) = {sp.sstr(f)}", sp.simplify(sp.diff(f, x))


def t_integral(rng):
    f = rng.choice([
        lambda: rng.randint(2, 6) * x**rng.randint(1, 5),
        lambda: _poly(rng, terms=2),
        lambda: rng.randint(1, 4) * sp.cos(rng.randint(1, 3) * x),
        lambda: rng.randint(1, 4) * sp.exp(rng.randint(1, 3) * x),
    ])()
    return f"Evaluate the integral of {sp.sstr(f)}", sp.simplify(sp.integrate(f, x))


def t_limit(rng):
    a, b = rng.randint(1, 4), rng.randint(1, 4)
    forms = [
        (sp.sin(a * x) / (b * x), 0, sp.Rational(a, b)),
        ((1 - sp.cos(a * x)) / x**2, 0, sp.Rational(a * a, 2)),
        ((sp.exp(a * x) - 1) / (b * x), 0, sp.Rational(a, b)),
    ]
    expr, pt, _ = rng.choice(forms)
    return f"Find the limit of {sp.sstr(expr)} as x -> {pt}", sp.simplify(sp.limit(expr, x, pt))


def t_arithmetic(rng):
    a, b, c, d = (rng.randint(2, 12) for _ in range(4))
    expr = f"{a}*({b}+{c}) - {d}**2"
    return f"{expr}", sp.nsimplify(sp.sympify(expr))


TEMPLATES = {
    'derivative': t_derivative, 'integral': t_integral,
    'limit': t_limit, 'arithmetic': t_arithmetic,
}


def main():
    args = sys.argv[1:]
    n = next((int(a) for a in args if a.isdigit()), 20)
    seed = next((int(args[i + 1]) for i, a in enumerate(args) if a == '--seed'), 0)
    topics = next((args[i + 1].split(',') for i, a in enumerate(args) if a == '--topic'), list(TEMPLATES))
    rng = random.Random(seed)
    for i in range(n):
        topic = rng.choice(topics)
        problem, answer = TEMPLATES[topic](rng)
        print(json.dumps({
            'id': f'gen-{seed}-{i}', 'template': topic, 'topic': topic,
            'problem': problem, 'answer': sp.sstr(answer),
        }))


if __name__ == '__main__':
    main()
