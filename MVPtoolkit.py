print('starting ...')
import requests
import jdcal
import datetime
import numpy as np
import matplotlib.pyplot as plt
import telnetlib
import re
from pprint import pprint
from mpl_toolkits.mplot3d import Axes3D
from mpl_toolkits.mplot3d.proj3d import proj_transform
from matplotlib.text import Annotation
from matplotlib import colors
from matplotlib import pyplot as plt
import matplotlib.dates as mdates
from matplotlib.ticker import LinearLocator
from pathlib import Path
import pickle
try:
    import tkinter
    from tkinter.colorchooser import *
    from tkinter import ttk
    from tkcalendar import DateEntry,Calendar
    from tkinter import filedialog
except:
    import Tkinter
    from Tkinter.colorchooser import *
    from Tkinter import ttk
    from tkcalendar import DateEntry,Calendar
    from Tkinter import filedialog


import operator
import csv
import configparser,ast
pykep_installed = True
try:
    from pykep import lambert_problem, ic2par
    # import somethingwhichdoescertainlynotexist
except:
    pykep_installed = False

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.ticker import ScalarFormatter
# Implement the appearance Matplotlib key bindings.
from matplotlib.backend_bases import key_press_handler

#fix for freezing needs multiprocessing freeze support:
import multiprocessing

class celestial_artist:
    def __init__(self,id,orbit,pos,date,name,text,keplers):
        self.id = id
        self.orbit_artist = None
        self.position_artist = None
        self.annotation_artist = None
        self.orbit = orbit
        self.pos = pos
        self.date = date
        self.color = None
        self.name = name
        self.displayname = name
        self.info_text = text
        self.moon = False
        self.center_body = [0,0,0] #sun in this referencesystem

        self.keplers = keplers

class plot_application:
    def __init__(self, master,pykep_installed):
        self.master = master
        self.master.withdraw()
        self.pykep_installed = pykep_installed
        self.AUinKM = 149597870.691 #km/AU
        self.G = 6.673e-20 / np.power(self.AUinKM,3) #km³/kg*s²
        self.GM_sun = 1.3271244018e11 / np.power(self.AUinKM,3) #AU³ /s²
        self.M_sun = self.GM_sun / self.G
        self.GM_sun = self.GM_sun.tolist()
        self.index = 0
        self.kepler_dict = {}
        self.planet_positions = []
        self.position_coordinates = []
        self.HOST = 'horizons.jpl.nasa.gov'
        self.port = '6775'
        self.filename = 'DBNumbers'
        self.filename2 = 'smallbodies'
        self.cursor = 'tcross'
        self.turn_cursor = 'exchange'
        self.zoom_cursor = 'sizing'
        self.JPL_numbers = []
        self.orbit_colors = []
        self.equinox_artists = []
        self.list = []
        self.current_objects = []
        self.sun = celestial_artist(0,None,[0,0,0],None,'sun','sun',None)
        self.current_center_object = self.sun

        #variables for porkchop menu
        self.pulse_direction_var = tkinter.StringVar()
        self.pulse_direction_var.set('prograde')
        self.porkchop_radiobuttons = []
        self.dV_var = tkinter.StringVar()
        self.dV_var.set('launch')

        #license
        with open('LICENSE','r') as f:
            self.license_text = f.read()
        self.version = 'v0.5.2w'

        self.default_colors = ['#191919','#7f7f7f','#ffffff','#000000']
        self.resolution = 1600
        self.set_default_colors()
        self.gridlinewidth = 0.2
        self.textsize = 8
        self.markersize = 7
        self.orbit_linewidth = 1
        self.refplane_linewidth = 0.3
        self.text_xoffset = 0
        self.text_yoffset = 4
        self.destroy_was_called = False
        self.cancel_was_pushed = False
        self.check_config()

        self.valid_format_list = ['png','jpeg', 'jpg', 'svg', 'pdf', 'pgf',  'ps', 'raw', 'rgba', 'eps', 'svgz', 'tif', 'tiff']
        self.valid_formats = [('','*.'+format) for format in self.valid_format_list]
        self.view_cid = None
        self.formatter = ScalarFormatter(useMathText=True,useOffset=True)
        self.dt = datetime.datetime.now()
        self.dates = []
        self.julian_date =  "'" + str(sum(jdcal.gcal2jd(self.dt.year, self.dt.month, self.dt.day))) + "'"
        self.order_of_keplers = ['eccentricity','periapsis_distance','inclination','Omega','omega','Tp','n','mean_anomaly','true_anomaly','a','apoapsis_distance','sidereal_period']
        self.objects = ["'399'","'499'","'-143205'"] #earth,mars,Tesla roadster, ... ceres : ,"'5993'"
        self.batchfile = {"COMMAND": "'399'","CENTER": "'500@10'","MAKE_EPHEM": "'YES'","TABLE_TYPE": "'ELEMENTS'","TLIST":self.julian_date,"OUT_UNITS": "'AU-D'","REF_PLANE": "'ECLIPTIC'","REF_SYSTEM": "'J2000'","TP_TYPE": "'ABSOLUTE'","ELEM_LABELS": "'YES'","CSV_FORMAT": "'YES'","OBJ_DATA": "'YES'"}
        self.batchfile_timerange = {"COMMAND": "'399'","CENTER": "'500@10'","MAKE_EPHEM": "'YES'","TABLE_TYPE": "'VECTORS'","START_TIME": '',"STOP_TIME": '',"STEP_SIZE": '1 d',"OUT_UNITS": "'AU-D'","REF_PLANE": "'ECLIPTIC'","REF_SYSTEM": "'J2000'","VECT_CORR":"'NONE'","VEC_LABELS": "'NO'","VEC_DELTA_T": "'NO'","CSV_FORMAT": "'YES'","OBJ_DATA": "'NO'","VEC_TABLE": "'2'"}

        self.my_file = Path("./"+self.filename+'.pkl')
        self.my_file2 = Path("./"+self.filename2+'.csv')
        self.search_term = tkinter.StringVar()
        self.search_term.set('')
        self.search_term.trace("w", lambda name, index, mode: self.update_listbox())
        self.prog_var = tkinter.DoubleVar(value = 0)
        self.check_db()

        self.fig = plt.figure(facecolor = self.custom_color)
        self.fig.subplots_adjust(left=0.01, right=0.99, bottom=0.01, top=0.99)
        self.master.wm_title("MVP toolkit - Mission Visualisation and Planning")
        self.notebook_frame = ttk.Frame(self.master,borderwidth=2)
        self.notebook_frame.grid(row=0,column=0,columnspan=10,rowspan=12,sticky=tkinter.N+tkinter.W+tkinter.E+tkinter.S)
        self.notebook_frame.columnconfigure(0,weight=1)
        self.notebook_frame.rowconfigure(0,weight=1)
        self.notebook = ttk.Notebook(self.notebook_frame)
        self.canvas_frame = ttk.Frame(self.notebook)
        self.canvas_frame.grid(row=0,column=0,columnspan=10,rowspan=12,sticky=tkinter.N+tkinter.W+tkinter.E+tkinter.S)
        self.canvas_frame.rowconfigure(0, weight=1)
        self.canvas_frame.columnconfigure(0, weight=1)
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.canvas_frame) # A tk.DrawingArea.
        self.notebook.add(self.canvas_frame,text="orbits")
        self.porkchop_frames = []
        self.notebook.grid(row=0,column=0,sticky=tkinter.N+tkinter.W+tkinter.E+tkinter.S)
        self.notebook.columnconfigure(0,weight=1)
        self.notebook.rowconfigure(0,weight=1)

        self.pick_event_cid = self.fig.canvas.mpl_connect('pick_event',self.clicked_on)
        self.canvas.get_tk_widget().bind('<ButtonPress-1>',self.canvas_mouseturn,add='+')
        self.canvas.get_tk_widget().bind('<ButtonPress-3>',self.canvas_mousezoom,add='+')
        self.canvas.get_tk_widget().bind('<ButtonRelease-3>',self.canvas_mouserelease,add='+')
        self.canvas.get_tk_widget().bind('<ButtonRelease-1>',self.canvas_mouserelease,add='+')

        self.canvas.get_tk_widget().config(cursor=self.cursor)

        plt.rcParams['savefig.facecolor']= 'w'
        plt.rcParams['grid.color'] = self.gridcolor
        plt.rcParams['grid.linewidth'] = self.gridlinewidth

        self.ax = self.fig.gca(projection = '3d',facecolor =  self.custom_color,proj_type = 'ortho')

        self.canvas.get_tk_widget().grid(row=0,column=0,sticky=tkinter.N+tkinter.W+tkinter.E+tkinter.S)
        self.viewbuttons_frame = tkinter.Frame(master= self.canvas.get_tk_widget())
        self.viewbuttons_frame.place(rely=1,relx=0,anchor=tkinter.SW)

        # self.equinox_cid = self.ax.callbacks.connect('xlim_changed',self.scale_equinox)

        self.menubar = tkinter.Menu(self.master)

        self.filemenu = tkinter.Menu(self.menubar,tearoff = 0)

        self.filemenu.add_command(label="export figure as", command=self.save_file_as)
        self.filemenu.add_command(label="save plot", command=self.save_object_list)
        self.filemenu.add_command(label="load plot", command=self.load_object_list)
        self.filemenu.add_command(label="preferences", command=self.preferences_menu)
        self.filemenu.add_separator()
        self.filemenu.add_command(label="Exit", command=self.master.quit)

        self.tools_menu = tkinter.Menu(self.menubar,tearoff = 0)
        self.tools_menu.add_command(label='calculate rendezvous (lambert solver)', command=self.lambert_menu)
        self.tools_menu.add_command(label='generate porkchop-plot', command=self.porkchop_menu)
        self.tools_menu.add_command(label='add custom object', command=self.custom_object_menu)
        self.tools_menu.add_command(label='plot linear distance over time', command=self.distance_menu)

        self.about_menu = tkinter.Menu(self.menubar,tearoff = 0)
        self.about_menu.add_command(label= 'about', command = self.about_popup)


        self.menubar.add_cascade(label='file',menu=self.filemenu)
        self.menubar.add_cascade(label='tools',menu=self.tools_menu)
        self.menubar.add_cascade(label='about', menu = self.about_menu)
        self.master.config(menu=self.menubar)

        self.button1 = tkinter.Button(master=self.master, text="new Plot", command=lambda : self.refresh_plot(True))
        self.button1.grid(row=3,column=11,columnspan=2,sticky=tkinter.N+tkinter.W+tkinter.E)
        self.button2  = tkinter.Button(master=self.master, text="add to Plot", command=lambda : self.refresh_plot(False))
        self.button2.grid(row=4,column=11,columnspan=2,sticky=tkinter.N+tkinter.W+tkinter.E)
        self.topview_button = tkinter.Button(master=self.viewbuttons_frame,text='TOP',borderwidth = 3, command=lambda:self.change_view('top'))
        self.topview_button.configure(width=3,height=1)
        self.topview_button.grid(row=0,column=0)
        self.rightview_button = tkinter.Button(master=self.viewbuttons_frame,text='XZ',borderwidth = 3, command=lambda:self.change_view('XZ'))
        self.rightview_button.configure(width=3,height=1)
        self.rightview_button.grid(row=0,column=1)
        self.xyzview_button = tkinter.Button(master=self.viewbuttons_frame,text='XYZ',borderwidth = 3,command=lambda:self.change_view('XYZ'))
        self.xyzview_button.configure(width=3,height=1)
        self.xyzview_button.grid(row=0,column=3)
        self.sun_button = tkinter.Button(master=self.viewbuttons_frame,text='sun',borderwidth = 3,command=lambda:self.set_camera_center([0,0,0]))
        self.sun_button.configure(width=3,height=1)
        self.sun_button.grid(row=0,column=4)


        self.listbox = tkinter.Listbox(master=self.master,selectmode=tkinter.MULTIPLE,exportselection=False)
        self.listbox.grid(row=0,column=11,columnspan=2,sticky=tkinter.N+tkinter.W+tkinter.E+tkinter.S)
        tkinter.Label(master=self.master,text= 'type search term:').grid(row=1,column=11,sticky=tkinter.N+tkinter.W)
        self.search_box = tkinter.Entry(master=self.master, textvariable=self.search_term)
        self.search_box.grid(row=1,column=12,sticky=tkinter.N+tkinter.W)
        self.calendar_widget = Calendar(self.master,font="Arial 18", selectmode='day',cursor="hand1", year=self.dt.year, month=self.dt.month, day=self.dt.day)
        self.calendar_widget.grid(row=5,column=11,columnspan=2,sticky=tkinter.N+tkinter.W+tkinter.E+tkinter.S)
        self.refplane_var = tkinter.IntVar(value=0)
        self.annot_var = tkinter.IntVar(value=0)
        self.axis_var = tkinter.IntVar(value=1)
        self.proj_var = tkinter.IntVar(value=0)
        self.refplane_checkbutton = tkinter.Checkbutton(master=self.master,text='referenceplane lines',variable = self.refplane_var,command=self.redraw_current_objects).grid(row=6,column=11,sticky=tkinter.N+tkinter.W)
        self.annot_checkbutton = tkinter.Checkbutton(master=self.master,text='show date at objectposition',variable = self.annot_var,command=self.redraw_current_objects).grid(row=6,column=12,sticky=tkinter.N+tkinter.W)
        self.axis_checkbutton = tkinter.Checkbutton(master=self.master,text='show coordinate axis',variable = self.axis_var,command=self.toggle_axis).grid(row=7,column=11,sticky=tkinter.N+tkinter.W)
        self.proj_checkbutton = tkinter.Checkbutton(master=self.master,text='perspective projection',variable = self.proj_var,command=self.toggle_proj).grid(row=7,column=12,sticky=tkinter.N+tkinter.W)
        self.prog_bar_frame = tkinter.Frame(self.master,)
        self.prog_bar = tkinter.ttk.Progressbar(self.prog_bar_frame,orient='horizontal',length=200,mode='determinate')
        self.prog_bar.pack(side=tkinter.LEFT,expand=True,fill=tkinter.X)
        self.prog_bar_cancel_button = tkinter.Button(self.prog_bar_frame,text='cancel',command=self.cancel_current_task,state=tkinter.DISABLED)
        self.prog_bar_cancel_button.pack(side=tkinter.RIGHT,anchor = tkinter.E)
        self.prog_bar_frame.grid(row=8,column=11,columnspan=2,sticky=tkinter.S+tkinter.W+tkinter.E)

        for k,v in self.JPL_numbers.items():
            self.listbox.insert(tkinter.END,v)
        self.canvas.draw()
        self.master.deiconify()

        self.nu = np.linspace(0,2*np.pi,self.resolution)
        orbits,positions = self.request_keplers(self.objects,self.batchfile)
        if orbits == False:
            pass
        else:
            # self.current_objects = {'orbits':orbits,'positions':positions}
            self.plot_orbits(self.ax,self.current_objects,refresh_canvas=True,refplane_var=self.refplane_var.get())
            # self.current_objects['dates'] = dates
            # self.current_objects['colors'] = colors
            # self.current_objects['artists'] = artists

        self.master.protocol("WM_DELETE_WINDOW", self.on_closing)

    def cancel_current_task(self):
        self.cancel_was_pushed = True

    def about_popup(self):
        top = tkinter.Toplevel()

        x = root.winfo_x()
        y = root.winfo_y()
        top.geometry("+%d+%d" % (x + 10, y + 20))
        top.title('about')


        tabcontrol = ttk.Notebook(top)
        copyright_tab = ttk.Frame(tabcontrol)
        license_tab = ttk.Frame(tabcontrol)
        tabcontrol.add(copyright_tab, text = 'copyright')
        tabcontrol.add(license_tab, text = 'GPL-3.0 license')
        tabcontrol.grid(row=0,column=0,sticky= tkinter.S+tkinter.N+tkinter.W+tkinter.E)
        copyright_text = tkinter.Text(copyright_tab)
        copyright_text.tag_configure("center",justify='center')
        copyright_text.insert(tkinter.END,'MVP-toolkit {0}\n(C) 2019 by Alexander M. Bauer under GPL-3.0 license\n\n'.format(self.version))
        copyright_text.insert(tkinter.END,'Algorythms for lambert problem solving:\n PyKEP (c) by ESA(pykep dev-Team) under GPL-3.0\n\nplotting and graphing:\n Matplotlib, see matplotlib.org\n\ndata by NASA JPL-HORIZONS, see https://ssd.jpl.nasa.gov/horizons.cgi#top\n\n')
        copyright_text.tag_add('center', "1.0", "end")
        copyright_text.config(state=tkinter.DISABLED)
        copyright_text.grid(row=0,column=0)

        license_text = tkinter.Text(license_tab)
        license_text.insert(tkinter.END, self.license_text)
        license_text.pack()
    class Annotation3D(Annotation):
        '''Annotate the point xyz with text s'''

        def __init__(self, s, xyz, *args, **kwargs):
            Annotation.__init__(self,s, xy=(0,0), *args, **kwargs)
            self._verts3d = xyz


        def draw(self, renderer):
            xs3d, ys3d, zs3d = self._verts3d
            xs, ys, zs = proj_transform(xs3d, ys3d, zs3d, renderer.M)
            self.xy=(xs,ys)
            Annotation.draw(self, renderer)

    def set_default_colors(self,redraw=False,buttons=None):
        '''sets colors to default, if buttons handed over: colors them accordingly'''
        self.custom_color =  self.default_colors[0]
        self.gridcolor = self.default_colors[1]
        self.text_color = self.default_colors[2]
        self.pane_color = self.default_colors[3]
        if redraw:
            self.redraw_current_objects()
            counter = 0
            for b in buttons:
                b.configure(bg=self.default_colors[counter])
                counter = counter + 1

    def check_config(self):
        '''check if config exists, makes default config if not'''
        file = Path("./config.ini")
        config = configparser.ConfigParser()
        if file.is_file():
            print('config found, reading from ./config.ini')
            config.read('config.ini')
            self.custom_color = config['appearance']['custom_color']
            self.gridcolor = config['appearance']['gridcolor']
            self.text_color = config['appearance']['text_color']
            self.pane_color = config['appearance']['pane_color']
            self.gridlinewidth = float(config['appearance']['gridlinewidth'])
            self.textsize = float(config['appearance']['textsize'])
            self.markersize = float(config['appearance']['markersize'])
            self.orbit_linewidth = float(config['appearance']['orbit_linewidth'])
            self.refplane_linewidth = float(config['appearance']['refplane_linewidth'])
            self.text_xoffset = float(config['appearance']['text_xoffset'])
            self.text_yoffset = float(config['appearance']['text_yoffset'])


        else:
            print('no config found, generating new ./config.ini')
            self.update_config()

    def update_config(self):
        '''update configfile with current memory variables'''
        config = configparser.ConfigParser()
        config['appearance'] = \
        {\
        'custom_color':str(self.custom_color), 'gridcolor':str(self.gridcolor),\
        'gridlinewidth':str(self.gridlinewidth), 'textsize':str(self.textsize), 'markersize':str(self.markersize),\
        'orbit_linewidth':str(self.orbit_linewidth), 'refplane_linewidth':str(self.refplane_linewidth),\
        'text_xoffset':str(self.text_xoffset), 'text_yoffset':str(self.text_yoffset), 'text_color':str(self.text_color),\
        'pane_color':str(self.pane_color)
        }
        with open('config.ini', 'w') as configfile:
            config.write(configfile)

    def canvas_mouseturn(self,event):
        self.canvas.get_tk_widget().config(cursor=self.turn_cursor)

    def canvas_mousezoom(self,event):
        self.canvas.get_tk_widget().config(cursor=self.zoom_cursor)

    def canvas_mouserelease(self,event):
        self.canvas.get_tk_widget().config(cursor=self.cursor)

    def hex_to_rgb(self,h,alpha=1):
        '''takes hex color code and returns rgb-alpha tuple'''
        h = h.strip('#')
        h = tuple(int(h[i:i+2], 16) for i in (0, 2 ,4))
        h = (h[0]/255,h[1]/255,h[2]/255,alpha)
        return h

    def save_file_as(self):
        '''saves figure (currently redraws figure and toggles visibility of axis to true)'''
        dir = filedialog.asksaveasfilename(defaultextension=".png", filetypes = self.valid_formats)
        if dir == '' or dir == ():
            return
        self.fig.canvas.mpl_disconnect(self.view_cid)
        plt.sca(self.ax)
        try:
            plt.savefig(dir,facecolor=self.custom_color)
            print(dir)
        except ValueError:
            self.error_message('unsupported format','Supported formats are :\n {0}'.format( str(self.valid_format_list).strip('[').strip(']') ))

        # self.axis_visibility(None,'z',True)
        # self.axis_visibility(None,'y',True)

        '''does weird stuff with the image (artifacts)'''
        # ps = self.canvas.get_tk_widget().postscript(colormode='color')
        # img = Image.open(io.BytesIO(ps.encode('utf-8')))
        # img.save(dir)

    def save_object_list(self):
        dir = filedialog.asksaveasfilename(filetypes = [("pickle files","*.pckl")])
        if dir == '' or dir == ():
            return
        self.save_obj(self.current_objects,dir=dir)

    def load_object_list(self):
        dir = filedialog.askopenfilename(filetypes = [("pickle files","*.pckl")])
        if dir == '' or dir == ():
            return
        self.current_objects = self.load_obj(dir=dir)
        self.redraw_current_objects()

    def get_color(self,b,parent):
        color=askcolor(b.cget('bg'),parent=parent)
        if None in color:
            return
        b.configure(bg=color[1])

    def preferences_menu(self):
        '''toplevel menu to adjust config file'''
        def validate(action, index, value_if_allowed,prior_value, text, validation_type, trigger_type, widget_name):
            if text in '0123456789.-+':
                try:
                    float(value_if_allowed)
                    return True
                except ValueError:
                    return False
            else:
                return False

        top = tkinter.Toplevel()

        x = root.winfo_x()
        y = root.winfo_y()
        top.geometry("+%d+%d" % (x + 10, y + 20))
        top.title("preferences")

        textsize_var = tkinter.StringVar()
        textsize_var.set(str(self.textsize))

        appearance_frame =  tkinter.LabelFrame(top, text= 'appearance')
        appearance_frame.grid(row=0,column= 0)

        button_frame = tkinter.Frame(top)
        button_frame.grid(row=1,column=0)

        vcmd = (appearance_frame.register(validate),'%d', '%i', '%P', '%s', '%S', '%v', '%V', '%W')

        tkinter.Label(appearance_frame,text='background color:').grid(row=0,column=0,sticky=tkinter.W)
        custom_color_button = tkinter.Button(appearance_frame,text='',bg = self.custom_color ,command=lambda: self.get_color(custom_color_button,top), width=10)
        custom_color_button.grid(row=0,column=1,sticky=tkinter.E)
        tkinter.Label(appearance_frame,text='grid color:').grid(row=1,column=0,sticky=tkinter.W)
        grid_color_button = tkinter.Button(appearance_frame,text='',bg = self.gridcolor ,command=lambda: self.get_color(grid_color_button,top), width=10)
        grid_color_button.grid(row=1,column=1,sticky=tkinter.E)
        tkinter.Label(appearance_frame,text='text color:').grid(row=2,column=0,sticky=tkinter.W)
        text_color_button = tkinter.Button(appearance_frame,text='',bg = self.text_color ,command=lambda: self.get_color(text_color_button,top), width=10)
        text_color_button.grid(row=2,column=1,sticky=tkinter.E)
        tkinter.Label(appearance_frame,text='pane color:').grid(row=3,column=0,sticky=tkinter.W)
        pane_color_button = tkinter.Button(appearance_frame,text='',bg = self.pane_color ,command=lambda: self.get_color(pane_color_button,top), width=10)
        pane_color_button.grid(row=3,column=1,sticky=tkinter.E)

        tkinter.Label(appearance_frame,text='textsize:').grid(row=4,column=0,sticky=tkinter.W)
        tkinter.Entry(appearance_frame, validate='key', validatecommand = vcmd,textvariable=textsize_var).grid(row=4,column=1,sticky=tkinter.E)

        dismiss_button = tkinter.Button(button_frame, text="cancel", command=top.destroy)
        dismiss_button.grid(row=0,column=0)
        accept_button = tkinter.Button(button_frame, text="save and apply", command = lambda: self.update_config_vars(custom_color_button,grid_color_button,text_color_button,pane_color_button,textsize_var.get()))
        accept_button.grid(row=0,column=1)
        default_button = tkinter.Button(button_frame, text='default colors', command = lambda: self.set_default_colors(redraw=True,buttons =[custom_color_button,grid_color_button,text_color_button,pane_color_button] ))
        default_button.grid(row=0,column=3)
        top.resizable(width=False,height=False)
        top.transient(self.master)

    def update_config_vars(self,custom_color_button,grid_color_button,text_color_button,pane_color_button,textsize_var):
        '''get colors of preference buttons, update config file and redraw figure with new colors'''
        self.custom_color = custom_color_button.cget('bg')
        self.gridcolor = grid_color_button.cget('bg')
        self.text_color = text_color_button.cget('bg')
        self.pane_color = pane_color_button.cget('bg')
        self.textsize = float(textsize_var)
        self.update_config()
        self.redraw_current_objects()

    def annotate3D(self,ax, s, *args, **kwargs):
        '''add anotation text s to to Axes3d ax'''

        tag = self.Annotation3D(s, *args, **kwargs)
        ax.add_artist(tag)
        return tag

    def rot_x(self,phi):
        '''returns rotational matrix around x, phi in rad'''
        return np.array([[1,0,0],[0,np.cos(phi),-np.sin(phi)],[0,np.sin(phi),np.cos(phi)]])
    def rot_z(self,rho):
        '''returns rotational matrix around z, rho in rad'''
        return np.array([[np.cos(rho),-np.sin(rho),0],[np.sin(rho),np.cos(rho),0],[0,0,1]])

    def change_view(self,view):
        '''sets the view angles of the plot and toggles visibility of the perpendicular axis to False until plot is moved/refreshed   '''
        if view == "top":
            self.axis_visibility(event = None,axis='z',visible=False) #produces clicking on artist beeing unresponsive
            self.ax.view_init(90,-90)
            self.view_cid = self.fig.canvas.mpl_connect('draw_event',lambda event: self.axis_visibility(event,axis='z',visible=True))
        elif view == "XZ":
            self.axis_visibility(event = None,axis='y',visible=False) #produces clicking on artist beeing unresponsives
            self.ax.view_init(0,-90)
            self.view_cid = self.fig.canvas.mpl_connect('draw_event',lambda event: self.axis_visibility(event,axis='y',visible=True))
        elif view == "XYZ":
            self.ax.view_init(45,-45)
        self.canvas.draw()


    def axis_visibility(self,event,axis,visible):
        if axis == 'z':
            self.ax.set_zticklabels(self.ax.get_zticklabels(),visible=visible)
            self.ax.set_zlabel(self.ax.get_zlabel(),visible=visible)
            # if visible:
            #     self.ax.tick_params(axis='z', colors=self.text_color)
            # else:
            #     self.ax.tick_params(axis='z', colors=self.custom_color)
        elif axis == 'y':
            self.ax.set_yticklabels(self.ax.get_yticklabels(),visible=visible)
            self.ax.set_ylabel(self.ax.get_ylabel(),visible=visible)
        elif axis == 'x':
            self.ax.set_xticklabels(self.ax.get_xticklabels(),visible=visible)
            self.ax.set_xlabel(self.ax.get_xlabel(),visible=visible)
        if self.view_cid != None:
            self.fig.canvas.mpl_disconnect(self.view_cid)


    def scale_equinox(self,event):
        '''function to draw a scaling vector-arrow on the x-axis(equinox)'''
        self.fig.canvas.mpl_disconnect(self.equinox_cid)
        if len(self.equinox_artists)>0:
            for i in range(0,len(self.equinox_artists)):
                if i == 3:
                    self.equinox_artists[i].remove()
                    continue
                self.equinox_artists[i][0].remove()
        self.equinox_artists = []
        xlim = self.ax.get_xlim()
        length = 0.15 *xlim[1]
        self.equinox_artists.append(self.ax.plot([0,length] , [0,0],[0,0],color=self.text_color,linewidth=self.refplane_linewidth))
        self.equinox_artists.append(self.ax.plot([length,0.7*length],[0,0.05*length],[0,0.05*length],color=self.text_color,linewidth=self.refplane_linewidth))
        self.equinox_artists.append(self.ax.plot([length,0.7*length],[0,-0.05*length],[0,-0.05*length],color=self.text_color,linewidth=self.refplane_linewidth))
        self.equinox_artists.append(self.annotate3D(self.ax, s='vernal equinox', xyz=[length,0,0], fontsize=self.textsize, xytext=(self.text_xoffset,-self.text_yoffset),textcoords='offset points', ha='center',va='top',color = self.text_color))
        self.equinox_cid = self.ax.callbacks.connect('xlim_changed',self.scale_equinox)

    def orbit_position(self,a,e,Omega,i,omega,true_anomaly=False,comp_true_anomaly=False):
        '''calculate orbit 3x1 radius vector'''
        if not(true_anomaly==False):
            p = a * (1-(e**2))
            r = p/(1+e*np.cos(true_anomaly))
            r = np.array([np.multiply(r,np.cos(true_anomaly)) , np.multiply(r,np.sin(true_anomaly)), np.zeros(len(true_anomaly))])
            r = np.matmul(self.rot_z(omega),r)
            r = np.matmul(self.rot_x(i),r)
            r = np.matmul(self.rot_z(Omega),r)
        elif e <=1:
            # e = 1 atually wrong, here just to prevent crash, exact eccentricity of 1 should not happen
            p = a * (1-(e**2))
            r = p/(1+e*np.cos(self.nu))
            r = np.array([np.multiply(r,np.cos(self.nu)) , np.multiply(r,np.sin(self.nu)), np.zeros(len(self.nu))])
            r = np.matmul(self.rot_z(omega),r)
            r = np.matmul(self.rot_x(i),r)
            r = np.matmul(self.rot_z(Omega),r)
        elif e >1:
            # if comp_true_anomaly > 2:
            #     print('first case')
            #     plot_range = 3*np.pi/4
            #     if plot_range <= np.abs(comp_true_anomaly):
            #         plot_range = np.abs(comp_true_anomaly)
            # else:
            #     print('second case')
            #     plot_range = 3/4 * np.pi -np.pi
            #     if plot_range > np.abs(comp_true_anomaly):
            #         plot_range = np.abs(comp_true_anomaly)

            if comp_true_anomaly >= 3*np.pi/4:
                if comp_true_anomaly > np.pi:
                    plot_range = np.abs(comp_true_anomaly - 2*np.pi)
                    # plot_range = np.arccos(-1/e)
                else:
                    plot_range = comp_true_anomaly
            else:
                plot_range = 3*np.pi/4
            nu = np.linspace(-plot_range,plot_range,self.resolution)
            p = a * (1-(e**2))
            r = p/(1+e*np.cos(nu))
            r = np.array([np.multiply(r,np.cos(nu)) , np.multiply(r,np.sin(nu)), np.zeros(len(nu))])
            r = np.matmul(self.rot_z(omega),r)
            r = np.matmul(self.rot_x(i),r)
            r = np.matmul(self.rot_z(Omega),r)
        return r

    def axisEqual3D(self,ax):
        '''fix for axis equal bug in 3D (z wont equal)'''
        extents = np.array([getattr(ax, 'get_{}lim'.format(dim))() for dim in 'xyz'])
        sz = extents[:,1] - extents[:,0]
        centers = np.mean(extents, axis=1)
        maxsize = max(abs(sz))
        r = maxsize/2
        for ctr, dim in zip(centers, 'xyz'):
            getattr(ax, 'set_{}lim'.format(dim))(ctr - r, ctr + r)

    def save_obj(self,obj, name=None, dir = None ):
        if dir == None:
            with open('./' + name + '.pkl', 'wb') as f:
                pickle.dump(obj, f, pickle.HIGHEST_PROTOCOL)
        else:
            with open(dir , 'wb') as f:
                pickle.dump(obj, f, pickle.HIGHEST_PROTOCOL)

    def load_obj(self,name=None, dir = None):
        if dir == None:
            with open('./' + name + '.pkl', 'rb') as f:
                return pickle.load(f)
        else:
            with open(dir , 'rb') as f:
                return pickle.load(f)

    def _quit(self):
        self.master.destroy()     # stops mainloop
        # root.destroy()  # this is necessary on Windows to prevent
                        # Fatal Python Error: PyEval_RestoreThread: NULL tstate

    def sort_vals(self,dictionary):
        '''sort dictionary values'''
        sorted_x = sorted(dictionary.items(), key=operator.itemgetter(1))
        return dict(sorted_x)

    def get_selected(self):
        '''get selected items from listbox'''
        user_choice = []
        index_list = map(int,self.listbox.curselection())
        for i in index_list:
            user_choice.append(self.listbox.get(i))
        return user_choice

    def refresh_plot(self,clear_axis = True):
        '''new plot, dismisses existing objects if clear_axis == True'''
        print('refreshing')
        if clear_axis:
            self.current_objects = []
            self.objects = []
        objects = self.get_selected()
        objects = [self.JPL_name2num[object] for object in objects]
        self.objects.extend(objects)
        orbits,positions = self.request_keplers(objects,self.batchfile)
        self.prog_bar_cancel_button['state'] = tkinter.DISABLED
        if orbits == False:
            pass
        else:
            self.plot_orbits(self.ax,self.current_objects,refresh_canvas = True,refplane_var=self.refplane_var.get())


    def shade_hex_color(self,hexcolor,shade_value=0.4):
        ''' shade a hex color by shade_value
            (shade_value is the perecntage of the input color to shade)
        '''
        RGB = self.hex_to_rgb(hexcolor)
        R = int(RGB[0]*255 - shade_value*RGB[0]*255)
        G = int(RGB[1]*255 - shade_value*RGB[1]*255)
        B = int(RGB[2]*255 - shade_value*RGB[2]*255)
        hexR = R.to_bytes(((R.bit_length() + 7) // 8),"big").hex()
        hexG = G.to_bytes(((G.bit_length() + 7) // 8),"big").hex()
        hexB = B.to_bytes(((B.bit_length() + 7) // 8),"big").hex()
        shaded_color = '#{0}{1}{2}'.format(hexR,hexG,hexB)
        return shaded_color

    def plot_orbits(self,ax,objects,refresh_canvas=True,refplane_var = 1):
        '''plots orbits, positions and annotations'''

        self.ax.cla()

        # plt.rcParams['savefig.facecolor']= self.custom_color
        plt.rcParams['grid.color'] = self.gridcolor
        plt.rcParams['grid.linewidth'] = self.gridlinewidth
        self.fig.set(facecolor = self.custom_color)
        self.ax.set(facecolor = self.custom_color)

        ax.scatter(0,0,0,marker='o',s = 20,color='yellow')
        self.annotate3D(ax, s='sun', xyz=[0,0,0], fontsize=self.textsize, xytext=(self.text_xoffset,self.text_yoffset),textcoords='offset points', ha='center',va='bottom',color ="white")
        ax.set_xlabel('X axis in AU')
        ax.set_ylabel('Y axis in AU')
        ax.set_zlabel('Z axis in AU')
        ax.xaxis.label.set_color(self.text_color)
        ax.yaxis.label.set_color(self.text_color)
        ax.zaxis.label.set_color(self.text_color)
        ax.tick_params(axis='x', colors=self.text_color)
        ax.tick_params(axis='y', colors=self.text_color)
        ax.tick_params(axis='z', colors=self.text_color)
        ax.w_xaxis.set_pane_color(self.hex_to_rgb(self.pane_color))
        ax.w_yaxis.set_pane_color(self.hex_to_rgb(self.pane_color))
        ax.w_zaxis.set_pane_color(self.hex_to_rgb(self.pane_color))
        for object in objects:
            if None in object.orbit:
                continue
            orbit = object.orbit
            pos = object.pos
            object.orbit_artist= []
            if object.moon:
                threshold = object.center_body[2]
            else:
                threshold = 0
            orbit_pos = np.array(orbit)
            orbit_neg = np.array(orbit)
            positive = orbit_pos[2] > threshold
            negative = orbit_pos[2] <= threshold
            orbit_neg[0][negative] = np.nan
            orbit_neg[1][negative] = np.nan
            orbit_neg[2][negative] = np.nan

            orbit_pos[0][positive] = np.nan
            orbit_pos[1][positive] = np.nan
            orbit_pos[2][positive] = np.nan

            if object.color == None:
                color = next(self.ax._get_lines.prop_cycler)['color']
                object.color = color
                object.orbit_artist.append(ax.plot(orbit_neg[0],orbit_neg[1],orbit_neg[2],linewidth=self.orbit_linewidth,clip_on=False,color=object.color))
                object.orbit_artist.append(ax.plot(orbit_pos[0],orbit_pos[1],orbit_pos[2],linewidth=self.orbit_linewidth,clip_on=False,color=self.shade_hex_color(object.color)))

            else:
                object.orbit_artist.append(ax.plot(orbit_neg[0],orbit_neg[1],orbit_neg[2],linewidth=self.orbit_linewidth,clip_on=False,color=object.color))
                object.orbit_artist.append(ax.plot(orbit_pos[0],orbit_pos[1],orbit_pos[2],linewidth=self.orbit_linewidth,clip_on=False,color=self.shade_hex_color(object.color)))

            if refplane_var == 1:
                counter = 0
                for x,y,z in zip(*object.orbit.tolist()):
                    if (counter%20 == 0):
                        ax.plot([x,x],[y,y],[z,threshold],'white',linewidth=self.refplane_linewidth,clip_on=False)
                    counter = counter + 1

            if object.id == None:
                object.position_artist = self.ax.plot(pos[0],pos[1],pos[2], marker='*', MarkerSize=self.markersize,MarkerFaceColor=object.color ,markeredgecolor = object.color ,clip_on=False,picker=5)
            else:
                object.position_artist = self.ax.plot(pos[0],pos[1],pos[2], marker='o', MarkerSize=self.markersize,MarkerFaceColor=object.color ,markeredgecolor = object.color ,clip_on=False,picker=5)
            object.annotation_artist = self.annotate3D(ax, s=object.displayname, xyz=[pos[0],pos[1],pos[2]], fontsize=self.textsize, xytext=(self.text_xoffset,self.text_yoffset),textcoords='offset points', ha='center',va='bottom',color = self.text_color,clip_on=False)
            if self.annot_var.get() == 1:
                self.annotate3D(ax, s=str(object.date), xyz=[pos[0],pos[1],pos[2]], fontsize=self.textsize, xytext=(self.text_xoffset,-self.text_yoffset),textcoords='offset points', ha='center',va='top',color = self.text_color,clip_on=False)

        # # # recompute the ax.dataLim
        # # ax.relim()
        # # # update ax.viewLim using the new dataLim
        # # ax.autoscale(True)
        #
        self.axisEqual3D(ax)
        self.set_camera_center(self.current_center_object.pos)

        # self.formatter.set_scientific(True)
        # self.ax.xaxis.set_major_formatter(self.formatter)
        # self.ax.yaxis.set_major_formatter(self.formatter)

        # self.scale_equinox(None)
        # ylim = self.ax.get_ylim()
        # xlim = self.ax.get_xlim()
        # self.ax.plot([20*xlim[0],20*xlim[1]],[0,0],[0,0],linewidth=0.3,clip_on=False,color='white')
        # self.ax.plot([0,0],[20*ylim[0],20*ylim[1]],[0,0],linewidth=0.3,clip_on=False,color='white')

        if self.axis_var.get() == 1:
            self.ax.set_axis_on()
        else:
            self.ax.set_axis_off()

        if refresh_canvas:
            self.canvas.draw()
        return # marker_artists,orbit_colors,dates

    def ask_ok_popup(self, title, question):
        return tkinter.messagebox.askokcancel(title, question)

    def on_closing(self):
        if self.ask_ok_popup("Quit", "Do you want to quit?"):
            self.destroy_was_called = True
            self.master.quit()
            self.master.destroy()

    def error_message(self,title,message):
        '''generates an error message-popup with generic title and message'''
        tkinter.messagebox.showerror(title,message)

    def request_keplers(self,objects,batchfile,errors=0):
        '''requests kepler elements from HORIZONS-batch-interface for objects'''
        self.prog_bar_cancel_button['state'] = tkinter.NORMAL
        print('requesting keplers for selected items')
        orbits = []
        positions = []
        kepler_dict = {}
        self.prog_bar["maximum"] = len(objects)
        moon = False
        count = 0
        objects = sorted(objects,reverse=True)
        for object in objects:
            batchfile['COMMAND'] = object
            object_stripped = object.strip("'")
            parent_position = [0,0,0]
            if len(object_stripped) == 3:
                if int(object_stripped[1:3]) != 99:
                    #its a moon, query with centerbody instead of sun
                    # x99 is majorbody with x 1 to 9 representing mercury, venus, earth, mars .... , x01 is first moon of x, x02 second,...
                    center_body =  "'" + object_stripped[0] + "99'"
                    batchfile['CENTER'] = "'500@" + center_body[1:5]
                    moon = True

                else:
                    #no moon! reset to sun as center
                    batchfile['CENTER'] = "'500@10'"
                    moon = False

            self.dt = self.calendar_widget.selection_get()
            batchfile['TLIST'] = "'" + str(sum(jdcal.gcal2jd(self.dt.year, self.dt.month, self.dt.day))) + "'"
            try:
                r = requests.get("https://ssd.jpl.nasa.gov/horizons_batch.cgi?batch=1", params = batchfile,timeout=2.0)
            except (requests.exceptions.ConnectionError,requests.exceptions.Timeout):
                print('connection failed, retrying...')
                if errors<=2:
                    return self.request_keplers(objects,batchfile,errors = errors+1)
                self.error_message('Connection Error','Could not reach the Server, please check your internet connection.')
                return False,False

            # print(r.text)
            count = count + 1
            if self.destroy_was_called:
                return
            if self.cancel_was_pushed:
                self.cancel_was_pushed = False
                self.prog_bar["value"] = 0
                self.prog_bar_cancel_button['state'] = tkinter.DISABLED
                self.redraw_current_objects()
                return False,False
            self.prog_bar["value"] = count
            self.prog_bar.update()
            if 'No ephemeris for target' in r.text:
                print('No ephemeris for target{0} at date {1}'.format(self.JPL_numbers[object],self.dt))
                self.error_message('DB Error','No ephemeris for target {0} at date {1}'.format(self.JPL_numbers[object],self.dt))
                orbit = [None,None]
                position = [None,None]
                orbits.append([None,None])
                positions.append([None,None])
            elif 'is out of bounds, no action taken' in r.text:
                print('{0} is out of bounds, no action taken (couldnt find {1} in batch interface of JPL horizonss)'.format(self.JPL_numbers[object],object))
                self.error_message('DB Error','{0} is out of bounds, no action taken (couldnt find {1} in batch interface of JPL horizonss)'.format(self.JPL_numbers[object],object))
                orbit = [None,None]
                position = [None,None]
                orbits.append([None,None])
                positions.append([None,None])
            elif 'No such record, positive values only' in r.text:
                print('No record for {0}({1}), positive values only'.format(object,self.JPL_numbers[object]))
                self.error_message('DB Error','No record for {0}({1}), positive values only'.format(object,self.JPL_numbers[object]))
                orbit = [None,None]
                position = [None,None]
                orbits.append([None,None])
                positions.append([None,None])
            else:
                keplers = r.text.split('$$SOE')[1].split('$$EOE')[0].replace(' ','').split(',')
                del keplers[0:2]
                del keplers[-1]
                keplers = [float(element) for element in keplers]
                for i in range(len(keplers)):
                    kepler_dict[self.order_of_keplers[i]] = keplers[i]
                kepler_dict['Omega'] = np.deg2rad(kepler_dict['Omega'])
                kepler_dict['inclination'] = np.deg2rad(kepler_dict['inclination'])
                kepler_dict['omega'] = np.deg2rad(kepler_dict['omega'])
                kepler_dict['true_anomaly'] = np.deg2rad(kepler_dict['true_anomaly'])
                # print('\n\n{0}:\n'.format(self.JPL_numbers[object]))
                # pprint(kepler_dict)
                orbit = self.orbit_position(kepler_dict['a'],kepler_dict['eccentricity'],kepler_dict['Omega'],kepler_dict['inclination'],kepler_dict['omega'] , comp_true_anomaly=kepler_dict['true_anomaly'] )
                position = self.orbit_position(kepler_dict['a'],kepler_dict['eccentricity'],kepler_dict['Omega'],kepler_dict['inclination'],kepler_dict['omega'],[kepler_dict['true_anomaly']])
                orbits.append(orbit)
                positions.append(position)
            added = False
            found = False
            if moon:
                for obj in self.current_objects:
                    if obj.id == center_body:
                        orbit = orbit + obj.pos
                        parent_position = obj.pos
                        position = position + parent_position
                        found = True
                        break
                if not found:
                    if self.ask_ok_popup("Centerbody Missing", "The centerbody of the queried moon is not currently on the plot, add it to the query list?"):
                        objects.append("'" + object_stripped[0] + "99'")
                        return self.request_keplers(objects,self.batchfile)
                    else:
                        continue
            self.current_objects.append(celestial_artist(object,orbit,position,self.dt,self.JPL_numbers[object],r.text,kepler_dict))
            self.current_objects[-1].moon = moon
            self.current_objects[-1].center_body = parent_position
        return orbits,positions

    def update_listbox(self):
        '''update listbox according to search term'''
        search_term = self.search_term.get()
        selected_items = self.get_selected()
        self.listbox.delete(0,tkinter.END)
        for k,v in self.JPL_numbers.items():
            if search_term.lower() in v.lower() and not (search_term.lower() in selected_items):
                self.listbox.insert(tkinter.END,v)
        for item in selected_items:
            self.listbox.insert(0,item)
            self.listbox.selection_set(0)
        return True

    def toggle_axis(self):
        ''' function to toggle coordinate axes'''
        if self.axis_var.get() == 1:
            self.ax.set_axis_on()
            self.canvas.draw()
        else:
            self.ax.set_axis_off()
            self.canvas.draw()

    def redraw_current_objects(self):
        '''just redrawing the plot to accept user changes to appearance'''
        self.plot_orbits(self.ax,self.current_objects,refplane_var=self.refplane_var.get())

    def toggle_proj(self):
        if self.proj_var.get() == 1:
            self.ax.set_proj_type('persp')
        else:
            self.ax.set_proj_type('ortho')
        self.canvas.draw()

    def clicked_on(self,event):
        '''takes pick event of object'''
         # artist_dir = dir(event.artist)
         # pprint(arist_dir)
        for object in self.current_objects:
            if object.position_artist[0].get_label() == event.artist.get_label():
                name= object.name
                selected_object = object
        print('clicked {0}'.format(name))
        # for object in self.current_objects:
        #     object.position_artist[0].set_markeredgecolor(object.position_artist[0].get_markerfacecolor())
        # selected_object.position_artist[0].set_markeredgecolor('white')
        if event.mouseevent.button == 1:
            self.current_center_object = selected_object
            self.set_camera_center(selected_object.pos)
        elif event.mouseevent.button == 3:
            self.artist_menu(selected_object)

    def set_camera_center(self,pos):
        '''centers camera around pos = [x,y,z]'''
        if np.array_equal(pos,[0,0,0]):
            self.current_center_object = self.sun
        ylim = self.ax.get_ylim()
        xlim = self.ax.get_xlim()
        zlim = self.ax.get_zlim()
        xlim = xlim[1]-xlim[0]
        ylim = ylim[1]-ylim[0]
        zlim = zlim[1]-zlim[0]
        max = np.amax([ylim,xlim,zlim])/2
        self.ax.set_xlim([-max+pos[0], max+pos[0]])
        self.ax.set_ylim([-max+pos[1], max+pos[1]])
        self.ax.set_zlim([-max+pos[2], max+pos[2]])
        self.canvas.draw()

    def artist_menu(self,object):
        ''' popup menu to alter artist color and name or remove artist'''
        top = tkinter.Toplevel()

        x = root.winfo_x()
        y = root.winfo_y()
        top.geometry("+%d+%d" % (x + 10, y + 20))
        top.title("{0}".format(object.displayname))


        tabcontrol = ttk.Notebook(top)
        parameters_tab = ttk.Frame(tabcontrol)
        info_text_tab = ttk.Frame(tabcontrol)
        tabcontrol.add(parameters_tab, text = 'object parameters')
        tabcontrol.add(info_text_tab, text = 'DB information')
        tabcontrol.grid(row=0,column=0,sticky= tkinter.S+tkinter.N+tkinter.W+tkinter.E)

        button_frame = ttk.Frame(top)
        button_frame.grid(row=1,column=0)
        displayname_var = tkinter.StringVar()
        displayname_var.set(str(object.displayname))


        info_text_widget = tkinter.Text(info_text_tab)
        info_text_widget.insert(tkinter.END,object.info_text)
        info_text_widget.config(state=tkinter.DISABLED)
        info_text_widget.grid(row=0,column=0)
        settings_frame =  tkinter.LabelFrame(parameters_tab, text= 'parameters')
        settings_frame.grid(row=0,column= 0,sticky= tkinter.S+tkinter.N+tkinter.W+tkinter.E)

        tkinter.Label(settings_frame,text='object color:').grid(row=0,column=0,sticky= tkinter.S+tkinter.N+tkinter.W+tkinter.E)
        artist_color_button = tkinter.Button(settings_frame,text='',bg = object.color ,command=lambda: self.get_color(artist_color_button,top), width=10)
        artist_color_button.grid(row=0,column=1,sticky= tkinter.S+tkinter.N+tkinter.W+tkinter.E)

        tkinter.Label(settings_frame,text='displayname:').grid(row=2,column=0,sticky= tkinter.S+tkinter.N+tkinter.W+tkinter.E)
        tkinter.Entry(settings_frame,textvariable=displayname_var).grid(row=2,column=1,sticky= tkinter.S+tkinter.N+tkinter.W+tkinter.E)

        dismiss_button = tkinter.Button(button_frame, text="cancel", command=lambda: self.destroy_toplevel(top))
        dismiss_button.grid(row=0,column=0)
        accept_button = tkinter.Button(button_frame, text="apply changes", command = lambda: self.update_artist(object,artist_color_button,displayname_var.get(),top))
        accept_button.grid(row=0,column=1)
        remove_button = tkinter.Button(button_frame, text="remove this from plot", command = lambda: self.remove_artist(object,top))
        remove_button.grid(row=0,column=2)
        top.resizable(width=False,height=False)
        top.transient(self.master)
        root.tk.call('wm','iconphoto',top._w,icon_img)

    def remove_artist(self,object,top):
        try:
            object.position_artist[0].remove()
        except ValueError:
            top.destroy()
            self.error_message('Artist error','Object is already removed!')
            return
        stripped_id = object.id.strip("'")

        #check if object has moons on plot and remove them first
        if (len(stripped_id) == 3) and (stripped_id[1:3] == '99'):
            for obj in self.current_objects:
                if (stripped_id[0] == obj.id.strip("'")[0]) and (not(obj.id.strip("'")[1:3] == '99')):
                    print('found moon {0}, removing it together with {1}'.format(obj.displayname,object.displayname))
                    obj.position_artist[0].remove()
                    for art in obj.orbit_artist:
                        art[0].remove()
                    obj.annotation_artist.remove()
                    index = 0
                    for o in self.current_objects:
                        if o.position_artist[0].get_label() == obj.position_artist[0].get_label():
                            self.current_objects.pop(index)
                            break
                        index = index + 1

        #remove artist
        for artist in object.orbit_artist:
            artist[0].remove()
        object.annotation_artist.remove()
        index = 0
        for obj in self.current_objects:
            if obj.position_artist[0].get_label() == object.position_artist[0].get_label():
                self.current_objects.pop(index)
                break
            index = index + 1
        self.redraw_current_objects()
        top.destroy()

    def destroy_toplevel(self,top):
        self.master.deiconify()
        top.destroy()

    def update_artist(self,object,artist_color_button,displayname,top):
        object.color = artist_color_button.cget('bg')
        object.displayname = displayname
        self.redraw_current_objects()
        self.master.deiconify()
        top.destroy()

    def check_db(self):
        '''checks if DB file exists, if not, queries HORIZONS socket service to extract major bodies'''
        if not self.my_file.is_file():
            #telnet session to extract Major Bodies dict

            tn = telnetlib.Telnet(self.HOST,self.port)
            print('waiting for Horizons socket service')
            tn.read_until("Horizons>".encode('UTF-8'))
            print('Querying Major Bodies')
            tn.write('MB\n'.encode('UTF-8'))
            list = str(tn.read_until('0'.encode('UTF-8')))
            list = list[-2] + str(tn.read_until('Number'.encode('UTF-8')))[1:]
            tn.close()
            list = str(list)
            JPL_numbers = list.split()
            list = []
            ID = True
            safe_str = ''
            for s in JPL_numbers:
                if ID == True:
                    list.append(s)
                    ID = False
                elif not(s == '\\r\\n'):
                    safe_str = safe_str + ' ' + s
                else:
                    list.append(safe_str)
                    safe_str = ''
                    ID = True
            JPL_numbers = list
            del JPL_numbers[-1]
            JPL_numbers = dict(zip(JPL_numbers[::2],JPL_numbers[1::2]))
            self.JPL_numbers = dict(("'"+k.strip()+"'",v.strip()) for k,v in JPL_numbers.items())
            self.save_obj(self.JPL_numbers,self.filename)
        else:
            print('found .pckl file with DB IDs')
            self.JPL_numbers = self.load_obj(self.filename)
        if self.my_file2.is_file():
            print('{0} found! adding small bodies to list'.format(self.my_file2))
            with open('{0}'.format(self.my_file2),mode='r') as csvfile:
                small_bodies = csv.reader(csvfile)
                small_bodies = {"'"+row[0].strip()+";'":row [1].strip() for row in small_bodies}
        else:
            print('{0}'.format(self.my_file2))
            small_bodies = {}
        self.JPL_numbers.update(small_bodies)
        self.JPL_numbers = dict((k,v) for k,v in self.JPL_numbers.items() if not (v==''))
        #when all objects should be loaded and named after their numbering (laggy!!!)

        self.JPL_numbers = dict ( (k,v) if not (v=='') else (k,k) for k,v in self.JPL_numbers.items())
        self.JPL_numbers = self.sort_vals(self.JPL_numbers)
        self.JPL_name2num = dict((v,k) for k,v in self.JPL_numbers.items())

    def solve_lambert(self,r1,r2,delta_t,object1,object2,numiters=50,tolerance=1e-6,popup = True):
        ''' solve lambert problem for a single resolution and return v1,v2 and keplers of orbit
            self.GM_sun is G times mass of centerbody

        '''
        r1 = [float(entry) for entry in r1]
        r2 = [float(entry) for entry in r2]
        r1 = np.array(r1)
        r2 = np.array(r2)
        c = np.linalg.norm(r1-r2)
        s = 0.5*(c +np.linalg.norm(r1) + np.linalg.norm(r2))

        def lambert_rhs(a):
            X = np.sqrt(a**3 / self.GM_sun) * ( 2*np.arcsin(np.sqrt(s/(2*a))) - 2*np.arcsin(np.sqrt((s-c)/(2*a))) - np.sin(2*np.arcsin(np.sqrt(s/(2*a)))) + np.sin(2*np.arcsin(np.sqrt((s-c)/(2*a)))) )
            return X

        a_min = s/2
        a_max = s*2
        a = 0.5*(a_min+a_max)

        # print('a:{0}\nc:{1}\ns:{2}\nsun_GM:{3}\nsqrt(s/2*a):{4}\nnp.sqrt((s-c)/2*a):{5}\n'.format(a,c,s,self.GM_sun,np.sqrt(s/(2*a)),np.sqrt((s-c)/2*a)))

        min_tof = (np.sqrt(2)/3)  * np.sqrt((s**3)/self.GM_sun) * ( 1 - (((s-c)/s)**(3/2)) )
        max_tof = lambert_rhs(a_min)
        if delta_t < min_tof:
            # print('time is to short')
            if popup:
                self.error_message('error','time period is to short to make a elliptical transfer')
            return False,False,False,False,False
        if delta_t > max_tof:
            # print('time is to long')
            if popup:
                self.error_message('error','time period is to long to make a elliptical transfer')
            return False,False,False,False,False

        iter = 0

        while 1 :
            tof = lambert_rhs(a)
            if  tof < delta_t:
                a_max = a
            else:
                a_min = a
            a = 0.5*(a_min+a_max)

            #did converge
            if np.abs((tof-delta_t)) <= tolerance:
                break
            iter = iter + 1

            #did not converge
            if iter == numiters or tof == 'nan':
                # print('did not converge')
                if popup:
                    self.error_message('error','lambert solver did not converge in {0} itterations'.format(numiters))
                return False,False,False,False,False

        coeff = 0.5*np.sqrt(self.GM_sun/a)
        A = coeff * (1/np.tan(np.arcsin(np.sqrt(s/(2*a)))))
        B = coeff * (1/np.tan(np.arcsin(np.sqrt((s-c)/(2*a)))))
        u_1 = r1/np.linalg.norm(r1)
        u_2 = r2/np.linalg.norm(r2)
        u_c = (r2-r1)/c
        v_1 = (B+A)*u_c + (B-A)*u_1
        v_2 = (B+A)*u_c - (B-A)*u_2
        # if popup:
        #     # v_1 = [val for sublist in v_1 for val in sublist]
        #     # v_2 = [val for sublist in v_2 for val in sublist]
        #     r1 = [val for sublist in r1 for val in sublist]
        #     r2 = [val for sublist in r2 for val in sublist]
        if popup:
            v_p1 = self.kep2velocity(object1)
            v_p2 = self.kep2velocity(object2)
        else:
            v_p1 = [float(entry) for entry in object1]
            v_p2 = [float(entry) for entry in object2]
            v_p1 = np.array(v_p1) / (24*60*60)
            v_p2 = np.array(v_p2) / (24*60*60)
        # print('v_p1 : {0}\nv_p2 : {1}\n'.format(v_p1*self.AUinKM,v_p2*self.AUinKM))
        delta_v1 = np.linalg.norm(v_1 - v_p1)
        delta_v2 = np.linalg.norm(v_2 - v_p2)
        ecc, inclination, Omega, omega, true_anomaly = self.kart2kep(r2,v_2)
        if not popup:
            if self.pulse_direction_var.get() == 'prograde':
                if inclination > np.pi/2:
                    return False,False,False,False,False
            elif self.pulse_direction_var.get() == 'retrograde':
                if inclination <= np.pi/2:
                    return False,False,False,False,False
        keplers = {'eccentricity':ecc,'inclination':inclination,'Omega':Omega,'omega':omega,'true_anomaly':true_anomaly,'a':a}
        return v_1, v_2, keplers, delta_v1, delta_v2

    def calc_rendezvous(self,selection1,selection2):
        ''' function to calculate a rendeszvous orbit'''
        for object in self.current_objects:
            if object.displayname == selection1:
                object1 = object
            if object.displayname == selection2:
                object2 = object

        dt = object2.date -object1.date
        if float(dt.total_seconds()) <=0:
            self.error_message('error','you can only plan a rendezvous forward in time!')
            return
        dt = dt.total_seconds()
        pos1 = object1.pos #* self.AUinKM
        pos2 = object2.pos #* self.AUinKM

        v1,v2,keplers, delta_v1, delta_v2 = self.solve_lambert(pos1,pos2,dt,object1,object2)

        if type(v1) ==type(False):
            return
        # print('v1: {0}\nv2:{1}\nkeplers:{2}\n'.format(v1,v2,keplers))
        #def orbit_position(self,a,e,Omega,i,omega,true_anomaly=False):
        orbit = self.orbit_position(keplers['a'],keplers['eccentricity'],keplers['Omega'],keplers['inclination'],keplers['omega'],comp_true_anomaly=kepler_dict['true_anomaly'])
        pos = self.orbit_position(keplers['a'],keplers['eccentricity'],keplers['Omega'],keplers['inclination'],keplers['omega'],[keplers['true_anomaly'] + np.pi/2])


        #class celestial_artist:
            # def __init__(self,id,orbit,pos,date,name,text,keplers):
        lambert_object = celestial_artist(None,orbit,pos,str(object1.date) + ' to ' + str(object2.date),'Lambert solution',
        '*********\nthis is the 0 rev. solution to the Lambertproblem of the transfer from:\n{0} -> {1}\n\n*********\n'
        'Delta V for Transferorbit as single pulse:\t{2:.4} km/s \nDelta V for Injection into target orbit:\t{3:.4} km/s\nOverall Delta V:\t{4:.4} km/s'.format(object1.displayname,object2.displayname,delta_v1*self.AUinKM,delta_v2*self.AUinKM,np.abs(delta_v1+delta_v2)*self.AUinKM) , keplers)

        self.current_objects.append(lambert_object)
        self.redraw_current_objects()

        return

    def calc_rendezvous_pykep(self,selection1,selection2):
        ''' function to calculate a rendeszvous orbit via PyKEP'''
        for object in self.current_objects:
            if object.displayname == selection1:
                object1 = object
            if object.displayname == selection2:
                object2 = object
        dt = object2.date -object1.date
        if float(dt.total_seconds()) <=0:
            self.error_message('error','you can only plan a rendezvous forward in time!')
            return
        dt = dt.total_seconds()
        pos1 = object1.pos
        pos2 = object2.pos
        v_p1 = self.kep2velocity(object1)
        v_p2 = self.kep2velocity(object2)

        delta_v1,delta_v2, l = self.solve_lambert_pykep(pos1,pos2,dt,v_p1,v_p2)

        v1 = l.get_v1()[0]
        print(pos1,v1)

        ecc, inclination, Omega, omega, true_anomaly, a = self.kart2kep(pos1.flatten(),v1,a=True)
        #,a,e,Omega,i,omega,true_anomaly=False,comp_true_anomaly=False)
        orbit = self.orbit_position(a,ecc,Omega,inclination,omega, comp_true_anomaly = true_anomaly)
        pos =  self.orbit_position(a,ecc,Omega,inclination,omega , true_anomaly = [true_anomaly + np.pi/2])
        lambert_object = celestial_artist(None,orbit,pos,str(object1.date) + ' to ' + str(object2.date),'Lambert solution',
        '*********\nthis is the 0 rev. solution to the Lambertproblem of the transfer from:\n{0} -> {1}\n\n*********\n'
        'Delta V for Transferorbit as single pulse:\t{2:.4f} km/s \nDelta V for Injection into target orbit:\t{3:.4f} km/s\nOverall Delta V:\t{4:.4f} km/s'.format(object1.displayname,object2.displayname,delta_v1*self.AUinKM,delta_v2*self.AUinKM,np.abs(delta_v1+delta_v2)*self.AUinKM) , None)
        self.current_objects.append(lambert_object)
        self.redraw_current_objects()

        return

    def kart2kep(self,r,v, a=False):
        ''' function to transform cartesian statevectors to kepler elements'''
        h = np.cross(r,v)
        h_norm = h / np.linalg.norm(h)
        ecc_vector = (np.cross(v,h)/self.GM_sun) - (r/np.linalg.norm(r))
        ecc = np.linalg.norm(ecc_vector)
        n = np.array([ -h[1] , h[0] , 0 ])
        if np.dot(r,v) >= 0:
            true_anomaly = np.arccos(np.dot(ecc_vector,r)/(np.linalg.norm(ecc_vector)*np.linalg.norm(r)))
        else:
            true_anomaly = 2*np.pi - np.arccos(np.dot(ecc_vector,r)/(np.linalg.norm(ecc_vector)*np.linalg.norm(r)))
        inclination = np.arccos(h[2]/np.linalg.norm(h))
        # inclination = np.arctan2(np.sqrt(h_norm[0]**2 + h_norm[1]**2) , h_norm[2])
        if n[1] >=0:
            Omega = np.arccos(n[0]/np.linalg.norm(n))
        else:
            Omega = 2*np.pi - np.arccos(n[0]/np.linalg.norm(n))
        if ecc_vector[2] >= 0:
            omega = np.arccos(np.dot(n,ecc_vector)/(np.linalg.norm(n)*np.linalg.norm(ecc_vector)))
        else:
            omega = 2*np.pi - np.arccos(np.dot(n,ecc_vector)/(np.linalg.norm(n)*np.linalg.norm(ecc_vector)))

        if a:
            a = 1 / ( (2/np.linalg.norm(r)) - (np.power(np.linalg.norm(v), 2) / self.GM_sun) )
            return ecc, inclination, Omega, omega, true_anomaly, a
        else:
            return ecc, inclination, Omega, omega, true_anomaly

    def lambert_menu(self):
        ''' menu to choose parameters for the lambert solver to plot a rendeszvous orbit'''
        choice_1_var = tkinter.StringVar()
        choice_2_var = tkinter.StringVar()

        choice_list = []
        for object in self.current_objects:
            choice_list.append(object.displayname)
        if len(choice_list) < 2:
            self.error_message('error','there must be atleast 2 objects to plan a rendezvous')
            return
        choice_1_var.set(choice_list[0])
        choice_2_var.set(choice_list[1])

        top = tkinter.Toplevel(self.master)
        x = root.winfo_x()
        y = root.winfo_y()
        top.geometry("+%d+%d" % (x + 10, y + 20))
        top.title("rendezvous tool")
        top.rowconfigure(0, weight=1)
        top.columnconfigure(0, weight=1)
        dropdown_frame = tkinter.Frame(top)
        info_frame = tkinter.Frame(top)
        button_frame = tkinter.Frame(top)
        dropdown_frame.columnconfigure(0, weight=1)
        info_frame.columnconfigure(0, weight=1)
        dropdown_frame.rowconfigure(0, weight=1)
        info_frame.rowconfigure(0, weight=1)

        dropdown_frame.grid(row=0,column=0,sticky=tkinter.W+tkinter.E)
        info_frame.grid(row=1,column=0,sticky=tkinter.W+tkinter.E)
        button_frame.grid(row=2,column=0)
        choice_1 = tkinter.OptionMenu(dropdown_frame, choice_1_var, *choice_list)
        choice_2 = tkinter.OptionMenu(dropdown_frame, choice_2_var, *choice_list)
        tkinter.Label(dropdown_frame,text='start object:').grid(row=0,column=0,sticky=tkinter.W)
        tkinter.Label(dropdown_frame,text='target object:').grid(row=1,column=0,sticky=tkinter.W)
        choice_1.grid(row=0,column=1,sticky=tkinter.E)
        choice_2.grid(row=1,column=1,sticky=tkinter.E)

        info_text_widget = tkinter.Label(info_frame,text = 'Attention: Always check for plausibility of the solution!\n This tool can calculate a rendezvous between two\n points in space with an elliptical transfer. \nYou have to plot the two desired objects on their\n corresponding dates first to plan a rendezvous between them.\n It is advised to make a porkchop-plot first!')
        info_text_widget.grid(row=0,column=0)

        close_button = tkinter.Button(button_frame,text='close',command=top.destroy)
        calculate_button = tkinter.Button(button_frame,text='calculate!',command=lambda : self.calc_rendezvous_pykep(choice_1_var.get(),choice_2_var.get()))
        close_button.grid(row=0,column=0)
        calculate_button.grid(row=0,column=1)
        top.transient(self.master)
        top.resizable(width=False,height=False)
        return

    def calc_approx__timefree_dv(self,object1,object2, dt):
        self.error_message('coming soon','function isnt implemented yet')
        return

    def approx_timefree_dv(self,r1,r2,dt,starting_object):
        ''' function to calculate an approximate dV of the lambert problem
            MULTIPLE REVOLUTION LAMBERT´S TARGETING PROBLEM: AN ANALYTICAL
            APPROXIMATION
            by Claudio Bombardelli, Juan Luis Gonzalo, and Javier Roa
            ****WIP****
        '''
        r1_norm = np.linalg.norm(r1)
        r2_norm = np.linalg.norm(r2)
        c = np.linalg.norm(r1-r2)

        v0 = self.kep2velocity(starting_object)
        u_r1 = r1/r1_norm
        u_c = (r2-r1)/c
        n = np.cross(u_r1,u_c)/np.linalg.norm(np.cross(u_r1,u_c))
        d_Theta = np.arccos( np.dot(r1,r2) / (r1_norm * r2_norm) )

        v0_pi = v0 - ( (np.dot(v0,n) / np.linalg.norm(n)**2 ) * n )
        P = np.sqrt( (2*r1_norm*r2_norm) / (self.GM_sun*c) ) * np.cos(d_Theta/2) * np.dot(v0_pi , u_r1)
        Q = np.sqrt( (2*r1_norm*r2_norm) / (self.GM_sun*c) ) * np.cos(d_Theta/2) * np.dot(v0_pi , u_c)
        roots = np.roots([1, P, 0, Q, 1])
        print(roots)
        return

    def custom_object_menu(self):
        ''' menu to choose custom object parameters'''
        #validates an integer for tkinter entry
        def validate_int(action, index, value_if_allowed,prior_value, text, validation_type, trigger_type, widget_name):

            if not value_if_allowed:
                return True
            try:
                int(value_if_allowed)
                return True
            except ValueError:
                return False
        #validates an float for tkinter entry
        def validate_float(action, index, value_if_allowed,prior_value, text, validation_type, trigger_type, widget_name):
            if not value_if_allowed:
                return True
            try:
                float(value_if_allowed)
                return True
            except ValueError:
                return False

        top = tkinter.Toplevel(self.master)
        x = root.winfo_x()
        y = root.winfo_y()
        top.geometry("+%d+%d" % (x + 10, y + 20))
        top.title("add custom object")
        top.rowconfigure(0, weight=1)
        top.columnconfigure(0, weight=1)

        a_var = tkinter.StringVar()
        ecc_var = tkinter.StringVar()
        i_var = tkinter.StringVar()
        omega_var = tkinter.StringVar()
        OMEGA_var = tkinter.StringVar()
        anomaly_var = tkinter.StringVar()
        name_var = tkinter.StringVar()
        name_frame = tkinter.Frame(top,pady=10)
        kepler_frame = tkinter.LabelFrame(top,text='kepler elements',pady=10,padx=5)
        button_frame = tkinter.Frame(top)
        name_frame.rowconfigure(0, weight=1)
        name_frame.columnconfigure(0, weight=1)
        button_frame.rowconfigure(0, weight=1)
        button_frame.columnconfigure(0, weight=1)
        kepler_frame.rowconfigure(0, weight=1)
        kepler_frame.columnconfigure(0, weight=1)
        vcmd_int = (button_frame.register(validate_int),'%d', '%i', '%P', '%s', '%S', '%v', '%V', '%W')
        vcmd_float = (button_frame.register(validate_float), '%d', '%i', '%P', '%s', '%S', '%v', '%V', '%W')
        name_frame.grid(row=0,column=0,sticky=tkinter.W+tkinter.E+tkinter.N+tkinter.S)
        kepler_frame.grid(row=1,column=0,sticky=tkinter.W+tkinter.E+tkinter.N+tkinter.S)
        button_frame.grid(row=2,column=0,sticky=tkinter.W+tkinter.E+tkinter.N+tkinter.S)
        tkinter.Label(name_frame,text='displayname').grid(row=0,column=0,sticky=tkinter.W+tkinter.N+tkinter.S)
        tkinter.Entry(name_frame,validate = 'key',textvariable=name_var).grid(row=0,column=1,columnspan=2,sticky=tkinter.W+tkinter.E+tkinter.N+tkinter.S)
        kepler_array = [ ['semimajor axis:' , 'AU', a_var] , ['numerical eccentricity:' , '', ecc_var] , ['inclination:' , 'degrees', i_var] , ['argument of periapsis:' , 'degrees', omega_var] , ['longitude of the ascending node:' , 'degrees', OMEGA_var], ['true anomaly' , 'degrees', anomaly_var]]
        row_count = 0
        for element in kepler_array:
            tkinter.Label(kepler_frame,text=element[0]).grid(row=row_count,column=0,sticky=tkinter.W+tkinter.N+tkinter.S)
            tkinter.Entry(kepler_frame,validate = 'key', validatecommand=vcmd_float,textvariable=element[2]).grid(row=row_count,column=1,sticky=tkinter.W+tkinter.E+tkinter.N+tkinter.S)
            tkinter.Label(kepler_frame,text=element[1]).grid(row=row_count,column=2,sticky=tkinter.W+tkinter.E+tkinter.N+tkinter.S)
            row_count = row_count + 1


        tkinter.Button(button_frame,text='add to plot',command= lambda: self.add_custom_object(a_var,ecc_var,i_var,omega_var,OMEGA_var,anomaly_var,name_var,top)).grid(row=0,column=0,sticky=tkinter.W+tkinter.E+tkinter.N+tkinter.S)
        tkinter.Button(button_frame,text='close',command= lambda: top.destroy() ).grid(row=0,column=1,sticky=tkinter.W+tkinter.E+tkinter.N+tkinter.S)

        top.transient(self.master)
        top.resizable(width=False,height=False)
        return

    def add_custom_object(self,a,ecc,i,omega,Omega,true_anomaly,name,top):
        ''' function to add a custom object to the current object list'''
        try:
            a = float(a.get())
            ecc = float(ecc.get())
            i =  np.deg2rad(float(i.get()))
            omega =  np.deg2rad(float(omega.get()))
            Omega =  np.deg2rad(float(Omega.get()))
            true_anomaly =  np.deg2rad(float(true_anomaly.get()))
            name = name.get()
        except:
            self.error_message('Invalid input','Please check your input parameters')
            return
        top.destroy()
        keplers = {'eccentricity' : ecc, 'a' : a, 'inclination' : i , 'omega' : omega, 'Omega' : Omega, 'true_anomaly' : true_anomaly}
        orbit = self.orbit_position(a,ecc,Omega,i,omega,comp_true_anomaly=true_anomaly)
        position = self.orbit_position(a,ecc,Omega,i,omega,[true_anomaly])
        keplers = {'eccentricity' : ecc, 'a' : a, 'inclination' : i , 'omega' : omega, 'Omega' : Omega, 'true_anomaly' : true_anomaly}
        current_date = datetime.datetime.now().date()
        custom_object = celestial_artist('',orbit,position, current_date ,name,'custom object added by user',keplers)
        self.current_objects.append(custom_object)
        self.redraw_current_objects()

        return

    def distance_menu(self):
        '''popup menu to choose objects and timerange to plot linear distance for'''
        choice_list = []
        choice_1_var = tkinter.StringVar()
        choice_2_var = tkinter.StringVar()
        for object in self.current_objects:
            choice_list.append(object.displayname)
        if len(choice_list) < 2:
            self.error_message('error','there must be atleast 2 objects to calculate a distance plot')
            return
        choice_1_var.set(choice_list[0])
        choice_2_var.set(choice_list[1])

        top = tkinter.Toplevel(self.master)
        top.group(self.master)
        x = root.winfo_x()
        y = root.winfo_y()
        top.geometry("+%d+%d" % (x + 10, y + 20))
        top.title("distance plot generator")
        top.rowconfigure(0, weight=1)
        top.columnconfigure(0, weight=1)
        dropdown_frame = tkinter.Frame(top)
        button_frame = tkinter.Frame(top)
        dropdown_frame.columnconfigure(0, weight=1)
        dropdown_frame.rowconfigure(0, weight=1)

        dropdown_frame.grid(row=0,column=0,sticky=tkinter.W+tkinter.E)
        object_frame = tkinter.Frame(dropdown_frame,borderwidth=4)
        object_frame.grid(row=0,column=0,sticky=tkinter.W+tkinter.E)
        object_frame.columnconfigure(0,weight=1)
        date_frame = tkinter.Frame(dropdown_frame,borderwidth=4)
        date_frame.grid(row=1,column=0,sticky=tkinter.W+tkinter.E)
        date_frame.columnconfigure(0,weight=1)
        button_frame.grid(row=2,column=0)

        choice_1 = tkinter.OptionMenu(object_frame, choice_1_var, *choice_list)
        choice_2 = tkinter.OptionMenu(object_frame, choice_2_var, *choice_list)
        cal1 = DateEntry(date_frame,dateformat=3,width=12, background='darkblue',foreground='white', borderwidth=4,Calendar =2018,year=self.dt.year, month=self.dt.month, day=self.dt.day)
        cal2 = DateEntry(date_frame,dateformat=3,width=12, background='darkblue',foreground='white', borderwidth=4,Calendar =2018,year=self.dt.year+3, month=self.dt.month, day=self.dt.day)

        tkinter.Label(object_frame,text='start object:').grid(row=0,column=0,sticky=tkinter.W)
        tkinter.Label(object_frame,text='target object:').grid(row=1,column=0,sticky=tkinter.W)
        tkinter.Label(date_frame, text='from').grid(row=0,column=1)
        tkinter.Label(date_frame, text='to').grid(row=0,column=2)
        tkinter.Label(date_frame, text='date range:').grid(row=1,column=0,sticky=tkinter.W)
        choice_1.grid(row=0,column=1,columnspan=2,sticky=tkinter.E)
        choice_2.grid(row=1,column=1,columnspan=2,sticky=tkinter.E)
        cal1.grid(row=1,column = 1,sticky=tkinter.E+tkinter.W)
        cal2.grid(row=1,column = 2,sticky=tkinter.E+tkinter.W)

        close_button = tkinter.Button(button_frame,text='close',command=top.destroy)
        calculate_button = tkinter.Button(button_frame,text='generate plot',command= lambda: self.calculate_distance_plot (choice_1_var.get(), choice_2_var.get(), cal1.get_date(), cal2.get_date() ) )
        close_button.grid(row=0,column=0)
        calculate_button.grid(row=0,column=1)

        top.resizable(width=False,height=False)
        top.transient(self.master)

    def calculate_distance_plot(self,selection1,selection2,date1,date2,resolution = 12,time_format = 'h'):
        self.prog_bar_cancel_button['state'] = tkinter.NORMAL
        for object in self.current_objects:
            if object.displayname == selection1:
                object1 = object
            if object.displayname == selection2:
                object2 = object
        self.prog_bar["value"] = 0
        self.prog_bar["maximum"] = 2
        print('requesting data...')
        vectors1 = self.request_vector_timerange(object1.id,date1,date2,resolution,time_format = time_format)
        try:
            if vectors1 == None:
                return
        except:
            pass
        if self.destroy_was_called:
            return
        self.prog_bar["value"] = self.prog_bar["value"] + 1
        self.prog_bar.update()

        vectors2 = self.request_vector_timerange(object2.id,date1,date2,resolution,time_format = time_format)
        try:
            if vectors2 == None:
                return
        except:
            pass

        if self.destroy_was_called:
            return
        self.prog_bar["value"] = self.prog_bar["value"] + 1
        self.prog_bar.update()

        distance = []
        date_vector = []
        if self.destroy_was_called:
            return
        self.prog_bar["value"] = 0
        self.prog_bar["maximum"] = len(vectors1)
        print('calculating ...')
        for vector1,vector2 in zip(vectors1,vectors2):
            r1 = [float(entry) for entry in vector1[2:5]]
            r2 = [float(entry) for entry in vector2[2:5]]
            r1 = np.array(r1)
            r2 = np.array(r2)
            distance.append(np.linalg.norm(r1 - r2))
            date_vector.append(datetime.datetime.strptime(vector1[1],"A.D.%Y-%b-%d%H:%M:%S.0000"))
            if self.destroy_was_called:
                return
            if self.cancel_was_pushed:
                self.cancel_was_pushed = False
                self.prog_bar["value"] = 0
                self.prog_bar_cancel_button['state'] = tkinter.DISABLED
                return
            self.prog_bar["value"] = self.prog_bar["value"] + 1
            self.prog_bar.update()
        self.prog_bar_cancel_button['state'] = tkinter.DISABLED
        distance = np.array(distance)
        date_vector_for_matplotlib = mdates.date2num(date_vector)

        min_distance = np.amin(distance)
        xpos = np.argmin(distance)
        date_at_min = date_vector_for_matplotlib[xpos]
        date_at_min2 = date_vector[xpos]
        print('Done!')
        distance_frame =  ttk.Frame(self.notebook)
        distance_frame.rowconfigure(0,weight=1)
        distance_frame.columnconfigure(0,weight=1)

        fig = plt.figure()
        fig.subplots_adjust(left=0.16, right=0.98, bottom=0.18, top=0.9)
        canvas_frame = tkinter.Frame(distance_frame)
        bottom_frame = tkinter.Frame(distance_frame)
        canvas_frame.columnconfigure(0,weight=1)
        bottom_frame.columnconfigure(0,weight=1)
        canvas_frame.rowconfigure(0,weight=1)
        bottom_frame.rowconfigure(0,weight=1)
        canvas_frame.grid(row=0,column=0,sticky=tkinter.N+tkinter.W+tkinter.E+tkinter.S)
        bottom_frame.grid(row=1,column=0,sticky=tkinter.N+tkinter.W+tkinter.E+tkinter.S)
        toolbarframe = tkinter.Frame(bottom_frame)
        close_button_frame = tkinter.Frame(bottom_frame)
        close_button_frame.columnconfigure(0,weight=1)
        toolbarframe.columnconfigure(0,weight=1)
        canvas = FigureCanvasTkAgg(fig, master=canvas_frame)
        canvas.get_tk_widget().grid(row=0,column=0,sticky=tkinter.N+tkinter.W+tkinter.E+tkinter.S)

        toolbarframe.grid(row=0,column=0,sticky=tkinter.W)
        close_button_frame.grid(row=0,column=1,sticky=tkinter.E)
        canvas.get_tk_widget().rowconfigure(0,weight=1)
        canvas.get_tk_widget().columnconfigure(0,weight=1)
        toolbar = NavigationToolbar2Tk(canvas,toolbarframe)
        tkinter.Button(close_button_frame,text='close',command= lambda: self.notebook.forget(self.notebook.select())).grid(row=0,column=1,sticky=tkinter.E)
        ax = fig.gca()

        plot_handle = ax.plot_date(date_vector_for_matplotlib,distance,xdate=True,linestyle='solid', marker='None')
        annot = ax.text(date_at_min,min_distance, ' {:.4f} AU'.format(min_distance) , verticalalignment='top')
        annot = ax.text(date_at_min,min_distance, '{:%Y-%m-%d %H:%M:%S} '.format(date_at_min2) , verticalalignment='top',horizontalalignment='right')

        ax.xaxis_date()
        ax.xaxis.set_major_locator(LinearLocator())
        ax.yaxis.set_major_locator(LinearLocator())

        date_format = mdates.DateFormatter('%Y-%m-%d')
        ax.xaxis.set_major_formatter(date_format)

        ax.set_xlabel('date YYYY/MM/DD [UTC]')
        ax.set_ylabel('distance in AU')
        ax.grid(b=True,axis='both',linestyle= '--',dashes=(10,15) ,color='k')
        ax.set_aspect('auto')
        ax.set_title('distance between\n{0} and {1}'.format(object1.displayname,object2.displayname))
        fig.autofmt_xdate()
        canvas.draw()
        name1= object1.displayname
        name2= object2.displayname
        if len(name1) >15:
            name1 = name1[0:15]+'..'
        if len(name2) >15:
            name2 = name2[0:15]+'..'
        self.notebook.add(distance_frame,text='{0} <-> {1}'.format(name1,name2))
        self.notebook.select(self.notebook.tabs()[-1])

    def porkchop_menu(self):
        ''' popup menu to choose parameters for porkchop plot generation'''

        #validates an integer for tkinter entry
        def validate_int(action, index, value_if_allowed,prior_value, text, validation_type, trigger_type, widget_name):

            if not value_if_allowed:
                return True
            try:
                int(value_if_allowed)
                return True
            except ValueError:
                return False
        #validates an float for tkinter entry
        def validate_float(action, index, value_if_allowed,prior_value, text, validation_type, trigger_type, widget_name):
            if not value_if_allowed:
                return True
            try:
                float(value_if_allowed)
                return True
            except ValueError:
                return False

        def Entry_Callback(event):
            resolution_entry.selection_range(0, tkinter.END)

        choice_1_var = tkinter.StringVar()
        choice_2_var = tkinter.StringVar()
        resolution_var = tkinter.StringVar()
        resolution_var.set('10')
        iteration_var = tkinter.StringVar()
        iteration_var.set('50')
        tolerance_var = tkinter.StringVar()
        tolerance_var.set('0.0001')
        revolution_list = [ '0' , '1' , '2' , '3' , '4' , '5' ]
        revolution_var = tkinter.StringVar()
        revolution_var.set('0')
        interpolation_list = ['none', 'nearest', 'bilinear', 'bicubic', 'spline16', 'spline36', 'hanning', 'hamming', 'hermite', 'kaiser', 'quadric', 'catrom', 'gaussian', 'bessel', 'mitchell', 'sinc', 'lanczos']
        interpolation_var = tkinter.StringVar()
        interpolation_var.set('bilinear')
        if not self.pykep_installed:
            pulse_direction_options = [('prograde','prograde') , ('retrograde','retrograde') , ('both', 'both')]
        else:
            pulse_direction_options = [('prograde','prograde') , ('retrograde','retrograde')]

        dV_options = [('launch','launch') , ('arrival' , 'arrival') , ('both','both')]


        choice_list = []
        for object in self.current_objects:
            choice_list.append(object.displayname)
        if len(choice_list) < 2:
            self.error_message('error','there must be atleast 2 objects to calculate a porkchop plot')
            return
        choice_1_var.set(choice_list[0])
        choice_2_var.set(choice_list[1])

        top = tkinter.Toplevel(self.master)
        top.group(self.master)
        x = root.winfo_x()
        y = root.winfo_y()
        top.geometry("+%d+%d" % (x + 10, y + 20))
        top.title("porkchop plot generator")
        top.rowconfigure(0, weight=1)
        top.columnconfigure(0, weight=1)
        dropdown_frame = tkinter.Frame(top)
        button_frame = tkinter.Frame(top)
        dropdown_frame.columnconfigure(0, weight=1)
        dropdown_frame.rowconfigure(0, weight=1)


        dropdown_frame.grid(row=0,column=0,sticky=tkinter.W+tkinter.E)
        object_frame = tkinter.Frame(dropdown_frame,borderwidth=4)
        object_frame.grid(row=0,column=0,sticky=tkinter.W+tkinter.E)
        object_frame.columnconfigure(0,weight=1)
        date_frame = tkinter.Frame(dropdown_frame,borderwidth=4)
        date_frame.grid(row=1,column=0,sticky=tkinter.W+tkinter.E)
        date_frame.columnconfigure(0,weight=1)
        misc_frame = tkinter.LabelFrame(dropdown_frame,text='advanced settings',pady=5,padx=5)
        misc_frame.grid(row=2,column=0,sticky=tkinter.W+tkinter.E)
        misc_frame.columnconfigure(0,weight=1)
        button_frame.grid(row=2,column=0)

        vcmd_int = (dropdown_frame.register(validate_int),'%d', '%i', '%P', '%s', '%S', '%v', '%V', '%W')
        vcmd_float = (dropdown_frame.register(validate_float), '%d', '%i', '%P', '%s', '%S', '%v', '%V', '%W')

        choice_1 = tkinter.OptionMenu(object_frame, choice_1_var, *choice_list)
        choice_2 = tkinter.OptionMenu(object_frame, choice_2_var, *choice_list)
        cal1 = DateEntry(date_frame,dateformat=3,width=12, background='darkblue',foreground='white', borderwidth=4,Calendar =2018,year=self.dt.year, month=self.dt.month, day=self.dt.day)
        cal2 = DateEntry(date_frame,dateformat=3,width=12, background='darkblue',foreground='white', borderwidth=4,Calendar =2018,year=self.dt.year+3, month=self.dt.month, day=self.dt.day)
        resolution_entry = tkinter.Entry(misc_frame,validate = 'key', validatecommand=vcmd_int,textvariable=resolution_var)
        resolution_entry.bind("<FocusIn>",Entry_Callback)
        iteration_entry = tkinter.Entry(misc_frame,validate = 'key', validatecommand=vcmd_int ,textvariable=iteration_var)
        tolerance_entry = tkinter.Entry(misc_frame,validate = 'key', validatecommand=vcmd_float ,textvariable=tolerance_var)
        interpolation_choice = tkinter.OptionMenu(misc_frame, interpolation_var, *interpolation_list)
        revolution_choice = tkinter.OptionMenu(misc_frame, revolution_var, *revolution_list )

        tkinter.Label(object_frame,text='start object:').grid(row=0,column=0,sticky=tkinter.W)
        tkinter.Label(object_frame,text='target object:').grid(row=1,column=0,sticky=tkinter.W)
        tkinter.Label(date_frame, text='from').grid(row=0,column=1)
        tkinter.Label(date_frame, text='to').grid(row=0,column=2)
        tkinter.Label(date_frame, text='date range:').grid(row=1,column=0,sticky=tkinter.W)
        tkinter.Label(misc_frame, text='resolution in days:').grid(row=0,column=0,sticky=tkinter.W)
        tkinter.Label(misc_frame, text='image interpolation:').grid(row=1,column=0,sticky=tkinter.W)
        if not self.pykep_installed:
            tkinter.Label(misc_frame, text='number of iterations:').grid(row=2,column=0,sticky=tkinter.W)
            tkinter.Label(misc_frame, text='numerical tolerance:').grid(row=3,column=0,sticky=tkinter.W)
        else:
            # tkinter.Label(misc_frame, text='number of revolutions:').grid(row = 2,column =0, sticky= tkinter.W)
            pass

        choice_1.grid(row=0,column=1,columnspan=2,sticky=tkinter.E)
        choice_2.grid(row=1,column=1,columnspan=2,sticky=tkinter.E)
        cal1.grid(row=1,column = 1,sticky=tkinter.E+tkinter.W)
        cal2.grid(row=1,column = 2,sticky=tkinter.E+tkinter.W)
        resolution_entry.grid(row=0,column=2,sticky=tkinter.E)
        interpolation_choice.grid(row=1,column=2,sticky=tkinter.E)
        if not self.pykep_installed:
            iteration_entry.grid(row=2,column=2, sticky = tkinter.E)
            tolerance_entry.grid(row=3,column=2,sticky=tkinter.E)
        else:
            # revolution_choice.grid(row=2,column=2,sticky=tkinter.E)
            pass
        #############radiobuttons###############
        pulse_frame = tkinter.LabelFrame(misc_frame, text= 'pulse direction')
        # pulse_frame.columnconfigure(0,weight=1)
        pulse_frame.grid(row = 4 ,column = 0, columnspan = 3,sticky= tkinter.W )
        count = 0
        for text,mode in pulse_direction_options:
            b = tkinter.Radiobutton(pulse_frame,text=text,variable = self.pulse_direction_var , value = mode)
            b.grid(row=0 , column=count)
            self.porkchop_radiobuttons.append(b)
            count = count + 1
        dV_frame = tkinter.LabelFrame(misc_frame,text = 'delta-V')
        # dV_frame.columnconfigure(0,weight=1)
        dV_frame.grid(row = 5,column = 0, columnspan = 3,sticky= tkinter.W )
        count=0
        for text,mode in dV_options:
            b = tkinter.Radiobutton(dV_frame, text=text,variable= self.dV_var , value = mode)
            b.grid(row=0, column = count )
            self.porkchop_radiobuttons.append(b)
            count = count + 1
        #######################################

        close_button = tkinter.Button(button_frame,text='close',command=top.destroy)
        calculate_button = tkinter.Button(button_frame,text='generate plot',command=lambda : self.calc_porkchop(choice_1_var.get(),choice_2_var.get() , int(resolution_var.get()),cal1.get_date(),cal2.get_date() , interpolation_var.get(), int(iteration_var.get()), float(tolerance_var.get()) , top, rev=int(revolution_var.get())))
        close_button.grid(row=0,column=0)
        calculate_button.grid(row=0,column=1)
        top.resizable(width=False,height=False)
        top.transient(self.master)

    def calc_porkchop(self,selection1,selection2,resolution,date1,date2,interpolation,iterations,tolerance,top,rev=0):
        ''' function to calculate porkchop plot and plot the array as heatmap'''
        top.destroy()
        self.prog_bar_cancel_button['state'] = tkinter.NORMAL
        for object in self.current_objects:
            if object.displayname == selection1:
                object1 = object
            if object.displayname == selection2:
                object2 = object
        vectors1 = self.request_vector_timerange(object1.id,date1,date2,resolution)
        vectors2 = self.request_vector_timerange(object2.id,date1,date2,resolution)
        dV_array_depart = np.zeros((len(vectors1),len(vectors2)))
        dV_array_arrival = dV_array_depart
        counter1 = 0
        counter2 = 0
        #def solve_lambert(self,r1,r2,delta_t,object1,object2,numiters=100,tolerance=1e-6,popup = True):
        #v_1, v_2, keplers, delta_v1, delta_v2
        self.prog_bar["value"] = 0
        self.prog_bar["maximum"] = len(vectors1)
        print('calculating ...')
        # for button in self.porkchop_radiobuttons:
        #     button.configure(state= 'disabled')
        for vector1 in vectors1:
            for vector2 in vectors2:
                date_vector1 = datetime.datetime.strptime(vector1[1],"A.D.%Y-%b-%d00:00:00.0000")
                date_vector2 = datetime.datetime.strptime(vector2[1],"A.D.%Y-%b-%d00:00:00.0000")
                delta_t = date_vector2 - date_vector1
                if delta_t.total_seconds() > 0:
                     if self.pykep_installed:
                         dV_array_depart[counter2][counter1], dV_array_arrival[counter2][counter1] , _ = self.solve_lambert_pykep(vector1[2:5] , vector2[2:5] , delta_t.total_seconds() , vector1[5:8] , vector2[5:8],clockwise=False,rev=rev)
                     else:
                         _,_,_,dV_array_depart[counter2][counter1],dV_array_arrival[counter2][counter1] = self.solve_lambert(vector1[2:5] , vector2[2:5] , delta_t.total_seconds() , vector1[5:8] , vector2[5:8] , popup = False, numiters=iterations, tolerance = tolerance)

                else:
                    dV_array_depart[counter2][counter1] = np.nan
                    dV_array_arrival[counter2][counter1] = np.nan
                if dV_array_depart[counter2][counter1] == False:
                    dV_array_depart[counter2][counter1] = np.nan
                    dV_array_arrival[counter2][counter1] = np.nan
                counter2 = counter2 +1
                if self.destroy_was_called:
                    return
                if self.cancel_was_pushed:
                    self.cancel_was_pushed = False
                    self.prog_bar["value"] = 0
                    self.prog_bar_cancel_button['state'] = tkinter.DISABLED
                    return
            self.prog_bar["value"] = counter1
            self.prog_bar.update()
            counter1 = counter1 + 1
            counter2 = 0
        # for button in self.porkchop_radiobuttons:
        #     button.configure(state= 'normal')

        self.prog_bar_cancel_button['state'] = tkinter.DISABLED
        date_list_1 = [datetime.datetime.strptime(vector[1],"A.D.%Y-%b-%d00:00:00.0000") for vector in vectors1 ]
        date_list = mdates.date2num(date_list_1)
        dV_array_depart = dV_array_depart * self.AUinKM
        dV_array_arrival = dV_array_arrival * self.AUinKM
        dV_array_depart[ dV_array_depart > 16] = np.nan
        dV_array_arrival[ dV_array_arrival > 16] = np.nan
        print('done!')
        if self.dV_var.get() == 'launch':
            dV_array = dV_array_depart
        elif self.dV_var.get() == 'arrival':
            dV_array = dV_array_arrival
        else:
            dV_array = dV_array_depart + dV_array_arrival

        ind = np.unravel_index(np.nanargmin(dV_array[:]), dV_array.shape)
        min_launch_date = date_list[ind[1]]
        min_arrival_date = date_list[ind[0]]
        min_dV = np.nanmin(dV_array[:])

        porkchop_frame =  ttk.Frame(self.notebook)
        porkchop_frame.rowconfigure(0,weight=1)
        porkchop_frame.columnconfigure(0,weight=1)

        fig = plt.figure()
        fig.subplots_adjust(left=0.19, right=0.98, bottom=0.18, top=0.9)
        canvas_frame = tkinter.Frame(porkchop_frame)
        bottom_frame = tkinter.Frame(porkchop_frame)
        canvas_frame.columnconfigure(0,weight=1)
        bottom_frame.columnconfigure(0,weight=1)
        canvas_frame.rowconfigure(0,weight=1)
        bottom_frame.rowconfigure(0,weight=1)
        canvas_frame.grid(row=0,column=0,sticky=tkinter.N+tkinter.W+tkinter.E+tkinter.S)
        bottom_frame.grid(row=1,column=0,sticky=tkinter.N+tkinter.W+tkinter.E+tkinter.S)
        toolbarframe = tkinter.Frame(bottom_frame)
        close_button_frame = tkinter.Frame(bottom_frame)
        close_button_frame.columnconfigure(0,weight=1)
        toolbarframe.columnconfigure(0,weight=1)
        canvas = FigureCanvasTkAgg(fig, master=canvas_frame)
        canvas.get_tk_widget().grid(row=0,column=0,sticky=tkinter.N+tkinter.W+tkinter.E+tkinter.S)

        toolbarframe.grid(row=0,column=0,sticky=tkinter.W)
        close_button_frame.grid(row=0,column=1,sticky=tkinter.E)
        canvas.get_tk_widget().rowconfigure(0,weight=1)
        canvas.get_tk_widget().columnconfigure(0,weight=1)
        toolbar = NavigationToolbar2Tk(canvas,toolbarframe)
        tkinter.Button(close_button_frame,text='close',command= lambda: self.notebook.forget(self.notebook.select())).grid(row=0,column=1,sticky=tkinter.E)
        ax = fig.gca()
        im = ax.imshow(dV_array,origin='lower',cmap='jet',interpolation = interpolation,vmin=0,vmax = 15, extent = [date_list[0] , date_list[-1] , date_list[0] , date_list[-1]])
        # im = ax.contour(dV_array,origin='lower',cmap='jet',vmin=2,vmax = 15, extent = [date_list[0] , date_list[-1] , date_list[0] , date_list[-1]])
        ax.xaxis_date()
        ax.yaxis_date()
        ax.xaxis.set_major_locator(LinearLocator())
        ax.yaxis.set_major_locator(LinearLocator())

        date_format = mdates.DateFormatter('%Y-%m-%d')
        ax.xaxis.set_major_formatter(date_format)
        ax.yaxis.set_major_formatter(date_format)
        ax.set_xlabel('launch date YYYY/MM/DD')
        ax.set_ylabel('arrival date YYYY/MM/DD')
        ax.grid(b=True,axis='both',linestyle= '--',dashes=(10,15) ,color='k')
        ax.set_aspect('auto')
        ax.set_title('0 rev. transfers from\n{0} to {1}'.format(object1.displayname,object2.displayname))
        fig.autofmt_xdate()

        #annotate minimum dV
        annot = ax.text(min_launch_date,min_arrival_date, '  launch: {:%Y-%m-%d}\n  arrival: {:%Y-%m-%d}\n  delta-V: {:.2f} km/s'.format(date_list_1[ind[1]],date_list_1[ind[0]] , min_dV),verticalalignment='center',weight='bold',zorder=100)
        mark = ax.plot_date(min_launch_date,min_arrival_date,'X', MarkerEdgeColor='k',markersize=7,MarkerFaceColor='w',xdate=True,ydate=True)
        cbar = fig.colorbar(im, ax=ax)
        cbar.set_label(r'departure $\Delta$V in $\frac{km}{s}$')
        canvas.draw()
        name1= object1.displayname
        name2= object2.displayname
        if len(name1) >15:
            name1 = name1[0:15]+'..'
        if len(name2) >15:
            name2 = name2[0:15]+'..'
        self.notebook.add(porkchop_frame,text='{0} -> {1}'.format(name1,name2))
        self.notebook.select(self.notebook.tabs()[-1])

        return

    def solve_lambert_pykep(self, r1, r2,dt,object1,object2,clockwise=False,rev=0):

        r1 = [float(r1[0]) , float(r1[1]) , float(r1[2])]
        r2 = [float(r2[0]) , float(r2[1]) , float(r2[2])]
        l = lambert_problem(r1,r2,dt,self.GM_sun,clockwise,rev)
        v_p1 = [float(entry) for entry in object1]
        v_p2 = [float(entry) for entry in object2]
        v_p1 = np.array(v_p1) / (24*60*60)
        v_p2 = np.array(v_p2) / (24*60*60)
        delta_v1 = np.linalg.norm(l.get_v1()[rev] - v_p1)
        delta_v2 = np.linalg.norm(l.get_v2()[rev] - v_p2)
        return delta_v1,delta_v2, l

    def request_vector_timerange(self,id,date1,date2,resolution,errors=0,time_format = 'd'):
        ''' function to request a timerange of ephemerides of one object from the JPL horizons DB as cartesian state vectors'''
        batchfile = self.batchfile_timerange
        batchfile['COMMAND'] = str(id)
        batchfile['START_TIME'] = "'"+str(date1)+"'"
        batchfile['STOP_TIME'] = "'"+str(date2)+"'"
        if resolution <1:
            print('only time formats >1')
            return

        batchfile['STEP_SIZE'] = "'"+str(resolution) + " " +time_format +"'"

        try:
            r = requests.get("https://ssd.jpl.nasa.gov/horizons_batch.cgi?batch=1", params = batchfile,timeout=2.0)
        except (requests.exceptions.ConnectionError,requests.exceptions.Timeout):
            print('connection failed, retrying...')
            if errors<=2:
                return self.request_vector_timerange(id,date1,date2,resolution,errors=errors+1)
            self.error_message('Connection Error','Could not reach the Server, please check your internet connection.')
            return False,False
        # print(r.text)
        try:
            vectors = r.text.split('$$SOE')[1].split('$$EOE')[0].replace(' ','').splitlines()
        except:
            self.error_message('Sorry!','Something with the Database textparsing went wrong')
            return
        del vectors[0]
        vectors = [vector.split(',') for vector in vectors]
        vectors = np.array(vectors)
        return vectors


    def kep2velocity(self,object):
        ''' function to calculate the velocity-vector of an object from its kepler elements'''
        ecc = object.keplers['eccentricity']
        true_anomaly = object.keplers['true_anomaly']
        a = object.keplers['a']
        # ecc_anomaly = np.arccos( (ecc + np.cos(true_anomaly)) / (1 + ecc*np.cos(true_anomaly)) )
        # ecc_anomaly = np.arcsin( (np.sqrt(1-ecc**2) *np.sin(true_anomaly)) / (1 + ecc*np.cos(true_anomaly)) )
        # r = a*(1-ecc*np.cos(ecc_anomaly))
        r = np.linalg.norm(object.pos)
        ecc_anomaly = np.arccos((1 -(r/a))/ecc )
        v = (np.sqrt(self.GM_sun*a) / r) * np.array([ -np.sin(ecc_anomaly) , np.sqrt(1-(ecc)**2)*np.cos(ecc_anomaly) , 0 ])
        v = np.matmul(self.rot_z(-object.keplers['omega']) , v)
        v = np.matmul(self.rot_x(-object.keplers['inclination']) , v)
        v = np.matmul(self.rot_z(-object.keplers['Omega']) , v)
        v = v.flatten()
        v = v*24*60*60 #convert to AU/d to keep consitency
        pprint(ecc)
        pprint(true_anomaly)
        pprint(a)
        pprint(r)
        pprint(ecc_anomaly)
        pprint(v)
        return v


if __name__ == '__main__':
    #pyinstaller fix
    multiprocessing.freeze_support()
    root = tkinter.Tk()
    icon_img = tkinter.Image("photo",file='./galaxy.png')
    root.tk.call('wm','iconphoto',root._w,icon_img)
    tkinter.Grid.rowconfigure(root, 0, weight=1)
    tkinter.Grid.columnconfigure(root, 0, weight=1)
    gui = plot_application(root,pykep_installed)
    root.mainloop()
