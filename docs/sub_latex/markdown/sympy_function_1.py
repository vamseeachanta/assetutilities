# Standard library imports
# Standard library imports
import os
from pathlib import Path

# Third party imports
import sympy as sp
from markdown_pdf import MarkdownPdf, Section

current_directory = os.path.dirname(os.path.realpath(__file__))
filename_stem = Path(__file__).stem
filename_md = os.path.join(current_directory, filename_stem + ".md")
filename_pdf = os.path.join(current_directory, filename_stem + ".pdf")
out_file = open(filename_md, "w")


def define_function():
    """
    Define the function
    """
    y = sp.symbols("y")
    y = sp.Symbol("y")
    f = y**3 + 4 * y + sp.cos(y)
    return f, y


def integrate_function(f, y):
    """
    Integrate the function
    """
    i_f = sp.integrate(f, y)
    print(f"Function Integration is: {i_f}")
    return i_f, y


print("Evaluating the integration of the function ...")
f, y = define_function()
i_f, y = integrate_function(f, y)

out_file.write("Function")
latex_form = sp.latex(f)
out_file.write(f"$${latex_form}$$")
out_file.write("\n\n")

out_file.write("Integrate function")
latex_form = sp.latex(i_f)
out_file.write(f"$${latex_form}$$")
out_file.write("\n\n")

out_file.write("Evaluate at y = 10")
y_value = 10
limit_value = sp.limit(i_f, y, y_value)
latex_form = sp.latex(limit_value)
out_file.write(f"$${latex_form}$$")
out_file.write("\n\n")

out_file.close()

with open(filename_md) as f:
    markdown_content = f.read()

pdf = MarkdownPdf()
pdf.meta["title"] = "Title"
pdf.add_section(Section(markdown_content, toc=False))
pdf.save(filename_pdf)
