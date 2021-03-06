import numpy as np
from os import path
from astropy.io import fits
from astropy.table import Table
from astropy.nddata import NDData
from photutils.psf import extract_stars
from photutils.psf import EPSFBuilder

from holopy.logging import logging
from holopy.io.parameterset import ParameterSet
from holopy.io.psffile import PSFfile

from holopy.utils.plot import imshow

class EPSFExtraction(object):

    def __init__(self, params):
        if not isinstance(params, ParameterSet):
            raise TypeError("params argument of the PSFExtractor class must be instance of holopy.io.parameterset.ParameterSet!")
        self.params = params
        self.radius = params.psfRadius

        # Extract stars out of params.refSourceFile
        self.star_table = Table.read(params.refSourceFile, format='ascii')


    @property
    def box_size(self):
        return self.radius * 2 + 1


    def extract(self):
        epsf_builder = EPSFBuilder(oversampling=4, maxiters=3, progress_bar=True)

        for file in self.params.inFiles:
            logging.info("Extracting PSFs from file {}".format(file))
            psf_file = PSFfile(file, self.params.tmpDir, frame_shape=(self.box_size, self.box_size))

            frame_number = fits.getheader(file)['NAXIS3']
            for frame_index in range(frame_number):
                print("\rExtracting PSF from frame {}/{}".format(frame_index + 1, frame_number), end='')
                with fits.open(file) as hdulist:
                    frame = hdulist[0].data[frame_index]
                    stars = extract_stars(NDData(data=frame), self.star_table, size=self.box_size)

                    # Compute instantaneous PSF
                    # epsf, fitted_stars = epsf_builder(stars)
                    epsf = np.zeros(stars[0].data.shape)
                    for star in stars:
                        epsf += star.data

                    psf_file.update_frame(frame_index, epsf)
            print('\r')
