# -*- coding: utf-8 -*-
"""
cligui - 
"""
from datetime import date, time, datetime

import os
import tkinter
from tkinter import (
    Tk,
    StringVar,
    IntVar,
    DoubleVar,
    BooleanVar,
    ttk,
    filedialog,
)

# from tkinter.scrolledtext import ScrolledText


class GUI:
    def __init__(self, windowname):
        """class to create a simple dialog to collect information for a program

        Parameters:
            windowname: the name of the window to display the widgets.

        """
        self.name = windowname
        self.items = {}  # stores each add() call
        self.frame = None
        self.data = {}
        self.actions = {}
        self.widgets = {}
        # change frameopts if you want to change the frame styles
        self.frameopts = {"padding": 10}
        # chack packopts if you want to change the frame packing.
        self.packopts = {"fill": "x"}
        pass

    def add(self, name, values, id=None, init=None, type=None, **kwargs):
        """add a widget

        Parameters:
            name: the widget name, to store the value in an object, sometimes
                 also a displayed name
            values: values the widget can take. The type of values is used to infer
                the type of widget.
            id: in case the name isn't unique enough
            init: initial value
            type: override the default widget type. Possible values are
                'entry', 'numeric', 'date', 'datetime', 'checkbox', 'color',
                'radio', 'dropdown', 'buttons', 'openfile', 'savefile', 'openfolder',
                'progress'

            **kwargs - used for some widget types.

        This defines a widget in the GUI window. If type is not given, the widget
        type is determined by the type of values. The defaults are:
            bool: checkbox
            string: text entry
            int or float: numeric entry
            array of 3 ints 0-255: colour picker (maybe change this?)
            array: dropdown
            date, datetime: date or datetime
            None: defer to the type value (for type = 'openfile', 'savefile', or 'openfolder')

        **The type always has to be supplied for 'radio', 'buttons', 'openfile',
        'savefile', 'openfolder', or 'progress'.**

        When the gui is run, it creates a dict `data` and `widgets`. These are keyed by
        the widget id, or name if the id is not given.
        The data dict contains the current values (StringVar, IntVar ... ) of the widgets, and
        the widgets dict contains the widgets themselves, so that they can be updated.
        """
        if type is None:
            type = self.infer_type(values)
        # gather all parameters as a config object
        config = {
            "values": values,
            "id": id,
            "init": init,
            "type": type,
            "args": kwargs,
        }
        if self.frame is None:
            # add the config as the next item
            self.items[name] = config
        else:
            # add the config as the next item in the frame
            self.items[self.frame]["items"][name] = config

    def group(self, framename=None, **options):
        """following items are put in a labelled frame

        Parameters:
            framename: the frame label. If None,
               the frame ends. If it starts with a _, the frame is not labelled.
              **options: keyword args passed to the widget command
        """
        self.frame = framename
        if framename is not None:
            self.items[framename] = {
                "type": "frame",
                "items": {},
                "args": options,
            }

    def infer_type(self, values):
        """guesses the type of widget based on values"""
        if type(values) == str:
            return "entry"
        if type(values) in [int, float]:
            return "numeric"
        if type(values) == date:
            return "date"
        if type(values) == datetime:
            return "datetime"
        if values == bool:
            return "checkbox"
        if type(values) in [list, tuple]:
            if len(values) == 3 and all(
                map(lambda x: type(x) == int and x >= 0 and x <= 255, values)
            ):
                return "colour"
            if len(values) > 0 and all(
                map(lambda x: type(x) is bytes, values)
            ):
                return "buttons"
            return "dropdown"

    def layout(self, host, items):
        # add the controls
        for name, opts in items.items():
            type = opts["type"]
            if type == "frame":
                self._frame(host, name, opts)
            elif type == "entry":
                self._entry(host, name, opts)
            elif type == "numeric":
                self._numeric(host, name, opts)
            elif type == "dropdown":
                self._dropdown(host, name, opts)
            elif type == "checkbox":
                self._checkbox(host, name, opts)
            elif type == "radio":
                self._radio(host, name, opts)
            elif type == "buttons":
                self._buttons(host, name, opts)
            elif type in ["openfile", "savefile", "openfolder"]:
                self._picker(host, name, type, opts)
            elif type == "progress":
                self._progress(host, name, opts)

    def _frame(self, host, name, options):
        # create the frame
        args = {**self.frameopts, **options["args"]}
        if name.startswith("_"):
            frame = ttk.Frame(host, **args)
        else:
            frame = ttk.LabelFrame(host, text=name, **args)
        frame.pack(**self.packopts)
        self.layout(frame, options["items"])

    def _entry(self, host, name, options):
        # create an entry widget in its own frame
        id = options["id"] or name
        args = options["args"]
        # the text entry is framed
        panel = ttk.LabelFrame(host, text=name, **self.frameopts)
        panel.pack(**self.packopts)
        # the textvar for the entry widget
        textvar = StringVar()
        textvar.set(options["init"] or options["values"])
        # and the entry widget itself
        entry = ttk.Entry(panel, textvariable=textvar, **args)
        entry.pack(fill="x")
        # save references to var and widget
        self.data[id] = textvar
        self.widgets[id] = entry

    def _numeric(self, host, name, options):
        # create an numeric widget in its own frame
        id = options["id"] or name
        args = {"from_": 0, "to": 100}
        args = {**args, **options["args"]}
        # the numeric entry is framed
        panel = ttk.LabelFrame(host, text=name, **self.frameopts)
        panel.pack(**self.packopts)
        # the textvar for the entry widget
        nvar = DoubleVar()
        nvar.set(options["init"] or options["values"])
        # and the entry widget itself
        entry = ttk.Spinbox(panel, textvariable=nvar, **args)
        entry.pack(fill="x")
        # save references to var and widget
        self.data[id] = nvar
        self.widgets[id] = entry

    def _dropdown(self, host, name, options):
        # create a dropdown combobox widget in its own frame
        id = options["id"] or name
        args = options["args"]
        # the dropdown box is framed
        panel = ttk.LabelFrame(host, text=name, **self.frameopts)
        panel.pack(**self.packopts)
        # the textvar for the dropdown
        textvar = StringVar()
        textvar.set(options["init"] or "")
        # and the widget itself
        dropdown = ttk.Combobox(
            panel, values=options["values"], textvariable=textvar, **args
        )
        dropdown.pack(fill="x")
        # save references to var and widget
        self.data[id] = textvar
        self.widgets[id] = dropdown

    def _checkbox(self, host, name, options):
        # creates a checkbox - this is not framed
        id = options["id"] or name
        args = options["args"]
        # the boolvar for the checkbox
        boolvar = BooleanVar()
        if options["init"] is not None:
            boolvar.set(options["init"])
        # and the widget itself
        checkbox = ttk.Checkbutton(host, text=name, variable=boolvar, **args)
        checkbox.pack(fill="x")
        # save references to var and widget
        self.data[id] = boolvar
        self.widgets[id] = checkbox

    def _radio(self, host, name, options):
        # creates a radio button group in a named frame
        id = options["id"] or name
        args = options["args"]
        # the radio group box is framed
        panel = ttk.LabelFrame(host, text=name, **self.frameopts)
        panel.pack(**self.packopts)
        # the var for the radio group
        textvar = StringVar()
        textvar.set(options["init"] or "")
        # the radio button widgets are stored in an array
        buttons = []
        for name in options["values"]:
            b = ttk.Radiobutton(
                panel, text=name, variable=textvar, value=name, **args
            )
            b.pack(fill="x")
            buttons.append(b)
        # save references to the var and the array of widgets
        self.data[id] = textvar
        self.widgets[id] = buttons

    def _picker(self, host, name, type, options):
        # file picker item, which has a button & a text entry to display the current file name
        id = options["id"] or name
        args = options["args"]
        # the file picker is framed
        panel = ttk.LabelFrame(host, text=name, **self.frameopts)
        panel.pack(**self.packopts)
        panel.columnconfigure(0, weight=1)
        panel.columnconfigure(1, weight=2)
        # the var to hold t
        fname = StringVar()
        fname.set("")

        # the args holds keywords to pass to the picker dialog.
        # The title is inherited from the frame, if not given
        if "title" not in args:
            args["title"] = name

        def handler(*args):
            # open the dialog when the button is pressed,
            # then save the path & display the filename
            if type == "openfile":
                path = filedialog.askopenfilename(parent=self.root, **args)
            elif type == "savefile":
                path = filedialog.asksaveasfilename(parent=self.root, **args)
            elif type == "openfolder":
                path = filedialog.askdirectory(parent=self.root, **args)
            fname.set(path or fname.get())
            labeltxt["text"] = os.path.basename(fname.get())

        # the browse button
        button = ttk.Button(
            panel,
            text="Browse",
            command=handler,
        )
        button.pack(side="left")
        # the label which holds the filename
        labeltxt = ttk.Label(panel, text=" ", padding=(10, 0, 0, 0))
        labeltxt.pack(side="left")
        # save references to the var and the Browse button
        self.data[id] = fname
        self.widgets[id] = button

    def _buttons(self, host, name, options):
        # create a panel of buttons
        id = options["id"] or name
        args = options["args"]
        # the panel is not named
        if name.startswith("_"):
            panel = ttk.Frame(host, **self.frameopts)
        else:
            panel = ttk.LabelFrame(host, text=name, **self.frameopts)
        panel.pack(**self.packopts)
        # this var holds the value of the last pressed button.
        pressed = StringVar()
        pressed.set("")

        # create the buttons & save in a list
        buttonlist = {}
        layout = args.get("layout", "grid")
        if "layout" in args:
            del args["layout"]

        def make_handler(name):
            # create a handler for the button.
            def handler(*args):
                pressed.set(name)
                self.onchange(name, "pressed")

            return handler

        for i, b in enumerate(options["values"]):
            if type(b) is bytes:
                b = b.decode("utf-8")
            button = ttk.Button(panel, text=b, command=make_handler(b), **args)
            if layout == "grid":
                # standard
                button.grid(row=0, column=i)
                panel.columnconfigure(i, pad=5, weight=1)
            if layout == "grid_fill":
                button.grid(row=0, column=i, sticky="NSEW", padx=5)
                panel.columnconfigure(i, pad=5, weight=1)
            buttonlist[b] = button
        # save references to the var and the button widgets
        self.data[id] = pressed
        for k in buttonlist:
            self.widgets[k] = buttonlist[k]

    def _progress(self, host, name, options):
        # create a progress bar in a frame
        id = options["id"] or name
        args = {"orient": tkinter.HORIZONTAL}
        args = {**args, **options["args"]}
        # create the anonymous panel
        panel = ttk.Frame(host, **self.frameopts)
        panel.pack(**self.packopts)
        # create the var for the progress
        progress = IntVar()
        pbar = ttk.Progressbar(panel, variable=progress, **args)
        pbar.pack(fill="x")
        # save references to the var and the button list
        self.data[id] = progress
        self.widgets[id] = pbar

    def get(self, name):
        """get the current value of some widget by name

        Parameters:
            name: the name (or id) of the widget

        Returns:
            the widget value
        """
        return self.data[name].get()

    def set(self, name, value):
        """sets the current value of some widget by name
        and allows the gui to update

        Parameters:
            name: the name (or id) of the widget
            value: its value
        """
        self.data[name].set(value)
        self.root.update_idletasks()

    def getvalues(self):
        """get the current values of all the widgets in self.data

        Parameters:
            none

        Returns:
            a dict whose keys are the widget names or ids and whose values are
            the current widget values.
        """
        result = {}
        for name, value in self.data.items():
            result[name] = value.get()
        return result

    def onchange(self, name, value):
        # called every time a widget value changes
        # name is the name/id of the widget and value is the new value
        result = None
        if name in self.actions:
            result = self.actions[name](name, value, self)
        if "*" in self.actions and result is None:
            self.actions["*"](name, value, self)

    def on(self, name, callback=None):
        """connect or decorate a callback

        Parameters:
            name: the name or id of the widget to connect the callback to
            callback: the callback function.

        Returns:
            if callback is given, it connects it will be called
            any time the widget is used
            If not given, on() returns a decorator function.

        The callback takes (name, value, gui) parameters. gui is the
        entire gui object.
        """
        if callback is None:

            def decorator(f):
                self.actions[name] = f
                return f

            return decorator
        else:
            self.actions[name] = callback

    def run(self, root=None, minsize=(400, 10)):
        """creates the gui & runs it

        Parameters:
            root: the root window. If not given, a new root window is created
                by a call to Tk() and mainloop is entered. This is just for
                the case when you just want to run this window.
            minsize: the minimum size of the gui window

        If root is the tk root window, then the tk mainloop is also started.
        """
        if root is None:
            root = Tk()
        root.minsize(*minsize)
        root.title(self.name)
        self.root = root

        # put the themeable frame inside the root.
        mainframe = ttk.Frame(root, **self.frameopts)
        mainframe.pack(fill="both")

        # layout the widgets
        self.vars = {}
        self.layout(mainframe, self.items)

        # setup tracing on all variables to call onchange
        def put_trace(name, var):
            var.trace(
                "w",
                lambda *args: self.onchange(name, var.get()),
            )

        for name, value in self.data.items():
            put_trace(name, value)

        # trigger the init callback if any
        self.onchange("init", None)

        # start the mainloop if we've been passed the root window
        if str(Tk.winfo_parent(root)) == "":
            root.mainloop()


if __name__ == "__main__":
    # demo
    g = GUI("Test GUI")
    g.add("Enter some text", "")
    g.add("Pick a number", 0, to=10, increment=0.5)
    g.add("Choose an alternative", ["a", "b", "c"])
    g.group("Some checkboxes")
    g.add("check this ", bool)
    g.add("check this too", bool)
    g.group()
    g.add(
        "Choose an alternative with radio buttons",
        ["a", "b", "c"],
        type="radio",
    )
    g.add(
        "Save file",
        "",
        type="savefile",
        id=42,
        title="Save a csv or excel file",
        filetypes=(("CSV", "*.csv"), ("Excel", "*.xlsx")),
    )
    g.add("_buttons", [b"Run", b"Quit"], layout="grid_fill")
    g.add("progress", 0, type="progress")

    g.on("dropdown")(lambda *args: print(*args))
    g.on("init", lambda *args: print(" callback init"))

    @g.on("Run")
    def runner(name, value, gui):
        gui.data["progress"].set(gui.data["progress"].get() + 10)

    g.on("Quit", lambda *args: g.root.destroy())
    g.run(minsize=(300, 200))
    print(g.getvalues())
