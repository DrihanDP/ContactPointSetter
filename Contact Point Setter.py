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


RED = const(0xFF0000)
GREEN = const(0x00FF00)
PURPLE = const(0xA020F0)
ORANGE = const(0xFF5F1F)
gnss_status = False


antennaA = const(0)
antennaB = const(1)
points = const(2)

antenna_dir = {
    antennaA: ("Antenna A", 1),
    antennaB: ("Antenna B", 2),
    points: ("Points", 3),
}

backlight.set(5000)

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
    cp_x_y_list = []

class ball_position:

    def __init__(self):
        self.mid_lat = 0
        self.mid_long = 0
        self.current_lat = 0
        self.current_long = 0
        self.ball_pos_x = -50
        self.ball_pos_y = -50

    def mid_vals(self, mid_lat, mid_long):
        self.mid_lat = mid_lat
        self.mid_long = mid_long

    def update(self):
        gui_list[8][0] = gui.DL_VERTEX2F(ball.ball_pos_x, ball.ball_pos_y)

    def update_vals(self, ball_pos_x, ball_pos_y):
        self.ball_pos_x = ball_pos_x
        self.ball_pos_y = ball_pos_y


class Point():

    def __init__(self):
        self.x_y_list = []
        self.stored_points_colour = [gui.DL_COLOR_RGB(0,0,0xFF)]
        self.antenna_colour = [gui.DL_COLOR_RGB(150, 0, 0)]
        self.set_points =  [
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
        self.point_gui_list = [gui.SUBLIST,
                        self.stored_points_colour,
                        [gui.DL_POINT_SIZE(8)],
                        [gui.DL_BEGIN(gui.PRIM_POINTS)],
                        self.set_points,
                        [gui.DL_END()],
                        ]
        self.antenna_a_gui = [gui.SUBLIST,
                        self.antenna_colour,
                        [gui.DL_POINT_SIZE(10)],
                        [gui.DL_BEGIN(gui.PRIM_POINTS)],
                        self.set_a,
                        [gui.DL_END()],
                        ]
        self.antenna_b_gui =  [gui.SUBLIST,
                        self.antenna_colour,
                        [gui.DL_POINT_SIZE(10)],
                        [gui.DL_BEGIN(gui.PRIM_POINTS)],
                        self.set_b,
                        [gui.DL_END()],
                        ]
    #TODO Get "A" and "B" in the middle
    def set_contact_point(self, point, x, y):
        if 0 < point < (len(self.set_points)):
            self.set_points[point][0] = gui.DL_VERTEX2F(x, y)
            return True
        else:
            return False

    def remove_contact_point(self, point):
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

def degE7_to_minE5(degE7):
        return int((float(degE7) * 0.6) + (0.5 if degE7 >= 0.0 else -0.5))


def position_calc():
    global x_dist, y_dist
    if GV.a_set == False:
        pass
    else:
        # TODO need to divide x/y_scale by 2? 
        x_dist = 370 / int(GV.x_scale[0].replace("m", "")) * (sample.x_m - 0.63)
        y_dist = 350 / int(GV.y_scale[0].replace("m", "")) * (sample.y_m - 0.2)
        ball.update_vals(200 + x_dist, 270 + y_dist)
        ball.update()


def gnss_callback():
    global sample
    sample = vbox.get_sample_hp()
    set_sats_status(gnss_status)
    GV.sats[0] = "{}".format(sample.sats_used)
    if sample.sats_used > 3:
        GV.lat[0] = "{:04.5f}".format((sample.lat_degE7)/10000000)
        GV.long[0] = "{:04.5f}".format((sample.lng_degE7)/10000000)
        if sample.fix_type > 1: #TODO change to rtk fix
            if ball.mid_lat == 0 and ball.mid_long == 0:
                ball.mid_vals(((sample.lat_degE7)/10000000), ((sample.lng_degE7)/10000000))
                ball.update_vals(200, 270)
                ball.update()
            else:
                position_calc()


def set_cp_number(btn):
    GV.cp_number = btn.current


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
    GV.cp_x_y_list = []


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
        if sample.fix_type == 4:
            get_picture_button('GNSS').set_colour((160, 32, 240))
        elif sample.fix_type == 5:
            get_picture_button('GNSS').set_colour((255, 95, 31))
    else:
        get_picture_button('GNSS').set_colour((255, 0,  0))


def set_sats_status(state):
    global gnss_status
    if sample.sats_used > 3:
        gnss_status = True
        GV.sats_colour[0] = gui.DL_COLOR(GREEN)
        if sample.fix_type == 4:
            GV.sats_colour[0] = gui.DL_COLOR(PURPLE)
        elif sample.fix_type == 5:
            GV.sats_colour[0] = gui.DL_COLOR(ORANGE)
    else:
        GV.sats_colour[0] = gui.DL_COLOR(RED)
        gnss_status = False


def set_cp(l):
    # if sample.fix_type == 4:
    # TODO make sure that antenna A is set first
    if GV.set_button == "Points":
        if len(GV.cp_list) < 24:
            GV.cp_list.append(((sample.lat_degE7)/10000000, (sample.lng_degE7)/10000000))
            GV.cp_number[0] = str(len(GV.cp_list))
            point.set_contact_point((len(GV.cp_list)), ball.ball_pos_x, ball.ball_pos_y)
            GV.cp_x_y_list.append([sample.x_m, sample.y_m])
    elif GV.set_button == "Antenna A":
        if len(GV.antennaAcoords) < 1:
            GV.a_set = True
            lat_base = degE7_to_minE5(sample.lat_degE7)
            long_base = degE7_to_minE5(sample.lng_degE7)
            GV.antennaAcoords.append(((sample.lat_degE7)/10000000, (sample.lng_degE7)/10000000))
            vbox.set_basepoint(lat_base, long_base)
            point.set_antenna_a(ball.ball_pos_x, ball.ball_pos_y)
    elif GV.set_button == "Antenna B":
        if len(GV.antennaBcoords) < 1:
            GV.antennaBcoords.append(((sample.lat_degE7)/10000000, (sample.lng_degE7)/10000000))
            point.set_antenna_b(ball.ball_pos_x, ball.ball_pos_y)


def delete_last_point(l):
    if GV.set_button == "Points":
        if len(GV.cp_list) > 0:
            point.remove_contact_point(len(GV.cp_list))
            GV.cp_list.pop(-1)
            GV.cp_number[0] = str(int(GV.cp_number[0]) - 1)
            GV.cp_x_y_list.pop(-1)
    elif GV.set_button == "Antenna A":
        if len(GV.antennaAcoords) == 1:
            GV.antennaAcoords.pop(-1)
            point.delete_antenna_a()
    elif GV.set_button == "Antenna B":
        if len(GV.antennaBcoords) == 1:
            GV.antennaBcoords.pop(-1)
            point.delete_antenna_b()

#If y is positive +, if y is negative - 

def zoom_out(l):
    if int(GV.x_scale[0].replace("m", "")) < 15:
        x_scale_int = int(GV.x_scale[0].replace("m", ""))
        y_scale_int = int(GV.y_scale[0].replace("m", ""))
        GV.x_scale[0] = (str(x_scale_int + 1) + "m")
        GV.y_scale[0] = (str(y_scale_int + 1) + "m")

    else:
        pass


def zoom_in(l):
    # TODO zoom in and out for all of the contact points
    x = 0
    if int(GV.x_scale[0].replace("m", "")) > 1:
        x_scale_int = int(GV.x_scale[0].replace("m", ""))
        y_scale_int = int(GV.y_scale[0].replace("m", ""))
        GV.x_scale[0] = (str(x_scale_int - 1) + "m")
        GV.y_scale[0] = (str(y_scale_int - 1) + "m")
        while x < len(GV.cp_x_y_list):
            new_x_coord = 370 / int(GV.x_scale[0].replace("m", "")) * (GV.cp_x_y_list[x][0] - 0.63)
            new_y_coord = 350 / int(GV.y_scale[0].replace("m", "")) * (GV.cp_x_y_list[x][1] - 0.2)
            point.set_contact_point(x, new_x_coord, new_y_coord)
            GV.cp_x_y_list[0] = new_x_coord
            GV.cp_x_y_list[1] = new_y_coord
            x += 1 
    else:
        pass


def save(l):
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
        [gui.DL_END()],]
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
        [gui.CTRL_TEXT, 450, 70, 30, 0, 'Latitude:'],
        [gui.CTRL_TEXT, 650, 70, 30, 0, GV.lat],
        [gui.CTRL_TEXT, 450, 110, 30, 0, 'Longitude:'],
        [gui.CTRL_TEXT, 650, 110, 30, 0, GV.long],
        [gui.CTRL_TEXT, 450, 150, 30, 0, "Points set:"],
        [gui.CTRL_TEXT, 650, 150, 30, 0, GV.cp_number],
        [gui.CTRL_TEXT, 650, 360, 30, 0, 'Set point'],
        [gui.CTRL_TEXT, 494, 360, 30, 0, 'Zoom'],
        [gui.CTRL_TEXT, 670, 260, 30, 0, 'To set'],
        [gui.CTRL_TEXT, 450, 260, 30, 0, 'Delete Last'],
    ])
    gui_list.extend(button_options())
    gui_list.extend([
        [gui.DL_COLOR_RGB(255, 255, 255)],
        antenna_or_cp_button(),
        [gui.CTRL_FLATBUTTON, 630, 200, 160, 60, 30, 'Coldstart', coldstart_cb],
        [gui.CTRL_FLATBUTTON, 630, 400, 160, 60, 30, 'Set', set_cp],
        [gui.CTRL_FLATBUTTON, 535, 400, 75, 60, 30, '+', zoom_in],
        [gui.CTRL_FLATBUTTON, 450, 400, 75, 60, 30, '-', zoom_out],
        [gui.CTRL_FLATBUTTON, 450, 300, 160, 60, 30, 'Del Last', delete_last_point],
        [gui.CTRL_FLATBUTTON, 450, 200, 160, 60, 30, 'Save', save],
    ])
    gui.show(gui_list)


def main():
    global bank, antenna_or_cp_button, ball, point
    antenna_or_cp_button = LoopingButton(630, 300, 160, 60, [x[0] for x in antenna_dir.values()], 30, set_antenna_or_cp)
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
    vbox.set_new_data_callback(gnss_callback)

main()