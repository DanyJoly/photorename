"""GUI wrapper application around exiftool to rename photos based on their meta 
information.

"""

# Coding standards: http://www.python.org/dev/peps/pep-0008/

# Public
import configparser
import os
import os.path
import sys
import time
import tkinter
import tkinter.font
import tkinter.filedialog

# Internal
import exiftoolwrap
import exiftoolinst

class App:
    """The photorename main TKinter UI object."""

    APPLICATION_NAME = "photorename"

    _root = None
    _local_appdata_path = None


    def __init__(self, root):
        self._root = root
        self._ensure_local_appdata()
        self._exiftool = exiftoolwrap.ExiftoolWrap(self._local_appdata_path)

        self._create_layout()
        self._set_initial_state()


    def _ensure_local_appdata(self):
        """Ensure that we have a local application data directory."""

        # Our local application storage directory (Win32 only)
        self._local_appdata_path = os.path.join(
            os.environ['LOCALAPPDATA'], self.APPLICATION_NAME)
        try:
            os.mkdir(self._local_appdata_path)
        except OSError:
            pass # The directory already exists


    def _create_layout(self):
        """Create all layout objects and set them on the screen"""

        WIDTH_ENTRY_MEDIAS_LOCATION = 50
        WIDTH_BTN_OK = 10

        sticky_centered = tkinter.W+tkinter.E+tkinter.S+tkinter.N

        # Bind to the event that will close this window
        self._root.protocol("WM_DELETE_WINDOW", self._on_closing)

        self._frame = tkinter.Frame(self._root)
        self._frame.grid()

        ROW_TITLE = 0

        font_title = tkinter.font.Font(size=15)

        self._lbl_title = tkinter.Label(
            self._frame,
            text="Photorename \n Helps you rename your digital pictures and videos",
            height=2, justify=tkinter.CENTER, borderwidth=1,
            relief=tkinter.RAISED,
            font=font_title)
        self._lbl_title.grid(
            row=ROW_TITLE, columnspan=3, sticky=sticky_centered)

        ROW_INPUT_FILE_INFO = ROW_TITLE + 1

        tkinter.Label(
            self._frame, text="-- Input files informations ----------------------").grid(
            row=ROW_INPUT_FILE_INFO, column=0, columnspan=3, sticky=tkinter.W)

        ROW_MEDIAS_LOCATION = ROW_INPUT_FILE_INFO + 1

        self._lbl_medias_location = tkinter.Label(
            self._frame, text="Medias location:")
        self._lbl_medias_location.grid(
            row=ROW_MEDIAS_LOCATION, column=0, sticky=tkinter.W)

        self._entry_medias_location = tkinter.Entry(
            self._frame, width=WIDTH_ENTRY_MEDIAS_LOCATION)
        self._entry_medias_location.grid(
            row=ROW_MEDIAS_LOCATION, column=1, sticky=tkinter.W)

        self._btn_medias_location = tkinter.Button(self._frame, text="Open...",
            command=self._on_medias_location_clicked)
        self._btn_medias_location.grid(
            row=ROW_MEDIAS_LOCATION, column=2, sticky=tkinter.W)

        ROW_FILE_TYPES = ROW_MEDIAS_LOCATION + 1

        self._lbl_file_types = tkinter.Label(self._frame, text="File types:")
        self._lbl_file_types.grid(row=ROW_FILE_TYPES, column=0, sticky=tkinter.W)

        self._entry_file_types = tkinter.Entry(self._frame)
        self._entry_file_types.grid(row=ROW_FILE_TYPES, column=1, sticky=tkinter.W)
        self._entry_file_types.bind_class("Entry", sequence="<FocusOut>", func=self._on_file_types_changed)

        ROW_ALL_FILE_TYPES = ROW_FILE_TYPES + 1

        self._checkbox_all_file_types_state = tkinter.IntVar()

        self._checkbox_all_filetypes = tkinter.Checkbutton(
            self._frame,
            text="All file types",
            command=self._on_all_file_types_clicked,
            variable=self._checkbox_all_file_types_state)
        self._checkbox_all_filetypes.grid(row=ROW_ALL_FILE_TYPES, column=0)

        ROW_OUTPUT_INFORMATION = ROW_ALL_FILE_TYPES + 1

        tkinter.Label(self._frame, text="-- Output filename informations ------------------").grid(
            row=ROW_OUTPUT_INFORMATION, column=0, columnspan=3, sticky=tkinter.W)

        ROW_FILE_PREFIX = ROW_OUTPUT_INFORMATION + 1

        self._lbl_label_file_prefix = tkinter.Label(self._frame, text="File prefix:")
        self._lbl_label_file_prefix.grid(
            row=ROW_FILE_PREFIX, column=0, sticky=tkinter.W)

        self._entry_label_file_prefix = tkinter.Entry(self._frame)
        self._entry_label_file_prefix.grid(
            row=ROW_FILE_PREFIX, column=1, sticky=tkinter.W)

        ROW_INCLUDE_DATE_AND_TIME = ROW_FILE_PREFIX + 1

        self._checkbox_include_date_and_time_state = tkinter.IntVar()

        self._checkbox_include_date_and_time = tkinter.Checkbutton(
            self._frame,
            text="Include date and time",
            variable=self._checkbox_include_date_and_time_state)
        self._checkbox_include_date_and_time.grid(
            row=ROW_INCLUDE_DATE_AND_TIME, column=0, sticky=tkinter.W)

        ROW_EXIFTOOL_MISSING = ROW_FILE_PREFIX + 1

        self._lbl_exiftool_missing = tkinter.Label(
            self._frame, text="Exiftool is missing", fg="red")
        self._lbl_exiftool_missing.grid(
            row=ROW_EXIFTOOL_MISSING, column=0, columnspan=2, sticky=sticky_centered)

        self._btn_exiftool_missing = tkinter.Button(self._frame, text="Install it...",
            command=self._on_install_exiftool_clicked, fg="red")
        self._btn_exiftool_missing.grid(
            row=ROW_EXIFTOOL_MISSING, column=2, sticky=tkinter.W)

        ROW_OK_BUTTON = ROW_EXIFTOOL_MISSING + 1

        self._btn_ok = tkinter.Button(
            self._frame, text="OK", width=WIDTH_BTN_OK, command=self._on_btn_ok_clicked)
        self._btn_ok.grid(row=ROW_OK_BUTTON, column=2, sticky=sticky_centered)


    def _set_initial_state(self):
        """Set the layout controls to the initial control states, based on user
        preferences.

        """

        # Set our default user preferences
        self._checkbox_all_filetypes.select()
        self._checkbox_include_date_and_time.select()

        # Now load any persisted user preference
        self._load_config()

        # Set our dynamic UI states
        self._set_file_types_state()
        self._set_exiftool_install_state()


    def _set_file_types_state(self):
        if self._checkbox_all_file_types_state.get() == 1:
            # Populate won't work if the control is disabled. Enabling first
            self._enable_file_types()
            self._populate_all_file_types()
            self._disable_file_types()
        else:
            self._enable_file_types()


    def _populate_all_file_types(self):
        """Will populate the file types field by reading the different files in
        the medias location and extract their extensions.

        """

        try:
            allext = {}
            allfiles = os.listdir(self._entry_medias_location.get())
            for file in allfiles:
                ext = os.path.splitext(file)[1]
                if (ext != None) and (ext != ""):
                    allext[ext] = ext

            all_types = ""
            for key in allext:
                all_types += "*" + key + ";"

            self._entry_file_types.delete(0, tkinter.END)
            self._entry_file_types.insert(0, all_types)
        except:
            print("Couldn't extract all file types from: " +
                self._entry_medias_location.get())
            pass

    def _populate_all_file_types_if_needed(self):
        """Will populate the file types field from the files in the medias location
        only if the user has chosen to do so.

        """

        if self._checkbox_all_file_types_state.get() == 1:

            # We won't be able to write if it's not enabled
            self._entry_file_types.configure(state="normal")
            self._populate_all_file_types()
            self._entry_file_types.configure(state="disabled")

            # No unexpected side effects
            assert(self._checkbox_all_file_types_state.get() == 1)


    def _set_exiftool_install_state(self):
        if self._exiftool.is_installed():
            self._hide_exiftool_install()
        else:
            self._show_exiftool_install()


    #
    # Layout state manipulations
    #

    def _enable_file_types(self):
        self._lbl_file_types.configure(state="normal")
        self._entry_file_types.configure(state="normal")


    def _disable_file_types(self):
        self._lbl_file_types.configure(state="disabled")
        self._entry_file_types.configure(state="disabled")


    def _show_exiftool_install(self):
        self._lbl_exiftool_missing.grid()   # BUGBUG: We're supposed to give back all grid input.
        self._btn_exiftool_missing.grid()   # BUGBUG: We're supposed to give back all grid input.
        self._btn_ok.grid_forget()


    def _hide_exiftool_install(self):
        self._lbl_exiftool_missing.grid_forget()
        self._btn_exiftool_missing.grid_forget()
        self._btn_ok.grid() # BUGBUG: We're supposed to give back all grid input.

    #
    # Event handlers
    #

    def _on_closing(self):
        # Upon closing the application, we will persist the user's choices
        try:
            self._save_config()
            self._root.destroy()
        except:
            pass


    def _on_all_file_types_clicked(self):
        self._set_file_types_state()


    def _on_file_types_changed(self, event):
        """Focus change handler for the file_types entry widget."""
        # http://www.pythonware.com/library/tkinter/introduction/events-and-bindings.htm
        self._set_file_types_state()


    def _on_medias_location_clicked(self):
        dlg = tkinter.filedialog.FileDialog(self._frame)
        dir = dlg.go()
        if dir is not None:
            self._entry_medias_location.delete(0, tkinter.END)
            self._entry_medias_location.insert(0, dir)
            self._populate_all_file_types_if_needed()


    def _on_btn_ok_clicked(self):
        self._save_config()

        def exiftool_popen_generator():
            """Generator that will return:
                (command_line, popen_object)

            """

            input_info = self._get_user_input_info()
            output_info = self._get_output_info()

            filestypes_to_copy = ["*.*"]
            if input_info["InputAllFileTypes"] == "0":
               filestypes_to_copy = input_info["InputFileTypes"].split(";")

            for filetype in filestypes_to_copy:
                if filetype != "" and filetype != None:
                    yield self._exiftool.launch_file_rename(
                            path_to_images=input_info["InputMediaDirectory"],
                            prefix=output_info["OutputFileNamePrefix"],
                            file_ext=filetype,
                            use_date_time=(output_info["OutputFileNameUseDateAndTime"] != "0"))

        dlg = PopenOutputDlg(self._frame, exiftool_popen_generator)
        dlg.show()


    def _on_install_exiftool_clicked(self):
        installer = InstallExiftoolDlg(
            self._frame, self._exiftool, self._local_appdata_path)
        installer.show()

        # Recalculate our state
        self._set_exiftool_install_state()

    #
    # Configuration helpers
    #

    def _get_user_input_info(self):
        path_to_exiftool = self._exiftool.get_path_to_binary()
        if path_to_exiftool == None:
            path_to_exiftool = ""
        return {"PathToExiftool" : path_to_exiftool,
                "InputMediaDirectory" : self._entry_medias_location.get(),
                "InputFileTypes" : self._entry_file_types.get(),
                "InputAllFileTypes" : str(self._checkbox_all_file_types_state.get())}


    def _get_output_info(self):
        return {"OutputFileNamePrefix" : self._entry_label_file_prefix.get(),
                "OutputFileNameUseDateAndTime" : str(self._checkbox_include_date_and_time_state.get())}


    def _set_user_input_info(self, input_info):
        if "PathToExiftool" in input_info:
            self._exiftool.set_exiftool_path_manually(input_info["PathToExiftool"])

        if "InputMediaDirectory" in input_info:
            self._entry_medias_location.delete(0, tkinter.END)
            self._entry_medias_location.insert(0, input_info["InputMediaDirectory"])

        if "InputFileTypes" in input_info:
            self._entry_file_types.delete(0, tkinter.END)
            self._entry_file_types.insert(0, input_info["InputFileTypes"])

        if "InputAllFileTypes" in input_info:
            if input_info["InputAllFileTypes"] == "0":
                self._checkbox_all_filetypes.deselect()
            else:
                self._checkbox_all_filetypes.select()


    def _set_output_info(self, output_info):
        if "OutputFileNamePrefix" in output_info:
            self._entry_label_file_prefix.delete(0, tkinter.END)
            self._entry_label_file_prefix.insert(0, output_info["OutputFileNamePrefix"])

        if "OutputFileNameUseDateAndTime" in output_info:
            if output_info["OutputFileNameUseDateAndTime"] == "0":
                self._checkbox_include_date_and_time.deselect()
            else:
                self._checkbox_include_date_and_time.select()


    def _save_config(self):
        config = configparser.ConfigParser()
        config["PHOTOCOPY_USER_INPUT"] = self._get_user_input_info()
        config["PHOTOCOPY_OUTPUT"] = self._get_output_info()

        with open(self._get_config_path(), "w") as configfile:
            config.write(configfile)


    def _load_config(self):
        config = configparser.ConfigParser()
        config.read(self._get_config_path())
        if "PHOTOCOPY_USER_INPUT" in config:
            self._set_user_input_info(config["PHOTOCOPY_USER_INPUT"])

        if "PHOTOCOPY_OUTPUT" in config:
            self._set_output_info(config["PHOTOCOPY_OUTPUT"])


    def _get_config_path(self):
        return os.path.join(self._local_appdata_path, "config.ini")


class ModalDialog:
    # Toplevel window
    top = None

    def __init__(self, parent):
        self.top = tkinter.Toplevel(parent)

        # Set the focus on dialog window (needed on Windows)
        self.top.focus_set()

        # Make sure events only go to our dialog
        self.top.grab_set()

        # Make sure dialog stays on top of its parent window (if needed)
        self.top.transient(parent)


    def show(self):
        """Display the modal dialog and wait for it to close"""
        self.top.wait_window(self.top)


class ModalAlertBox(ModalDialog):
    """Very simple alert box. Handy for quick debugging or notifying the user about something."""
    _text = ""


    def __init__(self, parent, text):
        ModalDialog.__init__(self, parent)

        self._text = text
        frame = tkinter.Frame(self.top)
        frame.grid()

        tkinter.Label(frame, text=self._text).grid(
            row=0, column=0, sticky=tkinter.W+tkinter.W+tkinter.S+tkinter.N)

        tkinter.Button(frame, text="OK", command=self._on_btn_ok_clicked).grid(
            row=1, column=0)


    def _on_btn_ok_clicked(self):
        self.top.destroy()

class InstallExiftoolDlg(ModalDialog):
    _exiftool = None
    _local_appdata_path = ""

    _txt_status_searching = "Status: searching..."
    _txt_status_not_installed = "Status: not installed"
    _txt_status_installed = "Status: ok"


    def __init__(self, parent, exiftool, local_appdata):
        ModalDialog.__init__(self, parent)

        self._exiftool = exiftool
        self._local_appdata_path = local_appdata
        self._frame = tkinter.Frame(self.top)
        self._frame.grid()

        self._btn_set_location = tkinter.Button(
            self._frame,
            text="Set exiftool location...",
            command=self._on_set_location_clicked)
        self._btn_set_location.grid(row=0, column=0, sticky=tkinter.W)

        self._btn_auto_install = tkinter.Button(
            self._frame,
            text="Try to autoinstall",
            command=self._on_auto_install_clicked)
        self._btn_auto_install.grid(row=1, column=0, sticky=tkinter.W)

        self._btn_manual_install = tkinter.Button(
            self._frame,
            text="Install manually",
            command=self._on_manual_install_clicked)
        self._btn_manual_install.grid(row=2, column=0, sticky=tkinter.W)

        # Status view
        self._var_status = tkinter.StringVar()
        self._var_status.set(self._txt_status_searching)

        self._lbl_status = tkinter.Label(self._frame, textvariable=self._var_status)
        self._lbl_status.grid(row=0, column=1, sticky=tkinter.W)

        img_unchecked_path = os.path.join(sys.path[0], "img/unchecked.gif")
        self._img_unchecked = tkinter.PhotoImage(
            file=img_unchecked_path).subsample(3, 3)

        img_checked_path = os.path.join(sys.path[0], "img/checked.gif")
        self._img_checked = tkinter.PhotoImage(
            file=img_checked_path).subsample(3, 3)

        self._lbl_img_status = tkinter.Label(
            self._frame, image=self._img_unchecked)
        self._lbl_img_status.grid(row=1, rowspan=2, column=1, sticky=tkinter.W+tkinter.E)

        self._detect_current_state()


    def _detect_current_state(self):
        if self._exiftool.is_installed():
            self._var_status.set(self._txt_status_installed)
            self._lbl_img_status.configure(image=self._img_checked)
        else:
            self._var_status.set(self._txt_status_not_installed)
            self._lbl_img_status.configure(image=self._img_unchecked)


    def _set_current_state_to_searching(self):
        self._var_status.set(self._txt_status_searching)
        self._lbl_img_status.configure(image=self._img_unchecked)


    def _on_set_location_clicked(self):
        self._set_current_state_to_searching()
        dlg = tkinter.filedialog.LoadFileDialog(self._frame)
        file = dlg.go()
        if file is not None:
            self._exiftool.set_exiftool_path_manually(file)

        self._detect_current_state()


    def _on_auto_install_clicked(self):
        self._set_current_state_to_searching()

        ret = exiftoolinst.try_auto_install_exiftool(self._local_appdata_path)
        if ret[0] == True:
            # We only set our current path if the operation succeeded.
            # That way auto_install can be called multiple times without breaking
            # the object as exiftoolinst.try_auto_install_exiftool will fail to
            # overwrite a previous install
            self._exiftool.set_exiftool_path_manually(ret[1])

        # Recalculate our state with the new exiftool installation status
        self._detect_current_state()


    def _on_manual_install_clicked(self):
        """Send the user to the exiftool website for manual download.

        They will have to set the path manually afterward.

        """

        self._set_current_state_to_searching()
        exiftoolinst.browser_launches_exiftool_homepage()
        self._detect_current_state()


class PopenOutputDlg(ModalDialog):
    """Class that links an instance of a process with an output command line.

    Simply instantiate and show() the class to pop a modal dialog and execute
    the Popen command automatically.

    """

    _popen_generator = None
    _current_popen = None
    _aborted = False


    def __init__(self, parent, popen_generator):
        """ Will allow the user to launch and cancel the execution of a process
            while seeing its console output.

            Parameters:
                parent: parent tkinter widget.

                popen_generator: A function that will return (command_line, popen_object).
                    command_line: The command line passed to subprocess.open().

                    popen_object: The return value of subprocess.open().

        """

        ModalDialog.__init__(self, parent)
        self._popen_generator = popen_generator
        self._create_layout()


    def _create_layout(self):
        self._frame = tkinter.Frame(self.top)
        self._frame.grid()

        # Create the output window
        output_frame = tkinter.Frame(self._frame)
        output_frame.grid(column=0, row=0, sticky=tkinter.W)

        self._text_output = tkinter.Text(output_frame, width=80, height=30)
        self._text_output.grid(row=0, column=0, sticky=tkinter.W)
        self._text_output.configure(state="disabled")

        output_scrollbar = tkinter.Scrollbar(output_frame)
        output_scrollbar.grid(row=0, column=1, sticky=tkinter.W+tkinter.E+tkinter.S+tkinter.N)

        # Attach the listbox to the scrollbar
        self._text_output.config(yscrollcommand=output_scrollbar.set)
        output_scrollbar.config(command=self._text_output.yview)

        # Create the commands
        button_frame = tkinter.Frame(self._frame)
        button_frame.grid(column=0, row=1, sticky=tkinter.E)

        # Launch the Popen command requested
        self._launch()


    def _launch(self):
        for proc_info in self._popen_generator():
            self._append_output_txt("\n\nCommand: " + proc_info[0] + "\n\n...\n\n")
            self._current_popen = proc_info[1]

            outputs = self._current_popen.communicate()
            self._append_output_txt(outputs[1]) # stderr
            self._append_output_txt(outputs[0]) # stdout

            if self._aborted:
                break

        self._aborted = False


    def _on_btn_abort_clicked(self):
        if self._current_popen != None:
            self._aborted = true
            self._current_popen.terminate()


    def _append_output_txt(self, output_txt):
        self._text_output.configure(state="normal")
        self._text_output.insert(tkinter.INSERT, output_txt)
        self._text_output.configure(state="disabled")


# Bootstart
root = tkinter.Tk()
app = App(root)
root.mainloop()
