import math
import gui
import vts
from image import Image_Bank
from picture_button import Picture_Button
from button_utils import LoopingButton
from micropython import const
import backlight
import gnss
import vbox
import ustruct as us
import os
from sounds import Speaker
import serial

# Constants
RED = const(0xFF0000)
GREEN = const(0x00FF00)
PURPLE = const(0xFF00FF)
ORANGE = const(0xFF8000)
gnss_status = False


antennaA = const(0)
antennaB = const(1)
points = const(2)

Subject = const(0)
Target1 = const(1)
Target2 = const(2)
Target3 = const(3)
# antenna looping button option
antenna_dir = {
    antennaA: ("Antenna A", 1),
    antennaB: ("Antenna B", 2),
    points: ("Points", 3),
}
# vehicle looping button
vehicle_option_dir = {
    Subject: ("Subject", 1),
    Target1: ("Target 1", 2),
    Target2: ("Target 2", 3),
    Target3: ("Target 3", 3),
}

backlight.set(5000)

SubjectContactPoint = bytearray(48)
SubjectVehicleShape_0 = bytearray(256)
SubjectVehicleShape_1 = bytearray(128)
Target1ContactPoint = bytearray(16)
Target1VehicleShape_0 = bytearray(256)
Target1VehicleShape_1 = bytearray(128)
Target2ContactPoint = bytearray(16)
Target2VehicleShape_0 = bytearray(256)
Target2VehicleShape_1 = bytearray(128)
Target3ContactPoint = bytearray(16)
Target3VehicleShape_0 = bytearray(256)
Target3VehicleShape_1 = bytearray(128)

uploaded = 0

# Global variables
class GV:
    x_scale = ["10m"]
    y_scale = ["10m"]
    sats_colour = [gui.DL_COLOR(RED)]
    sats = ["0"]
    lat = ["000.00000"]
    long = ["000.00000"]
    cp_list = []
    antennaAcoords = []
    antennaBcoords = []
    set_button = "Antenna A"
    cp_number = ["0"]
    a_set = False
    point_list = []
    vehicle_option_str = "Subject"
    rtk_warning = [gui.DL_VERTEX_TRANSLATE_X(1000)]
    reset_warning = [gui.DL_VERTEX_TRANSLATE_X(1000)]
    antenna_b = []


class ball_position: # x position information 

    def __init__(self):
        self.mid_lat = 0
        self.mid_long = 0
        self.current_lat = 0
        self.current_long = 0
        self.ball_pos_x = -50 # draws the ball off screen
        self.ball_pos_y = -50

    def mid_vals(self, mid_lat, mid_long): # updates the mid point values
        self.mid_lat = mid_lat
        self.mid_long = mid_long

    def update(self): # updates ball position position
        gui_list[8][0] = gui.DL_VERTEX2F(ball.ball_pos_x - 6, ball.ball_pos_y - 8)
        gui_list[9][0] = gui.DL_VERTEX2F(ball.ball_pos_x + 6, ball.ball_pos_y + 8)
        gui_list[13][0] = gui.DL_VERTEX2F(ball.ball_pos_x + 6, ball.ball_pos_y - 8)
        gui_list[14][0] = gui.DL_VERTEX2F(ball.ball_pos_x - 6, ball.ball_pos_y + 8)

    def update_vals(self, ball_pos_x, ball_pos_y): # moves the ball 
        self.ball_pos_x = ball_pos_x
        self.ball_pos_y = ball_pos_y


class Point:

    def __init__(self):
        self.y_m_list = []
        self.stored_points_colour = [gui.DL_COLOR_RGB(0,0,0xFF)] 
        self.antenna_colour = [gui.DL_COLOR_RGB(150, 0, 0)]
        self.set_points =  [    # creates empty list in gui_list
            [gui.DL_NOP()],
            [gui.DL_NOP()],
            [gui.DL_NOP()],
            [gui.DL_NOP()],
            [gui.DL_NOP()],
            [gui.DL_NOP()],
            [gui.DL_NOP()],
            [gui.DL_NOP()],
            [gui.DL_NOP()],
            [gui.DL_NOP()],
            [gui.DL_NOP()],
            [gui.DL_NOP()],
            [gui.DL_NOP()],
            [gui.DL_NOP()],
            [gui.DL_NOP()],
            [gui.DL_NOP()],
            [gui.DL_NOP()],
            [gui.DL_NOP()],
            [gui.DL_NOP()],
            [gui.DL_NOP()],
            [gui.DL_NOP()],
            [gui.DL_NOP()],
            [gui.DL_NOP()],
            [gui.DL_NOP()],
            [gui.DL_NOP()],
            ]
        self.set_a = [
            [gui.DL_NOP()],
        ]
        self.set_b = [
            [gui.DL_NOP()],
        ]
        self.point_gui_list = [gui.SUBLIST, # creates a point when set is pressed
                        self.stored_points_colour,
                        [gui.DL_POINT_SIZE(8)],
                        [gui.DL_BEGIN(gui.PRIM_POINTS)],
                        self.set_points,
                        [gui.DL_END()],
                        ]
        self.antenna_a_gui = [gui.SUBLIST, # creates antenna A point
                        self.antenna_colour,
                        [gui.DL_POINT_SIZE(10)],
                        [gui.DL_BEGIN(gui.PRIM_POINTS)],
                        self.set_a,
                        [gui.DL_END()],
                        ]
        self.antenna_b_gui =  [gui.SUBLIST, # creates antenna B point
                        self.antenna_colour,
                        [gui.DL_POINT_SIZE(10)],
                        [gui.DL_BEGIN(gui.PRIM_POINTS)],
                        self.set_b,
                        [gui.DL_END()],
                        ]
    #TODO Get "A" and "B" in the middle
    def set_contact_point(self, point, x, y): # Sets contact point and fills the NOP position
        if 0 < point < (len(self.set_points)):
            self.set_points[point][0] = gui.DL_VERTEX2F(x, y)
            return True
        else:
            return False

    def remove_contact_point(self, point): # removes contact point and replaces with NOP 
        if 0 < point < (len(self.set_points)):
            self.set_points[point][0] = gui.DL_NOP()
            return True
        else:
            return False

    def set_stored_point_colour(self, r, g, b):
        self.stored_points_colour[0] = gui.DL_COLOR_RGB(r, g, b)

    def set_antenna_a(self, x, y):
        self.set_a[0] = gui.DL_VERTEX2F(x, y)

    def set_antenna_b(self, x, y):
        self.set_b[0] = gui.DL_VERTEX2F(x, y)

    def delete_antenna_a(self):
        self.set_a[0] = gui.DL_NOP()

    def delete_antenna_b(self):
        self.set_b[0] = gui.DL_NOP()

    def get_gui_list(self):
        return self.point_gui_list

    def get_gui_a(self):
        return self.antenna_a_gui

    def get_gui_b(self):
        return self.antenna_b_gui


class Point_position:
    def __init__(self): # class to obtain all relevant point parameters
        self.point_lat = self.point_lat
        self.point_long = self.point_long
        self.point_x_m = self.point_x_m
        self.point_y_m = self.point_y_m
        self.point_pixel_x = self.point_pixel_x
        self.point_pixel_y = self.point_pixel_y

    def get_point_position(point_lat, point_long, point_x_m, point_y_m, point_pixel_x, point_pixel_y):
        GV.point_list.append([point_lat, point_long, point_x_m, point_y_m, point_pixel_x, point_pixel_y])
    
    def delete_position(self):
        GV.point_list.pop(-1)


class Commands:
    get_seed = b"\x12\x04\x25\x95"
    set_quiet = b"\x07\x06\02\xFF\x9b\x1f"
    set_noise = b"\x07\x06\x02\x00\x85\xef"
    restart_stream = b"\x07\x06\02\x00\x85\xef"
    upload = b'\x04\x08\x00\x17\x18\x30\x7E\xf6'
    upload1 = b'\x04\x08\x00\x17\x48\x00\x46\x1a'
    upload2 = b'\x04\x08\x00\x18\x48\x80\xfb\xa3'
    upload3 = b'\x04\x08\x00\x18\xc8\x10\x63\x82'
    upload4 = b'\x04\x08\x00\x18\xd8\x00\x72\xc0'
    upload5 = b'\x04\x08\x00\x19\x58\x80\xcf\xe0'
    upload6 = b'\x04\x08\x00\x1a\x58\x10\x15\x74'
    upload7 = b'\x04\x08\x00\x1a\x68\x00\x02\xad'
    upload8 = b'\x04\x08\x00\x1b\x68\x80\xa4\x15'
    upload9 = b'\x04\x08\x00\x1b\xe8\x10\x3C\x34'
    upload10 = b'\x04\x08\x00\x1b\xf8\x00\x2D\x76'
    upload11 = b'\x04\x08\x00\x1c\xf8\x80\x39\x6E'
    # b'\x04\x08\x00\x00\x01\x00\x37\xbd' # all 256 bytes
    # b"\x04\x08\x00\x00\x01\x01\x27\x9c" # one byte?
    # b'\x04\x08\x00\x1d\xa8\x04\xd1\xed' # 4 bytes for adas mode
    # b'\x04\x08\x00\x10\xb8\x00\xce\xbb' # start address in v3 (4280) for 256 bytes
    # b'\x04\x08\x00\x17\x18\x30\x7E\xf6' # SubjectContactPoint (5912) for 48 bytes
    # b'\x04\x08\x00\x17\x48\x00\x46\x1a' # SubjectVehicleShape 1 (5960) for 256 bytes
    # b'\x04\x08\x00\x18\x48\x80\xfb\xa3' # SubjectVehicleShape 2 (6216) for 128 bytes
    # b'\x04\x08\x00\x18\xc8\x10\x63\x82' # Target1ContactPoint (6344) for 16 bytes
    # b'\x04\x08\x00\x18\xd8\x00\x72\xc0' # Target1VehicleShape 1 (6360) for 256 bytes
    # b'\x04\x08\x00\x19\x58\x80\xcf\xe0' # Target1VehicleShape 2 (6488) for 128 bytes
    # b'\x04\x08\x00\x1a\x58\x10\x15\x74' # Target2ContactPoint (6744) for 16 bytes
    # b'\x04\x08\x00\x1a\x68\x00\x02\xad' # Target2VehicleShape 1 (6760) for 256 bytes
    # b'\x04\x08\x00\x1b\x68\x80\xa4\x15' # Target2VehicleShape 2 (7016) for 128 bytes
    # b'\x04\x08\x00\x1b\xe8\x10\x3C\x34' # Target3ContactPoint (7144) for 16 bytes
    # b'\x04\x08\x00\x1b\xf8\x00\x2D\x76' # Target3VehicleShape 1 (7160) for 256 bytes
    # b'\x04\x08\x00\x1c\xf8\x80\x39\x6E' # Target3VehicleShape 2 (7416) for 128 bytes

    
def position_calc(): # calculates the position of the ball on the screen
    global x_dist, y_dist
    if GV.a_set == False:
        pass
    else: # converts meters and scale into a pixel position
        x_dist = 400 / int(GV.x_scale[0].replace("m", "")) * (sample.x_m) # 400 is the number of pixels in the x direction
        y_dist = 420 / int(GV.y_scale[0].replace("m", "")) * (sample.y_m) # 420 is the number of pixels in the y direction
        ball.update_vals(200 + x_dist, 270 + y_dist) # updates ball values by adding the offsets to the centre of the graph
        ball.update()


def gnss_callback():
    # gets and processes GNSS samples
    global sample
    while vbox.samples_pending():
        sample = vbox.get_sample_hp()
        set_sats_status(gnss_status)
        GV.sats[0] = "{}".format(sample.sats_used)
        if sample.sats_used > 3:
            GV.lat[0] = "{:04.5f}".format((sample.lat_degE7)/10000000)
            GV.long[0] = "{:04.5f}".format((sample.lng_degE7)/10000000)
            if sample.fix_type == vbox.VBOX_FIXTYPE_RTK_FIXED:
                if ball.mid_lat == 0 and ball.mid_long == 0:
                    ball.mid_vals(((sample.lat_degE7)/10000000), ((sample.lng_degE7)/10000000))
                    ball.update_vals(200, 270)
                    ball.update()
                else:
                    position_calc()
        if sample.fix_type == vbox.VBOX_FIXTYPE_RTK_FIXED:
            GV.rtk_warning[0] = gui.DL_VERTEX_TRANSLATE_X(800)


def create_checksum(msg):
    Polynomial = 0x45DC
    CRC = 0
    for byte in range(len(msg)):
        CRC = CRC ^ (msg[byte] << 8)
        CRC = CRC % 0x010000
        for _ in range(8):
            if ((CRC & 0x8000) == 0x8000):
                CRC = CRC << 1
                CRC = CRC ^ Polynomial
            else:
                CRC = CRC << 1
        CRC = CRC % 0x010000
    # return ((CRC >> 8) & 0xFF), (CRC & 0xFF) # Returns as two seperate bytes
    return CRC # Returns as one 16bit integer


def serial_callback():
    vts.delay_ms(100)
    msgIn = serial.read(serial.available())
    if msgIn[0:2] == b'\xff\x01' and len(msgIn) == 6:
        crc_int = create_checksum(msgIn[2:4])
        crc_bytes = crc_int.to_bytes(2, 'big')
        unlock_without_crc = b'\x13\x06' + crc_bytes + bytearray(2)
        unlock_bytearray = bytearray(unlock_without_crc)
        vbox.rlcrc(unlock_bytearray, 4)
        serial.write(bytes(unlock_bytearray))
    # elif b'\xff\x01\x13\xde\xff\x01' in msgIn[0:6]:
    #     print(msgIn[6:])
    else:
        print(msgIn[6:len(msgIn) - 2])
        if vts.sd_present() == True:
            f.write(bytes(msgIn[6:len(msgIn) - 2]))
            if uploaded == 11:
                f.close()
            


def set_cp_number(btn):
    GV.cp_number = btn.current


def vehicle_option(btn):
    if btn.current == "Subject":
        GV.vehicle_option_str = "Subject"
    elif btn.current == "Target 1":
        GV.vehicle_option_str = "Target 1"
    elif btn.current == "Target 2":
        GV.vehicle_option_str = "Target 2"
    elif btn.current == "Target 3":
        GV.vehicle_option_str = "Target 3"


def set_antenna_or_cp(btn):
    if btn.current == "Points":
        GV.set_button = "Points"
    elif btn.current == "Antenna A":
        GV.set_button = "Antenna A"
    elif btn.current == "Antenna B":
        GV.set_button = "Antenna B"


def coldstart_cb(l):
    gnss.command(b'\xb5\x62\x06\x04\x04\x00\xff\xff\x02\x00\x0e\x61')
    speaker.play_sound(2)
    GV.lat[0] = "000.00000"
    GV.long[0] = "000.00000"
    ball.update_vals(-50, -50)
    ball.update()
    vts.leds(* [0, 0, 75] * 4)
    vts.delay_ms(1000)
    vts.leds(* [0, 0, 0] * 4)


def pass_cb(l):
    pass


def centre_graph_cb(l):
    pass


def no_reset(l):
    GV.reset_warning[0] = gui.DL_VERTEX_TRANSLATE_X(1000)


def reset_screen(l):
    GV.reset_warning[0] = gui.DL_VERTEX_TRANSLATE_X(0)
    

def reset_cp(l): # completely resets all of the check points and antennas
    vts.leds(0, 20, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0)
    vts.delay_ms(500)
    vts.leds(0, 20, 0, 0, 20, 0, 0, 0, 0, 0, 0, 0)
    vts.delay_ms(500)
    vts.leds(0, 20, 0, 0, 20, 0, 0, 20, 0, 0, 0, 0)
    vts.delay_ms(500)
    vts.leds(0, 20, 0, 0, 20, 0, 0, 20, 0, 0, 20, 0)
    vts.delay_ms(500)
    vts.leds(* [0] * 12)
    for x in range(25):
        point.remove_contact_point(x)
    point.delete_antenna_a()
    point.delete_antenna_b()
    GV.cp_number[0] = '0'
    GV.cp_list = []
    GV.antennaAcoords = []
    GV.antennaBcoords = []
    GV.point_list = []
    GV.antenna_b = []
    ball.mid_vals(0, 0)
    GV.a_set = False
    speaker.play_sound(2)
    vts.delay_ms(1000)
    GV.reset_warning[0] = gui.DL_VERTEX_TRANSLATE_X(1000)


def get_picture_button(name):
    try:
        pb = next(pb for pb in buttons if pb.name == name)
    except:
        pb = None
    return pb


def wrap_callback(callback):
    def cb(*args, **kwargs):
        callback(*args, **kwargs)
    return cb


def create_buttons(*args): # creates picture buttons from imported picutres
    global buttons
    buttons = []
    if 'Reset' in args:
        buttons.append(Picture_Button(700, -8, bank.get('Reset'), 'Reset', reset_screen))
    if 'GNSS' in args:
        buttons.append(Picture_Button(10, 5, bank.get('GNSS'), 'GNSS', pass_cb))
    if 'Centre' in args:
        buttons.append(Picture_Button(90, 5, bank.get('Centre'), 'Centre', centre_graph_cb))

    button_cbs_l = []
    button_icons_l = [gui.DL_BEGIN(gui.PRIM_BITMAPS)]
    for i, button in enumerate(buttons):
        button_cb_l = [
            gui.PARAM_TAG_REGISTER,
            wrap_callback(button.get_callback()),
        ]
        button_cb_l.append(button.name)
        button_cbs_l.append(button_cb_l)
        button.set_gui_l_index(len(button_icons_l))
        button_icons_l.extend(button.generate_gui_l(i + 1))
    return button_cbs_l, button_icons_l


def init_buttons(): # dictates where the buttons will appear
    global button_layouts
    button_layouts = {}
    button_layouts['main'] = create_buttons('Reset', 'GNSS', 'Centre')


def button_options():
    global button_layouts
    gui_buttons = []
    gui_buttons.extend(button_layouts['main'][0])
    gui_buttons.append(button_layouts['main'][1])

    return gui_buttons


def set_gnss_btn_state(state): # changes the satellite image colour depending on fix type
    if state:
        get_picture_button('GNSS').set_colour((0, 255, 0))
        if sample.fix_type == vbox.VBOX_FIXTYPE_RTK_FIXED:
            get_picture_button('GNSS').set_colour((255, 0, 255))
        elif sample.fix_type == vbox.VBOX_FIXTYPE_RTK_FLOAT:
            get_picture_button('GNSS').set_colour((255, 128, 0))
    else:
        get_picture_button('GNSS').set_colour((255, 0,  0))


def set_sats_status(state): # sets satellite counter colour depending on fix type
    global gnss_status
    if sample.sats_used > 3:
        gnss_status = True
        GV.sats_colour[0] = gui.DL_COLOR(GREEN)
        if sample.fix_type == vbox.VBOX_FIXTYPE_RTK_FIXED:
            GV.sats_colour[0] = gui.DL_COLOR(PURPLE)
        elif sample.fix_type == vbox.VBOX_FIXTYPE_RTK_FLOAT:
            GV.sats_colour[0] = gui.DL_COLOR(ORANGE)
    else:
        GV.sats_colour[0] = gui.DL_COLOR(RED)
        gnss_status = False


def set_cp(l): # sets contact point when 'set' is pressed 
    global sample
    if sample.fix_type == vbox.VBOX_FIXTYPE_RTK_FIXED: # ensures there are RTK corrections
        if GV.a_set == True: # ensures antenna A is set first
            if GV.set_button == "Points":
                if len(GV.cp_list) < 24:
                    GV.cp_list.append((math.radians((sample.lat_degE7)/10000000), math.radians((sample.lng_degE7)/10000000), sample.alt_msl_m)) # appends relevant contact point data to a list
                    GV.cp_number[0] = str(len(GV.cp_list)) # updates number of contact points
                    point.set_contact_point((len(GV.cp_list)), ball.ball_pos_x, ball.ball_pos_y) # sets pixel x and y position
                    Point_position.get_point_position((sample.lat_degE7)/10000000, (sample.lng_degE7)/10000000, sample.x_m, sample.y_m, ball.ball_pos_x, ball.ball_pos_y) # gets relevant information for that point
                    vts.leds(* [0, 20, 0] * 4)
                    vts.delay_ms(70)
                    vts.leds(* [0] * 12)
                    speaker.play_sound(4)
            elif GV.set_button == "Antenna B":
                if len(GV.antennaBcoords) < 1:
                    GV.antennaBcoords.append((math.radians((sample.lat_degE7)/10000000), math.radians((sample.lng_degE7)/10000000), sample.alt_msl_m))
                    point.set_antenna_b(ball.ball_pos_x, ball.ball_pos_y)
                    GV.antenna_b = [(sample.x_m, sample.y_m)]
                    vts.leds(* [0, 20, 0] * 4)
                    vts.delay_ms(70)
                    vts.leds(* [0] * 12)
                    speaker.play_sound(4)
        else:
            if GV.set_button == "Antenna A":
                if len(GV.antennaAcoords) < 1:
                    GV.a_set = True
                    GV.antennaAcoords.append((math.radians((sample.lat_degE7)/10000000), math.radians((sample.lng_degE7)/10000000), sample.alt_msl_m))
                    vbox.set_basepoint()
                    point.set_antenna_a(ball.ball_pos_x, ball.ball_pos_y)
                    vts.leds(* [0, 20, 0] * 4)
                    vts.delay_ms(70)
                    vts.leds(* [0] * 12)
                    speaker.play_sound(4)
            else:
                pass
    else: 
        speaker.play_sound(1)
        GV.rtk_warning[0] = gui.DL_VERTEX_TRANSLATE_X(0)


def delete_last_point(l): # deletes the last point depending on the what is being set
    if GV.set_button == "Points":
        if len(GV.cp_list) > 0:
            point.remove_contact_point(len(GV.cp_list))
            GV.cp_list.pop(-1)
            GV.cp_number[0] = str(int(GV.cp_number[0]) - 1)
            Point_position.delete_position(GV.point_list)
            vts.leds(* [20, 7, 0] * 4)
            vts.delay_ms(70)
            vts.leds(* [0] * 12)
            speaker.play_sound(3)
    elif GV.set_button == "Antenna A":
        if len(GV.antennaAcoords) == 1:
            GV.antennaAcoords.pop(-1)
            point.delete_antenna_a()
            vts.leds(* [20, 7, 0] * 4)
            vts.delay_ms(70)
            vts.leds(* [0] * 12)
            speaker.play_sound(3)
    elif GV.set_button == "Antenna B":
        if len(GV.antennaBcoords) == 1:
            GV.antennaBcoords.pop(-1)
            point.delete_antenna_b()
            vts.leds(* [20, 7, 0] * 4)
            vts.delay_ms(70)
            vts.leds(* [0] * 12)
            speaker.play_sound(3)


def zoom_out(l): # zooms in around antenna A
    if int(GV.x_scale[0].replace("m", "")) < 15:
        x_scale_int = int(GV.x_scale[0].replace("m", ""))
        y_scale_int = int(GV.y_scale[0].replace("m", ""))
        GV.x_scale[0] = (str(x_scale_int + 1) + "m")
        GV.y_scale[0] = (str(y_scale_int + 1) + "m")
        for x in range(len(GV.point_list)):
            pixel_change_x = (400 / int(GV.x_scale[0].replace("m", "")) * float(GV.point_list[x][2])) + 200
            pixel_change_y = (420 / int(GV.y_scale[0].replace("m", "")) * float(GV.point_list[x][3])) + 270         
            point.set_contact_point(x + 1, pixel_change_x, pixel_change_y)
            GV.point_list[x][4] = pixel_change_x
            GV.point_list[x][5] = pixel_change_y
        for vals in range(len(GV.antenna_b)):
            pixel_change_x = (400 / int(GV.x_scale[0].replace("m", "")) * float(GV.antenna_b[vals][0])) + 200
            pixel_change_y = (420 / int(GV.y_scale[0].replace("m", "")) * float(GV.antenna_b[vals][1])) + 270
            point.set_antenna_b(pixel_change_x, pixel_change_y)
    else:
        pass


def zoom_in(l): # zooms out around antenna A
    if int(GV.x_scale[0].replace("m", "")) > 1:
        x_scale_int = int(GV.x_scale[0].replace("m", ""))
        y_scale_int = int(GV.y_scale[0].replace("m", ""))
        GV.x_scale[0] = (str(x_scale_int - 1) + "m")
        GV.y_scale[0] = (str(y_scale_int - 1) + "m")
        for x in range(len(GV.point_list)):
            pixel_change_x = (400 / int(GV.x_scale[0].replace("m", "")) * float(GV.point_list[x][2])) + 200
            pixel_change_y = (420 / int(GV.y_scale[0].replace("m", "")) * float(GV.point_list[x][3])) + 270
            point.set_contact_point(x + 1, pixel_change_x, pixel_change_y)
            GV.point_list[x][4] = pixel_change_x
            GV.point_list[x][5] = pixel_change_y
        for vals in range(len(GV.antenna_b)):
            pixel_change_x = (400 / int(GV.x_scale[0].replace("m", "")) * float(GV.antenna_b[vals][0])) + 200
            pixel_change_y = (420 / int(GV.y_scale[0].replace("m", "")) * float(GV.antenna_b[vals][1])) + 270
            point.set_antenna_b(pixel_change_x, pixel_change_y)
    else:
        pass


def save(l):
    # saves the selected role to the units SD card in a VBC file format
    if vts.sd_present() == True:
        file_struct = 0
        if GV.vehicle_option_str == "Subject":
            file_name = "Subject.VBC"
            file_struct |= (1 << 5)
        elif GV.vehicle_option_str == "Target 1":
            file_name = "Target_1.VBC"
            file_struct |= (1 << 6)
        elif GV.vehicle_option_str == "Target 2":
            file_name = "Target_2.VBC"
            file_struct |= (1 << 7)
        elif GV.vehicle_option_str == "Target 3":
            file_name = "Target_3.VBC"
            file_struct |= (1 << 9)
        f = open(file_name, 'wb')
        f.write(b"RLVB3iCFG")
        f.write(us.pack('H', 0x55AA))
        f.write(us.pack('>H', 0))
        f.write(us.pack('>I', file_struct))
        f.write(us.pack('>I', 5))
        f.write(us.pack('>H', 22))
        f.write(b'Vehicle contact points')
        f.write(us.pack('>H', 1080))
        f.write(us.pack('>I', 0xCCCCCCCC))
        f.write(us.pack('>I', len(GV.cp_list)))
        for vals in GV.antennaAcoords:
            for i in vals:
                f.write(us.pack('>d', i))
        f.write(us.pack('>f', -6500000.00))
        f.write(us.pack('>f', -6500000.00))
        f.write(us.pack('>f', -6500000.00))
        f.write(us.pack('>f', -1.0))        
        f.write(us.pack('>f', -6500000.00))
        f.write(us.pack('>f', -6500000.00))
        f.write(us.pack('>f', -6500000.00))
        f.write(us.pack('>f', -1.0))
        for vals in GV.antennaAcoords:
            for i in vals:
                f.write(us.pack('>d', i))
        for vals in GV.antennaBcoords:
            for i in vals:
                f.write(us.pack('>d', i))
        for vals in GV.cp_list:
            for i in vals:
                f.write(us.pack('>d', i))
        for i in range(24 - len(GV.cp_list)):
            f.write(us.pack('>f', -6500000.00))
            f.write(us.pack('>f', -6500000.00))
            f.write(us.pack('>f', -1.0))
        for i in range(24):
            f.write(us.pack('>f', -6500000.00))
            f.write(us.pack('>f', -6500000.00))
            f.write(us.pack('>f', -6500000.00))
            f.write(us.pack('>f', -1.0))
        f.close()
        # TODO Make happy sound
        speaker.play_sound(0)
    else:
        speaker.play_sound(1)


def upload_points(l):
    global uploaded, f
    f = open("read_file", 'wb')
    print("set quiet")
    serial.write(Commands.set_quiet)
    serial_callback()
    print("get seed")
    serial.write(Commands.get_seed)
    serial_callback()
    print("upload")
    serial.write(bytes(Commands.upload))
    serial_callback()
    serial.write(bytes(Commands.upload1))
    serial_callback()
    serial.write(bytes(Commands.upload2))
    serial_callback()
    serial.write(bytes(Commands.upload3))
    serial_callback()
    serial.write(bytes(Commands.upload4))
    serial_callback()
    serial.write(bytes(Commands.upload5))
    serial_callback()
    serial.write(bytes(Commands.upload6))
    serial_callback()
    serial.write(bytes(Commands.upload7))
    serial_callback()
    serial.write(bytes(Commands.upload8))
    serial_callback()
    serial.write(bytes(Commands.upload9))
    serial_callback()
    serial.write(bytes(Commands.upload10))
    serial_callback()
    serial.write(bytes(Commands.upload11))
    uploaded = 11
    serial_callback()
    

    # serial.write(Commands.set_noise)


def redraw_cb(b):
    ball.update()
    gui.redraw()


def vsync_cb(b):
    global gnss_status
    set_gnss_btn_state(gnss_status)
    gui.redraw()


def main_screen(): # display list
    global gui_list
    gui_list = [
        [gui.EVT_VSYNC, vsync_cb],
        [gui.EVT_REDRAW, redraw_cb],
        [gui.DL_CLEAR_COLOR_RGB(255, 255, 255)],
        [gui.DL_SCISSOR_SIZE(400, 420)],
        [gui.DL_SCISSOR_XY(0, 61)],
        [gui.DL_COLOR_RGB(0, 0, 0)],
        [gui.DL_LINE_WIDTH(1.5)],
        [gui.DL_BEGIN(gui.PRIM_LINE_STRIP)],
        [gui.DL_VERTEX2F(ball.ball_pos_x - 6, ball.ball_pos_y - 8)],
        [gui.DL_VERTEX2F(ball.ball_pos_x + 6, ball.ball_pos_y + 8)],
        [gui.DL_END()],
        [gui.DL_LINE_WIDTH(1.5)],
        [gui.DL_BEGIN(gui.PRIM_LINE_STRIP)],
        [gui.DL_VERTEX2F(ball.ball_pos_x + 6, ball.ball_pos_y - 8)],
        [gui.DL_VERTEX2F(ball.ball_pos_x - 6, ball.ball_pos_y + 8)],
        [gui.DL_END()],
        ] 
    gui_list.append(point.get_gui_list())
    gui_list.append(point.get_gui_a())
    gui_list.append(point.get_gui_b())
    gui_list.extend([
        [gui.DL_CLEAR_COLOR_RGB(255, 255, 255)],
        [gui.DL_SCISSOR_SIZE(800, 480)],
        [gui.DL_SCISSOR_XY(0, 0)],
        [gui.PARAM_CLRCOLOR, gui.RGB(255, 255, 255)],
        [gui.DL_COLOR_RGB(0, 36, 64)],
        [gui.PRIM_RECTS, [
            [gui.DL_VERTEX2F(0, 0)],
            [gui.DL_VERTEX2F(800, 60)],
        ]],
        [gui.DL_COLOR_RGB(255, 255, 255)],
        [gui.CTRL_TEXT, 400, 0, 32, gui.OPT_CENTERX,'Contact Point Setter'],
        [gui.DL_COLOR_RGB(0, 0, 0)],
        [gui.PRIM_LINE_STRIP, [
            gui.DL_LINE_WIDTH(1.5),
            gui.DL_VERTEX2F(0, 60),
            gui.DL_VERTEX2F(800, 60),
        ]],
        [gui.PRIM_LINE_STRIP, [
            gui.DL_LINE_WIDTH(1.5),
            gui.DL_VERTEX2F(400, 60),
            gui.DL_VERTEX2F(400, 480),
        ]],
        GV.sats_colour,
        [gui.CTRL_TEXT, 55, 35, 23, gui.OPT_CENTERX, GV.sats],
        [gui.DL_COLOR_RGB(0, 0, 0)],
        [gui.CTRL_TEXT, 322, 65, 28, gui.OPT_CENTERX, GV.x_scale],
        [gui.CTRL_TEXT, 375, 65, 28, gui.OPT_CENTERX, GV.y_scale],
        [gui.CTRL_TEXT, 350, 65, 28, gui.OPT_CENTERX, "x"],
        [gui.CTRL_TEXT, 5, 440, 27, 0, 'Latitude:'],
        [gui.CTRL_TEXT, 100, 440, 27, 0, GV.lat],
        [gui.CTRL_TEXT, 5, 460, 27, 0, 'Longitude:'],
        [gui.CTRL_TEXT, 100, 460, 27, 0, GV.long],
        [gui.CTRL_TEXT, 5, 65, 28, 0, "Points set:"],
        [gui.CTRL_TEXT, 115, 66, 28, 0, GV.cp_number],
        [gui.CTRL_TEXT, 700, 370, 30, gui.OPT_CENTERX, 'Set point'],
        [gui.CTRL_TEXT, 500, 370, 30, gui.OPT_CENTERX, 'Zoom'],
        [gui.CTRL_TEXT, 700, 270, 30, gui.OPT_CENTERX, 'To set'],
        [gui.CTRL_TEXT, 500, 270, 30, gui.OPT_CENTERX, 'Delete last'],
        [gui.CTRL_TEXT, 500, 170, 30, gui.OPT_CENTERX, 'Save to SD'],
        [gui.CTRL_TEXT, 700, 170, 30, gui.OPT_CENTERX, 'Serial upload'],
        [gui.CTRL_TEXT, 500, 70, 30, gui.OPT_CENTERX, 'Coldstart'],
        [gui.CTRL_TEXT, 700, 70, 30, gui.OPT_CENTERX, 'Submode'],
    ])
    gui_list.extend(button_options())
    gui_list.extend([
        [gui.DL_COLOR_RGB(255, 255, 255)],
        antenna_or_cp_button(),
        subject_or_target(),
        [gui.CTRL_FLATBUTTON, 425, 110, 160, 60, 30, 'Coldstart', coldstart_cb],
        [gui.CTRL_FLATBUTTON, 620, 410, 160, 60, 30, 'Set', set_cp],
        [gui.CTRL_FLATBUTTON, 510, 410, 75, 60, 30, '+', zoom_in],
        [gui.CTRL_FLATBUTTON, 425, 410, 75, 60, 30, '-', zoom_out],
        [gui.CTRL_FLATBUTTON, 425, 310, 160, 60, 30, 'Delete', delete_last_point],
        [gui.CTRL_FLATBUTTON, 425, 210, 160, 60, 30, 'Save', save],
        [gui.DL_COLOR_RGB(100, 100, 100)],
        [gui.CTRL_FLATBUTTON, 620, 210, 160, 60, 30, 'Upload', upload_points],
        GV.rtk_warning,
        [gui.DL_COLOR_RGB(255, 0, 0)],
        [gui.CTRL_TEXT, 200, 220, 32, gui.OPT_CENTERX,'RTK Required'],
        [gui.DL_VERTEX_TRANSLATE_X(0)],
        GV.reset_warning,
        [gui.DL_COLOR_A(230)],
        [gui.DL_COLOR_RGB(255, 255, 255)],
        [gui.PRIM_RECTS, [
            [gui.DL_VERTEX2F(0, 0)],
            [gui.DL_VERTEX2F(800, 480)],
        ]],
        [gui.DL_CLEAR_COLOR_A(0)],
        [gui.DL_COLOR_RGB(255, 0, 0)],
        [gui.CTRL_TEXT, 400, 120, 32, gui.OPT_CENTERX, 'Do you want to reset'],
        [gui.CTRL_TEXT, 400, 170, 32, gui.OPT_CENTERX, 'all contact points?'],
        [gui.DL_COLOR_RGB(255, 255, 255)],
        [gui.CTRL_BUTTON, 230, 270, 160, 60, 30, 'Yes', reset_cp],
        [gui.CTRL_BUTTON, 430, 270, 160, 60, 30, 'No', no_reset],
        [gui.DL_VERTEX_TRANSLATE_X(0)],
    ])
    gui.show(gui_list)


def main():
    global bank, antenna_or_cp_button, ball, point, subject_or_target, speaker
    antenna_or_cp_button = LoopingButton(620, 310, 160, 60, [x[0] for x in antenna_dir.values()], 30, set_antenna_or_cp)
    subject_or_target = LoopingButton(620, 110, 160, 60, [x[0] for x in vehicle_option_dir.values()], 30, vehicle_option)
    ball = ball_position()
    point = Point()
    speaker = Speaker(255)
    path = os.getcwd() + '/'
    bank = Image_Bank((
        (path + '/icon-reset.png', 'Reset'),
        (path + '/icons8-gnss-50.png', 'GNSS'),
        (path + '/centre_icon.png', 'Centre')
    ))
    init_buttons()
    main_screen()
    while (gnss.init_status() > 0):
        pass
    try:
        vbox.init(vbox.VBOX_SRC_GNSS_BASIC)
    except Exception as e:
        if str(e) == "VBox source already configured":
            pass
        else:
            print(e)
    while vbox.samples_pending():
        _ = vbox.get_sample_hp()
    serial.open(115200)
    serial.set_callback(serial_callback)
    vbox.set_new_data_callback(gnss_callback)
    # vts.config({'serialConn': 1}) # Connect Serial port 1 directly to GNSS engine port
    # vbox.cfg_gnss({'UART2 Output': [('NMEA', 'GGA', 5)]}) # Enable GGA message output for NTRIP
    # vbox.cfg_gnss({'DGPS Baudrate':115200}) # Set RTK Baud rate to 115200 - May need settings option in future

main()