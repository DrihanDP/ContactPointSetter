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
# Global variables
class GV:
    x_scale = ["6m"]
    y_scale = ["6m"]
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
    rtk_warning = [gui.DL_VERTEX_TRANSLATE_X(800)]
    antenna_b = []

class ball_position: # ball position information 

    def __init__(self):
        self.mid_lat = 0
        self.mid_long = 0
        self.current_lat = 0
        self.current_long = 0
        self.ball_pos_x = -50 # draws the bal off screen
        self.ball_pos_y = -50

    def mid_vals(self, mid_lat, mid_long): # updates the mid point values
        self.mid_lat = mid_lat
        self.mid_long = mid_long

    def update(self): # updates ball position position
        gui_list[8][0] = gui.DL_VERTEX2F(ball.ball_pos_x, ball.ball_pos_y)

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
    global sample
    while vbox.samples_pending():
        sample = vbox.get_sample_hp()
        set_sats_status(gnss_status)
        GV.sats[0] = "{}".format(sample.sats_used)
        if sample.sats_used > 3:
            GV.lat[0] = "{:04.5f}".format((sample.lat_degE7)/10000000)
            GV.long[0] = "{:04.5f}".format((sample.lng_degE7)/10000000)
            if sample.fix_type == vbox.VBOX_FIXTYPE_RTK_FIXED: #TODO change to rtk fix
                if ball.mid_lat == 0 and ball.mid_long == 0:
                    ball.mid_vals(((sample.lat_degE7)/10000000), ((sample.lng_degE7)/10000000))
                    ball.update_vals(200, 270)
                    ball.update()
                else:
                    position_calc()
        if sample.fix_type == vbox.VBOX_FIXTYPE_RTK_FIXED:
            GV.rtk_warning[0] = gui.DL_VERTEX_TRANSLATE_X(800)

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
    GV.lat[0] = "000.00000"
    GV.long[0] = "000.00000"
    ball.update_vals(-50, -50)
    ball.update()


def pass_cb(l):
    pass


def centre_graph_cb(l):
    pass


def reset_cp(l):
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


def create_buttons(*args):
    global buttons
    buttons = []
    if 'Reset' in args:
        buttons.append(Picture_Button(700, -8, bank.get('Reset'), 'Reset', reset_cp))
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


def init_buttons():
    global button_layouts
    button_layouts = {}
    button_layouts['main'] = create_buttons('Reset', 'GNSS', 'Centre')


def button_options():
    global button_layouts
    gui_buttons = []
    gui_buttons.extend(button_layouts['main'][0])
    gui_buttons.append(button_layouts['main'][1])

    return gui_buttons


def set_gnss_btn_state(state):
    if state:
        get_picture_button('GNSS').set_colour((0, 255, 0))
        if sample.fix_type == vbox.VBOX_FIXTYPE_RTK_FIXED:
            get_picture_button('GNSS').set_colour((255, 0, 255))
        elif sample.fix_type == vbox.VBOX_FIXTYPE_RTK_FLOAT:
            get_picture_button('GNSS').set_colour((255, 128, 0))
    else:
        get_picture_button('GNSS').set_colour((255, 0,  0))


def set_sats_status(state):
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


def set_cp(l):
    global sample
    if sample.fix_type == vbox.VBOX_FIXTYPE_RTK_FIXED:
        if GV.a_set == True:
            if GV.set_button == "Points":
                if len(GV.cp_list) < 24:
                    GV.cp_list.append((math.radians((sample.lat_degE7)/10000000), math.radians((sample.lng_degE7)/10000000), sample.alt_msl_m))
                    GV.cp_number[0] = str(len(GV.cp_list))
                    point.set_contact_point((len(GV.cp_list)), ball.ball_pos_x, ball.ball_pos_y)
                    Point_position.get_point_position((sample.lat_degE7)/10000000, (sample.lng_degE7)/10000000, sample.x_m, sample.y_m, ball.ball_pos_x, ball.ball_pos_y)
            elif GV.set_button == "Antenna B":
                if len(GV.antennaBcoords) < 1:
                    GV.antennaBcoords.append((math.radians((sample.lat_degE7)/10000000), math.radians((sample.lng_degE7)/10000000), sample.alt_msl_m))
                    point.set_antenna_b(ball.ball_pos_x, ball.ball_pos_y)
                    GV.antenna_b = [(sample.x_m, sample.y_m)]
        else:
            if GV.set_button == "Antenna A":
                if len(GV.antennaAcoords) < 1:
                    GV.a_set = True
                    GV.antennaAcoords.append((math.radians((sample.lat_degE7)/10000000), math.radians((sample.lng_degE7)/10000000), sample.alt_msl_m))
                    vbox.set_basepoint()
                    point.set_antenna_a(ball.ball_pos_x, ball.ball_pos_y)
            else:
                pass
    else: 
        GV.rtk_warning[0] = gui.DL_VERTEX_TRANSLATE_X(0)


def delete_last_point(l):
    if GV.set_button == "Points":
        if len(GV.cp_list) > 0:
            point.remove_contact_point(len(GV.cp_list))
            GV.cp_list.pop(-1)
            GV.cp_number[0] = str(int(GV.cp_number[0]) - 1)
            Point_position.delete_position(GV.point_list)
    elif GV.set_button == "Antenna A":
        if len(GV.antennaAcoords) == 1:
            GV.antennaAcoords.pop(-1)
            point.delete_antenna_a()
    elif GV.set_button == "Antenna B":
        if len(GV.antennaBcoords) == 1:
            GV.antennaBcoords.pop(-1)
            point.delete_antenna_b()


def zoom_out(l):
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


def zoom_in(l):
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


def upload_points(l):
    pass


def redraw_cb(b):
    ball.update()
    gui.redraw()


def vsync_cb(b):
    global gnss_status
    set_gnss_btn_state(gnss_status)
    gui.redraw()


def main_screen():
    global gui_list
    gui_list = [
        [gui.EVT_VSYNC, vsync_cb],
        [gui.EVT_REDRAW, redraw_cb],
        [gui.DL_CLEAR_COLOR_RGB(255, 255, 255)],
        [gui.DL_SCISSOR_SIZE(400, 420)],
        [gui.DL_SCISSOR_XY(0, 61)],
        [gui.DL_COLOR_RGB(0, 102, 17)],
        [gui.DL_POINT_SIZE(11)],
        [gui.DL_BEGIN(gui.PRIM_POINTS)],
        [gui.DL_VERTEX2F(ball.ball_pos_x, ball.ball_pos_y)],
        [gui.DL_END()],
        GV.rtk_warning,
        # TODO move to back so that is appears on top of all the dots
        [gui.DL_COLOR_RGB(255, 0, 0)],
        [gui.CTRL_TEXT, 200, 220, 32, gui.OPT_CENTERX,'RTK Required'],
        [gui.DL_VERTEX_TRANSLATE_X(0)],]
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
        [gui.CTRL_TEXT, 0, 440, 27, 0, 'Latitude:'],
        [gui.CTRL_TEXT, 100, 440, 27, 0, GV.lat],
        [gui.CTRL_TEXT, 0, 460, 27, 0, 'Longitude:'],
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
        [gui.CTRL_TEXT, 700, 70, 30, gui.OPT_CENTERX, 'Role'],
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
        [gui.DL_COLOR_RGB(200, 200, 200)],
        [gui.CTRL_FLATBUTTON, 620, 210, 160, 60, 30, 'Upload', upload_points],
    ])
    gui.show(gui_list)


def main():
    global bank, antenna_or_cp_button, ball, point, subject_or_target
    vts.config({'serialConn': 1}) # Connect Serial port 1 directly to GNSS engine port
    vbox.cfg_gnss({'UART2 Output': [('NMEA', 'GGA', 5)]}) # Enable GGA message output for NTRIP
    vbox.cfg_gnss({'DGPS Baudrate':115200}) # Set RTK Baud rate to 115200 - May need settings option in future
    antenna_or_cp_button = LoopingButton(620, 310, 160, 60, [x[0] for x in antenna_dir.values()], 30, set_antenna_or_cp)
    subject_or_target = LoopingButton(620, 110, 160, 60, [x[0] for x in vehicle_option_dir.values()], 30, vehicle_option)
    ball = ball_position()
    point = Point()
    bank = Image_Bank((
        ('/sd/icon-reset.png', 'Reset'),
        ('/sd/icons8-gnss-50.png', 'GNSS'),
        ('/sd/centre_icon.png', 'Centre')
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
    vbox.set_new_data_callback(gnss_callback)

main()