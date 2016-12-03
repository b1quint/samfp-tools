#!/usr/bin/env python2
# -*- coding: utf8 -*-
"""
    Wavelength Calibration

    This script calculates the wavelength calibration using a Terminal Interface
    with the User.

    Todo
    ----
    -   Look in the header for other options of FP_ZFSR.
    -   Look in the header for other options of FP_ZSTEP.
    -
"""
from __future__ import division, print_function

import argparse
import astropy.io.fits as pyfits
import logging as log
import numpy as np
import time

from scipy import signal
from scipy import ndimage, stats
from numpy import ma

__author__ = 'Bruno Quint'


class WavelengthCalibration:
    def __init__(self, verbose=False, debug=False):

        self._log = log
        self.set_verbose(verbose)
        self.set_debug(debug)

        return

    def center_peak(self, data, center):
        """
        Based on the most probable center position, rolls the line so it lies in
        the center of the data-cube.
        """
        cube_center = data.shape[0] // 2
        shift_size = cube_center - center
        data = np.roll(data, shift_size, axis=0)

        return data

    def debug(self, message):
        """Print a debug message using the log system."""
        self._log.debug(message)
        return

    def find_current_peak_position(self, data):
        """
        Finds the current average peak position.

        Parameters
        ----------
            data : numpy.ndarray
            A phase-corrected datacube.

        Returns
        -------
            peak_position : int
            The argument of the highest local maximum.
        """
        self.info('Finding current peak position.')
        data = data.sum(axis=2)
        data = data.sum(axis=1)
        data = np.where(data < 0.75 * data.max(), 0, data)
        peaks = signal.argrelmax(data, axis=0, order=4)
        self.debug('Encountered {:d} peaks: '.format(len(peaks)))
        #for i in range(len(peaks)):
        #    self.debug(' Peak #{:d} = channels'.format(peaks[i]))

        #peak_position = np.argmax(data)

        # around_peak = np.arange(5) - 2
        # around_peak = np.delete(around_peak, 2)
        # around_peak += peak_position
        # around_peak = np.where(around_peak < 0, 0, around_peak)
        # around_peak = np.where(around_peak > data.size - 1, data.size - 1,
        #                        around_peak)
        #
        # is_peak = True
        # for i in range(around_peak.size):
        #     p = data[around_peak[i]] < data[peak_position]
        #     is_peak *= p
        #     log.debug('Comparing %d and %d frames - %s' % (
        #     peak_position, around_peak[i], 'True' if p else 'False'))
        #
        # return peak_position

        # depth = data.shape[0]

        # data = ndimage.median_filter(data, size=[3, 1, 1])
        # data = ma.MaskedArray(data, mask=np.zeros_like(data))
        #
        # peaks = np.argmax(data, axis=0)
        #
        # for i in range(interactions):
        #
        #     peak_neighbors = (peaks
        #         + np.arange(5, dtype=int)[:, np.newaxis, np.newaxis] - 2)
        #
        #     peak_neighbors = np.where(peak_neighbors > 0, peak_neighbors, 0)
        #     peak_neighbors = np.where(peak_neighbors < depth - 1,
        #                               peak_neighbors, depth - 1)
        #
        #     peak_neighbors = np.delete(peak_neighbors, 2, 0)
        #
        # for i in range(5):
        #     print(i)
        #     print(data.take(peak_neighbors[i]).astype(int))
        #     cond += np.where(temp < max_frame, 1, 0)
        # print(cond.astype(int))

        # peaks = ma.MaskedArray(data.argmax(0), mask=cond)
        # print(peaks)
        # data = ma.MaskedArray(data, mask=cond * np.ones_like(data))
        # peaks = peaks.ravel()
        # new_peak = int(stats.mstats.mode(peaks).mode[0])

        # if new_peak == peak:
        #     peak = new_peak
        #     log.debug('Final peak found at %d' % peak)
        #     break
        # peak = new_peak
        # log.debug('New peak found at %d' % peak)

    def get_central_wavelength(self, header=None, key='FP_WOBS'):
        """
        Read the central wavelength from a header or from the user input.

        :param header:
        :return central_wavelength: systemic central wavelength.
        :rtype central_wavelength: float
        """
        log = self.log

        try:
            central_wavelength = float(header[key])
        except KeyError:
            log.warning('%s card was not found in the header.' % key)
            central_wavelength = input(' Please, enter the systemic observed '
                                       'wavelength: \n >')
        except TypeError:
            log.warning('Header was not passed to "WCal.get_central_wavelength"'
                        ' method')
            central_wavelength = input(' Please, enter the systemic observed '
                                       'wavelength: \n > ')

        return central_wavelength

    def get_logger(self):
        """Create and return a customized logger object.

        :return log: the logger object.
        :rtype log: log.Logger
        """
        lf = MyLogFormatter()

        ch = self.log.StreamHandler()
        ch.setFormatter(lf)

        self.log.captureWarnings(True)
        log = self.log.getLogger("phasemap_fit")
        log.addHandler(ch)

        return log

    def get_wavelength_step(self, w_central, header=None, key_gap_size='FP_GAP',
                            key_zfsr='PHMFSR', key_z_step='PHMSAMP'):
        """
        Calculates the wavelength step between channels.

        :return w_step: wavelength increment beween channels.
        :rtype w_step: float
        """
        log = self.log

        try:
            gap_size = header[key_gap_size]
        except KeyError:
            log.warning('%s card was not found in the header.' % key_gap_size)
            gap_size = input('Please, enter the FP nominal gap size in microns:'
                             '\n > ')
        except TypeError:
            log.warning('Header was not passed to "WCal.get_wavelength_step"'
                        ' method')
            gap_size = input('Please, enter the FP nominal gap size in microns:'
                             '\n > ')

        try:
            z_fsr = header[key_zfsr]
        except KeyError:
            log.warning('%s card was not found in the header.' % key_zfsr)
            z_fsr = input('Please, enter the Free-Spectral-Range in bcv:'
                          '\n > ')
        except TypeError:
            log.warning('Header was not passed to "WCal.get_wavelength_step"'
                        ' method')
            z_fsr = input('Please, enter the Free-Spectral-Range in bcv:'
                          '\n > ')

        try:
            z_step = header[key_z_step]
        except KeyError:
            log.warning('%s card was not found in the header.' % key_z_step)
            z_step = input('Please, enter the step between channels in bcv'
                           '\n > ')
        except TypeError:
            log.warning('Header was not passed to "WCal.get_wavelength_step"'
                        ' method')
            z_step = input('Please, enter the step between channels in bcv'
                           '\n > ')

        w_fsr = w_central / (gap_size * (1 + 1 / gap_size ** 2))
        w_step = w_fsr / z_fsr * z_step

        return w_step

    def info(self, message):
        """Print an info message using the log system."""
        self._log.info(message)
        return

    def load_data(self, input_filename):
        """Load the input data and header."""

        self.info('Loading %s' % input_filename)
        data = pyfits.getdata(input_filename)
        hdr = pyfits.getheader(input_filename)
        self.info('Done')

        return data, hdr

    def print_header(self):
        """
        Simply print a header for the script.
        """
        msg = "\n " \
              " Data-Cube Wavelength Calibration\n" \
              " by Bruno C. Quint (bquint@ctio.noao.edu)\n"
        self.info(msg)
        return

    def run(self, filename, output=None):

        data, hdr = self.load_data(filename)
        cpp = self.find_current_peak_position(data)
        data = self.center_peak(data, cpp)

        w_center = self.get_central_wavelength(hdr)
        w_step = self.get_wavelength_step(w_center, hdr)

        hdr['CRPIX3'] = data.shape[0] / 2 + 1
        hdr['CRVAL3'] = w_center
        hdr['C3_3'] = w_step
        hdr['CR3_3'] = hdr['CDELT3'] = hdr['C3_3']
        hdr['CUNIT3'] = 'angstroms'

        pyfits.writeto(filename.replace('.fits', '.wcal.fits'), data, hdr,
                       clobber=True)

    def set_log_level(self, level):
        """
        Set the internal logger level.

        :param level: logger level.
        :type level: logger.DEBUG|logger.WARNING|logger.CRITICAL
        """
        self.log.setLevel(level)

    def set_debug(self, debug):
        """
        Turn on debug mode.

        Parameter
        ---------
            debug : bool
        """
        if debug:
            self._log.basicConfig(level=self._log.DEBUG, format='%(message)s')

    def set_verbose(self, verbose):
        """
        Turn on verbose mode.

        Parameter
        ---------
            verbose : bool
        """
        if verbose:
            self._log.basicConfig(level=self._log.INFO, format='%(message)s')
        else:
            self._log.basicConfig(level=self._log.WARNING, format='%(message)s')

    def warn(self, message):
        """Print a warning message using the log system."""
        self._log.warning(message)


class MyLogFormatter(log.Formatter):
    err_fmt = "ERROR: %(msg)s"
    dbg_fmt = " DBG: %(module)s: %(lineno)d: %(msg)s"
    info_fmt = " %(msg)s"
    warn_fmt = " %(msg)s"

    def __init__(self, fmt="%(levelno)s: %(msg)s"):
        log.Formatter.__init__(self, fmt)

    def format(self, record):

        # Save the original format configured by the user
        # when the logger formatter was instantiated
        format_orig = self._fmt

        # Replace the original format with one customized by log level
        if record.levelno == log.DEBUG:
            self._fmt = MyLogFormatter.dbg_fmt

        elif record.levelno == log.INFO:
            self._fmt = MyLogFormatter.info_fmt

        elif record.levelno == log.ERROR:
            self._fmt = MyLogFormatter.err_fmt

        elif record.levelno == log.WARNING:
            self._fmt = MyLogFormatter.warn_fmt

        # Call the original formatter class to do the grunt work
        result = log.Formatter.format(self, record)

        # Restore the original format configured by the user
        self._fmt = format_orig

        return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description="Fits an existing phase-map."
    )

    parser.add_argument(
        'filename', type=str,
        help="Input phase-map name."
    )
    parser.add_argument(
        '-D', '--debug', action='store_true',
        help="Run program in debug mode."
    )
    parser.add_argument(
        '-o', '--output', type=str, default=None,
        help="Name of the output phase-map file."
    )
    parser.add_argument(
        '-q', '--quiet', action='store_true',
        help="Run program quietly."
    )

    args = parser.parse_args()

    wcal = WavelengthCalibration(verbose=not args.quiet, debug=args.debug)
    wcal.run(args.filename, output=args.output)
