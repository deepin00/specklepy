import unittest
import numpy as np
from matplotlib.colors import LogNorm

from holopy.core.aperture import Aperture
from holopy.utils.transferfunctions import psf, otf, mtf, powerspec
from holopy.utils.plot import imshow, plot_powerspec1d


class TestTransferFunctions(unittest.TestCase):

    def setUp(self):
        size = 256
        amp = np.ones((size, size))
        pha = np.random.rand(size, size) * 1e1
        # imshow(pha, title="Phase")
        amp = Aperture(x0=128, y0=128, radius=64, data=amp, subset_only=False)()
        self.aperture = amp * np.exp(1j * pha)
        # imshow(np.abs(self.aperture), title="abs Aperture")

    def test_plot_powerspec1d(self):
        psf_image = psf(self.aperture)
        imshow(psf_image, title="PSF", norm=LogNorm())
        plot_powerspec1d(psf_image)

if __name__ == "__main__":
    unittest.main()