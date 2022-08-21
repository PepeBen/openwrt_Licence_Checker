#!/usr/bin/env python
# Copyright (C) 2022 Ben Pepe
import os
import sys
import glob
import argparse
import re

# This script will check for gpl infractions and license information in a package's Makefile
# During the build process a script generates a license page for each installed non proprietary package.
# To do this the script needs the correct information in the Makefile of installed
# packages. The variables PKG_LICENSE and PKG_LICENSE_FILES need to be filled in correctly
# for the script to work correcty.
#
# Makefile license info format:
# 1. The first item in PKG_LICENSE needs to be the main license type used by the package
#    and the corresponding file name of the license notice file needs to be first
#    in PKG_LICENSE_FILES.
# 2. After the first license type is where you can list other license types they
#    do not need corresponding file name of the license file name in the right
#    order unless they are gpl licenses.
# 3. It is ok to have multiple license notice files as long as they are listed
#    after file names with corresponding licenses in PKG_LICENSE_FILES.
# 4. gpl license type format for PKG_LICENSE is "<GPL or LGPL>-<version>" (GPL-2.0, LGPL-2.1+, etc)
#
# EXAMPLE Makefile:
#    LICENSE:= GPL-3.0 LGPL-2.1+
#    LICENSE_FILES:= COPYING COPYING.LGPL
# -------------------------------------------------------------------------------
#    LICENSE:= MIT
#    LICENSE_FILES:= LICENSE COPYING
# -------------------------------------------------------------------------------
#    LICENSE:= LGPL-2.1+ GPL-2.0 BSD-3-Clause BZIP2
#    LICENSE_FILES:= Documentation/licenses/COPYING.LGPLv2.1 \
#                    Documentation/licenses/COPYING.GPLv2 \
#                    Documentation/licenses/COPYING.BSD-3 \
#                    archival/libarchive/bz/LICENSE \
#                    libtomcrypt/LICENSE libtommath/LICENSE
# -------------------------------------------------------------------------------


class CheckLicense(object):
    def __init__(self, verbose):
        self.current_dir = os.getcwd()
        self.pkg_list = []
        self.verbose_bol = verbose
        self.exclude_list = ['feeds', 'build_dir', 'staging_dir', 'tmp', 'buildap', 'script', 'docker']

    def find_dir(self, start_dir, target_name):
        if target_name in start_dir:
            return start_dir
        for root, dirs, files in os.walk(start_dir):
            # Exclude directories from search to improve effeciency
            # xxx dir has packages under "feeds" dir
            if not 'xxx' in root:
                dirs[:] = [d for d in dirs if d not in self.exclude_list]
            for target in glob.glob(os.path.join(root, target_name)):
                if os.path.isdir(target):
                    return target
        # Exit script if no file or directory is found
        print('{0} was not found in {1}'.format(target_name, start_dir))
        sys.exit(1)

    def check_license_info(self, package_args):
        for package_name in package_args:
            # Get path to package Makefile
            package_root_dir = self.find_dir(self.current_dir, package_name)
            # Reset metadata for new package
            metadata = {"package_name": package_name, "package_root_dir": package_root_dir,
                        "root_makefile": False, "proprietary": False,
                        "license_types": '', "license_file_names": '',
                        "contains_gpl": False, "pass": True}
            # Get data from makefile
            if self.verbose_bol:
                print('Reading Makefile information: {0}'.format(metadata['package_name']))
            metadata = self.parse_makefile(metadata)

            if not metadata["root_makefile"]:
                print('{0}........FAILED {1}/Makefile does not exist:'.format(metadata['package_name'], metadata['package_root_dir']))

            # If package is proprietary
            if metadata["proprietary"]:
                if self.verbose_bol:
                    print('{0}........PROPRIETARY'.format(metadata['package_name']))
                print('{0}........PASS'.format(package_name))
                if self.verbose_bol:
                    print('')
                continue

            if metadata['license_types']:
                # Checks if first license is gpl regardless of format presented
                if re.match('^L?GPL.*$', metadata['license_types'][0], re.IGNORECASE):
                    # If gpl license is not in correct format print error
                    if not re.match('^L?GPL\-[0-9]\.[0-9]\+?$', metadata['license_types'][0]):
                        print('{0}........FAILED PKG_LICENSE:={1} format is incorrect'.format(metadata['package_name'], metadata['license_types'][0]))
                        print('\nCorrect format: <GPL type> - <version> ex: LGPL-2.1+ , GPL-3.0 , GPL-2.0+\n')
                        metadata['pass'] = False
                    elif self.verbose_bol:
                        print('{0}........PKG_LICENSE OK'.format(metadata['package_name']))
                # Non-gpl license
                elif self.verbose_bol:
                    print('{0}........PKG_LICENSE OK'.format(metadata['package_name']))
            else:
                print('{0}........FAILED PKG_LICENSE is missing or empty'.format(metadata['package_name']))
                metadata['pass'] = False

            if not metadata['license_file_names']:
                print('{0}........FAILED PKG_LICENSE_FILES is missing or empty'.format(metadata['package_name']))
                metadata['pass'] = False
            elif self.verbose_bol:
                print('{0}........PKG_LICENSE_FILES OK'.format(metadata['package_name']))

            if metadata['pass']:
                print('{0}........PASS'.format(metadata['package_name']))
                if self.verbose_bol:
                    print('')
            else:
                if self.verbose_bol:
                    print('{0}........FAILED'.format(metadata['package_name']))
                    print('')
        return

    def parse_makefile(self, metadata):
        # Multiple Makefiles may exist, so parse each one
        for root, dirs, files in os.walk(metadata['package_root_dir']):
            for makefile_path in glob.glob(os.path.join(root, 'Makefile')):
                if self.verbose_bol:
                    print(makefile_path)
                if makefile_path == os.path.join(metadata['package_root_dir'], 'Makefile'):
                    metadata['root_makefile'] = True
                with open(makefile_path, 'r') as read_file:
                    for line in read_file:
                        # Check makefile to see if user_headers is included
                        if 'PKG_PROPRIETARY' in line:
                            metadata['proprietary'] = True
                        if 'PKG_LICENSE:=' in line:
                            if re.match('^.*\=\s?L?GPL.*$', line):
                                metadata['contains_gpl'] = True
                            metadata['license_types'] = line.split(':=')[1].split()
                        if 'PKG_LICENSE_FILES:=' in line:
                            metadata['license_file_names'] = line.split(':=')[1].split()
        return metadata


def parse_program_arguments():
    """
    Uses argparse to display help text
    """
    parser = argparse.ArgumentParser(description="""Use chk-licenses-info to check the license info in the Makefile
                                                of desired packages under the current directory. If a package is
                                                proprietary then PKG_LICENSE and PKG_LICENSE_FILES are not needed.
                                                For packages under xxx directory run the script in the package's directory
                                                """,
                                     usage='chk-licenses-info <package name> <package_name> etc..')
    parser.add_argument('-v',
                        action='store_true',
                        dest='verbose_bol',
                        help='displays all information')
    parser.add_argument('input_pkg_name',
                        action='store',
                        type=str,
                        nargs='+')
    return parser.parse_known_args()


if __name__ == "__main__":
    arg, extra = parse_program_arguments()
    # For output formating purposes
    print('')
    if arg.verbose_bol:
        print('\t........Starting Check........\n')

    check_package = CheckLicense(arg.verbose_bol)
    check_package.check_license_info(arg.input_pkg_name)

    # For output formating purposes
    if not arg.verbose_bol:
        print('')
    if arg.verbose_bol:
        print('\t........End Of Check........\n')
