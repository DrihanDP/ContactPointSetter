##
# @package   utils
# @brief     Utilities for demonstration scripts
# @version   1.0
#

import gui
from math import cos, sin, radians
cosd = lambda x: cos(radians(x))
sind = lambda x: sin(radians(x))
lerp = lambda x, xi, xf, ai, af: ai + ((x - xi) * (af - ai) / (xf - xi))

def read_csv(fn):
    with open(fn) as f:
        data = [(x, []) for x in next(f).strip().split(',')]
        for l in f:
            for i, v in enumerate(l.strip().split(',')):
                v = float(v) if '.' in v else int(v)
                data[i][1].append(float(v))
    return dict(data)


class Colors:
    white = gui.RGB(255, 255, 255)
    lightgrey = gui.RGB(192, 192, 192)
    grey = gui.RGB(128, 128, 128)
    darkgrey = gui.RGB(64, 64, 64)
    black = gui.RGB(0, 0, 0)
    red = gui.RGB(255, 0, 0)
    green = gui.RGB(0, 255, 0)
    blue = gui.RGB(0, 0, 255)
    darkred = gui.RGB(192, 0, 0)
    darkgreen = gui.RGB(0, 192, 0)
    darkblue = gui.RGB(0, 0, 192)
    gold = gui.RGB(240, 240, 32)
    gradblue0 = gui.RGB(0, 0, 96)
    gradblue1 = gui.RGB(0, 0, 16)


bg_gradient = [
    0xffffff0b, 0, Colors.gradblue0, (480 << 16) | 200, Colors.gradblue1
]


class Filter:
    def __init__(self):
        # 2nd order IIR Gauss LP filter, 2.1 Hz BW, 3 Hz wc, fs = 60 Hz
        self.a = (1.0000000000, -1.4950558121,  0.5668457092)
        self.b = (0.0179474742,  0.0358949485,  0.0179474742)
        # Filter state
        self.w = [0, 0]

    def __call__(self, x):
        # Biquad transposed direct form 2
        w = x - self.a[1] * self.w[0] - self.a[2] * self.w[1]
        y = self.b[0] * w + self.b[1] * self.w[0] + self.b[2] * self.w[1]
        self.w[1] = self.w[0]
        self.w[0] = w
        return y


class Gauge:
    def __init__(self, x, y, d,
            vmin=0,
            vmax=100,
            dmin=180,
            dmax=45,
            ndivs=10,
            vred=None,
            color=gui.RGB(0, 0, 0),
            color_red=gui.RGB(246, 40, 23)):
        self.x = x
        self.y = y
        # d: 'characteristic dimension'
        self.d = d
        self.vmin = vmin
        self.vmax = vmax
        self.dmin = dmin
        self.dmax = dmax
        self.ndivs = ndivs
        self.vred = vred
        self.color = color
        self.color_red = color_red
        self.filter = Filter()
        self.gui_needle = [[0], [0], [0]]
        self.value = vmin
        self.update()

    def set_val(self, x):
        self.value = x
        self.update()

    def update(self):
        self.cur_val = self.filter(self.value)
        angle = lerp(self.cur_val, self.vmin, self.vmax, self.dmin, self.dmax)
        self.gui_needle[0][0] = gui.DL_VERTEX2F(
            self.x + .9 * self.d * cosd(angle),
            self.y - .9 * self.d * sind(angle)
        )
        self.gui_needle[1][0] = gui.DL_VERTEX2F(
            self.x + .05 * self.d * cosd(angle + 90),
            self.y - .05 * self.d * sind(angle + 90)
        )
        self.gui_needle[2][0] = gui.DL_VERTEX2F(
            self.x + .05 * self.d * cosd(angle - 90),
            self.y - .05 * self.d * sind(angle - 90)
        )

    def gui_l(self):
        ln = [gui.SUBLIST]
        # Draw numbers
        fontsize = int(lerp(self.d, 50, 250, 26, 32))
        if fontsize < 26:
            fontsize = 26
        elif fontsize > 31:
            fontsize = 31
        for i in range(self.ndivs + 1):
            angle = lerp(i, 0, self.ndivs, self.dmin, self.dmax)
            numval = int(lerp(i, 0, self.ndivs, self.vmin, self.vmax))
            if self.vred and numval >= self.vred:
                ln.append([gui.DL_COLOR(self.color_red)])
            ln.append([
                gui.CTRL_TEXT,
                int(self.x + .8 * self.d * cosd(angle)),
                int(self.y - .8 * self.d * sind(angle)),
                fontsize,
                gui.OPT_CENTER,
                str(numval)
            ])
        if self.vred:
            ln.append([gui.DL_COLOR(self.color)])
        # Draw ticks
        l = [gui.DL_SAVE_CONTEXT()]
        l.append(gui.DL_BEGIN(gui.PRIM_LINES))
        for i in range(self.ndivs + 1):
            angle = lerp(i, 0, self.ndivs, self.dmin, self.dmax)
            if i != 0:
                # Minor ticks
                angle_prev = lerp(i - 1, 0, self.ndivs, self.dmin, self.dmax)
                for j in range(1, 10):
                    angle_minor = lerp(j, 0, 10, angle_prev, angle)
                    if self.vred:
                        tickval = lerp(
                            angle_minor, self.dmin, self.dmax, self.vmin, self.vmax)
                        if tickval >= self.vred:
                            l.append(gui.DL_COLOR(self.color_red))
                    l.append(gui.DL_VERTEX2F(
                        self.x + self.d * cosd(angle_minor),
                        self.y - self.d * sind(angle_minor)
                    ))
                    f = .99 if j != 5 else .97
                    l.append(gui.DL_VERTEX2F(
                        self.x + f * self.d * cosd(angle_minor),
                        self.y - f * self.d * sind(angle_minor)
                    ))
            # Major ticks
            l.append(gui.DL_VERTEX2F(
                self.x + self.d * cosd(angle),
                self.y - self.d * sind(angle)
            ))
            l.append(gui.DL_VERTEX2F(
                self.x + .92 * self.d * cosd(angle),
                self.y - .92 * self.d * sind(angle)
            ))
        l.append(gui.DL_END())
        if self.vred:
            l.append(gui.DL_COLOR(self.color))
        # Draw needle
        import ft8xx as ft
        # Filled polygon
        l.extend([
            gui.DL_STENCIL_OP(ft.STENCILOP_INCR, ft.STENCILOP_INCR),
            gui.DL_COLOR_MASK(0, 0, 0, 0),
            gui.DL_BEGIN(gui.PRIM_EDGE_STRIP_B),
            self.gui_needle[0],
            self.gui_needle[1],
            self.gui_needle[2],
            self.gui_needle[0],
            gui.DL_END(),
            gui.DL_COLOR_MASK(1, 1, 1, 1),
            gui.DL_STENCIL_FUNC(ft.ALPHAFUNC_EQUAL, 1, 255),
            gui.DL_BEGIN(gui.PRIM_EDGE_STRIP_B),
            self.gui_needle[0],
            self.gui_needle[1],
            self.gui_needle[2],
            self.gui_needle[0],
            gui.DL_END(),
            gui.DL_STENCIL_FUNC(ft.ALPHAFUNC_ALWAYS, 0, 255),
            gui.DL_CLEAR(0, 1, 0),
        ])
        # Outline
        l.extend([
            gui.DL_LINE_WIDTH(1.6),
            gui.DL_BEGIN(gui.PRIM_LINE_STRIP),
            self.gui_needle[0],
            self.gui_needle[1],
            self.gui_needle[2],
            self.gui_needle[0],
            gui.DL_END()
        ])
        # Draw center pivot
        l.extend([
            gui.DL_POINT_SIZE(self.d * .08),
            gui.DL_BEGIN(gui.PRIM_POINTS),
            gui.DL_VERTEX2F(self.x, self.y),
            gui.DL_END()
        ])
        l.append(gui.DL_RESTORE_CONTEXT())
        ln.append(l)
        return ln


class ScreenTranslationEffect:
    def __init__(self):
        self.translate_l = [
            gui.DL_VERTEX_TRANSLATE_X(0),
            gui.DL_VERTEX_TRANSLATE_Y(0),
        ]
        self.time = 0
        self.dir = None
        self.time_dir = None
        self.dim = None
        self.active = False
        self.sequence = tuple((t**3) * (8/270) for t in range(1, 31))

    def get_l(self):
        return self.translate_l

    def update(self):
        if not self.active:
            return
        time = self.time if self.time_dir == 1 else 29 - self.time
        val = self.dir * self.sequence[time]
        if self.dim == 0:
            self.translate_l[0] = gui.DL_VERTEX_TRANSLATE_X(val)
        else:
            self.translate_l[1] = gui.DL_VERTEX_TRANSLATE_Y(val)
        self.time += 1
        if self.time >= 30:
            self.active = False
        gui.redraw()

    def decode_dir(self, transition_req):
        transition = transition_req.split()
        if transition[0] == 'from':
            self.time_dir = -1
        elif transition[0] == 'to':
            self.time_dir = 1
        else:
            raise Exception('invalid transition orientation')
        if transition[1] in {'top', 'bottom'}:
            self.dim = 1
        elif transition[1] in {'left', 'right'}:
            self.dim = 0
        else:
            raise Exception('invalid transition direction')
        if transition[1] in {'top', 'left'}:
            self.dir = -1
        elif transition[1] in {'bottom', 'right'}:
            self.dir = 1

    def run(self, transition_req, block=False):
        self.decode_dir(transition_req)
        self.time = 0
        if self.dim == 0:
            self.translate_l[1] = gui.DL_VERTEX_TRANSLATE_Y(0)
        else:
            self.translate_l[0] = gui.DL_VERTEX_TRANSLATE_X(0)
        self.active = True
        if block:
            while self.active:
                pass
