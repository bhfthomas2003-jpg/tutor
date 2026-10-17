"""SymPy checks of 'lhs == rhs' strings. Passing proves ONLY that identity; it is not a proof of the lesson."""
import re
import sympy as sp
from sympy.parsing.sympy_parser import parse_expr, standard_transformations, implicit_multiplication_application, convert_xor

_T = standard_transformations + (implicit_multiplication_application, convert_xor)
_OK = re.compile(r"^[0-9A-Za-z+\-*/^().,\s]+$")  # no underscores/quotes: blocks dunder tricks

def _p(s):
    if not _OK.match(s) or len(s) > 200:
        raise ValueError("unsupported characters")
    return parse_expr(s, transformations=_T)

def run(scenes):
    out = []
    for i, s in enumerate(scenes):
        for c in s.checks:
            res = "unverified"
            try:
                if "==" in c:
                    l, r = c.split("==", 1)
                    res = "pass" if sp.simplify(_p(l) - _p(r)) == 0 else "fail"
            except Exception:
                pass
            out.append({"scene": i, "check": c, "result": res})
    return out
