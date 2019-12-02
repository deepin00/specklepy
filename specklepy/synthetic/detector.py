import sys
import warnings
import numpy as np
from scipy.ndimage import zoom
from astropy import units as u

from specklepy.logging import logging
from specklepy.utils.plot import imshow



class Detector(object):

	"""Class carrying information of an astronomical detector.

	Attributes:
		shape (tuple, dtype=int): 2D tuple of the number of pixels.
		pixel_scale (astropy.units.Quantity): Pixel scale in arcsec.

	Optional attributes are:
		quantum_efficiency (u.Quantity):
		system_gain (u.Quantity):
		readout_noise (u.Quantity):
		dark_current (u.Quantity):
		saturation_level (u.Quantity):
		optics_transmission (u.Quantity):

	Future features:
		Attribute dictionary 'readout_modes': Shall enable the flexible use of
			different readout modes with different parameters.
		Pixel non-uniformity: Shall use a flatfield file to create static
			non-uniform pixel responses.
	"""

	__name__ = 'detector'
	typeerror = 'Detector received {} argument of {} type, but needs to be {}!'



	def __init__(self, shape, pixel_scale, optics_transmission=1, quantum_efficiency=1, system_gain=1, readout_noise=None, dark_current=None, saturation_level=None):
		"""Instantiate Detector class.

		Args:
			shape (tuple, dtype=int): Shape of the detector array, i.e. number
				of pixels. If provided as int, then the detector will be square
				shaped.
			pixel_scale (u.Quantity):
			optics_transmission (u.Quantity, optional):
			quantum_efficiency (u.Quantity, optional):
			system_gain (u.Quantity, optional):
			readout_noise (u.Quantity, optional):
			dark_current (u.Quantity, optional):
			saturation_level (u.Quantity, optional):
		"""

		# Input parameters
		if isinstance(shape, tuple):
			self.shape = shape
		elif isinstance(shape, int):
			self.shape = (shape, shape)
		else:
			raise TypeError(self.typeerror.format('shape', type(shape), 'tuple'))

		if isinstance(pixel_scale, u.Quantity):
			self.pixel_scale = pixel_scale
		elif isinstance(pixel_scale, float) or isinstance(pixel_scale, int):
			logging.warning("Interpreting float type pixel_scale as {}".format(pixel_scale * u.arcsec))
			self.pixel_scale = pixel_scale * u.arcsec
		else:
			raise TypeError(self.typeerror.format('pixel_scale', type(pixel_scale), 'u.Quantity'))

		if isinstance(optics_transmission, float) or isinstance(optics_transmission, int):
			self.optics_transmission = optics_transmission
		else:
			raise TypeError(self.typeerror.format('optics_transmission', type(optics_transmission), 'float'))

		if isinstance(quantum_efficiency, u.Quantity):
			self.quantum_efficiency = quantum_efficiency
		elif isinstance(quantum_efficiency, float) or isinstance(quantum_efficiency, int):
			logging.warning("Interpreting float type quantum_efficiency as {}".format(quantum_efficiency * u.electron / u.ph))
			self.quantum_efficiency = quantum_efficiency * u.electron / u.ph
		else:
			raise TypeError(self.typeerror.format('quantum_efficiency', type(quantum_efficiency), 'u.Quantity'))

		if isinstance(system_gain, u.Quantity):
			self.system_gain = system_gain
		elif isinstance(system_gain, float) or isinstance(system_gain, int):
			logging.warning("Interpreting float type system_gain as {}".format(system_gain * u.electron / u.adu))
			self.system_gain = system_gain * u.electron / u.adu
		else:
			raise TypeError(self.typeerror.format('system_gain', type(system_gain), 'u.Quantity'))

		if dark_current is None or isinstance(dark_current, u.Quantity):
			self.dark_current = dark_current
		elif isinstance(dark_current, float) or isinstance(dark_current, int):
			logging.warning("Interpreting float type dark_current as {}".format(dark_current * u.electron / u.s))
			self.dark_current = dark_current * u.electron / u.s
		else:
			raise TypeError(self.typeerror.format('dark_current', type(dark_current), 'u.Quantity'))

		if readout_noise is None or isinstance(readout_noise, u.Quantity):
			self.readout_noise = readout_noise
		elif isinstance(readout_noise, float) or isinstance(readout_noise, int):
			logging.warning("Interpreting float type readout_noise as {}".format(readout_noise * u.electron))
			self.readout_noise = readout_noise * u.electron
		else:
			raise TypeError(self.typeerror.format('readout_noise', type(readout_noise), 'u.Quantity'))

		if isinstance(saturation_level, u.Quantity) or saturation_level is None:
			self.saturation_level = saturation_level
		elif isinstance(saturation_level, float) or isinstance(saturation_level, int):
			logging.warning("Interpreting float type saturation_level as {}".format(saturation_level * u.electron))
			self.saturation_level = saturation_level * u.electron
		else:
			raise TypeError(self.typeerror.format('saturation_level', type(saturation_level), 'u.Quantity'))

		# Derive secondary parameters
		self.array = np.zeros(self.shape)
		self.FoV = (self.shape[0] * self.pixel_scale, self.shape[1] * self.pixel_scale)



	@property
	def resolution(self):
		return self.pixel_scale

	@resolution.setter
	def resolution(self, value):
		self.pixel_scale = value



	def __call__(self, *args, **kwargs):
		return self.get_counts(*args, **kwargs)



	def __str__(self):
		tmp = "Detector:\n"
		for key in self.__dict__:
			if key == 'array':
				continue
			tmp += "{}: {}\n".format(key, self.__dict__[key])
		return tmp



	def get_counts(self, photon_rate, integration_time, photon_rate_resolution, debug=False):
		"""Computes the counts array from the photon rate.

		Args:
			photon_rate (u.Quantity): Passed to expose() method.
			integration_time (u.Quantity): Passed to expose() and readout()
				methods.
			photon_rate_resolution (u.Quantity): Angular resolution of the
				photon_rate array, used for resampling this to the detectors
				grid.
			debug (bool, optional): Set True for debugging. Default is False.

		Returns:
			counts (u.Quantity): Array of the shape of the detector that
				contains the counts measured within every pixel.
		"""
		self.expose(photon_rate=photon_rate, integration_time=integration_time, photon_rate_resolution=photon_rate_resolution, debug=debug)
		return self.readout(integration_time=integration_time)



	def resample(self, photon_rate, photon_rate_resolution):
		"""Resamples the photon_rate array to the angular resolution of the
		detector.

		Args:
			photon_rate (u.Quantity):
			photon_rate_resolution (u.Quantity):

		Returns:
			photon_rate_resampled_subset (u.Quantity): Resampled subset of the
				photon_rate array.
		"""

		# Assert that the photon_rate covers a larger field of view than the detector field of view
		photon_rate_fieldofview = (photon_rate.shape[0] * photon_rate_resolution, photon_rate.shape[1] * photon_rate_resolution)
		if photon_rate_fieldofview[0] < self.FoV[0] or photon_rate_fieldofview[1] < self.FoV[1]:
			raise ValueError('The field of view of the photon rate is smaller than that of the detector ({}) in at least one dimension!'.format(photon_rate_fieldofview, self.FoV))

		# Resample the photon_rate array to the detector resolution
		zoom_ratio = float(photon_rate_resolution / self.resolution)
		with warnings.catch_warnings():
			warnings.simplefilter("ignore")
			photon_rate_resampled = zoom(photon_rate, zoom_ratio, order=1) * photon_rate.unit
			photon_rate_resampled = photon_rate_resampled / zoom_ratio**2 # This is necessary for flux conservation

		# Extract the central region of shape=Detector.shape
		center = (int(photon_rate_resampled.shape[0] / 2), int(photon_rate_resampled.shape[1] / 2))
		dx = int(self.shape[0] / 2)
		dy = int(self.shape[1] / 2)
		photon_rate_resampled_subset = photon_rate_resampled[center[0] - dx : center[0] + dx , center[1] - dy : center[1] + dy]

		return photon_rate_resampled_subset



	def expose(self, photon_rate, integration_time, photon_rate_resolution, debug=False):
		"""Compute the number of electrons in every pixel after the exposure.

		Args:
			photon_rate (u.Quantity): Passed to expose() method.
			integration_time (u.Quantity): Passed to expose() and readout()
				methods.
			photon_rate_resolution (u.Quantity): Angular resolution of the
				photon_rate array, used for resampling this to the detectors
				grid.
			debug (bool, optional): Set True for debugging. Default is False.
		Returns:
			electrons (u.Quantity)
		"""

		# Input parameters
		if isinstance(photon_rate, float) or isinstance(photon_rate, int):
			logging.warning("Interpreting float type photon_rate as {}".format(photon_rate * u.ph / u.s))
			photon_rate = photon_rate * u.ph / u.s
		elif not isinstance(photon_rate, u.Quantity):
			raise TypeError(self.typeerror.format('photon_rate', type(photon_rate), 'u.Quantity'))

		if isinstance(integration_time, float) or isinstance(integration_time, int):
			logging.warning("Interpreting float type integration_time as {}".format(integration_time * u.s))
			integration_time = integration_time * u.s
		elif not isinstance(integration_time, u.Quantity):
			raise TypeError(self.typeerror.format('integration_time', type(integration_time), 'u.Quantity'))

		if isinstance(photon_rate_resolution, float) or isinstance(photon_rate_resolution, int):
			logging.warning("Interpreting float type photon_rate_resolution as {}".format(photon_rate_resolution * u.arcsec))
			photon_rate_resolution = photon_rate_resolution * u.arcsec
		elif not isinstance(photon_rate_resolution, u.Quantity):
			raise TypeError(self.typeerror.format('photon_rate_resolution', type(photon_rate_resolution), 'u.Quantity'))


		# Resample the photon rate to the detector resolution
		photon_rate = self.resample(photon_rate=photon_rate, photon_rate_resolution=photon_rate_resolution)
		photons = photon_rate * integration_time
		if debug:
			imshow(photons, title='photons')

		# Compute photon shot noise with Poisson statistics
		photons = np.random.poisson(photons.value) * photons.unit

		# Incorporate efficiencies
		if self.optics_transmission is not None:
			photons = photons * self.optics_transmission
		electrons = photons * self.quantum_efficiency
		if debug:
			imshow(electrons, title='electrons')

		# Limit to the saturation level of the detector
		if self.saturation_level is not None:
			electrons = np.minimum(electrons, self.saturation_level) # * self.system_gain)
		electrons = np.round(electrons)
		self.array = electrons
		return electrons



	def readout(self, integration_time, reset=True):
		"""Computes the readout of the detector and returns the ADUs for every
			pixel.

		Args:
			integration_time (u.Quantity):
			reset (bool, optional): If set to True, then the electron count of
				every pixel is reset to zero for the next exposure. Default is
				True.

		Returns:
			counts (u.Quantity): Array of the ADUs for every pixel.
		"""

        # Read copy and clear the array
		electrons = self.array

		# Apply dark_current and readout noise following Poisson or Gaussian statistics
		if self.dark_current is not None:
			electrons = electrons + np.round(np.random.poisson(self.dark_current.value, self.shape) )* self.dark_current.unit * integration_time
		if self.readout_noise is not None:
			electrons = electrons + np.round(np.random.normal(0.0, self.readout_noise.value, self.shape)) * self.readout_noise.unit

		# Convert into ADU
		counts = electrons / self.system_gain
		if self.saturation_level is not None:
			return np.minimum(counts, self.saturation_level / self.system_gain)

		# Reset the detector array
		if reset:
			self.array = np.zeros(self.shape)

		return counts.decompose()
