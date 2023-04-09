from pathlib import Path
import threading

from tkinter import *
from tkinter import ttk
from tkinter import font as tkFont
import can
import cantools.database
from definitions import PROJECT_ROOT
import serial

interface = 'pican'
CANUSB_PORT = '/dev/ttyUSB0'
SERIAL_PORT = "/dev/tty.usbserial-AC00QTXJ"
SERIAL_BAUD_RATE = 500000

#import gps frame that's in same folder
import gps_display

WIDTH = 500
HEIGHT = 300
BCK_COLOR = "#381b4d" #dark purple
FG_COLOR = "#ebebeb" #silver

# Displayables
displayables = {"VehicleVelocity": 0.0, 
                "bbox_charge": 0.0, 
                "bbox_avgtemp": 0.0,
                "bbox_maxtemp": 0.0,
                "Output_current": 0.0,
                "secondaryvolt": 0.0,
                "regen_enabled": 0.0,
                "Odometer": 0.0,
                "vehicle_direction": 0.0,
                "Controller_temperature": 0.0
}

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
        self.bbox_charge = StringVar()
        self.bbox_avgtemp = StringVar()
        self.bbox_maxtemp = StringVar()
        self.mppt_current = StringVar()
        self.secondaryvolt = StringVar()
        self.regen_enabled = StringVar()
        self.odometer = StringVar()
        self.vehicle_direction = StringVar()
        self.motorc_temp = StringVar()

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


        #info labels
        #battery box charge
        bbox_charge_label = ttk.Label(self.info_frame, text = "Bbox Charge:", font = info_font)
        bbox_charge_label.grid(column = 0, row = 0, sticky = W)
        self.bbox_charge.set(0)
        bbox_charge_status = ttk.Label(self.info_frame, text = self.bbox_charge, font = info_font)
        bbox_charge_status.grid(column = 1, row = 0, sticky = E)

        #batter box average temp
        bbox_avgtemp_label = ttk.Label(self.info_frame, text = "Bbox Average Temp:", font = info_font)
        bbox_avgtemp_label.grid(column = 0, row = 1, sticky = W)
        self.bbox_avgtemp.set(0)
        bbox_avgtemp_status = ttk.Label(self.info_frame, text = self.bbox_avgtemp, font = info_font)
        bbox_avgtemp_status.grid(column = 1, row = 1, sticky = E)

        #battery box max temp
        bbox_maxtemp_label = ttk.Label(self.info_frame, text = "Bbox Max Temp:", font = info_font)
        bbox_maxtemp_label.grid(column = 0, row = 2, sticky = W)
        self.bbox_maxtemp.set(0)
        bbox_maxtemp_status = ttk.Label(self.info_frame, text = self.bbox_maxtemp, font = info_font)
        bbox_maxtemp_status.grid(column = 1, row = 2, sticky = E)

        #current out from cells
        mppt_current_label = ttk.Label(self.info_frame, text = "Current out from Cells:", font = info_font)
        mppt_current_label.grid(column = 0, row = 3, sticky = W)
        self.mppt_current.set("0")
        mppt_current_status = ttk.Label(self.info_frame, text = self.mppt_current, font = info_font)
        mppt_current_status.grid(column = 1, row = 3, sticky = E)

        #secondary voltage of battery box
        secondaryvolt_label = ttk.Label(self.info_frame, text = "Secondary Voltage of Battery Box:", font = info_font)
        secondaryvolt_label.grid(column = 0, row = 4, sticky = W)
        self.secondaryvolt.set(0)
        secondaryvolt_status = ttk.Label(self.info_frame, text = self.secondaryvolt, font = info_font)
        secondaryvolt_status.grid(column = 1, row = 4, sticky = E)

        #regen enabled?
        regen_enabled_label = ttk.Label(self.info_frame, text = "Regen Enable?", font = info_font)
        regen_enabled_label.grid(column = 0, row = 5, sticky = W)
        self.regen_enabled.set(0)
        regen_enabled_status = ttk.Label(self.info_frame, text = self.regen_enabled, font = info_font)
        regen_enabled_status.grid(column = 1, row = 5, sticky = E)

        #distance traveled
        odometer_label = ttk.Label(self.info_frame, text = "Distance Traveled:", font = info_font)
        odometer_label.grid(column = 0, row = 6, sticky = W)
        self.odometer.set(0)
        odometer_status = ttk.Label(self.info_frame, text = self.odometer, font = info_font)
        odometer_status.grid(column = 1, row = 6, sticky = E)

        #direction of vehicle
        vehicle_direction_label = ttk.Label(self.info_frame, text = "Direction of Vehicle:", font = info_font)
        vehicle_direction_label.grid(column = 0, row = 7, sticky = W)
        self.vehicle_direction.set(0)
        vehicle_direction_status = ttk.Label(self.info_frame, text = self.vehicle_direction, font = info_font)
        vehicle_direction_status.grid(column = 1, row = 7, sticky = E)

        #motor controller temperature
        motorc_temp_label = ttk.Label(self.info_frame, text = "Motor Controller Temperature:", font = info_font)
        motorc_temp_label.grid(column = 0, row = 8, sticky = W)
        self.motorc_temp.set(0)
        motorc_temp_status = ttk.Label(self.info_frame, text = self.motorc_temp, font = info_font)
        motorc_temp_status.grid(column = 1, row = 8, sticky = E)

        
        #set color
        for child in self.info_frame.winfo_children():
            child.configure(background=BCK_COLOR, foreground=FG_COLOR)

        #space out columns
        for ii in range(2):
            self.info_frame.columnconfigure(ii, weight=2)

        self.mainframe.columnconfigure(0, weight=1)

        #space out rows
        for ii in range(9):
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
        self.speed.set(round(displayables["VehicleVelocity"], 3))
        self.bbox_charge.set(round(displayables["bbox_charge"], 3))
        self.bbox_avgtemp.set(round(displayables["bbox_avgtemp"], 3))
        self.bbox_maxtemp.set(round(displayables["bbox_maxtemp"], 3))
        self.mppt_current.set(str(round(displayables["Output_current"], 3)))
        self.secondaryvolt.set(round(displayables["secondaryvolt"], 3))
        self.regen_enabled.set(round(displayables["regen_enabled"], 3))
        self.odometer.set(round(displayables["Odometer"], 3))
        self.vehicle_direction.set(round(displayables["vehicle_direction"], 3))
        self.motorc_temp.set(round(displayables["Controller_temperature"], 3))

        self.after(1000, self.updater)


# Worker function to receive packets off CAN line and
# update displayables
def receiver_worker():
    db = cantools.database.load_file(Path(PROJECT_ROOT).joinpath("resources").joinpath("mppt.dbc"))

    if interface == "canusb":
        with serial.Serial(SERIAL_PORT, SERIAL_BAUD_RATE) as receiver:
            while True:
                raw = receiver.read_until(b';').decode()
                if len(raw) != 23: continue
                raw = raw[1:len(raw) - 1]
                raw = raw.replace('S', '')
                raw = raw.replace('N', '')
                tag = int(raw[0:3], 16)
                data = bytearray.fromhex(raw[3:])
                msg = can.Message(arbitration_id=tag, data=data)

                for k, v in db.decode_message(msg.arbitration_id, msg.data).items():
                    if k in displayables:
                        displayables[k] = v
                print(displayables)        

    elif interface == "pican":
        with can.interface.Bus(channel='can0', bustype='socketcan') as bus:  # type: ignore
            while True:
                msg = bus.recv()
                for k, v in db.decode_message(msg.arbitration_id, msg.data).items():
                    if k in displayables:
                        displayables[k] = v
    else:
        raise Exception('Invalid interface')


def main():
    #if os.environ.get('DISPLAY', '') == '':
    #   os.environ.__setitem__('DISPLAY', ':0.0')

    # start CAN reciever daemon thread
    recd = threading.Thread(target=receiver_worker, daemon=True)
    recd.start()

    # while True:
    #     time.sleep(2)
    #     print(displayables)

    root = CarDisplay()
    root.mainloop()

    
if __name__ == '__main__':
    main()
