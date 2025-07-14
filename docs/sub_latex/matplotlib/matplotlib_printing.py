# Third party imports
import matplotlib.pyplot as plt

# Create the figure and axis
plt.figure()

# Display the equation using LaTeX
plt.text(0.5, 0.5, r"$\cos(y) + 4y + y^3$", fontsize=15, ha="center")

# Remove the axis
plt.axis("off")

plt.savefig("docs/sub_math/figures/matplotlib_printing.png")
# Show the plot
plt.show()
