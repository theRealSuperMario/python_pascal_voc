"""
Adapted from: https://gist.github.com/wllhf/a4533e0adebe57e3ed06d4b50c8419ae

Python implementation of the color map function for the PASCAL VOC data set.
Official Matlab version can be found in the PASCAL VOC devkit
http://host.robots.ox.ac.uk/pascal/VOC/voc2012/index.html#devkit
"""
import numpy as np
import matplotlib.pyplot as plt
from skimage.io import imshow
from matplotlib.colors import LinearSegmentedColormap
import voc_utils


def color_map(N=256, normalized=True, matplotlib=True):
    def bitget(byteval, idx):
        return (byteval & (1 << idx)) != 0

    dtype = "float32" if normalized else "uint8"
    cmap = np.zeros((N, 3), dtype=dtype)
    for i in range(N):
        r = g = b = 0
        c = i
        for j in range(8):
            r = r | (bitget(c, 0) << 7 - j)
            g = g | (bitget(c, 1) << 7 - j)
            b = b | (bitget(c, 2) << 7 - j)
            c = c >> 3

        cmap[i] = np.array([r, g, b])

    cmap = cmap / 255 if normalized else cmap
    if matplotlib:
        assert normalized is True
        return LinearSegmentedColormap.from_list("VOClabel_cmap", cmap)
    else:
        return cmap


def color_map_viz():
    labels = voc_utils.OBJECT_CLASS_NAMES
    nclasses = 21
    row_size = 50
    col_size = 500
    cmap = color_map()
    array = np.empty(
        (row_size * (nclasses + 1), col_size, cmap.shape[1]), dtype=cmap.dtype
    )
    for i in range(nclasses):
        array[i * row_size : i * row_size + row_size, :] = cmap[i]
    array[nclasses * row_size : nclasses * row_size + row_size, :] = cmap[-1]

    imshow(array)
    plt.yticks([row_size * i + row_size / 2 for i in range(nclasses + 1)], labels)
    plt.xticks([])
    plt.show()
