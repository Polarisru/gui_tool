#
# Copyright (C) 2016  UAVCAN Development Team  <uavcan.org>
#
# This software is distributed under the terms of the MIT License.
#
# Author: Pavel Kirienko <pavel.kirienko@zubax.com>
#

import uavcan
from functools import partial
from PyQt5.QtWidgets import QVBoxLayout, QHBoxLayout, QGridLayout, QWidget, QLabel, QDialog, QSlider, QSpinBox, \
    QPlainTextEdit, QLineEdit, QCheckBox
from PyQt5.QtCore import QTimer, Qt
from logging import getLogger
from ..widgets import make_icon_button, get_icon, get_monospace_font
import datetime
import math

__all__ = 'PANEL_NAME', 'spawn', 'get_icon'

PANEL_NAME = 'Actuator Panel (Volz)'


logger = getLogger(__name__)

_singleton = None

NODE_ID_OFFSET = 49
CURRENT_UNIT = 0.02
VOLTAGE_UNIT = 0.2
TEMPERATURE_OFFSET = 50


class PercentSlider(QWidget):
    def volz_response_callback(self, event):
        if self.get_id() == event.transfer.source_node_id - NODE_ID_OFFSET:
            self._cpu_temperature.setText(str(event.response.cpu_temperature - TEMPERATURE_OFFSET))
            self._stalls.setText(str(event.response.stall_counter))
            self._max_current.setText(str(round(event.response.max_current * CURRENT_UNIT, 2)))
            #self._power_on_time.setText(str(datetime.timedelta(seconds=event.response.total_power_on_time)))
            seconds = event.response.total_power_on_time
            self._power_on_time.setText('{}:{:02}:{:02}'.format(seconds // 3600, seconds % 3600 // 60, seconds % 60))

    def __init__(self, parent):
        super(PercentSlider, self).__init__(parent)
        
        self._parent = parent

        self._slider = QSlider(Qt.Horizontal, self)
        self._slider.setMinimum(-170)
        self._slider.setMaximum(170)
        self._slider.setValue(0)
        self._slider.setTickInterval(100)
        self._slider.setTickPosition(QSlider.TicksBothSides)
        self._slider.valueChanged.connect(lambda: self._spinbox.setValue(self._slider.value()))

        self._spinbox = QSpinBox(self)
        self._spinbox.setMinimum(-170)
        self._spinbox.setMaximum(170)
        self._spinbox.setValue(0)
        self._spinbox.valueChanged.connect(lambda: self._slider.setValue(self._spinbox.value()))
        self._spinbox.setFixedWidth(50)

        self._idbox = QSpinBox(self)
        self._idbox.setMinimum(0)
        self._idbox.setMaximum(255)
        self._idbox.setValue(1)
        self._idbox.setFixedWidth(40)

        self._zero_button = make_icon_button('arrow-up', 'Go to Zero', self, on_clicked=self.zero)
        self._zero_button.setFixedWidth(60)
        self._min_button = make_icon_button('arrow-left', 'Go to Min', self, on_clicked=self.do_min)
        self._min_button.setFixedWidth(60)
        self._max_button = make_icon_button('arrow-right', 'Go to Max', self, on_clicked=self.do_max)
        self._max_button.setFixedWidth(60)
        
        self._position = QLineEdit(self)
        self._position.setReadOnly(True)
        self._position.setAlignment(Qt.AlignCenter)
        self._position.setText('--.-')
        self._position.setFixedWidth(40)

        self._current = QLineEdit(self)
        self._current.setReadOnly(True)
        self._current.setAlignment(Qt.AlignCenter)
        self._current.setText('-.--')
        self._current.setFixedWidth(40)
        self._voltage = QLineEdit(self)
        self._voltage.setReadOnly(True)
        self._voltage.setAlignment(Qt.AlignCenter)
        self._voltage.setText('--.-')
        self._voltage.setFixedWidth(40)
        self._temperature = QLineEdit(self)
        self._temperature.setReadOnly(True)
        self._temperature.setAlignment(Qt.AlignCenter)
        self._temperature.setText('--')
        self._temperature.setFixedWidth(40)
        self._pwm = QLineEdit(self)
        self._pwm.setReadOnly(True)
        self._pwm.setAlignment(Qt.AlignCenter)
        self._pwm.setText('---')
        self._pwm.setFixedWidth(40)        
        
        self._cpu_temperature = QLineEdit(self)
        self._cpu_temperature.setReadOnly(True)
        self._cpu_temperature.setAlignment(Qt.AlignCenter)
        self._cpu_temperature.setText('--')
        self._cpu_temperature.setFixedWidth(40)
        self._stalls = QLineEdit(self)
        self._stalls.setReadOnly(True)
        self._stalls.setAlignment(Qt.AlignCenter)
        self._stalls.setText('---')
        self._stalls.setFixedWidth(40)        
        self._max_current = QLineEdit(self)
        self._max_current.setReadOnly(True)
        self._max_current.setAlignment(Qt.AlignCenter)
        self._max_current.setText('-.--')
        self._max_current.setFixedWidth(40)
        self._power_on_time = QLineEdit(self)
        self._power_on_time.setReadOnly(True)
        self._power_on_time.setAlignment(Qt.AlignCenter)
        self._power_on_time.setText('---:--:--')
        self._power_on_time.setFixedWidth(60)
        self._info_button = make_icon_button('info', 'Get Info', self, on_clicked=self.send_info_request)
        self._info_button.setFixedWidth(60)
        
        layout = QVBoxLayout(self)
        sub_layout = QHBoxLayout(self)
        sub_layout.addWidget(self._slider)
        sub_layout.addWidget(self._spinbox)
        layout.addLayout(sub_layout)
        sub_layout = QHBoxLayout(self)
        sub_layout.addWidget(QLabel('ID:', self))
        sub_layout.addWidget(self._idbox)
        sub_layout.addStretch()
        sub_layout.addWidget(self._min_button)
        sub_layout.addWidget(self._zero_button)
        sub_layout.addWidget(self._max_button)
        sub_layout.addStretch()
        sub_layout.addWidget(QLabel('Readout:', self))
        sub_layout.addWidget(self._position)
        layout.addLayout(sub_layout)
        sub_layout = QHBoxLayout(self)
        sub_layout.addWidget(QLabel('Current:', self))
        sub_layout.addWidget(self._current)
        sub_layout.addWidget(QLabel('A', self))
        sub_layout.addWidget(QLabel('Voltage:', self))
        sub_layout.addWidget(self._voltage)
        sub_layout.addWidget(QLabel('V', self))
        sub_layout.addWidget(QLabel('Temp.:', self))
        sub_layout.addWidget(self._temperature)
        sub_layout.addWidget(QLabel('°C', self))
        sub_layout.addWidget(QLabel('PWM:', self))
        sub_layout.addWidget(self._pwm)        
        layout.addLayout(sub_layout)
        sub_layout = QHBoxLayout(self)
        sub_layout.addWidget(QLabel('CPU Temp.:', self))
        sub_layout.addWidget(self._cpu_temperature)
        sub_layout.addWidget(QLabel('°C', self))
        sub_layout.addWidget(QLabel('Stalls:', self))
        sub_layout.addWidget(self._stalls)
        sub_layout.addWidget(QLabel('Max Current:', self))
        sub_layout.addWidget(self._max_current)
        sub_layout.addWidget(QLabel('A', self))
        sub_layout.addWidget(QLabel('Power-On:', self))
        sub_layout.addWidget(self._power_on_time)
        sub_layout.addWidget(self._info_button)
        layout.addLayout(sub_layout)
        self.setLayout(layout)

        self.setMinimumHeight(120)
        
        self._active = False
        
    def enable(self):
        self._slider.setEnabled(True)
        self._spinbox.setEnabled(True)
        self._idbox.setEnabled(True)
        self._zero_button.setEnabled(True)
        self._min_button.setEnabled(True)
        self._max_button.setEnabled(True)
    
    def disable(self):
        self._slider.setEnabled(False)
        self._spinbox.setEnabled(False)
        self._idbox.setEnabled(False)
        self._zero_button.setEnabled(False)
        self._min_button.setEnabled(False)
        self._max_button.setEnabled(False)

    def zero(self):
        self._slider.setValue(0)
        
    def do_min(self):
        self._slider.setValue(self._slider.minimum())

    def do_max(self):
        self._slider.setValue(self._slider.maximum())

    def get_value(self):
        return self._slider.value()
        
    def get_id(self):
        return self._idbox.value()
        
    def set_position(self, pos):
        self._active = True
        self._position.setText(pos)
        
    def set_active(self, value):
        self._active = value
    
    def is_active(self):
        return self._active
        
    def reset_position(self):
        self._position.setText('--.-')
        
    def set_current(self, value):
        current = str(round(value * CURRENT_UNIT, 2))
        self._current.setText(current)

    def set_voltage(self, value):
        voltage = str(round(value * VOLTAGE_UNIT, 1))
        self._voltage.setText(voltage)
        
    def set_temperature(self, value):
        if value == 0:
            temperature = 'XX'
        else:
            temperature = str(value - TEMPERATURE_OFFSET)
        self._temperature.setText(temperature)

    def set_pwm(self, value):
        pwm = str(value)
        self._pwm.setText(pwm)
        
    def reset_values(self):
        self._current.setText('-.--')
        self._voltage.setText('--.-')
        self._temperature.setText('--')
        self._pwm.setText('---')
        self._position.setText('--.-')
        
    def send_info_request(self):
        self._parent._node.request(uavcan.thirdparty.com.volz.GetActuatorInfo.Request(), self.get_id() + NODE_ID_OFFSET, self.volz_response_callback)

class ActuatorPanelVolz(QDialog):
    DEFAULT_FREQUENCY = 50
    ACTIVE_INTERVAL = 2.0
    MOVEMENT_INTERVAL = 2.0
                
    def volz_status_callback(self, event):
        for sl in self._sliders:
            #if sl.get_id() == event.transfer.source_node_id - NODE_ID_OFFSET:
            if event.message.actuator_id == sl.get_id():
                sl.set_current(event.message.current)
                sl.set_voltage(event.message.voltage)
                sl.set_temperature(event.message.motor_temperature)
                sl.set_pwm(event.message.motor_pwm)
                sl.set_position(str(round(math.degrees(event.message.actual_position), 1)))

    def __init__(self, parent, node):
        super(ActuatorPanelVolz, self).__init__(parent)
        self.setWindowTitle('Actuator Management Panel (Volz)')
        self.setAttribute(Qt.WA_DeleteOnClose)              # This is required to stop background timers!

        self._node = node
        
        self._paused = False

        self._sliders = [PercentSlider(self)]
        
        self._sliders_grid = [(i, j) for j in range(2) for i in range(4)]
        
        self._current_pos = 0

        self._num_sliders = QSpinBox(self)
        self._num_sliders.setMinimum(1)
        self._num_sliders.setMaximum(8)
        self._num_sliders.setValue(1)
        self._num_sliders.valueChanged.connect(self._update_number_of_sliders)

        self._bcast_interval = QSpinBox(self)
        self._bcast_interval.setMinimum(1)
        self._bcast_interval.setMaximum(100)
        self._bcast_interval.setSingleStep(1)
        self._bcast_interval.setValue(self.DEFAULT_FREQUENCY)
        self._bcast_interval.setMinimumWidth(50)
        self._bcast_interval.valueChanged.connect(
            lambda: self._bcast_timer.setInterval(1000 / self._bcast_interval.value()))

        self._stop_all = make_icon_button('arrow-up', 'Zero all channels', self, text='Zero All',
                                          on_clicked=self._do_zero_all)
        self._min_all = make_icon_button('arrow-left', 'Go to Min', self, text='Go to Min',
                                          on_clicked=self._do_min_all)
        self._max_all = make_icon_button('arrow-right', 'Go to Max', self, text='Go to Max',
                                          on_clicked=self._do_max_all)

        self._pause = make_icon_button('pause', 'Pause publishing', self, text='Pause',
                                       on_clicked=self._do_pause)
                                       
        self._cb_move = QCheckBox(self)
        self._cb_move.setText('Do movement')
        self._cb_move.stateChanged.connect(self._update_movement)

        self._msg_viewer = QPlainTextEdit(self)
        self._msg_viewer.setReadOnly(True)
        self._msg_viewer.setLineWrapMode(QPlainTextEdit.NoWrap)
        self._msg_viewer.setFont(get_monospace_font())
        self._msg_viewer.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self._msg_viewer.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        self._bcast_timer = QTimer(self)
        self._bcast_timer.start(1000 / self.DEFAULT_FREQUENCY)
        self._bcast_timer.timeout.connect(self._do_broadcast)
        
        self._active_timer = QTimer(self)
        self._active_timer.start(self.ACTIVE_INTERVAL * 1e3)
        self._active_timer.timeout.connect(self._show_active)
        
        self._movement_timer = QTimer(self)
        self._movement_timer.setInterval(self.MOVEMENT_INTERVAL * 1e3)
        self._movement_timer.timeout.connect(self._do_movement)

        layout = QVBoxLayout(self)

        alls_layout = QHBoxLayout(self)
        alls_layout.addWidget(self._min_all)
        alls_layout.addWidget(self._stop_all)
        alls_layout.addWidget(self._max_all)
        layout.addLayout(alls_layout)

        controls_layout = QHBoxLayout(self)
        controls_layout.addWidget(QLabel('Channels:', self))
        controls_layout.addWidget(self._num_sliders)
        controls_layout.addWidget(QLabel('Broadcast frequency:', self))
        controls_layout.addWidget(self._bcast_interval)
        controls_layout.addWidget(QLabel('Hz', self))
        controls_layout.addStretch()
        controls_layout.addWidget(self._cb_move)
        controls_layout.addStretch()
        controls_layout.addWidget(self._pause)
        layout.addLayout(controls_layout)

        self._slider_layout = QGridLayout(self)#QVBoxLayout(self)
        for i in range(len(self._sliders)):
            self._slider_layout.addWidget(self._sliders[i], *self._sliders_grid[i])
        layout.addLayout(self._slider_layout)

        layout.addWidget(QLabel('Generated message:', self))
        layout.addWidget(self._msg_viewer)
        layout.addLayout(layout)
        
        self.setLayout(layout)
        self.resize(self.minimumWidth(), self.minimumHeight())
        
        # Subscribing to volz.ActuatorStatus messages
        try:
            self.handle = self._node.add_handler(uavcan.thirdparty.com.volz.ActuatorStatus, self.volz_status_callback)
        except Exception as e:
            print('NODE ERROR: ', str(e))

    def _do_broadcast(self):
        try:
            if not self._paused:
                msg = uavcan.equipment.actuator.ArrayCommand()
                for sl in self._sliders:
                    raw_value = math.radians(sl.get_value())
                    #value = (-self.CMD_MIN if raw_value < 0 else self.CMD_MAX) * raw_value
                    #cmd = uavcan.equipment.actuator.Command(actuator_id=sl.get_id(), command_type=1, command_value=raw_value)
                    cmd = uavcan.equipment.actuator.Command()
                    cmd.actuator_id = sl.get_id()
                    cmd.command_type = cmd.COMMAND_TYPE_POSITION 
                    cmd.command_value = raw_value
                    msg.commands.append(cmd)

                self._node.broadcast(msg)
                self._msg_viewer.setPlainText(uavcan.to_yaml(msg))
            else:
                self._msg_viewer.setPlainText('Paused')
        except Exception as ex:
            self._msg_viewer.setPlainText('Publishing failed:\n' + str(ex))
            
    def _update_movement(self):
        if self._cb_move.isChecked():
            self._stop_all.setEnabled(False)
            self._min_all.setEnabled(False)
            self._max_all.setEnabled(False)
            self._num_sliders.setEnabled(False)
            for sl in self._sliders:
                sl.disable()
            self._movement_timer.start()
        else:
            self._stop_all.setEnabled(True)
            self._min_all.setEnabled(True)
            self._max_all.setEnabled(True)
            self._num_sliders.setEnabled(True)
            for sl in self._sliders:
                sl.enable()            
            self._movement_timer.stop()
            
    def _do_movement(self):
        if self._current_pos == 0:
            # move to max
            self._current_pos = 1
            self._do_max_all()
        else:
            # move to min
            self._current_pos = 0
            self._do_min_all()
            
    def _show_active(self):
        for sl in self._sliders:
            if not sl.is_active():
                sl.reset_values()
            sl.set_active(False)

    def _do_pause(self):
        if self._paused:
            self._paused = False
            self._pause.setText('Pause')
            self._pause.setIcon(get_icon('pause'))
        else:
            self._paused = True
            self._pause.setText('Continue')
            self._pause.setIcon(get_icon('play'))

    def _do_zero_all(self):
        for sl in self._sliders:
            sl.zero()
            
    def _do_min_all(self):
        for sl in self._sliders:
            sl.do_min()
    
    def _do_max_all(self):
        for sl in self._sliders:
            sl.do_max()            

    def _update_number_of_sliders(self):
        num_sliders = self._num_sliders.value()

        while len(self._sliders) > num_sliders:
            removee = self._sliders[-1]
            self._sliders = self._sliders[:-1]
            self._slider_layout.removeWidget(removee)
            removee.close()
            removee.deleteLater()

        while len(self._sliders) < num_sliders:
            new = PercentSlider(self)
            self._slider_layout.addWidget(new, *self._sliders_grid[num_sliders - 1])
            self._sliders.append(new)

        def deferred_resize():
            self.resize(self.minimumWidth(), self.minimumHeight())

        deferred_resize()

    def __del__(self):
        global _singleton
        _singleton = None

    def closeEvent(self, event):
        global _singleton
        _singleton = None
        self.handle.remove()
        super(ActuatorPanelVolz, self).closeEvent(event)


def spawn(parent, node):
    global _singleton
    if _singleton is None:
        _singleton = ActuatorPanelVolz(parent, node)

    _singleton.show()
    _singleton.raise_()
    _singleton.activateWindow()

    return _singleton


get_panel_icon = partial(get_icon, 'tachometer')
