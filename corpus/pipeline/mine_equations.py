#!/usr/bin/env python3
"""
mine_equations — empirically test the "few governing models per domain" thesis against
the real corpus. The insight: a GOVERNING law recurs across many courses; a one-off
worked calculation appears once. So we extract equation-like fragments from the brain
shards, normalize away the specific numbers/units (leaving the FORM), and rank forms by
how widely they recur. The high-recurrence forms are the domain's governing core —
which should be a small set, matching scripts/core_models.py.

Honest about noise: PDF/OCR math extraction is messy, so raw candidate counts are large;
the SIGNAL is the small head of cross-course-recurring forms, not the noisy tail.

Source: the brain shards (build-corpus.ts output) — text already classified by field.

Run:  python3 scripts/mine_equations.py [brain-dir] [--top N] [--field NAME]
"""
import sys, os, re, json, glob
from collections import defaultdict, Counter

_args = sys.argv[1:]
TOP = int(next((_args[i+1] for i, a in enumerate(_args) if a == '--top'), 12))
ONLY = next((_args[i+1] for i, a in enumerate(_args) if a == '--field'), None)
# positional brain-dir = a bare arg that isn't a flag or a flag's value
_flagvals = {_args[i+1] for i, a in enumerate(_args) if a in ('--top', '--field') and i+1 < len(_args)}
BRAIN = next((a for a in _args if not a.startswith('--') and a not in _flagvals),
             os.path.expanduser('~/Downloads/MIT OCW/_brain'))

# An equation candidate: a short fragment containing '=' flanked by math-ish content.
EQ = re.compile(r'([A-Za-zΑ-Ωα-ω][A-Za-zΑ-Ωα-ω0-9_\^\(\)\.\,\+\-\*/ ]{0,30}=[^=\n]{1,40})')
# Web/markup chrome that recurs across every OCW course (badges, mathjax config, HTML attrs).
JUNK = re.compile(r'[�"\'<>{}]|http|src=|href|url|\.js|badge|shield|semver|npm|flat|template|'
                  r'title=|label=|style=|color=|sort=|group|svg|mathjax|figure|table|chapter|'
                  r'page|\bsee\b|license|creative commons|copyright', re.I)
# Only math characters allowed in a clean equation form.
MATHY = re.compile(r'^[A-Za-zΑ-Ωα-ω0-9_\^\(\)\.\,\+\-\*/√∑∫∂π°≈≤≥ =]+$')
# Material types that are actual academic substance (skip 'reference' = mostly chrome).
ACADEMIC = {'lecture', 'recitation', 'exam', 'solution', 'assignment'}


def normalize(eq: str) -> str:
    """Strip specifics, keep the FORM: numbers→#, collapse ws, drop units/trailing punct."""
    s = eq.strip().lower()
    s = re.sub(r'\d+(\.\d+)?', '#', s)              # numbers → #
    s = re.sub(r'\s+', '', s)                        # drop whitespace
    s = re.sub(r'[.,;:]+$', '', s)
    return s


def good(eq: str) -> bool:
    if JUNK.search(eq) or not MATHY.match(eq):
        return False
    lhs, _, rhs = eq.partition('=')
    lhs, rhs = lhs.strip(), rhs.strip()
    if not lhs or not rhs or len(lhs) > 14:          # LHS is a variable/short expr, not prose
        return False
    # both sides must carry a letter (a real relation, not "x = 5"); reject all-numeric tail
    return bool(re.search(r'[A-Za-zΑ-Ωα-ω]', lhs)) and bool(re.search(r'[A-Za-zΑ-Ωα-ω]', rhs))


def main():
    # per-course files (BRAIN/<field>/<slug>.jsonl) + any legacy top-level shards
    shards = sorted(glob.glob(os.path.join(BRAIN, '**', '*.jsonl'), recursive=True))
    shards = [s for s in shards if not os.path.basename(s).startswith(('.', '_'))]
    if not shards:
        print(f"no brain shards in {BRAIN} yet — let build-corpus.ts bank more first.")
        return
    # field -> normalized-form -> set(slugs it appears in)
    forms = defaultdict(lambda: defaultdict(set))
    raw = Counter()
    chunks = Counter()
    for sh in shards:
        for line in open(sh, errors='ignore'):
            try:
                r = json.loads(line)
            except Exception:
                continue
            field = r.get('field', os.path.basename(os.path.dirname(sh)))
            if ONLY and field != ONLY:
                continue
            if r.get('material') not in ACADEMIC:    # skip reference/syllabus chrome
                continue
            chunks[field] += 1
            for m in EQ.findall(r.get('text', '')):
                if not good(m):
                    continue
                raw[field] += 1
                forms[field][normalize(m)].add(r.get('slug', ''))

    print(f"# EQUATION MINING — recurrence across courses = governing-model signal")
    print(f"# brain={BRAIN} · {len(shards)} shard(s)\n")
    for field in sorted(forms):
        f = forms[field]
        # governing = forms recurring in >=2 distinct courses
        recurring = sorted(((form, len(slugs)) for form, slugs in f.items() if len(slugs) >= 2), key=lambda kv: -kv[1])
        print(f"## {field}  — {chunks[field]} chunks · {raw[field]} eq-candidates · {len(f)} distinct forms · {len(recurring)} recur in ≥2 courses")
        for form, ncourses in recurring[:TOP]:
            print(f"     {ncourses:>2} courses   {form[:70]}")
        if not recurring:
            print("     (no cross-course recurrence yet — corpus still thin for this field)")
        print()
    print("# read: the SMALL head of cross-course-recurring forms ≈ the domain's governing core")
    print("# (matches the ~7/domain in core_models.py). Raw candidates are the noisy worked-example tail.")


if __name__ == '__main__':
    main()
