import numpy as np
from astropy.io import fits
from astropy.stats import sigma_clipped_stats
from photutils import DAOStarFinder, IRAFStarFinder

from specklepy.exceptions import SpecklepyTypeError, SpecklepyValueError
from specklepy.logging import logger


def extract_sources(image, noise_threshold, fwhm, star_finder='DAO', background_subtraction=False, write_to=None,
                    verbose=True):
    """Extract sources from an image with a StarFinder routine.

    Long description...

    Args:
        image (np.ndarray or str):
            Image array or the name of a file containing the image array.
        noise_threshold (float):
        fwhm (float):
        star_finder (str, optional):
            Choose whether the 'DAO' or 'IRAF' StarFinder implementations from photutils shall be used. Default is
            'DAO'.
        background_subtraction (bool, optional):
            Enable background subtraction. Default is False.
        write_to (str, optional):
            If provided as a str, the list of identified sources  is saved to this file.
        verbose (bool, optional):
            Set to False, if reducing the terminal output. Default is True.

    Returns:
        sources (astropy.table.Table): Table of identified sources, None if no
            sources are detected.
    """

    # Input parameters
    if isinstance(image, np.ndarray):
        filename = 'current cube'
    elif isinstance(image, str):
        logger.info("The argument image '{}' is interpreted as file name.".format(image))
        filename = image
        image = fits.getdata(filename)
    else:
        raise SpecklepyTypeError('extract_sources()', argname='image', argtype=type(image),
                                 expected='np.ndarray or str')

    # Prepare noise statistics
    mean, median, std = sigma_clipped_stats(image, sigma=3.0)
    logger.info(f"Noise statistics for {filename}:\n\tMean = {mean:.3}\n\tMedian = {median:.3}\n\tStdDev = {std:.3}")

    # Instantiate starfinder object
    if not isinstance(star_finder, str):
        raise SpecklepyTypeError('extract_sources', argname='starfinder', argtype=type(star_finder), expected='str')
    if 'dao' in star_finder.lower():
        star_finder = DAOStarFinder(fwhm=fwhm, threshold=noise_threshold * std)
    elif 'iraf' in star_finder.lower():
        star_finder = IRAFStarFinder(fwhm=fwhm, threshold=noise_threshold * std)
    else:
        raise SpecklepyValueError('extract_sources', argname='star_finder', argvalue=star_finder,
                                  expected="'DAO' or 'IRAF")

    # Find stars
    if background_subtraction:
        logger.info("Subtracting background...")
        image -= median
    logger.info("Finding sources...")
    sources = star_finder(image)

    # Reformatting sources table
    sources.sort('flux', reverse=True)
    sources.rename_column('xcentroid', 'x')
    sources.rename_column('ycentroid', 'y')
    sources.keep_columns(['x', 'y', 'flux'])
    for col in sources.colnames:
        sources[col].info.format = '%.8g'  # for consistent table output
    if verbose:
        logger.info("Found {} sources:\n{}".format(len(sources), sources))
    else:
        logger.info("Found {} sources".format(len(sources)))

    # Save sources table to file, if writeto is provided
    if write_to is not None:
        logger.info("Writing list of sources to file {}".format(write_to))
        sources.write(write_to, format='ascii', overwrite=True)

    return sources
