#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
     Phase-Map Apply - A script to apply a phase-map on a data-cube.
     by Bruno Quint (bquint@astro.iag.usp.br)
     and Fabricio Ferrari (fabricio@ferrari.pro.br)
     version 0.0 - Feb 2014
"""

from __future__ import division, print_function

import argparse
import astropy.io.fits as pyfits
import numpy as np
import os
import sys
import time

from scipy.interpolate import UnivariateSpline


def main():
    # Setting Options ---------------------------------------------------------
    parser = argparse.ArgumentParser(
        description="Apply a phase-map on a data-cube."
    )
    parser.add_argument(
        '-c', '--center', action='store_true',
        help="Try to center the strongest line in the cube."
    )
    parser.add_argument(
        '-n', '--npoints', type=int, default=10,
        help="Number of points in the re-sampling for channel [10]."
    )
    parser.add_argument(
        '-o', '--output', metavar='output', type=str, default=None,
        help="Name of the output corrected cube"
    )
    parser.add_argument(
        '-q', '--quiet', action='store_true',
        help="Run it quietly."
    )
    parser.add_argument(
        'cube_file', metavar='cube_file', type=str,
        help="Input calibration cube filename."
    )
    parser.add_argument(
        'map_file', metavar='map_file', type=str,
        help="Input phase-map image filename."
    )

    args = parser.parse_args()
    v = not args.quiet

    # Printing program header --------------------------------------------------
    if v:
        start = time.time()
        print("\n Phase-Map Apply")
        print(" by Bruno Quint & Fabricio Ferrari")
        print(" version 0.0 - Feb 2014")

    root_dir = os.path.dirname(args.cube_file)
    cube_file = args.cube_file
    map_file = args.map_file

    if args.output is None:
        out_file = 'phc_' + os.path.split(args.cube_file)[-1]
    else:
        out_file = args.output

    if v:
        print(" \n Root dir: %s" % root_dir)
        print(" Cube to be corrected: %s" % cube_file)
        print(" Phase-map to be applied: %s" % map_file)
        print(" Output corrected cube: %s" % out_file)

    # Reading input data ------------------------------------------------------
    if v:
        print("\n Reading cube to be corrected.")

    data_cube = pyfits.open(cube_file)[0]

    if v:
        print(" Done.")
        print("\n Reading phase-map to be applied.")

    phase_map = pyfits.open(map_file)[0]

    if v:
        print(" Done.")

    # Checking data -----------------------------------------------------------
    if data_cube.data[0].shape != phase_map.shape:
        print("[!] Cube and map does not have matching width and height.")
        print("[!] Leaving now.\n")
        sys.exit()

    if data_cube.data.ndim != 3:
        print("[!] Cube file is not really a cube.")
        print("[!] Leaving now.\n")
        sys.exit()

    if phase_map.data.ndim != 2:
        print("[!] Map file is not really an image.")
        print("[!] Leaving now.\n")
        sys.exit()

    m = data_cube.header['NAXIS1']
    n = data_cube.header['NAXIS2']

    ref_x = phase_map.header['PHMREFX']
    ref_y = phase_map.header['PHMREFY']
    units = phase_map.header['PHMUNIT']
    sample = float(phase_map.header['PHMSAMP'])

    # Reading the Free-Spectral-Range --------------------------------------
    try:
        if v:
            print(" Reading free-spectral-range from cube header.")
        # TODO add an option to use the FSR found while extracting
        # TODO the phase-map or while fitting it.
        # TODO or even to give the option for the user to enter it.
        # FSR = phase_map.header['PHMFITSR']
        f_s_r = phase_map.header['PHMFSR']
        if v:
            print(" Free Spectral Range = %.2f %s" % (f_s_r, units))

    except KeyError:
        print(" Please, enter the free-spectral-range in %s units" % units)
        f_s_r = input(" > ")

    f_s_r = round(f_s_r / abs(sample))  # From BCV to Channels
    if v:
        print(" Free-Spectral-Range is %d channels" % f_s_r)

    fsr = f_s_r * args.npoints  # From Channels to nPoints
    fsr = int(round(fsr))
    if v:
        print(" Free-Spectral-Range is %d points" % fsr)

    # Assure that the reference spectrum will not be moved ----------------
    try:
        phase_map.data = phase_map.data - phase_map.data[ref_y, ref_x]
    except IndexError:
        print("[!] Reference pixel out of field.")
        print("[!] Skipping reference pixel map subtraction.")
        pass
    phase_map.data *= -1

    # Converting phase-map values to channels ------------------------------
    phase_map.data /= sample

    # Converting phase-map from channels to number of points --------------
    phase_map.data = phase_map.data * args.npoints

    # Applying phase-map --------------------------------------------------
    if v:
        print("\n Applying phase-map:")

    n_channels = data_cube.header['NAXIS3']
    z = np.arange(3 * n_channels) - n_channels
    new_z = np.arange(0, z.size, 1.0 / args.npoints)

    for i in range(m):
        for j in range(n):

            # Extracting a spectrum
            spec = data_cube.data[:, j, i]
            spec = np.hstack((spec, spec, spec))
            dz = phase_map.data[j, i]

            # Re-sample spectrum
            spline = UnivariateSpline(z, spec, s=0.0)
            new_spec = spline(new_z)

            # Cutting spectrum
            new_z = new_z[0:fsr + 1]
            new_spec = new_spec[0:fsr + 1]

            # Shifting spectrum
            new_spec = np.roll(new_spec, int(dz))

            # Under-sampling spectrum
            spline = UnivariateSpline(new_z, new_spec, s=0.0)
            spec = spline(z)

            # Storing new spectrum
            data_cube.data[:, j, i] = spec[n_channels:2 * n_channels]

            # Giving a feedback to the user
            if v:
                temp = ((i + 1) * 100.00 / m)
                sys.stdout.write('\r  %2.2f%% ' % temp)
                sys.stdout.flush()

    end_of_cube = min(int(round(f_s_r)), data_cube.data.shape[0])
    data_cube.data = data_cube.data[0:end_of_cube, :, :]
    if v:
        print(" Done.")

    # Saving corrected data-cube ----------------------------------------------
    if v:
        print("\n Writing output to file %s." % out_file)
    data_cube.writeto(out_file, clobber=True)
    if v:
        print(" Done.")
        # noinspection PyUnboundLocalVariable
        end = time.time() - start
        print("\n Total time ellapsed: {0:02d}:{1:02d}:{2:02d}".format(
            end // 3600, end % 3600 // 60, end % 60))
        print(" All done!\n")


# Method shiftSpectrum ========================================================
# def shiftSpectrum(spec, dz, n_points=100):
#     dzSign = -np.sign(dz)
#     dz = abs(dz)
#     dz_points = int(dz * n_points)
#     if dz_points is 0: return spec
#
#     # Get the spectrum from cube
#     z = np.arange(spec.size)
#     spline = UnivariateSpline(z, spec, s=0.0)
#
#     # Re-sample spectrum
#     newZ = np.linspace(z[0], z[-1], z.size * n_points)
#     newSpec = spline(newZ)
#
#     # Add padded borders
#     newSpec = np.append(np.zeros(dz_points), newSpec)
#     newSpec = np.append(newSpec, np.zeros(dz_points))
#
#     # Shifting spectrum
#     newSpec = np.roll(newSpec, int(dzSign * dz_points))
#
#     # Cutting Spectrum
#     newSpec = newSpec[dz_points:-dz_points]
#
#     # Down-sampling
#     spline = UnivariateSpline(newZ, newSpec, s=0.0)
#     spec = spline(z)
#
#     return spec


# Method shift_spectrum ========================================================
def shift_spectrum(spec, dz, fsr=-1, sample=1.0, n_points=100):
    """
    Parameters
    ----------
        spec: np.array
            a spectrum to be shifted.

        dz: float
            How big is the shifting.

        fsr: float
            The free-spectra-range in sample units.

        sample: float
            The increment between each channel.

        n_points: int
            Number of points that will be used for super-sampling.
    """
    dz_sign = -np.sign(dz)
    dz = abs(dz) / sample  # From cube units to channels
    dz_points = int(dz * n_points)  # From channels to new sample units

    index = fsr / sample  # From cube units to channels
    index *= n_points  # From channels to new sample units

    if dz_points is 0:
        return spec

    # Get the spectrum from cube
    z = np.arange(spec.size)
    spline = UnivariateSpline(z, spec, s=0.0)

    # Re-sample spectrum
    new_z = np.linspace(z[0], z[-1], z.size * n_points)
    new_spec = spline(new_z)

    # Cutting Spectrum
    new_spec = new_spec[0:fsr]

    # Shifting spectrum
    new_spec = np.roll(new_spec, int(dz_sign * dz_points))

    # Down-sampling
    spline = UnivariateSpline(new_z, new_spec, s=0.0)
    spec = spline(z)

    return spec


def error(my_string):
    s = BColors.FAIL + '[ERROR] ' + BColors.ENDC
    s = s + my_string
    print(s)
    return


def warning(my_string):
    s = BColors.WARNING + '[WARNING] ' + BColors.ENDC
    s = s + my_string
    print(s)
    return


# noinspection PyClassHasNoInit
class BColors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'

    def disable(self):
        self.HEADER = ''
        self.OKBLUE = ''
        self.OKGREEN = ''
        self.WARNING = ''
        self.FAIL = ''
        self.ENDC = ''


# ===============================================================================
if __name__ == '__main__':
    main()
