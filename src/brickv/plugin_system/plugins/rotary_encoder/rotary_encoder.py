# -*- coding: utf-8 -*-
"""
Rotary Encoder Plugin
Copyright (C) 2013 Olaf Lüke <olaf@tinkerforge.com>
Copyright (C) 2014-2015 Matthias Bolte <matthias@tinkerforge.com>

rotary_encoder.py: Rotary Encoder Plugin Implementation

This program is free software; you can redistribute it and/or
modify it under the terms of the GNU General Public License
as published by the Free Software Foundation; either version 2
of the License, or (at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
General Public License for more details.

You should have received a copy of the GNU General Public
License along with this program; if not, write to the
Free Software Foundation, Inc., 59 Temple Place - Suite 330,
Boston, MA 02111-1307, USA.
"""

import functools

from PyQt4.QtCore import pyqtSignal, Qt
from PyQt4.QtGui import QLabel, QVBoxLayout, QHBoxLayout, QPushButton

from brickv.plugin_system.plugin_base import PluginBase
from brickv.bindings.bricklet_rotary_encoder import BrickletRotaryEncoder
from brickv.knob_widget import KnobWidget
from brickv.plot_widget import PlotWidget
from brickv.async_call import async_call
from brickv.callback_emulator import CallbackEmulator

class CountLabel(QLabel):
    def setText(self, text):
        text = "Count: " + text
        super(CountLabel, self).setText(text)

class RotaryEncoder(PluginBase):
    qtcb_pressed = pyqtSignal()
    qtcb_released = pyqtSignal()

    def __init__(self, *args):
        PluginBase.__init__(self, BrickletRotaryEncoder, *args)

        self.re = self.device

        self.cbe_count = CallbackEmulator(functools.partial(self.re.get_count, False),
                                          self.cb_count,
                                          self.increase_error_count)

        self.qtcb_pressed.connect(self.cb_pressed)
        self.re.register_callback(self.re.CALLBACK_PRESSED,
                                  self.qtcb_pressed.emit)

        self.qtcb_released.connect(self.cb_released)
        self.re.register_callback(self.re.CALLBACK_RELEASED,
                                  self.qtcb_released.emit)

        self.count_label = CountLabel('Count: 0')
        self.reset_button = QPushButton('Reset Count')
        self.reset_button.clicked.connect(self.reset_clicked)

        self.encoder_knob = KnobWidget(self)
        self.encoder_knob.setFocusPolicy(Qt.NoFocus)
        self.encoder_knob.set_total_angle(360)
        self.encoder_knob.set_range(0, 24)
        self.encoder_knob.set_scale(2, 2)
        self.encoder_knob.set_scale_text_visible(False)
        self.encoder_knob.set_scale_arc_visible(False)
        self.encoder_knob.set_knob_radius(25)
        self.encoder_knob.set_value(0)

        self.current_value = None

        plot_list = [['', Qt.red, self.get_current_value]]
        self.plot_widget = PlotWidget('Count', plot_list)

        layout_h1 = QHBoxLayout()
        layout_h1.addStretch()
        layout_h1.addWidget(self.count_label)
        layout_h1.addStretch()

        layout_h2 = QHBoxLayout()
        layout_h2.addStretch()
        layout_h2.addWidget(self.encoder_knob)
        layout_h2.addStretch()

        layout_h3 = QHBoxLayout()
        layout_h3.addStretch()
        layout_h3.addWidget(self.reset_button)
        layout_h3.addStretch()

        layout = QVBoxLayout(self)
        layout.addLayout(layout_h1)
        layout.addLayout(layout_h2)
        layout.addLayout(layout_h3)
        layout.addWidget(self.plot_widget)

    def get_current_value(self):
        return self.current_value

    def cb_released(self):
        self.encoder_knob.set_pressed(False)

    def cb_pressed(self):
        self.encoder_knob.set_pressed(True)

    def cb_count(self, count):
        self.current_value = count
        self.count_label.setText(str(count))
        self.encoder_knob.set_value((count + 12) % 24)

    def reset_clicked(self):
        async_call(self.re.get_count, True, None, self.increase_error_count)
        self.cb_count(0)

    def start(self):
        async_call(self.re.get_count, False, self.cb_count, self.increase_error_count)
        self.cbe_count.set_period(25)

        self.plot_widget.stop = False

    def stop(self):
        self.cbe_count.set_period(0)

        self.plot_widget.stop = True

    def destroy(self):
        pass

    def get_url_part(self):
        return 'rotary_encoder'

    @staticmethod
    def has_device_identifier(device_identifier):
        return device_identifier == BrickletRotaryEncoder.DEVICE_IDENTIFIER
