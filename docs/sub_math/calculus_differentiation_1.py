# Third party imports

# Third party imports
import sympy as sp

y = sp.Symbol("y")
f = sp.cos(y) + 4 * y + y**3
print(f"Function is: {f}")

x = sp.Symbol("x")
sp.pprint((sp.sqrt(1 / x), x), use_unicode=True)

print(latex(sp.sqrt(1 / x), x), use_unicode=False)

df = sp.diff(f, y)
print(f"Function differentiation is: {df}")

print("Evaluating the differentiation of the function ...")
y_value = 10
limit_value = sp.limit(df, y, 10)

print(f"Function Limit expression for y of {y_value}: {limit_value}")
print(f"Function Limit value for y of {y_value}: {limit_value.evalf()}")
