"""Utilities to install exiftool by Phil Harvey directly from the Internet."""

import os
import os.path
import shutil
import urllib.error
import urllib.parse
import urllib.request
import re
import sys
import tempfile
import webbrowser
import zipfile


EXIFTOOL_HOMEPAGE_URL = r"http://www.sno.phy.queensu.ca/~phil/exiftool/"

#
# Public
#

def browser_launches_exiftool_homepage():
    webbrowser.open(EXIFTOOL_HOMEPAGE_URL)


def try_auto_install_exiftool(install_path):
    """Does a best effort to download exiftool and install it to the install_path
    directory location.

    return: (success, executable_filepath)

    note: There is no standard way to install exiftool. We do a best effort by
          trying to parse the exiftool homepage for the installer path.

          The installer path changes regularly based on its version number.

          Last tested on 2/27/2012

    """

    ret = (False, None)
    try:
        request = urllib.request.urlopen(EXIFTOOL_HOMEPAGE_URL)
        homepage_content = request.read()

        # Try to find a full url of any version of the installer zip file on the page's content
        matches = re.findall(
            r"http://.*/exiftool-.*\.zip",
            homepage_content.decode())

        installer_full_path = None
        if matches:
            installer_full_path = matches[0]
        else:
            # Try to find a partial url and join it to the page's base url
            matches = re.findall(r"exiftool-.*\.zip", homepage_content.decode())
            if matches:
                installer_full_path = urllib.parse.urljoin(
                    EXIFTOOL_HOMEPAGE_URL,
                    matches[0],
                    allow_fragments=False)

        # We found the path. Download and install exiftool.
        if installer_full_path != None:
            ret = _install_exiftool_from_installer_path(
                        installer_full_path,
                        install_path)

    except (urllib.error.URLError, NameError):
        print("Couldn't download the homepage")

    return ret

#
# Private
#

def _install_exiftool_from_installer_path(installer_full_path, install_path):
    """return: (success, executable_filepath)"""

    ret = (False, None)
    try:
        http_request_installer = urllib.request.urlopen(installer_full_path)

        installer_filepath = None

        try:
            # Create a temp file to store the installer
            with tempfile.NamedTemporaryFile(
                            mode="w+b",
                            prefix="exiftoolinst",
                            delete=False) as file:
                file.write(http_request_installer.read())
                installer_filepath = file.name

            ret = _install_exiftool_from_zip_file(
                        installer_filepath,
                        install_path)
        finally:
            # delete our temp file
            if (installer_filepath != None):
                os.remove(installer_filepath)
    except (urllib.error.URLError, NameError):
        print("Couldn't download the package or write the temp file")

    return ret


def _install_exiftool_from_zip_file(installer_filepath, install_path):
    """
    Parameters:
        installer_filepath: zip file of the exiftool installer.

        install_path: Where to install exiftool.

    return: (success, executable_filepath)

    """

    print(installer_filepath)

    ret = (False, None)
    try:
        with zipfile.ZipFile(installer_filepath) as installer_zip:
            original_executable_filename = None

            # Before extracting all the files, try to match the exiftool
            # executable name.
            for filename in installer_zip.namelist():
                matches = re.match(r"exiftool.*\.exe", filename)
                if matches != None:
                    original_executable_filename = matches.group(0)

            if original_executable_filename:
                installer_zip.extractall(install_path)

                # The main executable file has a name such as "exiftool(-k).exe".
                # The Exiftool documentation recommends renaming the executable to
                # "exiftool.exe".
                # Ref: http://www.sno.phy.queensu.ca/~phil/exiftool/install.html

                original_executable_filepath = os.path.join(
                                                    install_path,
                                                    original_executable_filename)
                final_executable_filepath = os.path.join(
                                                    install_path,
                                                    "exiftool.exe")
                os.rename(original_executable_filepath, final_executable_filepath)

                ret = (True, final_executable_filepath)
    except:
        print("Couldn't extract the installer zip file content")

    return ret


# OS check since we only support the win32 version of exiftool
if sys.platform != "win32":
    print("Error: Only the win32 version of exiftool is supported.")
    assert(sys.platform == "win32")
