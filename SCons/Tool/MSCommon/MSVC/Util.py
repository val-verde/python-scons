# MIT License
#
# Copyright The SCons Foundation
#
# Permission is hereby granted, free of charge, to any person obtaining
# a copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so, subject to
# the following conditions:
#
# The above copyright notice and this permission notice shall be included
# in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY
# KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE
# WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE
# LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
# OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION
# WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

"""
Helper functions for Microsoft Visual C/C++.
"""

import os
import re

from collections import (
    namedtuple,
)

from . import Config

# path utilities

def listdir_dirs(p):
    """
    Return a list of tuples for each subdirectory of the given directory path.
    Each tuple is comprised of the subdirectory name and the qualified subdirectory path.
    Assumes the given directory path exists and is a directory.

    Args:
        p: str
            directory path

    Returns:
        list[tuple[str,str]]: a list of tuples

    """
    dirs = []
    for dir_name in os.listdir(p):
        dir_path = os.path.join(p, dir_name)
        if os.path.isdir(dir_path):
            dirs.append((dir_name, dir_path))
    return dirs

def process_path(p):
    """
    Normalize a system path

    Args:
        p: str
            system path

    Returns:
        str: normalized system path

    """
    if p:
        p = os.path.normpath(p)
        p = os.path.realpath(p)
        p = os.path.normcase(p)
    return p

# msvc version and msvc toolset version regexes

re_version_prefix = re.compile(r'^(?P<version>[0-9.]+).*$')

re_msvc_version_prefix = re.compile(r'^(?P<version>[1-9][0-9]?[.][0-9]).*$')

re_msvc_version = re.compile(r'^(?P<msvc_version>[1-9][0-9]?[.][0-9])(?P<suffix>[A-Z]+)*$', re.IGNORECASE)

re_extended_version = re.compile(r'''^
    (?P<version>(?:
        ([1-9][0-9]?[.][0-9]{1,2})|                     # XX.Y       - XX.YY
        ([1-9][0-9][.][0-9]{2}[.][0-9]{1,5})|           # XX.YY.Z    - XX.YY.ZZZZZ
        ([1-9][0-9][.][0-9]{2}[.][0-9]{2}[.][0-9]{1,2}) # XX.YY.AA.B - XX.YY.AA.BB
    ))
    (?P<suffix>[A-Z]+)*
$''', re.IGNORECASE | re.VERBOSE)

re_toolset_full = re.compile(r'''^(?:
    (?:[1-9][0-9][.][0-9]{1,2})|           # XX.Y    - XX.YY
    (?:[1-9][0-9][.][0-9]{2}[.][0-9]{1,5}) # XX.YY.Z - XX.YY.ZZZZZ
)$''', re.VERBOSE)

re_toolset_140 = re.compile(r'''^(?:
    (?:14[.]0{1,2})|       # 14.0    - 14.00
    (?:14[.]0{2}[.]0{1,5}) # 14.00.0 - 14.00.00000
)$''', re.VERBOSE)

re_toolset_sxs = re.compile(
    r'^[1-9][0-9][.][0-9]{2}[.][0-9]{2}[.][0-9]{1,2}$' # MM.mm.VV.vv format
)

# version prefix utilities

def get_version_prefix(version):
    """
    Get the version number prefix from a string.

    Args:
        version: str
            version specification

    Returns:
        str: the version number prefix

    """
    m = re_version_prefix.match(version)
    if m:
        rval = m.group('version')
    else:
        rval = ''
    return rval

def get_msvc_version_prefix(version):
    """
    Get the msvc version number prefix from a string.

    Args:
        version: str
            version specification

    Returns:
        str: the msvc version number prefix

    """
    m = re_msvc_version_prefix.match(version)
    if m:
        rval = m.group('version')
    else:
        rval = ''
    return rval

# toolset version query utilities

def is_toolset_full(toolset_version):
    if re_toolset_full.match(toolset_version):
        return True
    return False

def is_toolset_140(toolset_version):
    if re_toolset_140.match(toolset_version):
        return True
    return False

def is_toolset_sxs(toolset_version):
    if re_toolset_sxs.match(toolset_version):
        return True
    return False

# msvc version and msvc toolset version decomposition utilties

_MSVC_VERSION_COMPONENTS_DEFINITION = namedtuple('MSVCVersionComponentsDefinition', [
    'msvc_version', # msvc version (e.g., '14.1Exp')
    'msvc_verstr',  # msvc version numeric string (e.g., '14.1')
    'msvc_suffix',  # msvc version component type (e.g., 'Exp')
    'msvc_vernum',  # msvc version floating point number (e.g, 14.1)
    'msvc_major',   # msvc major version integer number (e.g., 14)
    'msvc_minor',   # msvc minor version integer number (e.g., 1)
])

def msvc_version_components(vcver):
    """
    Decompose an msvc version into components.

    Tuple fields:
        msvc_version: msvc version (e.g., '14.1Exp')
        msvc_verstr:  msvc version numeric string (e.g., '14.1')
        msvc_suffix:  msvc version component type (e.g., 'Exp')
        msvc_vernum:  msvc version floating point number (e.g., 14.1)
        msvc_major:   msvc major version integer number (e.g., 14)
        msvc_minor:   msvc minor version integer number (e.g., 1)

    Args:
        vcver: str
            msvc version specification

    Returns:
        None or MSVCVersionComponents namedtuple:
    """

    m = re_msvc_version.match(vcver)
    if not m:
        return None

    vs_def = Config.MSVC_VERSION_SUFFIX.get(vcver)
    if not vs_def:
        return None

    msvc_version = vcver
    msvc_verstr = m.group('msvc_version')
    msvc_suffix = m.group('suffix') if m.group('suffix') else ''
    msvc_vernum = float(msvc_verstr)

    msvc_major, msvc_minor = [int(x) for x in msvc_verstr.split('.')]

    msvc_version_components_def = _MSVC_VERSION_COMPONENTS_DEFINITION(
        msvc_version = msvc_version,
        msvc_verstr = msvc_verstr,
        msvc_suffix = msvc_suffix,
        msvc_vernum = msvc_vernum,
        msvc_major = msvc_major,
        msvc_minor = msvc_minor,
    )

    return msvc_version_components_def

_MSVC_EXTENDED_VERSION_COMPONENTS_DEFINITION = namedtuple('MSVCExtendedVersionComponentsDefinition', [
    'msvc_version', # msvc version (e.g., '14.1Exp')
    'msvc_verstr',  # msvc version numeric string (e.g., '14.1')
    'msvc_suffix',  # msvc version component type (e.g., 'Exp')
    'msvc_vernum',  # msvc version floating point number (e.g, 14.1)
    'msvc_major',   # msvc major version integer number (e.g., 14)
    'msvc_minor',   # msvc minor version integer number (e.g., 1)
    'msvc_toolset_version', # msvc toolset version
    'version',              # msvc version or msvc toolset version
])

def msvc_extended_version_components(version):
    """
    Decompose an msvc version or msvc toolset version into components.

    Args:
        version: str
            version specification

    Returns:
        None or MSVCExtendedVersionComponents namedtuple:
    """

    m = re_extended_version.match(version)
    if not m:
        return None

    msvc_toolset_version = m.group('version')

    msvc_verstr = get_msvc_version_prefix(msvc_toolset_version)
    if not msvc_verstr:
        return None

    msvc_suffix = m.group('suffix') if m.group('suffix') else ''
    msvc_version = msvc_verstr + msvc_suffix

    vs_def = Config.MSVC_VERSION_SUFFIX.get(msvc_version)
    if not vs_def:
        return None

    msvc_vernum = float(msvc_verstr)

    msvc_major, msvc_minor = [int(x) for x in msvc_verstr.split('.')]

    msvc_extended_version_components_def = _MSVC_EXTENDED_VERSION_COMPONENTS_DEFINITION(
        msvc_version = msvc_version,
        msvc_verstr = msvc_verstr,
        msvc_suffix = msvc_suffix,
        msvc_vernum = msvc_vernum,
        msvc_major = msvc_major,
        msvc_minor = msvc_minor,
        msvc_toolset_version = msvc_toolset_version,
        version = version,
    )

    return msvc_extended_version_components_def

