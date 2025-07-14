# Standard library imports
# Standard library imports
import os
from pathlib import Path

# Third party imports
import sympy as sp

current_directory = os.path.dirname(os.path.realpath(__file__))
filename_stem = Path(__file__).stem
filename = os.path.join(current_directory, filename_stem + ".md")

x, y, z, t = sp.symbols("x y z t")

latex_form = sp.latex(sp.Integral(sp.sqrt(1 / x), x))

out_file = open(filename, "w")
out_file.write(f"$${latex_form}$$")
out_file.close()
