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
    QPlainTextEdit
from PyQt5.QtCore import QTimer, Qt
from logging import getLogger
from ..widgets import make_icon_button, get_icon, get_monospace_font

__all__ = 'PANEL_NAME', 'spawn', 'get_icon'

PANEL_NAME = 'Actuator Panel'


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
        self._spinbox.setFixedWidth(80)

        self._idbox = QSpinBox(self)
        self._idbox.setMinimum(1)
        self._idbox.setMaximum(255)
        self._idbox.setValue(1)
        self._idbox.setFixedWidth(40)

        self._zero_button = make_icon_button('hand-stop-o', 'Zero setpoint', self, on_clicked=self.zero)
        self._zero_button.setFixedWidth(80)

        layout = QVBoxLayout(self)
        sub_layout = QHBoxLayout(self)
        sub_layout.addWidget(self._slider)
        layout.addLayout(sub_layout)
        sub_layout = QHBoxLayout(self)
        sub_layout.addStretch()
        sub_layout.addWidget(QLabel('ID:', self))
        sub_layout.addWidget(self._idbox)
        sub_layout.addStretch()
        sub_layout.addWidget(self._spinbox)
        sub_layout.addWidget(self._zero_button)
        sub_layout.addStretch()
        layout.addLayout(sub_layout)
        self.setLayout(layout)

        self.setMinimumHeight(80)

    def zero(self):
        self._slider.setValue(0)

    def get_value(self):
        return self._slider.value()
        
    def get_id(self):
        return self._idbox.value()


class ActuatorPanel(QDialog):
    DEFAULT_INTERVAL = 0.1

    def node_status_callback(event):
        print('NodeStatus message from node', event.transfer.source_node_id)
        print('Node uptime:', event.message.uptime_sec, 'seconds')
        # Messages, service requests, service responses, and entire events
        # can be converted into YAML formatted data structure using to_yaml():
        print(uavcan.to_yaml(event))

    def __init__(self, parent, node):
        super(ActuatorPanel, self).__init__(parent)
        self.setWindowTitle('Actuator Management Panel')
        self.setAttribute(Qt.WA_DeleteOnClose)              # This is required to stop background timers!

        self._node = node

        self._sliders = [PercentSlider(self)]

        self._num_sliders = QSpinBox(self)
        self._num_sliders.setMinimum(1)
        self._num_sliders.setMaximum(4)
        self._num_sliders.setValue(1)
        self._num_sliders.valueChanged.connect(self._update_number_of_sliders)

        self._bcast_interval = QDoubleSpinBox(self)
        self._bcast_interval.setMinimum(0.01)
        self._bcast_interval.setMaximum(1.0)
        self._bcast_interval.setSingleStep(0.1)
        self._bcast_interval.setValue(self.DEFAULT_INTERVAL)
        self._bcast_interval.setMinimumWidth(50)
        self._bcast_interval.valueChanged.connect(
            lambda: self._bcast_timer.setInterval(self._bcast_interval.value() * 1e3))

        self._stop_all = make_icon_button('hand-stop-o', 'Zero all channels', self, text='Zero All',
                                          on_clicked=self._do_stop_all)

        self._pause = make_icon_button('pause', 'Pause publishing', self, checkable=True, text='Pause')

        self._msg_viewer = QPlainTextEdit(self)
        self._msg_viewer.setReadOnly(True)
        self._msg_viewer.setLineWrapMode(QPlainTextEdit.NoWrap)
        self._msg_viewer.setFont(get_monospace_font())
        self._msg_viewer.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self._msg_viewer.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        self._bcast_timer = QTimer(self)
        self._bcast_timer.start(self.DEFAULT_INTERVAL * 1e3)
        self._bcast_timer.timeout.connect(self._do_broadcast)

        layout = QVBoxLayout(self)

        self._slider_layout = QVBoxLayout(self)
        for sl in self._sliders:
            self._slider_layout.addWidget(sl)
        layout.addLayout(self._slider_layout)

        layout.addWidget(self._stop_all)

        controls_layout = QHBoxLayout(self)
        controls_layout.addWidget(QLabel('Channels:', self))
        controls_layout.addWidget(self._num_sliders)
        controls_layout.addWidget(QLabel('Broadcast interval:', self))
        controls_layout.addWidget(self._bcast_interval)
        controls_layout.addWidget(QLabel('sec', self))
        controls_layout.addStretch()
        controls_layout.addWidget(self._pause)
        layout.addLayout(controls_layout)

        layout.addWidget(QLabel('Generated message:', self))
        layout.addWidget(self._msg_viewer)
        layout.addLayout(layout)
        
        self.setLayout(layout)
        self.resize(self.minimumWidth(), self.minimumHeight())
        
        # Subscribing to messages
        #handle = self._node.add_handler(uavcan.equipment.actuator.Status, node_status_callback)
        
    
    def closeEvent(self, evnt):
        print('Closed')


    def _do_broadcast(self):
        try:
            if not self._pause.isChecked():
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

    def _do_stop_all(self):
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
        super(ActuatorPanel, self).closeEvent(event)


def spawn(parent, node):
    global _singleton
    if _singleton is None:
        _singleton = ActuatorPanel(parent, node)

    _singleton.show()
    _singleton.raise_()
    _singleton.activateWindow()

    return _singleton


get_icon = partial(get_icon, 'asterisk')
