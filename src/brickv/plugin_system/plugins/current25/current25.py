# -*- coding: utf-8 -*-  
"""
Current25 Plugin
Copyright (C) 2011-2012 Olaf Lüke <olaf@tinkerforge.com>
Copyright (C) 2014-2015 Matthias Bolte <matthias@tinkerforge.com>

current25.py: Current25 Plugin Implementation

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

from PyQt4.QtCore import pyqtSignal, Qt
from PyQt4.QtGui import QVBoxLayout, QLabel, QPushButton, QHBoxLayout

from brickv.plugin_system.plugin_base import PluginBase
from brickv.bindings import ip_connection
from brickv.bindings.bricklet_current25 import BrickletCurrent25
from brickv.plot_widget import PlotWidget
from brickv.async_call import async_call
from brickv.callback_emulator import CallbackEmulator

class CurrentLabel(QLabel):
    def setText(self, text):
        text = "Current: " + text + " A"
        super(CurrentLabel, self).setText(text)
    
class Current25(PluginBase):
    qtcb_over = pyqtSignal()
    
    def __init__(self, *args):
        PluginBase.__init__(self, BrickletCurrent25, *args)
        
        self.cur = self.device
        
        self.cbe_current = CallbackEmulator(self.cur.get_current,
                                            self.cb_current,
                                            self.increase_error_count)
        
        self.qtcb_over.connect(self.cb_over)
        self.cur.register_callback(self.cur.CALLBACK_OVER_CURRENT,
                                   self.qtcb_over.emit) 
        
        self.current_label = CurrentLabel('Current: ')
        self.over_label = QLabel('Over Current: No')
        self.calibrate_button = QPushButton('Calibrate')
        self.calibrate_button.clicked.connect(self.calibrate_clicked)
        
        self.current_value = None
        
        plot_list = [['', Qt.red, self.get_current_value]]
        self.plot_widget = PlotWidget('Current [mA]', plot_list)
        
        layout_h1 = QHBoxLayout()
        layout_h1.addStretch()
        layout_h1.addWidget(self.current_label)
        layout_h1.addStretch()

        layout_h2 = QHBoxLayout()
        layout_h2.addStretch()
        layout_h2.addWidget(self.over_label)
        layout_h2.addStretch()

        layout = QVBoxLayout(self)
        layout.addLayout(layout_h1)
        layout.addLayout(layout_h2)
        layout.addWidget(self.plot_widget)
        layout.addWidget(self.calibrate_button)

    def start(self):
        async_call(self.cur.get_current, None, self.cb_current, self.increase_error_count)
        self.cbe_current.set_period(100)
        
        self.plot_widget.stop = False
        
    def stop(self):
        self.cbe_current.set_period(0)
        
        self.plot_widget.stop = True

    def destroy(self):
        pass

    def get_url_part(self):
        return 'current25'

    @staticmethod
    def has_device_identifier(device_identifier):
        return device_identifier == BrickletCurrent25.DEVICE_IDENTIFIER

    def get_current_value(self):
        return self.current_value

    def cb_current(self, current):
        self.current_value = current
        self.current_label.setText(str(current/1000.0)) 
        
    def cb_over(self):
        self.over_label.setText('Over Current: Yes')
        
    def calibrate_clicked(self):
        try:
            self.cur.calibrate()
        except ip_connection.Error:
            return
        
