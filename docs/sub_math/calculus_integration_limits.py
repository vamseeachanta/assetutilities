# Third party imports

# Third party imports
import sympy as sp

y = sp.Symbol("y")
f = y**3 + 4 * y + sp.cos(y)
print(f"Function is: {f}")

i_f = sp.integrate(f, y)
print(f"Function Integration is: {i_f}")

print("Evaluating the integration of the function ...")
y_value = 10
limit_value = sp.limit(i_f, y, y_value)

print(f"Function Limit expression for y of {y_value}: {limit_value}")
print(f"Function Limit value for y of {y_value}: {limit_value.evalf()}")

i_f_y_1_10 = sp.integrate(i_f, (y, 1, 10))
print(f"Function Integration in symbolic expression from 1 to 10 is: {i_f_y_1_10}")
print(f"Function Integration from 1 to 10 is: {i_f_y_1_10.evalf()}")
