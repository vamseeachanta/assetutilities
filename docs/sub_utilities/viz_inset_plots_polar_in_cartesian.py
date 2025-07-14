"""
https://matplotlib.org/2.0.2/examples/pylab_examples/axes_demo.html
https://stackoverflow.com/questions/7610973/matplotlib-inset-polar-plot
"""

import numpy as np
from matplotlib import pyplot as plt
from scipy import convolve, randn

# data
t = np.arange(0.0, 20.0, 0.001)
r = np.exp(-t[:1000] / 0.05)
x = randn(len(t))
s = convolve(x, r)[: len(x)] * 0.001
theta = 2 * np.pi * t
#
fig = plt.figure(figsize=(7, 6))

# main
plt.plot(t, s)
plt.axis([0, 1, np.amin(s), 2.5 * np.amax(s)])
plt.xlabel("xlabel")
plt.ylabel("ylabel")

# polar
ax = fig.add_axes([0.2, 0.47, 0.30, 0.40], polar=True, facecolor="yellow")
ax.plot(theta, t, color="blue", lw=3)
ax.set_rmax(1.0)
plt.grid(True)

plt.show()
