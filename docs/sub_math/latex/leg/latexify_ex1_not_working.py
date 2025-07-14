# Standard library imports

# Third party imports
import latexify


@latexify.function
def solve(a, b, c):
    return (-b + math.sqrt(b**2 - 4 * a * c)) / (2 * a)


solve
