# Third party imports
import numpy as np
from matplotlib.offsetbox import AnnotationBbox, OffsetImage

import matplotlib.pyplot as plt #noqa
from PIL import Image

def add_image_to_polar_plot(image_path, transparency):

    """
    Add an image to a polar plot 

    """
    im = Image.open(image_path)
    
    # Convert image to an array and set transparency
    im_array = np.array(im.convert("RGBA"))
    im_array[:, :, 3] = (im_array[:, :, 3].astype(float) * transparency).astype(np.uint8)
    
    fig, ax = plt.subplots(subplot_kw={'projection': 'polar'})
    
    theta_center = np.pi  
    r_center = 1.5  
    zoom_factor = 0.5  

    image_box = OffsetImage(im_array, zoom=zoom_factor)
    
    ab = AnnotationBbox(image_box, (theta_center, r_center), frameon=False, xycoords='polar')
    
    ax.add_artist(ab)
    
    theta = np.linspace(0, 2 * np.pi, 100)
    r = 2 + np.sin(theta)
    ax.plot(theta, r, color='blue', linewidth=2)
    
    # Set limits for the radial axis
    ax.set_ylim(0, 3) # this is optional , because it will effect existing polar plot  
    
    plt.savefig('docs/leg_pycodes/add_image_to_polar_plot.png')


image_path = r'C:\github\assetutilities\docs\leg_pycodes\image_for_plot.png'
transparency = 0.3

add_image_to_polar_plot(image_path, transparency)
