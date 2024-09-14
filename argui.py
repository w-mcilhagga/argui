# -*- coding: utf-8 -*-
"""
GUI program to collect values you'd normally do with a commandline program.'
"""

import os, traceback
import tkinter
from tkinter import (
    Tk,
    StringVar,
    IntVar,
    DoubleVar,
    BooleanVar,
    ttk,
    filedialog,
    messagebox,
)

# from tkinter.scrolledtext import ScrolledText

class GUI:
    def __init__(self, windowname, ico=None, minsize=(100, 100)):
        """class to create a simple dialog.

        Parameters:
            windowname: the name of the window that displays the widgets.
            ico: (optional) the path to the .ico file for the window.
            minsize: (optional) the minimum size of the window as a tuple (width, height)

        The workflow is:
            1. Create the GUI object
            2. Add widgets to it
            3. Create behaviours (if needed) using the on() method.
            4. Run the GUI, which creates a window & displays the widgets.
        """
        self.name = windowname
        self.iconpath = ico
        self.minsize = minsize
        self.items = []  # stores each addwidget() call
        self.frame = None
        self.data = {}
        self.actions = {}
        self.widgets = {}
        # change frameopts if you want to change the frame styles
        self.frameopts = {"padding": 10}
        # change packopts if you want to change the frame packing.
        self.packopts = {"fill": "x"}

        # make an error handler - can be overridden
        @self.on("__error__")
        def handler(name, value, g, err):
            trace = traceback.extract_tb(err.__traceback__, limit=None)[-1]
            fname = os.path.basename(trace.filename)
            messagebox.showerror(
                f'Error while executing "{name}"',
                f"{type(err).__name__} at line {trace.lineno} in {fname}:\n{err}",
            )

    def addwidget(self, widget):
        # adds a config object to the internal item list for later rendering
        if self.frame is None:
            # add the config as the next item
            self.items.append(widget)
        else:
            # add the config as the next item in the frame
            self.items[-1].append(widget)

    def layout(self, host, items):
        # add the controls
        for widget in items:
            if type(widget) is list:
                self.layout(self.create_panel(host, widget[0]), widget[1:])
            else:
                widget(host)

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

    def update(self, name, values, **options):
        """update the content of a widget. This is aimed
        specifically at dropdown widgets which frequently get
        their choices reset, but may expand to other widget
        types

        Parameters:
            name: the name of the widget
            values: an array of choices for the dropdown
            options: state='normal' and similar configuration values
        """
        w = self.widgets[name]
        oldvalues = w["values"]
        w["values"] = values
        if tuple(oldvalues) != tuple(values) or options.get(
            "state", "disabled"
        ):
            # the existing choice doesn't work
            self.set(name, "")
        w.configure(**options)

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
            if callback is given, it will be called
            any time the widget is used
            If not given, on() returns a decorator function.

        The callback takes (name, value, gui) parameters. gui is the
        entire gui object.
        """

        def wrap(f):
            # wraps f in an error handler
            if name == "__error__":
                return f

            def handler(name, value, g):
                try:
                    f(name, value, g)
                except tkinter.TclError:
                    # HACK!!!
                    # filtering these out because .destroy() causes them.
                    pass
                except Exception as err:
                    self.actions["__error__"](name, value, g, err)

            return handler

        if callback is None:

            def decorator(f):
                self.actions[name] = wrap(f)
                return f

            return decorator
        else:
            self.actions[name] = wrap(callback)

    def handle_error(self, name, value, g, err):
        pass

    def run(self, root=None):
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
        root.minsize(*self.minsize)
        root.title(self.name)
        self.root = root

        # put the themeable frame inside the root.
        mainframe = ttk.Frame(root, **self.frameopts)
        mainframe.pack(fill="both")

        # layout the widgets
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

        if self.iconpath is not None:
            root.iconbitmap(self.iconpath)

        # start the mainloop if we've been passed the root window
        if str(Tk.winfo_parent(root)) == "":
            root.mainloop()
        return self.getvalues()

    # widget builders

    def create_panel(self, host, name):
        # the frame_if_ is for button bars
        if not name:
            return host
        if name.startswith("_"):
            panel = ttk.Frame(host, **self.frameopts)
            panel.pack(**self.packopts)
            return panel
        panel = ttk.LabelFrame(host, text=name, **self.frameopts)
        panel.pack(**self.packopts)
        return panel

    def text_entry(self, name, value="", *, id=None, noframe=False, **kwargs):
        """text entry widget

        name: the widget name. This is the name given to a frame around the
            widget unless it starts with an underscore.
        value: initial value.
        id: If given, it is used instead of the name to index the
            widget's value in get or set methods.
        noframe: whether to frame the widget or not.
        **kwargs: additional arguments to pass to the widget
        """
        id = id or name

        def widget(host, *args):
            host = self.create_panel(host, name if not noframe else "")
            textvar = StringVar(value=value)
            entry = ttk.Entry(host, textvariable=textvar, **kwargs)
            entry.pack(fill="x")
            # save references to var and widget
            self.data[id] = textvar
            self.widgets[id] = entry

        self.addwidget( widget)

    def numeric_entry(
        self, name, value=0, *, id=None, noframe=False, **kwargs
    ):
        """numeric entry widget

        name: the widget name. This is the name given to a frame around the
            widget unless it starts with an underscore.
        value: initial value.
        id: If given, it is used instead of the name to index the
            widget's value in get or set methods.
        noframe: whether to frame the widget or not.
        **kwargs: additional arguments to pass to the widget
        """
        id = id or name

        def widget(host, *args):
            host = self.create_panel(host, name if not noframe else "")
            numvar = DoubleVar(value=value)
            entry = ttk.Spinbox(host, textvariable=numvar, **kwargs)
            entry.pack(fill="x")
            # save references to var and widget
            self.data[id] = numvar
            self.widgets[id] = entry

        self.addwidget( widget)

    def dropdown(
        self, name, values, *, id=None, init=None, noframe=False, **kwargs
    ):
        """dropdown widget

        name: the widget name. This is the name given to a frame around the
            widget unless it starts with an underscore.
        values: list or tuple of choices.
        id: If given, it is used instead of the name to index the
            widget's value in get or set methods.
        init: initial value of the widget (optional), one of the choices
        noframe: whether to frame the widget or not.
        **kwargs: additional arguments to pass to the widget
        """
        id = id or name

        def widget(host, *args):
            host = self.create_panel(host, name if not noframe else "")
            # the textvar for the dropdown
            textvar = StringVar(value=init or "")
            dropdown = ttk.Combobox(
                host, values=values, textvariable=textvar, **kwargs
            )
            dropdown.pack(fill="x")
            # save references to var and widget
            self.data[id] = textvar
            self.widgets[id] = dropdown

        self.addwidget( widget)

    def radio(self, name, values, *, id=None, noframe=False, **kwargs):
        """radio button cluster

        name: the widget name. This is the name given to a frame around the
            widget unless it starts with an underscore.
        values: dict of choices. The dict keys are used as radio button labels
            The dict values are used to work out if the buttons are on or off.
        id: If given, it is used instead of the name to index the
            widget's value in get or set methods.
        noframe: whether to frame the widget or not.
        **kwargs: additional arguments to pass to the widget
        """
        id = id or name

        def widget(host, *args):
            host = self.create_panel(host, name if not noframe else "")
            textvar = StringVar()
            buttons = []
            for label in values:
                b = ttk.Radiobutton(
                    host, text=label, variable=textvar, value=label, **kwargs
                )
                if values[label]:
                    textvar.set(label)
                b.pack(fill="x")
                buttons.append(b)
            # save references to the var and the array of widgets
            self.data[id] = textvar
            self.widgets[id] = buttons

        self.addwidget( widget)

    def checkbox(self, name, value=False, *, id=None, noframe=True, **kwargs):
        """single checkbox widget

        name: the widget name. This is the name given to a frame around the
            widget unless it starts with an underscore.
        value: True or False.
        id: If given, it is used instead of the name to index the
            widget's value in get or set methods.
        noframe: whether to frame the widget or not. Unlike most widgets, the
            default here is True
        **kwargs: additional arguments to pass to the widget
        """
        id = id or name

        def widget(host, *args):
            host = self.create_panel(host, name if not noframe else "")
            boolvar = BooleanVar(value=value)
            checkbox = ttk.Checkbutton(host, text=name, variable=boolvar, **kwargs)
            checkbox.pack(fill="x")
            # save references to var and widget
            self.data[id] = boolvar
            self.widgets[id] = checkbox
            
        self.addwidget( widget)


    def checklist(self, name, values, *, id=None, noframe=False, prefix='', **kwargs):
        """list of checkboxes in a frame.

        name: the widget name. This is the name given to a frame around the
            widget unless it starts with an underscore.
        values: dict of choices. The dict keys are used as checkbox labels
            The dict values are used to work out if the boxes are checked or not.
            The keys are also used to store the check results
        id: If given, it is used instead of the name to index the
            widget's value in get or set methods.
        noframe: whether to frame the widget or not.
        prefix: a string to prefix the checkbox names in the data, in case they aren't
            unique enough
        **kwargs: additional arguments to pass to the widget
        """
        id = id or name
        
        def widget(host, *args):
            # creates a framed list of checkboxes
            host = self.create_panel(host, name if not noframe else "")
            for label in values:
                boolvar = BooleanVar(value=values[label])
                checkbox = ttk.Checkbutton(host, text=label, variable=boolvar, **kwargs)
                checkbox.pack(fill="x")
                # save references to var and widget
                self.data[prefix+label] = boolvar
                self.widgets[prefix+label] = checkbox
            
        self.addwidget( widget)
        
    def picker(
        self,
        name,
        mode,
        *,
        id=None,
        filetypes=(("All Files", "*.*"),),
        title=None,
        **kwargs,
    ):
        """a file picker

        name: the widget name. This is the name given to a frame around the
            widget unless it starts with an underscore.
        mode: openfile, savefile, or openfolder
        id: If given, it is used instead of the name to index the
            widget's value in get or set methods.
        filetypes, title: some standard dialog options.
        **kwargs: additional arguments to pass to the widget
        """
        id = id or name
        if title:
            kwargs['title']=title
        kwargs['filetypes']=filetypes
        
        def widget(host, *args):
            # file picker item, which has a button & a text entry to display the current file name
            host = self.create_panel(host, name)
            host.columnconfigure(0, weight=1)
            host.columnconfigure(1, weight=2)
            fname = StringVar(value="")

            def handler():
                # open the dialog when the button is pressed,
                # then save the path & display the filename
                if mode == "openfile":
                    path = filedialog.askopenfilename(parent=self.root, **kwargs)
                elif mode == "savefile":
                    path = filedialog.asksaveasfilename(parent=self.root, **kwargs)
                elif mode == "openfolder":
                    path = filedialog.askdirectory(parent=self.root, **kwargs)
                fname.set(path or fname.get())
                labeltxt["text"] = os.path.basename(fname.get())

            # the browse button
            button = ttk.Button(
                host,
                text="Browse",
                command=handler,
            )
            button.pack(side="left")
            # the label which holds the filename
            labeltxt = ttk.Label(host, text=" ", padding=(10, 0, 0, 0))
            labeltxt.pack(side="left")
            # save references to the var and the Browse button
            self.data[id] = fname
            self.widgets[id] = button
            
        self.addwidget( widget)

    def buttons(self, name, values, *, id=None, layout="row", **kwargs):
        """push buttons in a panel

        name: the panel name. This is the name given to a frame around the
            widget unless it starts with an underscore.
        values: list of button texts. These can trigger callbacks with on()
        id: If given, it is used instead of the name to index the
            widget's value in get or set methods.
        layout: either 'row' or 'column'
        **kwargs: additional arguments to pass to the widget
        """
        id = id or name
        
        def widget(host, *args):
            host = self.create_panel(host, name)
            # this var holds the value of the last pressed button.
            pressed = StringVar(value="")
            # create the buttons & save in a list
            buttonlist = {}

            def make_handler(name):
                # create a handler for the button.
                def handler(*args):
                    pressed.set(name)
                    self.onchange(name, "pressed")

                return handler

            for i, b in enumerate(values):
                button = ttk.Button(host, text=b, command=make_handler(b), **kwargs)
                buttonlist[b] = button
                if layout == "row":
                    # standard single row layout
                    button.grid(row=0, column=i)
                    host.columnconfigure(i, pad=5, weight=1)
                if layout == "column":
                    # single column layout, buttons stretch to fill
                    button.grid(row=i, sticky="NSEW", pady=3)
                    host.rowconfigure(i, pad=5, weight=1)

            if layout == "column":
                host.columnconfigure(0, pad=5, weight=1)
            # save references to the var and the button widgets
            self.data[id] = pressed
            for k in buttonlist:
                self.widgets[k] = buttonlist[k]

        self.addwidget(widget)

    def progressbar(self, name, value=0, *, id=None, noframe=True, **kwargs):
        """add a progress bar
        
        name: the panel name. This is the name given to a frame around the
            widget unless it starts with an underscore.
        value: the initial value of the progress bar. Goes up to 100.
        id: If given, it is used instead of the name to index the
            widget's value in get or set methods.
        noframe: whether to frame the widget or not. Default is True
        **kwargs: additional arguments to pass to the widget
        """
        id = id or name
        kwargs = {"orient": tkinter.HORIZONTAL, **kwargs}
        
        def widget(host, *args):
            host = self.create_panel(host, name if not noframe else "")
            # create the var for the progress
            progress = IntVar(value=value)
            pbar = ttk.Progressbar(host, variable=progress, **kwargs)
            pbar.pack(fill="x")
            # save references to the var and the button list
            self.data[id] = progress
            self.widgets[id] = pbar
            
        self.addwidget(widget)

    def label(self, labeltext, *, id=None, **kwargs):
        ''' insert an unframed label label.
        
        labeltext: the text of the label.
        id: the label id, needed if you want to change the text
        **kwargs: additional arguments to pass to the widget
        '''
        
        def widget(host, *args):
            panel = ttk.Frame(host, **self.frameopts)
            panel.pack(**self.packopts)
            label = ttk.Label(panel, text=labeltext, **kwargs)
            label.pack()
            # save references to the widget
            if id:
                self.widgets[id] = label
                
        self.addwidget(widget)

    def group(self, framename=None, **options):
        """following items are put in a labelled frame

        Parameters:
            framename: the frame label. If None,
               the frame ends. If it starts with a _, the frame is not labelled.
              **options: keyword args passed to the widget command
        """
        self.frame = framename
        if framename is not None:
            self.items.append([framename])

if __name__ == "__main__":
    # demo
    g = GUI("Test GUI", minsize=(300, 200))
    g.text_entry("Enter some text", id="text")
    g.numeric_entry("Pick a number", 0, from_=-2, to=10, increment=0.5)
    g.dropdown("Choose an alternative", ["a", "b", "c"], init="a")
    g.checklist(
        "Some checkboxes", {"check this": False, "check this too": True}
    )
    g.radio(
        "Choose an alternative with radio buttons",
        {"a": False, "b": False, "c": True},
    )
    g.picker(
        "Save file",
        mode="savefile",
        id=42,
        title="Save a csv or excel file",
        filetypes=(("CSV", "*.csv"), ("Excel", "*.xlsx")),
    )
    g.buttons("_buttons", ["Run", "Quit"], layout="row")
    g.progressbar("_progress", noframe=False, id='progress')
    g.label('This is a label')

    @g.on("Run")
    def runner(name, value, gui):
        gui.data["progress"].set(gui.data["progress"].get() + 10)

    g.on("Quit", lambda *args: g.root.destroy())
    print(g.run())
