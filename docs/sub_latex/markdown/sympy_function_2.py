# Standard library imports
# Standard library imports
import os
from pathlib import Path

# Third party imports
import sympy as sp

cfg = {"md": []}


def define_variables(cfg):
    """
    Define the variables
    """
    y = sp.symbols("y")

    md_text = "Solving for variable :\n"
    cfg["md"].append(md_text)
    md_text = f"{sp.latex(y)}"
    cfg["md"].append(md_text)
    cfg["md"].append("\n\n")

    return y


def define_function(cfg, y):
    """
    Define the function
    """
    f = y**2 + 4 * y + 1

    md_text = "Equation to be solved:\n"
    cfg["md"].append(md_text)
    md_text = f"$${sp.latex(f)}$$"
    cfg["md"].append(md_text)
    cfg["md"].append("\n\n")

    return f


def solve_function(cfg, f, y):
    """
    Solve function
    """
    y_solution = sp.solvers.solve(f, y)

    md_text = "Solution to the above quadratic equation is:\n"
    cfg["md"].append(md_text)
    md_text = f"$${sp.latex(y_solution)}$$"
    cfg["md"].append(md_text)
    cfg["md"].append("\n\n")


y = define_variables(cfg)
f = define_function(cfg, y)
solve_function(cfg, f, y)

current_directory = os.path.dirname(os.path.realpath(__file__))
filename_stem = Path(__file__).stem
filename_md = os.path.join(current_directory, filename_stem + ".md")
filename_pdf = os.path.join(current_directory, filename_stem + ".pdf")

out_file = open(filename_md, "w")
for line in cfg["md"]:
    out_file.write(line)
out_file.close()
