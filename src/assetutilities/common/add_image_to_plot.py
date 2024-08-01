import matplotlib.pyplot as plt
import numpy as np
from PIL import Image

def add_image_to_plot(image_path, x_min, x_max, y_min, y_max, transperancy):
    """
    Add an image to a plot with specified parameters.
    """
    im = Image.open(image_path)

    fig, ax = plt.subplots()

    ax.imshow(im, aspect='auto', extent=(x_min, x_max, y_min, y_max), zorder=-1, alpha=transperancy)

    plt.xlabel('X Axis')
    plt.ylabel('Y Axis')
    plt.title('Plot with Image')

    x1, y1 = [-1, 12], [1, 4]
    x2, y2 = [1, 10], [3, 2]
    plt.plot(x1, y1, label='Line 1', marker='o')
    plt.plot(x2, y2, label='Line 2', marker='o')

    plt.legend()
    plt.show()

image_path = r'src\assetutilities\common\plot.png'
x_min, x_max = 10, 2 # horizontal alignment of image on plot
y_min, y_max = 2, 3  # vertical ......
transperancy = 0.3

add_image_to_plot(image_path, x_min, x_max, y_min, y_max, transperancy)
