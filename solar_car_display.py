#imports
from tkinter import *
from tkinter import ttk
from tkinter import font as tkFont
import threading
from can_modules.receiver import Receiver
import time
import pkg_resources, os

CANUSB_PORT = '/dev/ttyUSB0'

#import gps frame that's in same folder
import gps_display

WIDTH = 500
HEIGHT = 300
BCK_COLOR = "#381b4d" #dark purple
FG_COLOR = "#ebebeb" #silver

def getTags(tag_filename):
    tag_dict = {}
    # Open and read the file.
    filename = pkg_resources.resource_filename(
        __name__,
        os.path.join('resources', tag_filename))

    with open(filename) as f:
        contents = f.readlines()
        tags = list(map(lambda d:d.replace('\n', ''), contents))
        
        for tag in tags:
            tag_dict[tag] = 0.0
        
        return tag_dict

# CAN names to their values, global because it is accessed by multiple
# threads. Initialized with the names for the values we choose to display.
# For now these are dummy values.
displayables = getTags('mc_tags.txt')
print(displayables)

class CarDisplay(Tk):
    def __init__(self, *args, **kwargs):
        super().__init__()
        self.title("NU Solar Car")
        self._frame = None
        self.switchFrame(HomeFrame)
        self.configure(background=BCK_COLOR, padx=15, pady=15)

        #Fullscreen
        self.fullScreen = True
        self.attributes("-fullscreen", self.fullScreen)
        self.bind('<Escape>', self.toggleFullscreen)

        #set center screen window with following coordinates
        #self is tk.Tk
        self.MyLeftPos = (self.winfo_screenwidth() - 500) / 2
        self.myTopPos = (self.winfo_screenheight() - 300) / 2
        self.geometry( "%dx%d+%d+%d" % (WIDTH, HEIGHT, self.MyLeftPos, self.myTopPos))

        #full screen button
        self.is_full = StringVar()
        self.is_full.set("Minimize") #initial text
        fullscreen_btn = Button(self, textvariable=self.is_full,
            command = self.toggleFullscreen, font=("Helvetica", 15), height=2)
        fullscreen_btn.pack(side=TOP, anchor=NW)

    #for toggling full screen with esc
    def toggleFullscreen(self, *args):
        self.fullScreen = not self.fullScreen
        self.attributes("-fullscreen", self.fullScreen)

        #set button text
        if self.fullScreen == True:
            self.is_full.set("Minimize")
        else:
            self.is_full.set("Full Screen")

        #center window
        self.geometry( "%dx%d+%d+%d" % (WIDTH, HEIGHT, self.MyLeftPos, self.myTopPos))

    #when gps button clicked, change frame
    def switchFrame(self, frame_class):
        new_frame = frame_class(self)
        if self._frame is not None:
            self._frame.destroy()
        self._frame = new_frame
        self._frame.configure(background=BCK_COLOR)
        self._frame.pack(side=BOTTOM, expand=True, fill=BOTH)


class HomeFrame(Frame):
    def __init__(self, parent):
        Frame.__init__(self, parent)
        parent.configure(background=BCK_COLOR)
        #all stringvars
        self.speed = StringVar()
        self.errors = StringVar()
        self.can_on = StringVar()
        self.current = StringVar()
        self.voltage = StringVar()
        self.lowestV = StringVar()

        self.create_frames(parent)
        self.updater()


    def create_frames(self, parent):
        #frame that shows the velocity and buttons
        self.i = 0
        self.mainframe = Frame(self, bg=BCK_COLOR)

        #frame with all the deets
        self.info_frame = Frame(self, bg=BCK_COLOR)

        #font styles
        info_font = ("Helvetica", 20, "bold")
        vel_font = ("Helvetica", 160, "bold", "italic")
        gps_font = ("Helvetica", 20, "bold")

        #velocity label
        #self.speed = StringVar()
        self.speed.set("0")
        speed_label = ttk.Label(self.mainframe, textvariable=self.speed,
            font=vel_font, background=BCK_COLOR, foreground=FG_COLOR)
        speed_label.grid(column=0, row=0, sticky=S)

        #mph label
        units_label = ttk.Label(self.mainframe, text="MPH", font=("Helvetica", 30, "bold", "italic"),
            background=BCK_COLOR, foreground=FG_COLOR)
        units_label.grid(column=0, row=1, sticky=N, padx=(0, 300))

        #gps button
        gps_btn = Button(self.mainframe, text="GPS", font=gps_font, width=10, height = 2,
            command= lambda : parent.switchFrame(gps_display.gps_display))
        gps_btn.grid(column=0, row=2, sticky=SW)


        #info labels
        error_label = ttk.Label(self.info_frame, text="Error Status", font=info_font)
        error_label.grid(column=0, row=0, sticky=W)
        #self.errors = StringVar()
        self.errors.set("No active errors")
        error_status = ttk.Label(self.info_frame, textvariable=self.errors, font=info_font)
        error_status.grid(column=1, row=0, sticky=E)

        can_label = ttk.Label(self.info_frame, text="CAN Status", font=info_font)
        can_label.grid(column=0, row=1, sticky=W)
        #self.can_on = StringVar()
        self.can_on.set("Connected")
        can_status = ttk.Label(self.info_frame, textvariable=self.can_on, font=info_font)
        can_status.grid(column=1, row=1, sticky=E)

        current_label = ttk.Label(self.info_frame, text="Main Current (A)", font=info_font)
        current_label.grid(column=0, row=2, sticky=W)
        #self.current = StringVar()
        self.current.set(0)
        can_status = ttk.Label(self.info_frame, textvariable=self.current, font=info_font)
        can_status.grid(column=1, row=2, sticky=E)

        voltage_label = ttk.Label(self.info_frame, text="Main Voltage (V)", font=info_font)
        voltage_label.grid(column=0, row=3, sticky=W)
        #self.voltage = StringVar()
        self.voltage.set(0)
        voltage_status = ttk.Label(self.info_frame, textvariable=self.voltage, font=info_font)
        voltage_status.grid(column=1, row=3, sticky=E)

        lowestV_label = ttk.Label(self.info_frame, text="Lowest Voltage (V)", font=info_font)
        lowestV_label.grid(column=0, row=4, sticky=W)
        #self.lowestV = StringVar()
        self.lowestV.set(0)
        lowestV_status = ttk.Label(self.info_frame, textvariable=self.lowestV, font=info_font)
        lowestV_status.grid(column=1, row=4, sticky=E)

        #set color
        for child in self.info_frame.winfo_children():
            child.configure(background=BCK_COLOR, foreground=FG_COLOR)

        #space out columns
        for ii in range(2):
            self.info_frame.columnconfigure(ii, weight=2)

        self.mainframe.columnconfigure(0, weight=1)

        #space out rows
        for ii in range(5):
            self.info_frame.rowconfigure(ii, weight=1)

        self.mainframe.rowconfigure(0, weight=5) #make velocity box biggest
        self.mainframe.rowconfigure(1, weight=2) #make mph second biggest
        self.mainframe.rowconfigure(2, weight=1) #button is smallest

        #pack statements
        #expand - add extra available space
        #padx = (left, right)
        self.mainframe.pack(expand=True, fill=BOTH, side=LEFT)
        self.info_frame.pack(expand=False, fill=BOTH, side=RIGHT, padx=(0, 10))


    def updater(self):
        if 'MTMP' in displayables:
            self.speed.set(round(displayables['MTMP'], 3))
        
        if 'BVOL' in displayables:
            self.voltage.set(round(displayables['BVOL'], 3))
        
        if 'EFLA' in displayables and displayables['EFLA'] != 0:
            self.errors.set('Active errors!')
        else:
            self.errors.set('No active errors')
        
        self.after(1000, self.updater)


# Worker function to receive packets off CAN line and
# update displayables
def receiver_worker():
    r = Receiver(serial_port=CANUSB_PORT)
    for item in r.get_packets():
        if item['Tag'] in displayables:
            displayables[item['Tag']] = item['data']

def receiver_worker_from_file():
    r = Receiver(serial_port=CANUSB_PORT)
    filename = "example-data/collected_cleaned.txt"
    for item in r.get_packets_from_file(filename):
        if item['Tag'] in displayables:
            displayables[item['Tag']] = item['data']
            print(displayables)



def main():
    #if os.environ.get('DISPLAY', '') == '':
    #   os.environ.__setitem__('DISPLAY', ':0.0')

    # start CAN reciever daemon thread
    recd = threading.Thread(target=receiver_worker_from_file, daemon=True)
    recd.start()

    # while True:
    #     time.sleep(2)
    #     print(displayables)

    root = CarDisplay()
    root.mainloop()

if __name__ == '__main__':
    main()
