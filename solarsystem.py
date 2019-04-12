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
import tkinter
from tkinter.colorchooser import *
from tkinter import ttk
import operator
import csv
import configparser,ast
# from pykep import lambert_problem

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.ticker import ScalarFormatter
# Implement the appearance Matplotlib key bindings.
from matplotlib.backend_bases import key_press_handler
from tkcalendar import DateEntry,Calendar
from tkinter import filedialog
# import io
# from PIL import Image

class CustomNotebook(ttk.Notebook):
    """A ttk Notebook with close buttons on each tab"""

    __initialized = False

    def __init__(self, *args, **kwargs):
        if not self.__initialized:
            self.__initialize_custom_style()
            self.__inititialized = True

        kwargs["style"] = "CustomNotebook"
        ttk.Notebook.__init__(self, *args, **kwargs)

        self._active = None

        self.bind("<ButtonPress-1>", self.on_close_press, True)
        self.bind("<ButtonRelease-1>", self.on_close_release)

    def on_close_press(self, event):
        """Called when the button is pressed over the close button"""

        element = self.identify(event.x, event.y)

        if "close" in element:
            index = self.index("@%d,%d" % (event.x, event.y))
            self.state(['pressed'])
            self._active = index

    def on_close_release(self, event):
        """Called when the button is released over the close button"""
        if not self.instate(['pressed']):
            return

        element =  self.identify(event.x, event.y)
        index = self.index("@%d,%d" % (event.x, event.y))

        if "close" in element and self._active == index:
            self.forget(index)
            self.event_generate("<<NotebookTabClosed>>")

        self.state(["!pressed"])
        self._active = None

    def __initialize_custom_style(self):
        style = ttk.Style()
        self.images = (
            tkinter.PhotoImage("img_close", data='''
                R0lGODlhCAAIAMIBAAAAADs7O4+Pj9nZ2Ts7Ozs7Ozs7Ozs7OyH+EUNyZWF0ZWQg
                d2l0aCBHSU1QACH5BAEKAAQALAAAAAAIAAgAAAMVGDBEA0qNJyGw7AmxmuaZhWEU
                5kEJADs=
                '''),
            tkinter.PhotoImage("img_closeactive", data='''
                R0lGODlhCAAIAMIEAAAAAP/SAP/bNNnZ2cbGxsbGxsbGxsbGxiH5BAEKAAQALAAA
                AAAIAAgAAAMVGDBEA0qNJyGw7AmxmuaZhWEU5kEJADs=
                '''),
            tkinter.PhotoImage("img_closepressed", data='''
                R0lGODlhCAAIAMIEAAAAAOUqKv9mZtnZ2Ts7Ozs7Ozs7Ozs7OyH+EUNyZWF0ZWQg
                d2l0aCBHSU1QACH5BAEKAAQALAAAAAAIAAgAAAMVGDBEA0qNJyGw7AmxmuaZhWEU
                5kEJADs=
            ''')
        )

        style.element_create("close", "image", "img_close",
                            ("active", "pressed", "!disabled", "img_closepressed"),
                            ("active", "!disabled", "img_closeactive"), border=8, sticky='')
        style.layout("CustomNotebook", [("CustomNotebook.client", {"sticky": "nswe"})])
        style.layout("CustomNotebook.Tab", [
            ("CustomNotebook.tab", {
                "sticky": "nswe",
                "children": [
                    ("CustomNotebook.padding", {
                        "side": "top",
                        "sticky": "nswe",
                        "children": [
                            ("CustomNotebook.focus", {
                                "side": "top",
                                "sticky": "nswe",
                                "children": [
                                    ("CustomNotebook.label", {"side": "left", "sticky": ''}),
                                    ("CustomNotebook.close", {"side": "left", "sticky": ''}),
                                ]
                        })
                    ]
                })
            ]
        })
    ])


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

        self.keplers = keplers

class plot_application:
    def __init__(self, master):
        self.master = master
        self.AUinKM = 149597870.691 #km/AU
        self.G = 6.673e-20 / np.power(self.AUinKM,3) #km³/kg*s²
        self.GM_sun = 1.3271244018e11 / np.power(self.AUinKM,3)
        self.M_sun = self.GM_sun / self.G
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

        self.default_colors = ['#191919','#7f7f7f','#ffffff','#000000']
        self.resolution = 80
        self.set_default_colors()
        self.gridlinewidth = 0.2
        self.textsize = 8
        self.markersize = 7
        self.orbit_linewidth = 1
        self.refplane_linewidth = 0.3
        self.text_xoffset = 0
        self.text_yoffset = 4
        self.check_config()

        self.view_cid = None
        self.formatter = ScalarFormatter(useMathText=True,useOffset=True)
        self.dt = datetime.datetime.now()
        self.dates = []
        self.julian_date =  "'" + str(sum(jdcal.gcal2jd(self.dt.year, self.dt.month, self.dt.day))) + "'"
        self.order_of_keplers = ['excentricity','periapsis_distance','inclination','Omega','omega','Tp','n','mean_anomaly','true_anomaly','a','apoapsis_distance','sidereal_period']
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
        self.master.wm_title("JPL horizons DB visualisation")
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

        plt.rcParams['savefig.facecolor']= self.custom_color
        plt.rcParams['grid.color'] = self.gridcolor
        plt.rcParams['grid.linewidth'] = self.gridlinewidth

        self.ax = self.fig.gca(projection = '3d',facecolor =  self.custom_color,proj_type = 'ortho')

        self.canvas.get_tk_widget().grid(row=0,column=0,sticky=tkinter.N+tkinter.W+tkinter.E+tkinter.S)
        self.viewbuttons_frame = tkinter.Frame(master= self.canvas.get_tk_widget())
        self.viewbuttons_frame.place(rely=1,relx=0,anchor=tkinter.SW)

        # self.equinox_cid = self.ax.callbacks.connect('xlim_changed',self.scale_equinox)

        self.menubar = tkinter.Menu(self.master)
        self.filemenu = tkinter.Menu(self.menubar,tearoff = 0)

        self.filemenu.add_command(label="save figure as", command=self.save_file_as)
        self.filemenu.add_command(label="preferences", command=self.preferences_menu)
        self.filemenu.add_separator()
        self.filemenu.add_command(label="Exit", command=self.master.quit)

        self.tools_menu = tkinter.Menu(self.menubar,tearoff = 0)
        self.tools_menu.add_command(label='calculate rendezvous (lambert solver)', command=self.lambert_menu)
        self.tools_menu.add_command(label='generate porkchop-plot', command=self.porkchop_menu)

        self.menubar.add_cascade(label='File',menu=self.filemenu)
        self.menubar.add_cascade(label='Tools',menu=self.tools_menu)
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
        self.prog_bar = tkinter.ttk.Progressbar(self.master,orient='horizontal',length=200,mode='determinate')
        self.prog_bar.grid(row=8,column=11,columnspan=2,sticky=tkinter.S+tkinter.W+tkinter.E)
        for k,v in self.JPL_numbers.items():
            self.listbox.insert(tkinter.END,v)
        self.canvas.draw()

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
        dir = filedialog.asksaveasfilename(defaultextension=".png")
        if dir == '' or dir == ():
            return
        print(dir)
        self.fig.canvas.mpl_disconnect(self.view_cid)
        plt.savefig(dir)
        # self.axis_visibility(None,'z',True)
        # self.axis_visibility(None,'y',True)

        '''does weird stuff with the image (atrifacts)'''
        # ps = self.canvas.get_tk_widget().postscript(colormode='color')
        # img = Image.open(io.BytesIO(ps.encode('utf-8')))
        # img.save(dir)

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
        '''sets the view angles of the plot and toggles visibility of the perpendicular axis to false until plot is moved/refreshed   '''
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
            # e = 1 atually wrong, here just to prevent crash, exact excentricity of 1 should not happen
            p = a * (1-(e**2))
            r = p/(1+e*np.cos(self.nu))
            r = np.array([np.multiply(r,np.cos(self.nu)) , np.multiply(r,np.sin(self.nu)), np.zeros(len(self.nu))])
            r = np.matmul(self.rot_z(omega),r)
            r = np.matmul(self.rot_x(i),r)
            r = np.matmul(self.rot_z(Omega),r)
        elif e >1:
            if comp_true_anomaly > 2:
                plot_range = 3*np.pi/4
                if plot_range < np.abs(comp_true_anomaly):
                    plot_range = np.abs(comp_true_anomaly)
            else:
                plot_range = 3/4 * np.pi -np.pi
                if plot_range > np.abs(comp_true_anomaly):
                    plot_range = np.abs(comp_true_anomaly)
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

    def save_obj(self,obj, name ):
        with open('./'+ name + '.pkl', 'wb') as f:
            pickle.dump(obj, f, pickle.HIGHEST_PROTOCOL)

    def load_obj(self,name):
        with open('./' + name + '.pkl', 'rb') as f:
            return pickle.load(f)

    def _quit(self):
        self.master.quit()     # stops mainloop
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
        if orbits == False:
            pass
        else:
            self.plot_orbits(self.ax,self.current_objects,refresh_canvas = True,refplane_var=self.refplane_var.get())



    def plot_orbits(self,ax,objects,refresh_canvas=True,refplane_var = 1):
        '''plots orbits, positions and annotations'''

        self.ax.cla()

        plt.rcParams['savefig.facecolor']= self.custom_color
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
            if object.color == None:
                object.orbit_artist = ax.plot(orbit[0],orbit[1],orbit[2],linewidth=self.orbit_linewidth,clip_on=False)
            else:
                object.orbit_artist = ax.plot(orbit[0],orbit[1],orbit[2],color=object.color,linewidth=self.orbit_linewidth,clip_on=False)
            if refplane_var == 1:
                     for x,y,z in zip(*object.orbit.tolist()):
                         ax.plot([x,x],[y,y],[z,0],'white',linewidth=self.refplane_linewidth,clip_on=False)

            color = object.orbit_artist[0].get_color()
            object.color = color
            if object.id == None:
                object.position_artist = self.ax.plot(pos[0],pos[1],pos[2], marker='*', MarkerSize=self.markersize,MarkerFaceColor=color ,markeredgecolor = color ,clip_on=False,picker=5)
            else:
                object.position_artist = self.ax.plot(pos[0],pos[1],pos[2], marker='o', MarkerSize=self.markersize,MarkerFaceColor=color ,markeredgecolor = color ,clip_on=False,picker=5)
            object.annotation_artist = self.annotate3D(ax, s=object.displayname, xyz=[pos[0],pos[1],pos[2]], fontsize=self.textsize, xytext=(self.text_xoffset,self.text_yoffset),textcoords='offset points', ha='center',va='bottom',color = self.text_color,clip_on=False)
            if self.annot_var.get() == 1:
                self.annotate3D(ax, s=str(object.date), xyz=[pos[0],pos[1],pos[2]], fontsize=self.textsize, xytext=(self.text_xoffset,-self.text_yoffset),textcoords='offset points', ha='center',va='top',color = self.text_color,clip_on=False)

        # # # recompute the ax.dataLim
        # # ax.relim()
        # # # update ax.viewLim using the new dataLim
        # # ax.autoscale(True)
        #
        self.axisEqual3D(ax)
        ylim = np.max(np.abs(self.ax.get_ylim()))
        xlim = np.max(np.abs(self.ax.get_xlim()))
        zlim = np.max(np.abs(self.ax.get_zlim()))
        max = np.amax([ylim,xlim,zlim])
        self.ax.set_ylim([-max, max])
        self.ax.set_xlim([-max, max])
        self.ax.set_zlim([-max, max])

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

    def on_closing(self):
        if tkinter.messagebox.askokcancel("Quit", "Do you want to quit?"):
            self.master.quit()

    def error_message(self,title,message):
        '''generates an error message-popup with generic title and message'''
        tkinter.messagebox.showerror(title,message)

    def request_keplers(self,objects,batchfile,errors=0):
        '''requests kepler elements from HORIZONS-batch-interface for objects'''
        print('requesting keplers for selected items')
        orbits = []
        positions = []
        kepler_dict = {}
        self.prog_bar["maximum"] = len(objects)

        count = 0
        for object in objects:
            batchfile['COMMAND'] = object
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
            self.prog_bar["value"] = count
            self.prog_bar.update()
            if 'No ephemeris for target' in r.text:
                print('No ephemeris for target{0} at date {1}'.format(self.JPL_numbers[object],self.dt))
                orbit = [None,None]
                position = [None,None]
                orbits.append([None,None])
                positions.append([None,None])
            elif 'is out of bounds, no action taken' in r.text:
                print('{0} is out of bounds, no action taken (couldnt find {1} in batch interface of JPL horizonss)'.format(self.JPL_numbers[object],object))
                orbit = [None,None]
                position = [None,None]
                orbits.append([None,None])
                positions.append([None,None])
            elif 'No such record, positive values only' in r.text:
                print('No record for {0}({1}), positive values only'.format(object,self.JPL_numbers[object]))
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
                orbit = self.orbit_position(kepler_dict['a'],kepler_dict['excentricity'],kepler_dict['Omega'],kepler_dict['inclination'],kepler_dict['omega'] , comp_true_anomaly=kepler_dict['true_anomaly'] )
                position = self.orbit_position(kepler_dict['a'],kepler_dict['excentricity'],kepler_dict['Omega'],kepler_dict['inclination'],kepler_dict['omega'],[kepler_dict['true_anomaly']])
                orbits.append(orbit)
                positions.append(position)

            '''celestial artist : def __init__(self,id,artist,orbit,pos,date,color,name):'''
            self.current_objects.append(celestial_artist(object,orbit,position,self.dt,self.JPL_numbers[object],r.text,kepler_dict))
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
                pprint('clicked {0}'.format(name))
        for object in self.current_objects:
            object.position_artist[0].set_markeredgecolor(object.position_artist[0].get_markerfacecolor())
        selected_object.position_artist[0].set_markeredgecolor('white')
        self.canvas.draw()
        self.artist_menu(selected_object)

    def artist_menu(self,object):
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
        object.position_artist[0].remove()
        object.orbit_artist[0].remove()
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
            if inclination > np.pi/2:
                return False,False,False,False,False
        keplers = {'excentricity':ecc,'inclination':inclination,'Omega':Omega,'omega':omega,'true_anomaly':true_anomaly,'a':a}
        return v_1, v_2, keplers, delta_v1, delta_v2

    def calc_rendezvous(self,selection1,selection2):
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
        orbit = self.orbit_position(keplers['a'],keplers['excentricity'],keplers['Omega'],keplers['inclination'],keplers['omega'],comp_true_anomaly=kepler_dict['true_anomaly'])
        pos = self.orbit_position(keplers['a'],keplers['excentricity'],keplers['Omega'],keplers['inclination'],keplers['omega'],[keplers['true_anomaly'] + np.pi/2])


        #class celestial_artist:
            # def __init__(self,id,orbit,pos,date,name,text,keplers):
        lambert_object = celestial_artist(None,orbit,pos,str(object1.date) + ' to ' + str(object2.date),'Lambert solution',
        '*********\nthis is the 0 rev. solution to the Lambertproblem of the transfer from:\n{0} -> {1}\n\n*********\n'
        'Delta V for Transferorbit as single pulse:\t{2:.4} km/s \nDelta V for Injection into target orbit:\t{3:.4} km/s\nOverall Delta V:\t{4:.4} km/s'.format(object1.displayname,object2.displayname,delta_v1*self.AUinKM,delta_v2*self.AUinKM,np.abs(delta_v1+delta_v2)*self.AUinKM) , keplers)

        self.current_objects.append(lambert_object)
        self.redraw_current_objects()

        return

    def kart2kep(self,r,v):
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
            omega = np.arccos(np.dot(n,ecc_vector)/(np.linalg.norm(n)*np.linalg.norm(ecc_vector)))

        return ecc, inclination, Omega, omega, true_anomaly

    def lambert_menu(self):
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

        info_text_widget = tkinter.Label(info_frame,text = 'Attention: Always check for pausibillity of the solution!\n This tool can calculate a rendezvous between two\n points in space with an elliptical transfer. It uses a simple \nnumerical solver, especially at the lower\n and upper boundaries of possible solutions \nthe solver tends to shrink drastically in precision.')
        info_text_widget.grid(row=0,column=0)

        close_button = tkinter.Button(button_frame,text='close',command=top.destroy)
        calculate_button = tkinter.Button(button_frame,text='calculate!',command=lambda : self.calc_rendezvous(choice_1_var.get(),choice_2_var.get()))
        close_button.grid(row=0,column=0)
        calculate_button.grid(row=0,column=1)
        top.transient(self.master)
        top.resizable(width=False,height=False)
        return

    def calc_approx__timefree_dv(self,object1,object2, dt):
        self.error_message('coming soon','function isnt implemented yet')
        return

    def approx_timefree_dv(self,r1,r2,dt,starting_object):
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

    def porkchop_menu(self):

        def validate(action, index, value_if_allowed,prior_value, text, validation_type, trigger_type, widget_name):
            if text in '0123456789':
                try:
                    int(value_if_allowed)
                    return True
                except ValueError:
                    return False
            else:
                return False

        def Entry_Callback(event):
            resolution_entry.selection_range(0, tkinter.END)

        choice_1_var = tkinter.StringVar()
        choice_2_var = tkinter.StringVar()
        resolution_var = tkinter.StringVar()
        interpolation_list = ['none', 'nearest', 'bilinear', 'bicubic', 'spline16', 'spline36', 'hanning', 'hamming', 'hermite', 'kaiser', 'quadric', 'catrom', 'gaussian', 'bessel', 'mitchell', 'sinc', 'lanczos']
        interpolation_var = tkinter.StringVar()
        interpolation_var.set('bilinear')
        choice_list = []
        for object in self.current_objects:
            choice_list.append(object.displayname)
        if len(choice_list) < 2:
            self.error_message('error','there must be atleast 2 objects to calculate a porkchop plot')
            return
        choice_1_var.set(choice_list[0])
        choice_2_var.set(choice_list[1])
        resolution_var.set('10')
        top = tkinter.Toplevel(self.master)
        x = root.winfo_x()
        y = root.winfo_y()
        top.geometry("+%d+%d" % (x + 10, y + 20))
        top.title("porkchop plot generator")
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
        object_frame = tkinter.Frame(dropdown_frame,borderwidth=2)
        object_frame.grid(row=0,column=0,sticky=tkinter.W+tkinter.E)
        object_frame.columnconfigure(0,weight=1)
        date_frame = tkinter.Frame(dropdown_frame,borderwidth=2)
        date_frame.grid(row=1,column=0,sticky=tkinter.W+tkinter.E)
        date_frame.columnconfigure(0,weight=1)
        misc_frame = tkinter.Frame(dropdown_frame,borderwidth=2)
        misc_frame.grid(row=2,column=0,sticky=tkinter.W+tkinter.E)
        misc_frame.columnconfigure(0,weight=1)
        vcmd = (dropdown_frame.register(validate),'%d', '%i', '%P', '%s', '%S', '%v', '%V', '%W')
        button_frame.grid(row=2,column=0)
        choice_1 = tkinter.OptionMenu(object_frame, choice_1_var, *choice_list)
        choice_2 = tkinter.OptionMenu(object_frame, choice_2_var, *choice_list)
        cal1 = DateEntry(date_frame,dateformat=3,width=12, background='darkblue',foreground='white', borderwidth=4,Calendar =2018,year=self.dt.year, month=self.dt.month, day=self.dt.day)
        cal2 = DateEntry(date_frame,dateformat=3,width=12, background='darkblue',foreground='white', borderwidth=4,Calendar =2018,year=self.dt.year+3, month=self.dt.month, day=self.dt.day)
        resolution_entry = tkinter.Entry(misc_frame,validate = 'key', validatecommand=vcmd,textvariable=resolution_var)
        resolution_entry.bind("<FocusIn>",Entry_Callback)
        interpolation_choice = tkinter.OptionMenu(misc_frame, interpolation_var, *interpolation_list)


        tkinter.Label(object_frame,text='start object:').grid(row=0,column=0,sticky=tkinter.W)
        tkinter.Label(object_frame,text='target object:').grid(row=1,column=0,sticky=tkinter.W)
        tkinter.Label(date_frame, text='from').grid(row=2,column=1)
        tkinter.Label(date_frame, text='to').grid(row=2,column=2)
        tkinter.Label(date_frame, text='date range:').grid(row=3,column=0,sticky=tkinter.W)
        tkinter.Label(misc_frame, text='resolution in days:').grid(row=4,column=0,sticky=tkinter.W)
        tkinter.Label(misc_frame, text='image interpolation:').grid(row=5,column=0,sticky=tkinter.W)
        choice_1.grid(row=0,column=1,columnspan=2,sticky=tkinter.E)
        choice_2.grid(row=1,column=1,columnspan=2,sticky=tkinter.E)
        cal1.grid(row=3,column = 1,sticky=tkinter.E+tkinter.W)
        cal2.grid(row=3,column = 2,sticky=tkinter.E+tkinter.W)
        resolution_entry.grid(row=4,column=2,sticky=tkinter.E)
        interpolation_choice.grid(row=5,column=2,sticky=tkinter.E)

        close_button = tkinter.Button(button_frame,text='close',command=top.destroy)
        calculate_button = tkinter.Button(button_frame,text='generate plot',command=lambda : self.calc_porkchop(choice_1_var.get(),choice_2_var.get() , int(resolution_var.get()),cal1.get_date(),cal2.get_date() , interpolation_var.get()))
        close_button.grid(row=0,column=0)
        calculate_button.grid(row=0,column=1)
        top.transient(self.master)
        top.resizable(width=False,height=False)

    def calc_porkchop(self,selection1,selection2,resolution,date1,date2,interpolation):

        for object in self.current_objects:
            if object.displayname == selection1:
                object1 = object
            if object.displayname == selection2:
                object2 = object
        vectors1 = self.request_vector_timerange(object1.id,date1,date2,resolution)
        vectors2 = self.request_vector_timerange(object2.id,date1,date2,resolution)
        dV_array_depart = np.zeros((len(vectors1)+1,len(vectors2)+1))
        dV_array_arrival = dV_array_depart
        counter1 = 0
        counter2 = 0
        #def solve_lambert(self,r1,r2,delta_t,object1,object2,numiters=100,tolerance=1e-6,popup = True):
        #v_1, v_2, keplers, delta_v1, delta_v2
        self.prog_bar["value"] = 0
        self.prog_bar["maximum"] = len(vectors1)
        print('calculating ...')
        for vector1 in vectors1:
            for vector2 in vectors2:
                date_vector1 = datetime.datetime.strptime(vector1[1],"A.D.%Y-%b-%d00:00:00.0000")
                date_vector2 = datetime.datetime.strptime(vector2[1],"A.D.%Y-%b-%d00:00:00.0000")
                delta_t = date_vector2 - date_vector1
                if delta_t.total_seconds() > 0:
                    _,_,_,dV_array_depart[counter2][counter1],dV_array_arrival[counter2][counter1] = self.solve_lambert(vector1[2:5] , vector2[2:5] , delta_t.total_seconds() , vector1[5:8] , vector2[5:8] , popup = False)
                else:
                    dV_array_depart[counter2][counter1] = np.nan
                    dV_array_arrival[counter2][counter1] = np.nan
                if dV_array_depart[counter2][counter1] == False:
                    dV_array_depart[counter2][counter1] = np.nan
                    dV_array_arrival[counter2][counter1] = np.nan
                counter2 = counter2 +1
            self.prog_bar["value"] = counter1
            self.prog_bar.update()
            counter1 = counter1 + 1
            counter2 = 0
        date_list = [datetime.datetime.strptime(vector[1],"A.D.%Y-%b-%d00:00:00.0000") for vector in vectors1 ]
        date_list = mdates.date2num(date_list)
        dV_array_depart = dV_array_depart * self.AUinKM
        dV_array_arrival = dV_array_arrival * self.AUinKM
        print('done!')
        porkchop_frame =  ttk.Frame(self.notebook)
        porkchop_frame.rowconfigure(0,weight=1)
        porkchop_frame.columnconfigure(0,weight=1)

        fig = plt.figure()
        fig.subplots_adjust(left=0.19, right=0.98, bottom=0.18, top=0.92)
        toolbarframe = tkinter.Frame(porkchop_frame)
        canvas = FigureCanvasTkAgg(fig, master=porkchop_frame)
        canvas.get_tk_widget().grid(row=0,column=0,sticky=tkinter.N+tkinter.W+tkinter.E+tkinter.S)
        toolbarframe.grid(row=1,column=0,sticky=tkinter.N+tkinter.W+tkinter.E+tkinter.S)
        canvas.get_tk_widget().rowconfigure(0,weight=1)
        canvas.get_tk_widget().columnconfigure(0,weight=1)
        toolbar = NavigationToolbar2Tk(canvas,toolbarframe)
        ax = fig.gca()
        im = ax.imshow(dV_array_depart,origin='lower',cmap='jet',interpolation = interpolation,vmin=2,vmax = 15, extent = [date_list[0] , date_list[-1] , date_list[0] , date_list[-1]])
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
        ax.set_title('0 rev. transfers between {0} and {1}'.format(object1.displayname,object2.displayname))
        fig.autofmt_xdate()
        cbar = fig.colorbar(im, ax=ax)
        cbar.set_label(r'departure $\Delta$V in $\frac{km}{s}$')
        canvas.draw()
        self.notebook.add(porkchop_frame,text='{0} -> {1}'.format(object1.displayname,object2.displayname))
        self.notebook.select(self.notebook.tabs()[-1])

        return

    def request_vector_timerange(self,id,date1,date2,resolution,errors=0):
        batchfile = self.batchfile_timerange
        batchfile['COMMAND'] = str(id)
        batchfile['START_TIME'] = "'"+str(date1)+"'"
        batchfile['STOP_TIME'] = "'"+str(date2)+"'"
        batchfile['STEP_SIZE'] = "'"+str(resolution) + " d'"

        try:
            r = requests.get("https://ssd.jpl.nasa.gov/horizons_batch.cgi?batch=1", params = batchfile,timeout=2.0)
        except (requests.exceptions.ConnectionError,requests.exceptions.Timeout):
            print('connection failed, retrying...')
            if errors<=2:
                return self.request_vector_timerange(id,date1,date2,resolution,errors=errors+1)
            self.error_message('Connection Error','Could not reach the Server, please check your internet connection.')
            return False,False
        # print(r.text)
        vectors = r.text.split('$$SOE')[1].split('$$EOE')[0].replace(' ','').splitlines()
        del vectors[0]
        vectors = [vector.split(',') for vector in vectors]
        vectors = np.array(vectors)
        return vectors

    def kep2velocity(self,object):
        ecc = object.keplers['excentricity']
        true_anomaly = object.keplers['true_anomaly']
        a = object.keplers['a']
        ecc_anomaly = np.arccos( (ecc + np.cos(true_anomaly)) / (1 + ecc*np.cos(true_anomaly)) )
        r = a*(1-ecc*np.cos(ecc_anomaly))
        # print('{0}:'.format(object.displayname))
        # print(r)
        # print(ecc_anomaly)
        # print(a)
        # pprint(object.keplers)
        v = (np.sqrt(self.GM_sun*a) / r) * np.array([ -np.sin(ecc_anomaly) , np.sqrt(1-(ecc)**2)*np.cos(ecc_anomaly) , 0 ])
        return v


if __name__ == '__main__':
    root = tkinter.Tk()
    '''Icons made by "https://www.freepik.com/" from "https://www.flaticon.com/"
    www.flaticon.com is licensed by "http://creativecommons.org/licenses/by/3.0/"'''
    icon_img = tkinter.Image("photo",file='./galaxy.png')
    root.tk.call('wm','iconphoto',root._w,icon_img)
    tkinter.Grid.rowconfigure(root, 0, weight=1)
    tkinter.Grid.columnconfigure(root, 0, weight=1)
    gui = plot_application(root)
    root.mainloop()
