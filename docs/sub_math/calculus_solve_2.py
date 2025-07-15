# Third party imports
import pandas as pd
import sympy as sp

x = sp.Symbol("x")
function = x * sp.sin(x) / sp.cos(x) - x**2

array_size = 1001
x_max = 10
x_array = [item / (array_size - 1) * x_max for item in list(range(0, 1001))]
function_array = [sp.limit(function, x, item) for item in x_array]

df = pd.DataFrame({"x": x_array, "f(x)": function_array})
df.to_csv("calculus_solve_2.csv", index=False)
