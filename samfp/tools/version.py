"""
    0.0.0 - Starting from old version. Some features may not be working. My
                idea is to implement each of the scripts as a bin to be
                installed using setup.py and the entry_points keyword.
    0.1.0 - xjoin was released again. It is working and installed using
                entry_points.
    0.2.0 - mkcube can now be called as script again and it is installed using
                pip.
    0.3.0 - phmxtractor can now be called as script again and it is installed
                using pip.
    0.4.0 - phmfit can now be called as script again and it is installed using
                pip.
    0.4.1 - phmfit now stores fit parameters in the header.
    0.5.0 - phmapply back to work.
    0.6.0 - Add tools to combine Bias, Flats, Darks and Images.
       .1 - Fixed some installation issues.
       .2 - Now every script that is part of the samfp tools will carry the
                version of the package itself. Before, they were carrying only
                their own versions and it was difficult to track/update.
    0.7.0 - fp_tools are now inside samfp-tools
       .1 - updated phmfit - not sure if it is better or worse.
       .2 - Fixed fp_repeat and fp_overscan. Travis CI working for Linux.
       .3 - Fixed Travis CI and implemented tests for fp_repeat, fp_oversample,
                fp_cut and fp_roc.
          - fp_oversample is fixed.
       .4 - Fixed bug on mkcube while trying to fit a polynomium.
       .5 - Changed way that some libraries are imported.
          - Changed log system for some scripts.
          - Changed algorithm to extract the phase-map.
          - Changed method to find peaks on phmapply.
"""

api = 0
feature = 7
bug = 5

month = 8
year = 2018

__str__ = 'v{:d}.{:d}.{:d} {:d}-{:0d}'.format(api, feature, bug, year, month)
