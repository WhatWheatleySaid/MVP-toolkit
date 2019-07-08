import tkinter
from tkcalendar import DateEntry
from tkinter import ttk

class artist_menu_toplevel(tkinter.Toplevel):
    ''' popup menu to alter artist color and name or remove artist'''
    def __init__(self,application,object):
        tkinter.Toplevel.__init__(self)
        self.parent = application

        x = self.parent.master.winfo_x()
        y = self.parent.master.winfo_y()
        self.geometry("+%d+%d" % (x + 10, y + 20))
        self.title("{0}".format(object.displayname))


        self.tabcontrol = ttk.Notebook(self)
        self.parameters_tab = ttk.Frame(self.tabcontrol)
        self.info_text_tab = ttk.Frame(self.tabcontrol)
        self.tabcontrol.add(self.parameters_tab, text = 'object parameters')
        self.tabcontrol.add(self.info_text_tab, text = 'DB information')
        self.tabcontrol.grid(row=0,column=0,sticky= tkinter.S+tkinter.N+tkinter.W+tkinter.E)

        self.button_frame = ttk.Frame(self)
        self.button_frame.grid(row=1,column=0)
        self.displayname_var = tkinter.StringVar()
        self.displayname_var.set(str(object.displayname))


        self.info_text_widget = tkinter.Text(self.info_text_tab)
        self.info_text_widget.insert(tkinter.END,object.info_text)
        self.info_text_widget.config(state=tkinter.DISABLED)
        self.info_text_widget.grid(row=0,column=0)
        self.settings_frame =  tkinter.LabelFrame(self.parameters_tab, text= 'parameters')
        self.settings_frame.grid(row=0,column= 0,sticky= tkinter.S+tkinter.N+tkinter.W+tkinter.E)

        tkinter.Label(self.settings_frame,text='object color:').grid(row=0,column=0,sticky= tkinter.S+tkinter.N+tkinter.W+tkinter.E)
        self.artist_color_button = tkinter.Button(self.settings_frame,text='',bg = object.color ,command=lambda: self.parent.get_color(self.artist_color_button,self), width=10)
        self.artist_color_button.grid(row=0,column=1,sticky= tkinter.S+tkinter.N+tkinter.W+tkinter.E)

        tkinter.Label(self.settings_frame,text='displayname:').grid(row=2,column=0,sticky= tkinter.S+tkinter.N+tkinter.W+tkinter.E)
        tkinter.Entry(self.settings_frame,textvariable=self.displayname_var).grid(row=2,column=1,sticky= tkinter.S+tkinter.N+tkinter.W+tkinter.E)

        self.dismiss_button = tkinter.Button(self.button_frame, text="cancel", command=lambda: self.parent.destroy_toplevel(self))
        self.dismiss_button.grid(row=0,column=0)
        self.accept_button = tkinter.Button(self.button_frame, text="apply changes", command = lambda: self.parent.update_artist(object,self.artist_color_button,self.displayname_var.get(),self))
        self.accept_button.grid(row=0,column=1)
        self.remove_button = tkinter.Button(self.button_frame, text="remove this from plot", command = lambda: self.parent.remove_artist(object,self))
        self.remove_button.grid(row=0,column=2)
        self.resizable(width=False,height=False)
        self.transient(self.parent.master)
        # self.parent.master.tk.call('wm','iconphoto',self._w,icon_img)

class custom_object_menu_toplevel(tkinter.Toplevel):
    ''' menu to choose custom object parameters'''
    def __init__(self,application):
        tkinter.Toplevel.__init__(self)
        self.parent = application
        x = self.parent.master.winfo_x()
        y = self.parent.master.winfo_y()
        self.geometry("+%d+%d" % (x + 10, y + 20))
        self.title("add custom object")
        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)

        self.a_var = tkinter.StringVar()
        self.ecc_var = tkinter.StringVar()
        self.i_var = tkinter.StringVar()
        self.omega_var = tkinter.StringVar()
        self.OMEGA_var = tkinter.StringVar()
        self.anomaly_var = tkinter.StringVar()
        self.name_var = tkinter.StringVar()
        self.name_frame = tkinter.Frame(self,pady=10)
        self.kepler_frame = tkinter.LabelFrame(self,text='kepler elements',pady=10,padx=5)
        self.button_frame = tkinter.Frame(self)
        self.name_frame.rowconfigure(0, weight=1)
        self.name_frame.columnconfigure(0, weight=1)
        self.button_frame.rowconfigure(0, weight=1)
        self.button_frame.columnconfigure(0, weight=1)
        self.kepler_frame.rowconfigure(0, weight=1)
        self.kepler_frame.columnconfigure(0, weight=1)
        # vcmd_int = (self.button_frame.register(self.validate_int),'%d', '%i', '%P', '%s', '%S', '%v', '%V', '%W')
        self.vcmd_float = (self.button_frame.register(self.validate_float), '%d', '%i', '%P', '%s', '%S', '%v', '%V', '%W')
        self.name_frame.grid(row=0,column=0,sticky=tkinter.W+tkinter.E+tkinter.N+tkinter.S)
        self.kepler_frame.grid(row=1,column=0,sticky=tkinter.W+tkinter.E+tkinter.N+tkinter.S)
        self.button_frame.grid(row=2,column=0,sticky=tkinter.W+tkinter.E+tkinter.N+tkinter.S)
        tkinter.Label(self.name_frame,text='displayname').grid(row=0,column=0,sticky=tkinter.W+tkinter.N+tkinter.S)
        tkinter.Entry(self.name_frame,validate = 'key',textvariable=self.name_var).grid(row=0,column=1,columnspan=2,sticky=tkinter.W+tkinter.E+tkinter.N+tkinter.S)
        self.kepler_array = [ ['semimajor axis:' , 'AU', self.a_var] , ['numerical eccentricity:' , '', self.ecc_var] , ['inclination:' , 'degrees', self.i_var] , ['argument of periapsis:' , 'degrees', self.omega_var] , ['longitude of the ascending node:' , 'degrees', self.OMEGA_var], ['true anomaly' , 'degrees', self.anomaly_var]]
        row_count = 0
        for element in self.kepler_array:
            tkinter.Label(self.kepler_frame,text=element[0]).grid(row=row_count,column=0,sticky=tkinter.W+tkinter.N+tkinter.S)
            tkinter.Entry(self.kepler_frame,validate = 'key', validatecommand=self.vcmd_float,textvariable=element[2]).grid(row=row_count,column=1,sticky=tkinter.W+tkinter.E+tkinter.N+tkinter.S)
            tkinter.Label(self.kepler_frame,text=element[1]).grid(row=row_count,column=2,sticky=tkinter.W+tkinter.E+tkinter.N+tkinter.S)
            row_count = row_count + 1


        tkinter.Button(self.button_frame,text='add to plot',command= lambda: self.parent.add_custom_object(self.a_var,self.ecc_var,self.i_var,self.omega_var,self.OMEGA_var,self.anomaly_var,self.name_var,self)).grid(row=0,column=0,sticky=tkinter.W+tkinter.E+tkinter.N+tkinter.S)
        tkinter.Button(self.button_frame,text='close',command= lambda: self.destroy() ).grid(row=0,column=1,sticky=tkinter.W+tkinter.E+tkinter.N+tkinter.S)

        self.transient(self.parent.master)
        self.resizable(width=False,height=False)

    @staticmethod
    def validate_float(action, index, value_if_allowed,prior_value, text, validation_type, trigger_type, widget_name):
        '''validates an float for tkinter entry'''
        if not value_if_allowed:
            return True
        try:
            float(value_if_allowed)
            return True
        except ValueError:
            return False

    @staticmethod
    def validate_int(action, index, value_if_allowed,prior_value, text, validation_type, trigger_type, widget_name):
        '''validates an integer for tkinter entry'''
        if not value_if_allowed:
            return True
        try:
            int(value_if_allowed)
            return True
        except ValueError:
            return False

class distance_menu_toplevel(tkinter.Toplevel):
    '''popup menu to choose objects and timerange to plot linear distance for'''
    def __init__(self,application):
        tkinter.Toplevel.__init__(self)
        self.parent = application

        self.choice_list = []
        self.choice_1_var = tkinter.StringVar()
        self.choice_2_var = tkinter.StringVar()
        for object in self.parent.current_objects:
            self.choice_list.append(object.displayname)
        if len(self.choice_list) < 2:
            self.parent.error_message('error','there must be atleast 2 objects to calculate a distance plot')
            return
        self.choice_1_var.set(self.choice_list[0])
        self.choice_2_var.set(self.choice_list[1])

        self.group(self.parent.master)
        x = self.parent.master.winfo_x()
        y = self.parent.master.winfo_y()
        self.geometry("+%d+%d" % (x + 10, y + 20))
        self.title("distance plot generator")
        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)
        self.dropdown_frame = tkinter.Frame(self)
        self.button_frame = tkinter.Frame(self)
        self.dropdown_frame.columnconfigure(0, weight=1)
        self.dropdown_frame.rowconfigure(0, weight=1)

        self.dropdown_frame.grid(row=0,column=0,sticky=tkinter.W+tkinter.E)
        self.object_frame = tkinter.Frame(self.dropdown_frame,borderwidth=4)
        self.object_frame.grid(row=0,column=0,sticky=tkinter.W+tkinter.E)
        self.object_frame.columnconfigure(0,weight=1)
        self.date_frame = tkinter.Frame(self.dropdown_frame,borderwidth=4)
        self.date_frame.grid(row=1,column=0,sticky=tkinter.W+tkinter.E)
        self.date_frame.columnconfigure(0,weight=1)
        self.button_frame.grid(row=2,column=0)

        self.choice_1 = tkinter.OptionMenu(self.object_frame, self.choice_1_var, *self.choice_list)
        self.choice_2 = tkinter.OptionMenu(self.object_frame, self.choice_2_var, *self.choice_list)
        self.calendar_1 = DateEntry(self.date_frame,dateformat=3,width=12, background='darkblue',foreground='white', borderwidth=4,Calendar =2018,year=self.parent.dt.year, month=self.parent.dt.month, day=self.parent.dt.day)
        self.calendar_2 = DateEntry(self.date_frame,dateformat=3,width=12, background='darkblue',foreground='white', borderwidth=4,Calendar =2018,year=self.parent.dt.year+3, month=self.parent.dt.month, day=self.parent.dt.day)

        tkinter.Label(self.object_frame,text='start object:').grid(row=0,column=0,sticky=tkinter.W)
        tkinter.Label(self.object_frame,text='target object:').grid(row=1,column=0,sticky=tkinter.W)
        tkinter.Label(self.date_frame, text='from').grid(row=0,column=1)
        tkinter.Label(self.date_frame, text='to').grid(row=0,column=2)
        tkinter.Label(self.date_frame, text='date range:').grid(row=1,column=0,sticky=tkinter.W)
        self.choice_1.grid(row=0,column=1,columnspan=2,sticky=tkinter.E)
        self.choice_2.grid(row=1,column=1,columnspan=2,sticky=tkinter.E)
        self.calendar_1.grid(row=1,column = 1,sticky=tkinter.E+tkinter.W)
        self.calendar_2.grid(row=1,column = 2,sticky=tkinter.E+tkinter.W)

        self.close_button = tkinter.Button(self.button_frame,text='close',command=self.destroy)
        self.calculate_button = tkinter.Button(self.button_frame,text='generate plot',command= lambda: self.parent.calculate_distance_plot (self.choice_1_var.get(), self.choice_2_var.get(), self.calendar_1.get_date(), self.calendar_2.get_date() ) )
        self.close_button.grid(row=0,column=0)
        self.calculate_button.grid(row=0,column=1)

        self.resizable(width=False,height=False)
        self.transient(self.parent.master)

class lambert_menu_toplevel(tkinter.Toplevel):
    ''' menu to choose parameters for the lambert solver to plot a rendeszvous orbit'''
    def __init__(self,application):
        tkinter.Toplevel.__init__(self)
        self.parent = application
        self.choice_1_var = tkinter.StringVar()
        self.choice_2_var = tkinter.StringVar()

        self.choice_list = []
        for object in self.parent.current_objects:
            self.choice_list.append(object.displayname)
        if len(self.choice_list) < 2:
            self.parent.error_message('error','there must be atleast 2 objects to plan a rendezvous')
            return
        self.choice_1_var.set(self.choice_list[0])
        self.choice_2_var.set(self.choice_list[1])

        x = self.parent.master.winfo_x()
        y = self.parent.master.winfo_y()
        self.geometry("+%d+%d" % (x + 10, y + 20))
        self.title("rendezvous tool")
        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)
        self.dropdown_frame = tkinter.Frame(self)
        self.info_frame = tkinter.Frame(self)
        self.button_frame = tkinter.Frame(self)
        self.dropdown_frame.columnconfigure(0, weight=1)
        self.info_frame.columnconfigure(0, weight=1)
        self.dropdown_frame.rowconfigure(0, weight=1)
        self.info_frame.rowconfigure(0, weight=1)

        self.dropdown_frame.grid(row=0,column=0,sticky=tkinter.W+tkinter.E)
        self.info_frame.grid(row=1,column=0,sticky=tkinter.W+tkinter.E)
        self.button_frame.grid(row=2,column=0)
        self.choice_1 = tkinter.OptionMenu(self.dropdown_frame, self.choice_1_var, *self.choice_list)
        self.choice_2 = tkinter.OptionMenu(self.dropdown_frame, self.choice_2_var, *self.choice_list)
        tkinter.Label(self.dropdown_frame,text='start object:').grid(row=0,column=0,sticky=tkinter.W)
        tkinter.Label(self.dropdown_frame,text='target object:').grid(row=1,column=0,sticky=tkinter.W)
        self.choice_1.grid(row=0,column=1,sticky=tkinter.E)
        self.choice_2.grid(row=1,column=1,sticky=tkinter.E)

        self.info_text_widget = tkinter.Label(self.info_frame,text = 'Attention: Always check for plausibility of the solution!\n This tool can calculate a rendezvous between two\n points in space with an elliptical transfer. \nYou have to plot the two desired objects on their\n corresponding dates first to plan a rendezvous between them.\n It is advised to make a porkchop-plot first!')
        self.info_text_widget.grid(row=0,column=0)

        self.close_button = tkinter.Button(self.button_frame,text='close',command=self.destroy)
        self.calculate_button = tkinter.Button(self.button_frame,text='calculate!',command=lambda : self.parent.calc_rendezvous_pykep(self.choice_1_var.get(),self.choice_2_var.get()))
        self.close_button.grid(row=0,column=0)
        self.calculate_button.grid(row=0,column=1)
        self.transient(self.parent.master)
        self.resizable(width=False,height=False)


class preference_menu_toplevel(tkinter.Toplevel):
    '''toplevel menu to adjust config file'''
    def __init__(self,application):
        tkinter.Toplevel.__init__(self)
        self.parent = application
        x = self.parent.master.winfo_x()
        y = self.parent.master.winfo_y()
        self.geometry("+%d+%d" % (x + 10, y + 20))
        self.title("preferences")

        self.textsize_var = tkinter.StringVar()
        self.textsize_var.set(str(self.parent.textsize))

        self.appearance_frame =  tkinter.LabelFrame(self, text= 'appearance')
        self.appearance_frame.grid(row=0,column= 0)

        self.button_frame = tkinter.Frame(self)
        self.button_frame.grid(row=1,column=0)

        self.vcmd = (self.appearance_frame.register(self.validate),'%d', '%i', '%P', '%s', '%S', '%v', '%V', '%W')

        tkinter.Label(self.appearance_frame,text='background color:').grid(row=0,column=0,sticky=tkinter.W)
        self.custom_color_button = tkinter.Button(self.appearance_frame,text='',bg = self.parent.custom_color ,command=lambda: self.parent.get_color(self.custom_color_button,self), width=10)
        self.custom_color_button.grid(row=0,column=1,sticky=tkinter.E)
        tkinter.Label(self.appearance_frame,text='grid color:').grid(row=1,column=0,sticky=tkinter.W)
        self.grid_color_button = tkinter.Button(self.appearance_frame,text='',bg = self.parent.gridcolor ,command=lambda: self.parent.get_color(self.grid_color_button,self), width=10)
        self.grid_color_button.grid(row=1,column=1,sticky=tkinter.E)
        tkinter.Label(self.appearance_frame,text='text color:').grid(row=2,column=0,sticky=tkinter.W)
        self.text_color_button = tkinter.Button(self.appearance_frame,text='',bg = self.parent.text_color ,command=lambda: self.parent.get_color(self.text_color_button,self), width=10)
        self.text_color_button.grid(row=2,column=1,sticky=tkinter.E)
        tkinter.Label(self.appearance_frame,text='pane color:').grid(row=3,column=0,sticky=tkinter.W)
        self.pane_color_button = tkinter.Button(self.appearance_frame,text='',bg = self.parent.pane_color ,command=lambda: self.parent.get_color(self.pane_color_button,self), width=10)
        self.pane_color_button.grid(row=3,column=1,sticky=tkinter.E)

        tkinter.Label(self.appearance_frame,text='textsize:').grid(row=4,column=0,sticky=tkinter.W)
        tkinter.Entry(self.appearance_frame, validate='key', validatecommand = self.vcmd,textvariable=self.textsize_var).grid(row=4,column=1,sticky=tkinter.E)

        self.dismiss_button = tkinter.Button(self.button_frame, text="cancel", command=self.destroy)
        self.dismiss_button.grid(row=0,column=0)
        self.accept_button = tkinter.Button(self.button_frame, text="save and apply", command = lambda: self.parent.update_config_vars(self.custom_color_button,self.grid_color_button,self.text_color_button,self.pane_color_button,self.textsize_var.get()))
        self.accept_button.grid(row=0,column=1)
        self.default_button = tkinter.Button(self.button_frame, text='default colors', command = lambda: self.parent.set_default_colors(redraw=True,buttons =[self.custom_color_button,self.grid_color_button,self.text_color_button,self.pane_color_button] ))
        self.default_button.grid(row=0,column=3)
        self.resizable(width=False,height=False)
        self.transient(self.parent.master)

    @staticmethod
    def validate(action, index, value_if_allowed,prior_value, text, validation_type, trigger_type, widget_name):
        if text in '0123456789.-+':
            try:
                float(value_if_allowed)
                return True
            except ValueError:
                return False
        else:
            return False

class about_popup_toplevel(tkinter.Toplevel):
    def __init__(self,application):
        tkinter.Toplevel.__init__(self)
        self.parent = application

        x = self.parent.master.winfo_x()
        y = self.parent.master.winfo_y()
        self.geometry("+%d+%d" % (x + 10, y + 20))
        self.title('about')

        self.tabcontrol = ttk.Notebook(self)
        self.copyright_tab = ttk.Frame(self.tabcontrol)
        self.license_tab = ttk.Frame(self.tabcontrol)
        self.tabcontrol.add(self.copyright_tab, text = 'copyright')
        self.tabcontrol.add(self.license_tab, text = 'GPL-3.0 license')
        self.tabcontrol.grid(row=0,column=0,sticky= tkinter.S+tkinter.N+tkinter.W+tkinter.E)
        self.copyright_text = tkinter.Text(self.copyright_tab)
        self.copyright_text.tag_configure("center",justify='center')
        self.copyright_text.insert(tkinter.END,'MVP-toolkit {0}\n(C) 2019 by Alexander M. Bauer under GPL-3.0 license\n\n'.format(self.parent.version))
        self.copyright_text.insert(tkinter.END,'Algorythms for lambert problem solving:\n PyKEP (c) by ESA(pykep dev-Team) under GPL-3.0\n\nplotting and graphing:\n Matplotlib, see matplotlib.org\n\ndata by NASA JPL-HORIZONS, see https://ssd.jpl.nasa.gov/horizons.cgi#top\n\n')
        self.copyright_text.tag_add('center', "1.0", "end")
        self.copyright_text.config(state=tkinter.DISABLED)
        self.copyright_text.grid(row=0,column=0)

        self.license_text = tkinter.Text(self.license_tab)
        self.license_text.insert(tkinter.END, self.parent.license_text)
        self.license_text.pack()

class porkchop_menu_toplevel(tkinter.Toplevel):
    ''' popup menu to choose parameters for porkchop plot generation'''
    def __init__(self,application):
        tkinter.Toplevel.__init__(self)
        self.parent = application

        self.choice_1_var = tkinter.StringVar()
        self.choice_2_var = tkinter.StringVar()
        self.resolution_var = tkinter.StringVar()
        self.resolution_var.set('10')
        self.iteration_var = tkinter.StringVar()
        self.iteration_var.set('50')
        self.tolerance_var = tkinter.StringVar()
        self.tolerance_var.set('0.0001')
        self.revolution_list = [ '0' , '1' , '2' , '3' , '4' , '5' ]
        self.revolution_var = tkinter.StringVar()
        self.revolution_var.set('0')
        self.interpolation_list = ['none', 'nearest', 'bilinear', 'bicubic', 'spline16', 'spline36', 'hanning', 'hamming', 'hermite', 'kaiser', 'quadric', 'catrom', 'gaussian', 'bessel', 'mitchell', 'sinc', 'lanczos']
        self.interpolation_var = tkinter.StringVar()
        self.interpolation_var.set('bilinear')
        if not self.parent.pykep_installed:
            self.pulse_direction_options = [('prograde','prograde') , ('retrograde','retrograde') , ('both', 'both')]
        else:
            self.pulse_direction_options = [('prograde','prograde') , ('retrograde','retrograde')]

        self.dV_options = [('launch','launch') , ('arrival' , 'arrival') , ('both','both')]


        self.choice_list = []
        for object in self.parent.current_objects:
            self.choice_list.append(object.displayname)
        if len(self.choice_list) < 2:
            self.parent.error_message('error','there must be atleast 2 objects to calculate a porkchop plot')
            return
        self.choice_1_var.set(self.choice_list[0])
        self.choice_2_var.set(self.choice_list[1])

        self.group(self.parent.master)
        x = self.parent.master.winfo_x()
        y = self.parent.master.winfo_y()
        self.geometry("+%d+%d" % (x + 10, y + 20))
        self.title("porkchop plot generator")
        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)
        self.dropdown_frame = tkinter.Frame(self)
        self.button_frame = tkinter.Frame(self)
        self.dropdown_frame.columnconfigure(0, weight=1)
        self.dropdown_frame.rowconfigure(0, weight=1)


        self.dropdown_frame.grid(row=0,column=0,sticky=tkinter.W+tkinter.E)
        self.object_frame = tkinter.Frame(self.dropdown_frame,borderwidth=4)
        self.object_frame.grid(row=0,column=0,sticky=tkinter.W+tkinter.E)
        self.object_frame.columnconfigure(0,weight=1)
        self.date_frame = tkinter.Frame(self.dropdown_frame,borderwidth=4)
        self.date_frame.grid(row=1,column=0,sticky=tkinter.W+tkinter.E)
        self.date_frame.columnconfigure(0,weight=1)
        self.misc_frame = tkinter.LabelFrame(self.dropdown_frame,text='advanced settings',pady=5,padx=5)
        self.misc_frame.grid(row=2,column=0,sticky=tkinter.W+tkinter.E)
        self.misc_frame.columnconfigure(0,weight=1)
        self.button_frame.grid(row=2,column=0)

        self.vcmd_int = (self.dropdown_frame.register(self.validate_int),'%d', '%i', '%P', '%s', '%S', '%v', '%V', '%W')
        self.vcmd_float = (self.dropdown_frame.register(self.validate_float), '%d', '%i', '%P', '%s', '%S', '%v', '%V', '%W')

        self.choice_1 = tkinter.OptionMenu(self.object_frame, self.choice_1_var, *self.choice_list)
        self.choice_2 = tkinter.OptionMenu(self.object_frame, self.choice_2_var, *self.choice_list)
        self.calendar_1 = DateEntry(self.date_frame,dateformat=3,width=12, background='darkblue',foreground='white', borderwidth=4,Calendar =2018,year=self.parent.dt.year, month=self.parent.dt.month, day=self.parent.dt.day)
        self.calendar_2 = DateEntry(self.date_frame,dateformat=3,width=12, background='darkblue',foreground='white', borderwidth=4,Calendar =2018,year=self.parent.dt.year+3, month=self.parent.dt.month, day=self.parent.dt.day)
        self.resolution_entry = tkinter.Entry(self.misc_frame,validate = 'key', validatecommand=self.vcmd_int,textvariable=self.resolution_var)
        self.resolution_entry.bind("<FocusIn>",self.Entry_Callback)
        self.iteration_entry = tkinter.Entry(self.misc_frame,validate = 'key', validatecommand=self.vcmd_int ,textvariable=self.iteration_var)
        self.tolerance_entry = tkinter.Entry(self.misc_frame,validate = 'key', validatecommand=self.vcmd_float ,textvariable=self.tolerance_var)
        self.interpolation_choice = tkinter.OptionMenu(self.misc_frame, self.interpolation_var, *self.interpolation_list)
        self.revolution_choice = tkinter.OptionMenu(self.misc_frame, self.revolution_var, *self.revolution_list )

        tkinter.Label(self.object_frame,text='start object:').grid(row=0,column=0,sticky=tkinter.W)
        tkinter.Label(self.object_frame,text='target object:').grid(row=1,column=0,sticky=tkinter.W)
        tkinter.Label(self.date_frame, text='from').grid(row=0,column=1)
        tkinter.Label(self.date_frame, text='to').grid(row=0,column=2)
        tkinter.Label(self.date_frame, text='date range:').grid(row=1,column=0,sticky=tkinter.W)
        tkinter.Label(self.misc_frame, text='resolution in days:').grid(row=0,column=0,sticky=tkinter.W)
        tkinter.Label(self.misc_frame, text='image interpolation:').grid(row=1,column=0,sticky=tkinter.W)
        if not self.parent.pykep_installed:
            tkinter.Label(self.misc_frame, text='number of iterations:').grid(row=2,column=0,sticky=tkinter.W)
            tkinter.Label(self.misc_frame, text='numerical tolerance:').grid(row=3,column=0,sticky=tkinter.W)
        else:
            # tkinter.Label(self.misc_frame, text='number of revolutions:').grid(row = 2,column =0, sticky= tkinter.W)
            pass

        self.choice_1.grid(row=0,column=1,columnspan=2,sticky=tkinter.E)
        self.choice_2.grid(row=1,column=1,columnspan=2,sticky=tkinter.E)
        self.calendar_1.grid(row=1,column = 1,sticky=tkinter.E+tkinter.W)
        self.calendar_2.grid(row=1,column = 2,sticky=tkinter.E+tkinter.W)
        self.resolution_entry.grid(row=0,column=2,sticky=tkinter.E)
        self.interpolation_choice.grid(row=1,column=2,sticky=tkinter.E)
        if not self.parent.pykep_installed:
            self.iteration_entry.grid(row=2,column=2, sticky = tkinter.E)
            self.tolerance_entry.grid(row=3,column=2,sticky=tkinter.E)
        else:
            # revolution_choice.grid(row=2,column=2,sticky=tkinter.E)
            pass
        #############radiobuttons###############
        self.pulse_frame = tkinter.LabelFrame(self.misc_frame, text= 'pulse direction')
        # self.pulse_frame.columnconfigure(0,weight=1)
        self.pulse_frame.grid(row = 4 ,column = 0, columnspan = 3,sticky= tkinter.W )
        count = 0
        for text,mode in self.pulse_direction_options:
            b = tkinter.Radiobutton(self.pulse_frame,text=text,variable = self.parent.pulse_direction_var , value = mode)
            b.grid(row=0 , column=count)
            self.parent.porkchop_radiobuttons.append(b)
            count = count + 1
        self.dV_frame = tkinter.LabelFrame(self.misc_frame,text = 'delta-V')
        # self.dV_frame.columnconfigure(0,weight=1)
        self.dV_frame.grid(row = 5,column = 0, columnspan = 3,sticky= tkinter.W )
        count=0
        for text,mode in self.dV_options:
            b = tkinter.Radiobutton(self.dV_frame, text=text,variable= self.parent.dV_var , value = mode)
            b.grid(row=0, column = count )
            self.parent.porkchop_radiobuttons.append(b)
            count = count + 1
        #######################################

        self.close_button = tkinter.Button(self.button_frame,text='close',command=self.destroy)
        self.calculate_button = tkinter.Button(self.button_frame,text='generate plot',command=lambda : self.parent.calc_porkchop(self.choice_1_var.get(),self.choice_2_var.get() , int(self.resolution_var.get()),self.calendar_1.get_date(),self.calendar_2.get_date() , self.interpolation_var.get(), int(self.iteration_var.get()), float(self.tolerance_var.get()) , self, rev=int(self.revolution_var.get())))
        self.close_button.grid(row=0,column=0)
        self.calculate_button.grid(row=0,column=1)
        self.resizable(width=False,height=False)
        self.transient(self.master)

    @staticmethod
    def validate_int(action, index, value_if_allowed,prior_value, text, validation_type, trigger_type, widget_name):
        '''validates an integer for tkinter entry'''
        if not value_if_allowed:
            return True
        try:
            int(value_if_allowed)
            return True
        except ValueError:
            return False

    @staticmethod
    def validate_float(action, index, value_if_allowed,prior_value, text, validation_type, trigger_type, widget_name):
        '''validates an float for tkinter entry'''
        if not value_if_allowed:
            return True
        try:
            float(value_if_allowed)
            return True
        except ValueError:
            return False

    def Entry_Callback(self,event):
        self.resolution_entry.selection_range(0, tkinter.END)
