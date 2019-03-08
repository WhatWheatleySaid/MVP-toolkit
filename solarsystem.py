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
from pathlib import Path
import pickle
import tkinter
import operator
import csv

from matplotlib.backends.backend_tkagg import (
    FigureCanvasTkAgg, NavigationToolbar2Tk)
# Implement the default Matplotlib key bindings.
from matplotlib.backend_bases import key_press_handler
from tkcalendar import DateEntry,Calendar

class plot_application:
    def __init__(self, master):
        self.master = master
        self.index = 0
        self.kepler_dict = {}
        self.planet_positions = []
        self.position_coordinates = []
        self.HOST = 'horizons.jpl.nasa.gov'
        self.port = '6775'
        self.filename = 'DBNumbers'
        self.filename2 = 'smallbodies'
        self.JPL_numbers = []
        self.orbit_colors = []
        self.equinox_artists = []
        self.list = []
        self.resolution = 50
        self.custom_color =  [0.1,0.1,0.1]
        self.textsize = 8
        self.markersize = 7
        self.orbit_linewidth = 1
        self.refplane_linewidth = 0.1
        self.text_xoffset = 0
        self.text_yoffset = 4
        self.dt = datetime.datetime.now()
        self.julian_date =  "'" + str(sum(jdcal.gcal2jd(self.dt.year, self.dt.month, self.dt.day))) + "'"
        self.order_of_keplers = ['excentricity','periapsis_distance','inclination','Omega','omega','Tp','n','mean_anomaly','true_anomaly','a','apoapsis_distance','sidereal_period']
        self.objects = ["'399'","'499'","'-143205'"] #earth,mars,Tesla roadster, ... ceres : ,"'5993'"
        self.batchfile = {"COMMAND": "'399'","CENTER": "'500@10'","MAKE_EPHEM": "'YES'","TABLE_TYPE": "'ELEMENTS'","TLIST":self.julian_date,"OUT_UNITS": "'KM-S'","REF_PLANE": "'ECLIPTIC'","REF_SYSTEM": "'J2000'","TP_TYPE": "'ABSOLUTE'","ELEM_LABELS": "'YES'","CSV_FORMAT": "'YES'","OBJ_DATA": "'YES'"}
        self.my_file = Path("./"+self.filename+'.pkl')
        self.my_file2 = Path("./"+self.filename2+'.csv')
        self.search_term = tkinter.StringVar()
        self.search_term.set('')
        self.search_term.trace("w", lambda name, index, mode: self.update_listbox())
        self.prog_var = tkinter.DoubleVar(value = 0)
        self.check_db()

        self.fig = plt.figure(facecolor = self.custom_color)
        self.master.wm_title("JPL horizons DB visualisation")
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.master)  # A tk.DrawingArea.
        self.fig.canvas.mpl_connect('pick_event',self.clicked_on)
        self.equinox_cid = self.fig.canvas.mpl_connect('draw_event',self.scale_equinox)
        plt.rcParams['savefig.facecolor']= self.custom_color
        plt.rcParams['grid.color'] = [0.5,0.5,0.5]
        plt.rcParams['grid.linewidth'] = 0.2
        self.ax = self.fig.gca(projection = '3d',facecolor =  self.custom_color,proj_type = 'ortho')
        self.canvas.get_tk_widget().grid(row=0,column=0,columnspan=10,rowspan=10,sticky=tkinter.N+tkinter.W+tkinter.E+tkinter.S)
        self.viewbuttons_frame = tkinter.Frame(master= self.canvas.get_tk_widget())
        self.viewbuttons_frame.place(rely=1,relx=0,anchor=tkinter.SW)

        self.button1 = tkinter.Button(master=self.master, text="new Plot", command=lambda : self.refresh_plot(True))
        self.button1.grid(row=3,column=11,columnspan=2,sticky=tkinter.N+tkinter.W+tkinter.E)
        self.button2  = tkinter.Button(master=self.master, text="add to Plot", command=lambda : self.refresh_plot(False))
        self.button2.grid(row=4,column=11,columnspan=2,sticky=tkinter.N+tkinter.W+tkinter.E)
        self.topview_button = tkinter.Button(master=self.viewbuttons_frame,text='TOP', command=lambda:self.change_view('top'))
        self.topview_button.configure(width=3,height=1)
        self.topview_button.grid(row=0,column=0)
        self.rightview_button = tkinter.Button(master=self.viewbuttons_frame,text='XZ', command=lambda:self.change_view('XZ'))
        self.rightview_button.configure(width=3,height=1)
        self.rightview_button.grid(row=0,column=1)


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
        self.refplane_checkbutton = tkinter.Checkbutton(master=self.master,text='referenceplane lines',variable = self.refplane_var,command=self.toggle_refplane).grid(row=6,column=11,sticky=tkinter.N+tkinter.W)
        self.annot_checkbutton = tkinter.Checkbutton(master=self.master,text='show date at objectposition',variable = self.annot_var,command=self.toggle_refplane).grid(row=6,column=12,sticky=tkinter.N+tkinter.W)
        self.axis_checkbutton = tkinter.Checkbutton(master=self.master,text='show coordinate axis',variable = self.axis_var,command=self.toggle_axis).grid(row=7,column=11,sticky=tkinter.N+tkinter.W)
        self.proj_checkbutton = tkinter.Checkbutton(master=self.master,text='perspective projection',variable = self.proj_var,command=self.toggle_proj).grid(row=7,column=12,sticky=tkinter.N+tkinter.W)
        self.prog_bar = tkinter.ttk.Progressbar(self.master,orient='horizontal',length=200,mode='determinate')
        self.prog_bar.grid(row=8,column=11,columnspan=2,sticky=tkinter.S+tkinter.W+tkinter.E)
        for k,v in self.JPL_numbers.items():
            self.listbox.insert(tkinter.END,v)
        self.canvas.draw()

        self.nu = np.linspace(0,2*np.pi,self.resolution)
        orbits,positions = self.request_keplers(self.objects,self.batchfile)
        self.current_objects = {'orbits':orbits,'positions':positions}
        self.plot_orbits(self.ax,orbits,positions,self.objects,refresh_canvas=True,refplane_var=self.refplane_var.get())

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
        if view == "top":
            self.ax.view_init(90,-90)
        elif view == "XZ":
            self.ax.view_init(0,-90)
        self.canvas.draw()

    def scale_equinox(self,event):
        self.fig.canvas.mpl_disconnect(self.equinox_cid)
        if len(self.equinox_artists)>0:
            for i in range(0,len(self.equinox_artists)):
                if i == 3:
                    self.equinox_artists[i].remove()
                    continue
                self.equinox_artists[i][0].remove()
        self.equinox_artists = []
        xlim = self.ax.get_xlim()
        length = 0.2 *xlim[1]
        self.equinox_artists.append(self.ax.plot([0,length] , [0,0],[0,0],color='white'))
        self.equinox_artists.append(self.ax.plot([length,0.7*length],[0,0.05*length],[0,0],color='white'))
        self.equinox_artists.append(self.ax.plot([length,0.7*length],[0,-0.05*length],[0,0],color='white'))
        self.equinox_artists.append(self.annotate3D(self.ax, s='vernal equinox', xyz=[length,0,0], fontsize=self.textsize, xytext=(self.text_xoffset,-self.text_yoffset),textcoords='offset points', ha='center',va='top',color = 'white'))
        self.equinox_cid = self.fig.canvas.mpl_connect('draw_event',self.scale_equinox)

    def orbit_position(self,a,e,Omega,i,omega,true_anomaly=False):
        '''calculate orbit 3x1 radius vector'''
        if not(true_anomaly==False):
            p = a * (1-(e**2))
            r = p/(1+e*np.cos(true_anomaly))
            r = np.array([np.multiply(r,np.cos(true_anomaly)) , np.multiply(r,np.sin(true_anomaly)), np.zeros(len(true_anomaly))])
            r = np.matmul(self.rot_z(omega),r)
            r = np.matmul(self.rot_x(i),r)
            r = np.matmul(self.rot_z(Omega),r)
        elif e <=1:
            # e = 1 atually wrong, here just to prevent crash
            p = a * (1-(e**2))
            r = p/(1+e*np.cos(self.nu))
            r = np.array([np.multiply(r,np.cos(self.nu)) , np.multiply(r,np.sin(self.nu)), np.zeros(len(self.nu))])
            r = np.matmul(self.rot_z(omega),r)
            r = np.matmul(self.rot_x(i),r)
            r = np.matmul(self.rot_z(Omega),r)
        elif e >1:
            nu = np.linspace(-3*np.pi/4,3*np.pi/4,self.resolution)
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
        sorted_x = sorted(dictionary.items(), key=operator.itemgetter(1))
        return dict(sorted_x)

    def get_selected(self):
        user_choice = []
        index_list = map(int,self.listbox.curselection())
        for i in index_list:
            user_choice.append(self.listbox.get(i))
        return user_choice

    def refresh_plot(self,clear_axis = True):
        print('refreshing')
        if clear_axis:
            self.current_objects['orbits'] = []
            self.current_objects['positions'] = []
            self.objects = []
        objects = self.get_selected()
        objects = [self.JPL_name2num[object] for object in objects]
        self.objects.extend(objects)
        orbits,positions = self.request_keplers(objects,self.batchfile)
        self.current_objects['orbits'].extend(orbits)
        self.current_objects['positions'].extend(positions)
        self.plot_orbits(self.ax,orbits,positions,objects,refresh_canvas = True, clear_axis=clear_axis,refplane_var=self.refplane_var.get())

    def plot_orbits(self,ax,orbits,positions,objects,refresh_canvas=True,clear_axis = True,refplane_var = 1):
        orbit_colors = []
        if clear_axis:
            self.ax.cla()
            ax.scatter(0,0,0,marker='o',s = 20,color='yellow')
            self.annotate3D(ax, s='sun', xyz=[0,0,0], fontsize=self.textsize, xytext=(self.text_xoffset,self.text_yoffset),textcoords='offset points', ha='center',va='bottom',color ="white")
            ax.set_xlabel('X axis in km')
            ax.set_ylabel('Y axis in km')
            ax.set_zlabel('Z axis in km')
            ax.xaxis.label.set_color('white')
            ax.yaxis.label.set_color('white')
            ax.zaxis.label.set_color('white')
            ax.tick_params(axis='x', colors='white')
            ax.tick_params(axis='y', colors='white')
            ax.tick_params(axis='z', colors='white')
            ax.w_xaxis.set_pane_color((0, 0, 0, .6))
            ax.w_yaxis.set_pane_color((0, 0, 0, .6))
            ax.w_zaxis.set_pane_color((0, 0, 0, .6))
        index = 0
        for orbit in orbits:
            if None in orbit:
                continue
            ph = ax.plot(orbit[0],orbit[1],orbit[2],linewidth=self.orbit_linewidth,clip_on=False)
            if refplane_var == 1:
                for x,y,z in zip(*orbit.tolist()):
                    ax.plot([x,x],[y,y],[z,0],'white',linewidth=self.refplane_linewidth,clip_on=False)
            orbit_colors.append(ph[0].get_color())
        for pos, object in zip(positions,objects):
            if None in pos:
                continue
            ax.plot(pos[0],pos[1],pos[2], marker='o', MarkerSize=self.markersize,MarkerFaceColor=orbit_colors[index],markeredgecolor = orbit_colors[index],clip_on=False,picker=5.0,label=self.JPL_numbers[object])

            self.annotate3D(ax, s=self.JPL_numbers[object], xyz=[pos[0],pos[1],pos[2]], fontsize=self.textsize, xytext=(self.text_xoffset,self.text_yoffset),textcoords='offset points', ha='center',va='bottom',color = 'white',clip_on=False)
            if self.annot_var.get() == 1:
                self.annotate3D(ax, s=str(self.dt), xyz=[pos[0],pos[1],pos[2]], fontsize=self.textsize, xytext=(self.text_xoffset,-self.text_yoffset),textcoords='offset points', ha='center',va='top',color = 'white',clip_on=False)
            index = index + 1

        # # recompute the ax.dataLim
        # ax.relim()
        # # update ax.viewLim using the new dataLim
        # ax.autoscale(True)

        self.axisEqual3D(ax)
        ylim = np.max(np.abs(self.ax.get_ylim()))
        xlim = np.max(np.abs(self.ax.get_xlim()))
        zlim = np.max(np.abs(self.ax.get_zlim()))
        self.ax.set_ylim([-ylim, ylim])
        self.ax.set_xlim([-xlim, xlim])
        self.ax.set_zlim([-zlim, zlim])
        # ylim = self.ax.get_ylim()
        # xlim = self.ax.get_xlim()
        # x = 10*np.linspace(xlim[0],xlim[1],100)
        # y = 10*np.linspace(ylim[0],ylim[1],100)
        # xx , yy = np.meshgrid(x,y)
        # z = 0*xx
        # self.ax.plot_wireframe(xx,yy,z,linewidth=0.1,clip_on=False,color='white',rcount=400,ccount=400)

        if self.axis_var.get() == 1:
            self.ax.set_axis_on()
        else:
            self.ax.set_axis_off()

        if refresh_canvas:
            self.canvas.draw()

    def on_closing(self):
        if tkinter.messagebox.askokcancel("Quit", "Do you want to quit?"):
            self.master.quit()

    def request_keplers(self,objects,batchfile):
        print('requesting keplers for selected items')
        orbits = []
        positions = []

        self.prog_bar["maximum"] = len(objects)

        count = 0
        for object in objects:
            batchfile['COMMAND'] = object
            self.dt = self.calendar_widget.selection_get()
            batchfile['TLIST'] = "'" + str(sum(jdcal.gcal2jd(self.dt.year, self.dt.month, self.dt.day))) + "'"
            r = requests.get("https://ssd.jpl.nasa.gov/horizons_batch.cgi?batch=1", params = batchfile)
            # print(r.text)
            count = count + 1
            self.prog_bar["value"] = count
            self.prog_bar.update()
            if 'No ephemeris for target' in r.text:
                print('No ephemeris for target{0} at date {1}'.format(self.JPL_numbers[object],self.dt))
                orbits.append([None,None])
                positions.append([None,None])
            elif 'is out of bounds, no action taken' in r.text:
                print('{0} is out of bounds, no action taken (couldnt find {1} in batch interface of JPL horizonss)'.format(self.JPL_numbers[object],object))
                orbits.append([None,None])
                positions.append([None,None])
            else:
                keplers = r.text.split('$$SOE')[1].split('$$EOE')[0].replace(' ','').split(',')
                del keplers[0:2]
                del keplers[-1]
                keplers = [float(element) for element in keplers]
                for i in range(len(keplers)):
                    self.kepler_dict[self.order_of_keplers[i]] = keplers[i]
                self.kepler_dict['Omega'] = np.deg2rad(self.kepler_dict['Omega'])
                self.kepler_dict['inclination'] = np.deg2rad(self.kepler_dict['inclination'])
                self.kepler_dict['omega'] = np.deg2rad(self.kepler_dict['omega'])
                self.kepler_dict['true_anomaly'] = np.deg2rad(self.kepler_dict['true_anomaly'])
                print('\n\n{0}:\n'.format(self.JPL_numbers[object]))
                pprint(self.kepler_dict)
                orbits.append(self.orbit_position(self.kepler_dict['a'],self.kepler_dict['excentricity'],self.kepler_dict['Omega'],self.kepler_dict['inclination'],self.kepler_dict['omega']))
                positions.append(self.orbit_position(self.kepler_dict['a'],self.kepler_dict['excentricity'],self.kepler_dict['Omega'],self.kepler_dict['inclination'],self.kepler_dict['omega'],[self.kepler_dict['true_anomaly']]))
        return orbits,positions

    def update_listbox(self):
        search_term = self.search_term.get()
        selected_items = self.get_selected()
        self.listbox.delete(0,tkinter.END)
        for k,v in self.JPL_numbers.items():
            if search_term.lower() in v.lower() and not (search_term.lower() in selected_items):
                self.listbox.insert(tkinter.END,v)
        for item in selected_items:
            self.listbox.insert(1,item)
            self.listbox.selection_set(1)
        return True

    def toggle_axis(self):
        if self.axis_var.get() == 1:
            self.ax.set_axis_on()
            self.canvas.draw()
        else:
            self.ax.set_axis_off()
            self.canvas.draw()

    def toggle_refplane(self):
        self.plot_orbits(self.ax,self.current_objects['orbits'],self.current_objects['positions'],self.objects,refplane_var=self.refplane_var.get())

    def toggle_proj(self):
        if self.proj_var.get() == 1:
            self.ax.set_proj_type('persp')
        else:
            self.ax.set_proj_type('ortho')#
        self.canvas.draw()
    def clicked_on(self,event):
        # artist_dir = dir(event.artist)
        # pprint(arist_dir)
        name= event.artist.get_label()
        pprint('clicked {0}'.format(name))
        if event.artist.get_markeredgecolor() =='white':
            event.artist.set_markeredgecolor(event.artist.get_markerfacecolor())
        else:
            event.artist.set_markeredgecolor('white')
        self.canvas.draw()


    def check_db(self):
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

if __name__ == '__main__':
    root = tkinter.Tk()
    tkinter.Grid.rowconfigure(root, 0, weight=1)
    tkinter.Grid.columnconfigure(root, 0, weight=1)
    gui = plot_application(root)
    root.mainloop()
