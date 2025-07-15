# Third party imports

# Third party imports
import sympy as sp

y = sp.Symbol("y")
y_solution = sp.solvers.solve(y**2 - 1, y)

print(f"Solution for y**2-1=0 is: {y_solution}")
