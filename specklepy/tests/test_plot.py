import unittest
import numpy as np
from matplotlib.colors import LogNorm

from specklepy.core.aperture import Aperture
from specklepy.utils.transferfunctions import psf, otf, mtf, powerspec
from specklepy.utils import plot


class TestTransferFunctions(unittest.TestCase):

    def setUp(self):
        size = 256
        amp = np.ones((size, size))
        amp = Aperture(x0=128, y0=128, radius=64, data=amp, subset_only=False)().filled(0)
        pha = np.random.rand(size, size) * 2*np.pi * 2**(-1)
        self.aperture = amp * np.exp(1j * pha)

    def test_plot_powerspec1d(self):
        psf_image = psf(self.aperture)
        plot.imshow(psf_image, title="PSF", norm=LogNorm())
        plot.plot_powerspec1d(psf_image)

    def test_desaturate_color(self):
        plot.desaturate_color('tab:blue', ncolors=3)
        plot.desaturate_color('#00FF00', ncolors=3)
        plot.desaturate_color((0, 1, 0), ncolors=3)

if __name__ == "__main__":
    unittest.main()