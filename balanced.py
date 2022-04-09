#!/usr/bin/env python3
# vim: set expandtab tabstop=4 shiftwidth=4:

# Copyright (c) 2018, 2022, CJ Kucera
# All rights reserved.
#   
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#     * Redistributions of source code must retain the above copyright
#       notice, this list of conditions and the following disclaimer.
#     * Redistributions in binary form must reproduce the above copyright
#       notice, this list of conditions and the following disclaimer in the
#       documentation and/or other materials provided with the distribution.
#     * Neither the name of the development team nor the
#       names of its contributors may be used to endorse or promote products
#       derived from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL CJ KUCERA BE LIABLE FOR ANY
# DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
# ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

import os
import sys
from PyQt5 import QtWidgets, QtGui, QtCore

class Line(object):

    def __init__(self, parent, container, index, top, initial_weight=None):
        self.parent = parent
        self.container = container
        self.index = index
        self.rescaling = False

        # Checkbox to lock
        # (not going to do this at the moment -- I think it's a bit superfluous)
        #self.lockbox = QtWidgets.QCheckBox('Lock', parent)
        #self.lockbox.stateChanged.connect(self.lock_switched)
        #self.container.addWidget(self.lockbox, self.index, 0)

        # Main Slider
        self.slider = QtWidgets.QSlider(QtCore.Qt.Horizontal, parent)
        self.slider.setMinimum(0)
        self.slider.setMaximum(int(top*100))
        if initial_weight is None:
            self.slider.setValue(int(top*100))
        else:
            self.slider.setValue(int(initial_weight*100))
        self.slider.valueChanged.connect(self.slider_changed)
        self.container.addWidget(self.slider, self.index, 1)

        # Textbox for setting the weight
        self.weightbox = QtWidgets.QLineEdit('', parent)
        self.weightbox.setSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Minimum)
        self.weightbox.setMaximumWidth(50)
        if initial_weight is not None:
            self.weightbox.setText(str(initial_weight))
        if self.parent.restrict_target():
            self.disable_weightbox()
        self.weightbox.editingFinished.connect(self.weight_edited)
        self.container.addWidget(self.weightbox, self.index, 2)

        # Perecentage display label
        self.percentlabel = QtWidgets.QLabel('', parent)
        self.percentlabel.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        self.percentlabel.setMinimumWidth(40)
        self.percentlabel.setMaximumWidth(40)
        self.container.addWidget(self.percentlabel, self.index, 3)

        # Remove button
        self.remove_button = QtWidgets.QPushButton('Remove', parent)
        self.remove_button.clicked.connect(self.remove)
        self.container.addWidget(self.remove_button, self.index, 4)

    def remove(self):
        if len(self.parent.lines) > 1:
            for widget in [
                    self.remove_button,
                    self.slider,
                    self.weightbox,
                    self.percentlabel,
                    #self.lockbox,
                    ]:
                self.container.removeWidget(widget)
                widget.deleteLater()
                widget = None
            self.parent.removed_line(self)

    def lock_switched(self):
        if self.lockbox.isChecked():
            self.slider.setDisabled(True)
            self.weightbox.setDisabled(True)
        else:
            self.slider.setDisabled(False)
            self.weightbox.setDisabled(False)

    def enable_remove(self):
        self.remove_button.setDisabled(False)

    def disable_remove(self):
        self.remove_button.setDisabled(True)

    def enable_weightbox(self):
        self.weightbox.setReadOnly(False)

    def disable_weightbox(self):
        self.weightbox.setReadOnly(True)

    def slider_changed(self, value):
        if not self.rescaling:
            self.parent.update_weights()

    def value(self):
        return self.slider.value()/100

    def weight(self):
        try:
            return float(self.weightbox.text())
        except ValueError:
            return 100

    def set_weight(self, weight):
        if weight == 0:
            self.weightbox.setText('0')
        elif weight < 1:
            self.weightbox.setText('{}'.format(round(weight, 2)))
        elif weight < 10:
            self.weightbox.setText('{}'.format(round(weight, 1)))
        else:
            self.weightbox.setText('{}'.format(round(weight)))

    def set_percent(self, percent):
        percent *= 100
        if percent == 0:
            self.percentlabel.setText('0%')
        elif percent < 1:
            self.percentlabel.setText('{}%'.format(round(percent, 2)))
        elif percent < 10:
            self.percentlabel.setText('{}%'.format(round(percent, 1)))
        else:
            self.percentlabel.setText('{}%'.format(round(percent)))

    def set_new_max(self, new_top):
        self.rescaling = True
        self.slider.setMaximum(int(new_top*100))
        self.rescaling = False

    def rescale_to_new_absolute(self, new_top, value):
        self.rescaling = True
        self.slider.setMaximum(int(new_top*100))
        self.slider.setValue(int(value*100))
        self.rescaling = False

    def rescale_to_new_max(self, new_top, percent):
        self.rescaling = True
        self.slider.setMaximum(int(new_top*100))
        self.slider.setValue(int(new_top*100*percent))
        self.rescaling = False

    def weight_edited(self):
        try:
            new_value = float(self.weightbox.text())
        except ValueError:
            return
        new_value *= 100
        if new_value < 0:
            new_value = 0
        elif new_value > self.slider.maximum():
            new_value = self.slider.maximum()
        self.slider.setValue(int(new_value))

class Gui(QtWidgets.QMainWindow):

    def __init__(self):
        super().__init__()
        self.lines = []
        self.initUI()

    def initUI(self):

        # Basic UI
        self.setMinimumSize(500, 400)
        self.setWindowTitle('Balanced Weight Generator')

        # Menu
        menubar = self.menuBar()
        fileMenu = menubar.addMenu('&File')
        fileMenu.addAction('&Quit', self.close, 'Ctrl+Q')

        # Set up a main vbox to use
        layout = QtWidgets.QVBoxLayout()
        vbox = QtWidgets.QWidget()
        vbox.setLayout(layout)
        self.setCentralWidget(vbox)

        # Frame for our top controls
        frame = QtWidgets.QFrame()
        frame.setFrameShadow(frame.Raised)
        frame.setFrameShape(frame.Panel)
        frame.setLineWidth(2)
        layout.addWidget(frame, 0, QtCore.Qt.AlignTop)

        # Set up an hbox for the top row
        hlayout = QtWidgets.QHBoxLayout()
        frame.setLayout(hlayout)

        # Checkbox for if we're locking to target
        self.target_box = QtWidgets.QCheckBox('Target Weight:', self)
        self.target_box.setChecked(False)
        self.target_box.stateChanged.connect(self.target_weight_toggled)
        hlayout.addWidget(self.target_box)

        # Input for our Target Weight
        self.target_weight = QtWidgets.QLineEdit('100', self)
        self.target_weight.setSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Minimum)
        self.target_weight.setDisabled(True)
        self.target_weight.setMinimumWidth(50)
        self.target_weight.setMaximumWidth(50)
        self.target_weight.textEdited.connect(self.target_updated)
        hlayout.addWidget(self.target_weight)

        # Spacer
        spacer = QtWidgets.QLabel()
        spacer.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        hlayout.addWidget(spacer)

        # Add Item button
        self.add_item_button = QtWidgets.QPushButton('Add Item', self)
        self.add_item_button.clicked.connect(self.add_line)
        hlayout.addWidget(self.add_item_button)

        # Now a separate GridLayout to hold our items
        self.itembox = QtWidgets.QGridLayout()
        widget = QtWidgets.QWidget()
        widget.setLayout(self.itembox)
        layout.addWidget(widget, 0, QtCore.Qt.AlignTop)

        # Spacer at the bottom
        spacer_bottom = QtWidgets.QLabel()
        spacer_bottom.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        layout.addWidget(spacer_bottom)

        # Add a single line to start with
        self.add_line()

        # Show ourselves
        self.show()

    def target(self):
        try:
            return float(self.target_weight.text())
        except ValueError:
            return 100

    def get_max_and_top_value(self):
        """
        Returns a tuple...
        """
        if self.restrict_target():
            return (None, 10000)
        else:
            if len(self.lines) > 0:
                max_weight = max([line.value() for line in self.lines])
            else:
                max_weight = 100
            return (max_weight, max_weight*2)

    def add_line(self):
        (max_weight, top) = self.get_max_and_top_value()
        if self.restrict_target():
            initial_weight = None
        else:
            initial_weight = max_weight
            for line in self.lines:
                line.set_new_max(top)
        line = Line(self, self.itembox, self.itembox.rowCount(), top, initial_weight=initial_weight)
        self.lines.append(line)
        self.update_remove_buttons()
        self.update_weights()

    def removed_line(self, line):
        self.lines.remove(line)
        self.update_remove_buttons()
        if not self.restrict_target():
            (max_weight, top) = self.get_max_and_top_value()
            for line in self.lines:
                line.set_new_max(top)
        self.update_weights()

    def update_remove_buttons(self):
        if len(self.lines) < 2:
            for line in self.lines:
                line.disable_remove()
        else:
            for line in self.lines:
                line.enable_remove()

    def update_weights(self):

        # First calculate percentages, which works the same whether we're
        # limiting our total weight or not
        total = sum([line.value() for line in self.lines])
        if total > 0:
            percents = [line.value()/total for line in self.lines]
        else:
            percents = [0 for line in self.lines]
        for (line, percent) in zip(self.lines, percents):
            line.set_percent(percent)

        # Now see if we do anything with the weights.  If we're restricting
        # the total weight, all our weights might change.  Otherwise, just
        # keep 'em the way they are.
        if self.restrict_target():
            target = self.target()
            weights = [p * target for p in percents]
            for (line, weight) in zip(self.lines, weights):
                line.set_weight(weight)
        else:
            for line in self.lines:
                line.set_weight(line.value())

            # Also update our locked weight box
            if total == 0:
                self.target_weight.setText('100')
            elif total < 1:
                self.target_weight.setText('{}'.format(round(total, 2)))
            elif total < 10:
                self.target_weight.setText('{}'.format(round(total, 1)))
            else:
                self.target_weight.setText('{}'.format(round(total)))

    def target_weight_toggled(self):
        if self.restrict_target():
            for line in self.lines:
                line.disable_weightbox()
            self.target_weight.setDisabled(False)
            total = sum([line.value() for line in self.lines])
            if total > 0:
                percents = [line.value()/total for line in self.lines]
            else:
                percents = [0 for line in self.lines]
            (max_weight, top) = self.get_max_and_top_value()
            for (line, percent) in zip(self.lines, percents):
                line.rescale_to_new_max(top, percent)
            self.update_weights()
        else:
            for line in self.lines:
                line.enable_weightbox()
            self.target_weight.setDisabled(True)
            real_max = max([line.weight() for line in self.lines])
            if real_max == 0:
                real_max = 100
            for line in self.lines:
                line.rescale_to_new_absolute(real_max*2, line.weight())

    def restrict_target(self):
        return self.target_box.isChecked()

    def target_updated(self):
        self.update_weights()

def main():

    app = QtWidgets.QApplication(sys.argv)
    gui = Gui()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()

