"""
https://python-mss.readthedocs.io/examples.html
https://www.thepythoncode.com/article/make-screen-recorder-python
https://datatofish.com/screenshot-python/
"""

import os
import os.path

import mss


def on_exists(fname):
    # type: (str) -> None
    """
    Callback example when we try to overwrite an existing screenshot.
    """

    if os.path.isfile(fname):
        newfile = fname + ".old"
        print(f"{fname} -> {newfile}")
        os.rename(fname, newfile)


with mss.mss() as sct:
    # The screen part to capture
    monitor = {"top": 160, "left": 160, "width": 160, "height": 135}
    output = "sct-{top}x{left}_{width}x{height}.png".format(**monitor)

    # Grab the data
    sct_img = sct.grab(monitor)

    # Save to the picture file
    mss.tools.to_png(sct_img.rgb, sct_img.size, output=output)
    print(output)
