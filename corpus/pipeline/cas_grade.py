#!/usr/bin/env python3
"""
cas_grade — deterministic (T1) grading for the templatable subset of math problems.

The insight: a calculus/arithmetic problem is a parametric template — a known
operation over an expression with swappable literals. So we don't *judge* the
answer with a model (T2), we *compute* the canonical answer with a CAS and check
the student's final for symbolic/numeric equivalence (T1, replayable).

Coverage is honest: problems we can't reduce to a rule return gradeable=false, and
the caller falls back to T2. We never guess a verdict we didn't compute.

I/O: JSON on stdin {"problem": str, "student": str (optional)} → JSON on stdout
     {"type", "gradeable", "canonical", "correct"(if student), "reason"}
"""
import sys, json, re
import sympy as sp
from sympy.parsing.sympy_parser import (
    parse_expr, standard_transformations, implicit_multiplication_application,
    convert_xor,
)

X = sp.Symbol('x')
TRANS = standard_transformations + (implicit_multiplication_application, convert_xor)
LOCAL = {'x': X, 'e': sp.E, 'pi': sp.pi, 'ln': sp.log, 'sin': sp.sin, 'cos': sp.cos,
         'tan': sp.tan, 'sec': sp.sec, 'csc': sp.csc, 'cot': sp.cot, 'exp': sp.exp,
         'sqrt': sp.sqrt, 'log': sp.log, 'sinh': sp.sinh, 'cosh': sp.cosh,
         'arcsin': sp.asin, 'arccos': sp.acos, 'arctan': sp.atan}


def clean(s: str) -> str:
    """Normalize human/OCR math notation toward sympy-parseable text."""
    s = s.strip()
    s = s.replace('−', '-').replace('–', '-').replace('·', '*').replace('×', '*')
    s = s.replace('∞', 'oo').replace('√', 'sqrt')
    s = re.sub(r'e\s*\^', 'exp', s)          # e^(..) -> exp(..)
    s = re.sub(r'\\frac\{([^}]*)\}\{([^}]*)\}', r'((\1)/(\2))', s)  # LaTeX frac
    s = s.replace('\\', ' ')
    s = re.sub(r'\s+', ' ', s)
    return s.strip()


def parse(expr: str):
    return parse_expr(clean(expr), local_dict=LOCAL, transformations=TRANS, evaluate=True)


def grab_expr(text: str):
    """Pull the operand expression out of a problem statement."""
    t = clean(text)
    m = re.search(r'f\s*\(\s*x\s*\)\s*=\s*([^.;,\n]+)', t)          # f(x) = ...
    if m: return m.group(1)
    m = re.search(r'(?:of|derivative of|integral of|differentiate|integrate)\s+([^.;,\n]+)', t, re.I)
    if m: return m.group(1)
    return None


def classify(text: str) -> str:
    t = text.lower()
    if re.search(r"derivative|differentiate|d/dx|f\s*'\s*\(", t): return 'derivative'
    if re.search(r'integral|integrate|antiderivative|∫', t): return 'integral'
    if re.search(r'\blim(it)?\b', t): return 'limit'
    # pure arithmetic / word-problem numeric: only if it's a bare numeric expression
    if re.fullmatch(r'[-+*/^().\d\s]+', text.strip()): return 'arithmetic'
    return 'unknown'


# OCR of OCW math PDFs is noisy and exercises are often multi-part word problems. A
# deterministic grade is only trustworthy on a PRISTINE single directive — otherwise we
# must abstain (gradeable=false) and let the T2 judge handle it. High precision > recall.
JUNK = re.compile(r'[�“”]|exercises|unit\s+\d|chapter|theorem|prove|sketch|graph\b', re.I)
CLEAN_EXPR = re.compile(r'^[\w\s+\-*/^().,]*$')


def is_clean_directive(text: str) -> bool:
    if len(text) > 200 or JUNK.search(text):
        return False
    # at most one sub-part marker; a real word problem has several
    if len(re.findall(r'\b[a-d]\)\s|\(\d+\)|\b\d\.\s', text)) > 1:
        return False
    return True


def valid_expr(expr_s: str, expr, need_x: bool) -> bool:
    if not expr_s or not CLEAN_EXPR.match(expr_s.strip()):
        return False
    if len(sp.sstr(expr)) < 2:
        return False
    if need_x and X not in expr.free_symbols:
        return False
    return True


def canonical_answer(text: str):
    """Return (type, sympy_answer) or (type, None) if not reducible/clean."""
    kind = classify(text)
    if kind == 'unknown':
        return kind, None
    if not is_clean_directive(text):
        return kind, None                      # noisy/multi-part ⇒ abstain → T2
    try:
        if kind == 'arithmetic':
            return kind, sp.nsimplify(parse(text))
        expr_s = grab_expr(text)
        if not expr_s:
            return kind, None
        if kind == 'limit':
            expr_s = re.split(r'\bas\b|\bwhen\b|\bx\s*(?:->|→)', expr_s, flags=re.I)[0]
        expr = parse(expr_s)
        if not valid_expr(expr_s, expr, need_x=True):
            return kind, None                  # garbled extraction ⇒ abstain → T2
        if kind == 'derivative':
            return kind, sp.simplify(sp.diff(expr, X))
        if kind == 'integral':
            return kind, sp.simplify(sp.integrate(expr, X))   # indefinite; +C implied
        if kind == 'limit':
            mp = re.search(r'(?:x\s*(?:->|→|to)\s*)(-?\w+|oo|0|infinity)', clean(text), re.I)
            pt = mp.group(1) if mp else '0'
            pt = {'infinity': sp.oo, 'oo': sp.oo}.get(pt, pt)
            return kind, sp.simplify(sp.limit(expr, X, sp.sympify(pt, locals=LOCAL)))
    except Exception:
        return kind, None
    return kind, None


def student_final(s: str):
    m = re.search(r'FINAL\s*:?\s*(.+)', s, re.I)
    cand = (m.group(1) if m else s).strip().splitlines()[0] if s.strip() else ''
    cand = re.sub(r'^[a-dA-D]\)\s*', '', cand)
    cand = re.sub(r'\+\s*C\b', '', cand)         # drop integration constant for compare
    try:
        return parse(cand)
    except Exception:
        return None


def equivalent(a, b) -> bool:
    if a is None or b is None: return False
    try:
        d = sp.simplify(a - b)
        if d == 0: return True
        # numeric fallback over a few sample points (handles forms simplify misses)
        pts = [sp.Rational(1, 3), sp.Rational(7, 5), sp.Rational(11, 4)]
        for p in pts:
            try:
                if abs(complex(d.subs(X, p))) > 1e-6: return False
            except Exception:
                return False
        return True
    except Exception:
        return False


def main():
    data = json.load(sys.stdin)
    problem, student = data.get('problem', ''), data.get('student')
    kind, ans = canonical_answer(problem)
    out = {'type': kind, 'gradeable': ans is not None,
           'canonical': (sp.sstr(ans) if ans is not None else None)}
    if ans is not None and student is not None:
        sf = student_final(student)
        out['correct'] = equivalent(ans, sf)
        out['student_parsed'] = sp.sstr(sf) if sf is not None else None
        out['reason'] = 'symbolic/numeric equivalence to computed answer'
    print(json.dumps(out))


if __name__ == '__main__':
    main()
