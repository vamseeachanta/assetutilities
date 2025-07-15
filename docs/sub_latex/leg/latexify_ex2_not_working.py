# Standard library imports

# Third party imports
import latexify


def fib(x):
    if x == 0:
        return 1
    elif x == 1:
        return 1
    else:
        return fib(x - 1) + fib(x - 2)


latexify.get_latex(fib)
