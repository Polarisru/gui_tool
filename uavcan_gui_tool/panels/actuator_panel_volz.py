#
# Copyright (C) 2016  UAVCAN Development Team  <uavcan.org>
#
# This software is distributed under the terms of the MIT License.
#
# Author: Pavel Kirienko <pavel.kirienko@zubax.com>
#

import uavcan
from functools import partial
from PyQt5.QtWidgets import QVBoxLayout, QHBoxLayout, QWidget, QLabel, QDialog, QSlider, QSpinBox, QDoubleSpinBox, \
    QPlainTextEdit, QLineEdit
from PyQt5.QtCore import QTimer, Qt
from logging import getLogger
from ..widgets import make_icon_button, get_icon, get_monospace_font

__all__ = 'PANEL_NAME', 'spawn', 'get_icon'

PANEL_NAME = 'Actuator Panel (Volz)'


logger = getLogger(__name__)

_singleton = None


class PercentSlider(QWidget):
    def __init__(self, parent):
        super(PercentSlider, self).__init__(parent)

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

        layout = QVBoxLayout(self)
        sub_layout = QHBoxLayout(self)
        sub_layout.addWidget(self._slider)
        sub_layout.addWidget(self._spinbox)
        layout.addLayout(sub_layout)
        sub_layout = QHBoxLayout(self)
        sub_layout.addStretch()
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
        self.setLayout(layout)

        self.setMinimumHeight(90)
        
        self._active = False

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
        current = str(round(value * 0.025, 2))
        self._current.setText(current)

    def set_voltage(self, value):
        voltage = str(round(value * 0.2, 1))
        self._voltage.setText(voltage)
        
    def set_temperature(self, value):
        if value == 0xff:
            temperature = 'XX'
        else:
            temperature = str(value - 50)
        self._voltage.setText(temperature)

class ActuatorPanelVolz(QDialog):
    DEFAULT_FREQUENCY = 50
    ACTIVE_INTERVAL = 2.0

    def node_status_callback(self, event):
        # Messages, service requests, service responses, and entire events
        # can be converted into YAML formatted data structure using to_yaml():
        #print('Message: ', uavcan.to_yaml(event))
        for sl in self._sliders:
            if sl.get_id() == event.message.actuator_id:
                sl.set_position(str(round(event.message.position * 100, 1)))
                
    def vols_status_callback(self, event):
        for sl in self._sliders:
            if sl.get_id() == event.transfer.source_node_id:
                sl.set_current(event.message.current)
                sl.set_voltage(event.message.voltage)
                sl.set_temperature(event.message.temperature)

    def __init__(self, parent, node):
        super(ActuatorPanelVolz, self).__init__(parent)
        self.setWindowTitle('Actuator Management Panel (Volz)')
        self.setAttribute(Qt.WA_DeleteOnClose)              # This is required to stop background timers!

        self._node = node
        
        self._paused = False

        self._sliders = [PercentSlider(self)]

        self._num_sliders = QSpinBox(self)
        self._num_sliders.setMinimum(1)
        self._num_sliders.setMaximum(4)
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

        self._pause = make_icon_button('pause', 'Pause publishing', self, text='Pause',
                                       on_clicked=self._do_pause)

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

        layout = QVBoxLayout(self)

        self._slider_layout = QVBoxLayout(self)
        for sl in self._sliders:
            self._slider_layout.addWidget(sl)
        layout.addLayout(self._slider_layout)

        layout.addWidget(self._stop_all)

        controls_layout = QHBoxLayout(self)
        controls_layout.addWidget(QLabel('Channels:', self))
        controls_layout.addWidget(self._num_sliders)
        controls_layout.addWidget(QLabel('Broadcast frequency:', self))
        controls_layout.addWidget(self._bcast_interval)
        controls_layout.addWidget(QLabel('Hz', self))
        controls_layout.addStretch()
        controls_layout.addWidget(self._pause)
        layout.addLayout(controls_layout)

        layout.addWidget(QLabel('Generated message:', self))
        layout.addWidget(self._msg_viewer)
        layout.addLayout(layout)
        
        self.setLayout(layout)
        self.resize(self.minimumWidth(), self.minimumHeight())
        
        # Subscribing to uavcan.equipment.actuator.Status messages
        try:
            self.handle = self._node.add_handler(uavcan.equipment.actuator.Status, self.node_status_callback)
        except Exception as e:
            print('NODE ERROR: ', str(e))
        # Subscribing to volz.ActuatorStatus messages
        try:
            self.handle = self._node.add_handler(uavcan.thirdparty.volz.ActuatorStatus, self.volz_status_callback)
        except Exception as e:
            print('NODE ERROR: ', str(e))

    def _do_broadcast(self):
        try:
            if not self._paused:
                msg = uavcan.equipment.actuator.ArrayCommand()
                for sl in self._sliders:
                    raw_value = sl.get_value() / 100
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
            
    def _show_active(self):
        for sl in self._sliders:
            if not sl.is_active():
                sl.reset_position()
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
            self._slider_layout.addWidget(new)
            self._sliders.append(new)

        def deferred_resize():
            self.resize(self.width(), self.minimumHeight())

        deferred_resize()
        # noinspection PyCallByClass,PyTypeChecker
        #QTimer.singleShot(200, deferred_resize)

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
