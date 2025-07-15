# Third party imports
# import latex  # noqa
# Third party imports
import matplotlib.pyplot as plt
import sympy as sp

plt.figure()

x, y, z, t = sp.symbols("x y z t")

latex_form = sp.latex(sp.Integral(sp.sqrt(1 / x), x))
print(latex_form)
# Display the equation using LaTeX
plt.text(0.5, 0.5, latex_form, fontsize=15, ha="center")

# Remove the axis
plt.axis("off")

plt.savefig("docs/sub_math/sympy_latex_matplotlib.png")

# Show the plot
# plt.show()
