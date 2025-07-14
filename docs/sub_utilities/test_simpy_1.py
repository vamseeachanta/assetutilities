"""
Key References:
- https://docs.sympy.org/latest/modules/functions/index.html
- https://docs.sympy.org/latest/tutorial/calculus.html
"""

import math

import pytest
import sympy as sym


def test_sympy_1():
    x = sym.Symbol("x", real=True)
    x_value = sym.nsolve(2 * sym.cos(x) - x, 0)
    pytest.approx(2 * math.cos(x_value) - x_value, 0)


test_sympy_1()


def test_sympy_catenary_equation_1():
    y = 1874.64
    x = 806.286
    a = sym.Symbol("a", real=True)
    # a_value = sym.nsolve(sym.cosh(x / a) - y / a - 1, 0)
    sym.nsolve(a * sym.cosh(x / a), y)

    pytest.approx(2 * math.cos(x_value) - x_value, 0)


# TODO : Not working
# test_sympy_catenary_equation_1()


def test_sympy_catenary_equation_2():
    y = 1874.64
    x = 806.286
    w = 10000
    F = sym.Symbol("F", real=True)
    s = sym.Symbol("s", real=True)

    eq1 = sym.Eq(y * (2 * F / w - y), s)
    eq2 = sym.Eq(((F / w - y) * math.log((s + F / w) / (F / w - y))), x)

    result = sym.solve([eq1, eq2], (F, s))
    print(result)


#     S = data["d"] * (2 * data["F"] / data["w"] - data["d"])
#     #Horizontal Distance.
#     X = ( ( (data["F"] / data["w"]) - data["d"]) * math.log(
#         (S +
#             (data["F"] / data["w"])) / ((data["F"] / data["w"]) - data["d"]) ) )

# TODO : Not working
# test_sympy_catenary_equation_2()
