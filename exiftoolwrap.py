"""Basic facade for the exiftool executable"""

# Public
import os.path
import shlex
import subprocess
import sys

# Internal
import exiftoolinst


class ExiftoolWrap:
    _path = None
    _path_to_binary = None


    def __init__(self, path=""):
        self._path = path
        self._detect_installation()


    #
    # Public
    #
    def launch_file_rename(self, path_to_images, prefix, file_ext, use_date_time):
        """Launches exiftool with a command to rename all images files

        Parameters:
            path_to_images: directory where to look for images (non recursive)

            prefix: prefix to add to the renamed files

            file_ext: which file types to rename specified by file extension
                       (ex. .jpg)

            use_date_time: True will add the date and time taken to the
                       filename of the images

        """

        if not self.is_installed():
            return

        # Date format: "%Y-%m-%d_%Hh%Mm%Ss

        # Extra notations:
        # %e: Extension of the original file
        # %c: Add a copy number to avoid name collision with existing filenames
        # Note that these codes must be escaped with an extra % if used within a
        # date format string.

        # The full command should look something like this:
        # exiftool.exe "-FileName<MyPrefix_${DateTimeOriginal}%-c.%e" -d "%Y-%m-%d_%Hh%Mm%Ss" c:\myfolder

        date_time_original = ""
        if use_date_time:
            date_time_original = "${DateTimeOriginal}"

        command_line = "\"" + self._path_to_binary + \
                  "\" \"-FileName<" + \
                  prefix + \
                  date_time_original + \
                  "%-c.%e\" -d %Y-%m-%d_%Hh%Mm%Ss \"" + \
                  os.path.join(path_to_images, file_ext) + "\""

        return command_line, self._createProcess(command_line)


    def is_installed(self):
        return self._path_to_binary != None


    def set_exiftool_path_manually(self, file):
        """Will set the exiftool executable filepath if it's valid.

        If the location is invalid, our previous location will be kept.

        return: True if the path is valid.

        """

        valid = False
        if self._is_valid_exiftool_executable(file):
            self._path_to_binary = file
            valid = True
        return valid

    def get_path_to_binary(self):
        return self._path_to_binary

    #
    # Private
    #

    def _detect_installation(self):
        """Returns True if the installation has been detected successfully."""

        self._path_to_binary = None
        if not self._try_installation_path(self._path, "exiftool.exe"):
            self._try_installation_path("", "exiftool.exe")

        return self._path_to_binary != None


    def _try_installation_path(self, path, executable_name):
        """True if the path to the binary was found and _path_to_binary was set"""

        ret = False
        if self._is_valid_exiftool_executable(os.path.join(path, executable_name)):
            self._path = path
            self._path_to_binary = os.path.join(path, executable_name)
            ret = True
        return ret


    def _is_valid_exiftool_executable(self, path_to_bin):
        """Will check to see if path_to_bin is pointing to a copy of exiftool.exe"""
        ret = False
        try:
            popen = self._createProcess("\"" + path_to_bin + "\" -ver")
            popen.wait()    # returncode is set by wait() as we need to wait for the program to finish
            if (popen.returncode == 0) and (len(popen.stdout.read()) > 0):
                print("Found exiftool: " + path_to_bin)
                ret = True
        except:
            pass

        return ret


    def _createProcess(self, command):
        """Helper that wraps the Popen arguments that we require to launch exiftool"""

        # DJOLY:TODO: Known issues to fix before deployment:
        #
        # The current Popen setup works for our needs but breaks the following
        # rules:
        #
        # * Technically we shoud be splitting the command in a list and not
        #   execute in a shell prompt. Unfortunately, this seems to break on
        #   Windows and more investigation is needed to understand how we are
        #   supposed to call exiftool. The drawbacks of this bastardized call
        #   don't seem severe for this application.
        #
        # * The subprocess.Popen documentation has the following note: Do not
        #   use stdout=PIPE or stderr=PIPE with this function. As the pipes are
        #   not being read in the current process, the child process may block
        #   if it generates enough output to a pipe to fill up the OS pipe
        #   buffer.
        #
        # ref: http://docs.python.org/dev/library/subprocess.html
        return subprocess.Popen(
            command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)


# OS check since currently we only support win32
if sys.platform != "win32":
    print("Error: Only win32 is supported.")
    assert(sys.platform == "win32")
