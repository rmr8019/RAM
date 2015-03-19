"""Code to create the graphical user interface to be used for performing
temperature emissivity separation.

title:              tes_gui

author:             Ryan LaClair
                    rgl8828@rit.edu

date:               April-June 2014
"""

import sys
from PyQt4 import QtGui, QtCore
import numpy as np
import xml.etree.ElementTree as et

import matplotlib.pyplot as plt
import matplotlib.animation as ani
from matplotlib.backends.backend_qt4agg import (FigureCanvasQTAgg
    as FigureCanvas)
from matplotlib.backends.backend_qt4agg import (NavigationToolbar2QT
    as NavigationToolbar)

import dp_radiance_calibration as dp
import tes
from bb_radiance import bbRadiance

class MainWindow(QtGui.QWidget):
    """The main window of the GUI that is composed of 3 selectable tabs.
    """

    def __init__(self):
        """Constructor method for main window.
        """

        super(MainWindow, self).__init__()

        self.initUI()
        self.show()

    def initUI(self):
        """Initialize the top level of the main window user interface layout.
        The layout consists of a tabbed interface, a text box used to display
        the estimated temperature, and a set of OK and Cancel buttons.
        """

        layout = QtGui.QVBoxLayout()

        layout.addWidget(self._windowTabs())
        layout.addWidget(self._temperatureBox())
        layout.addLayout(self._buttons())

        self.setLayout(layout)
        self.setWindowTitle('Temperature Emissivity Separation')
        self.setMinimumHeight(451)

        self.cancelButton.setFocus(True)

    def _windowTabs(self):
        """Creates the tabbed interface with tabs for file selection, program
        option selection, and information about the program.
        """

        windowTabs = QtGui.QTabWidget()

        filesTab = QtGui.QWidget()
        filesTab.setLayout(self._fileSelector())

        optionsTab = QtGui.QWidget()
        optionsTab.setLayout(self._optionSelector())

        aboutTab = QtGui.QWidget()
        aboutTab.setLayout(self._about())

        windowTabs.addTab(filesTab, 'Files')
        windowTabs.addTab(optionsTab, 'Options')
        windowTabs.addTab(aboutTab, 'About')

        return windowTabs

    def _fileSelector(self):
        """Creates the layout used for the file selection tab.
        """

        self.cbb = QtGui.QLabel('Cold blackbody:')
        self.wbb = QtGui.QLabel('Warm blackbody:')
        self.sam = QtGui.QLabel('Sample:')
        self.dwr = QtGui.QLabel('Downwelling:')
        self.plate = QtGui.QLabel('Plate emissivity:')

        self.cbbEdit = QtGui.QLineEdit()
        self.cbbEdit.setPlaceholderText('Required..')
        self.wbbEdit = QtGui.QLineEdit()
        self.wbbEdit.setPlaceholderText('Required..')
        self.samEdit = QtGui.QLineEdit()
        self.samEdit.setPlaceholderText('Required..')
        self.dwrEdit = QtGui.QLineEdit()
        self.dwrEdit.setPlaceholderText('Optional..')
        self.plateEdit = QtGui.QLineEdit()
        self.plateEdit.setPlaceholderText('Optional..')

        self.cbbButton = QtGui.QPushButton('Browse')
        self.cbbButton.setFixedWidth(100)
        self.wbbButton = QtGui.QPushButton('Browse')
        self.wbbButton.setFixedWidth(100)
        self.samButton = QtGui.QPushButton('Browse')
        self.samButton.setFixedWidth(100)
        self.dwrButton = QtGui.QPushButton('Browse')
        self.dwrButton.setFixedWidth(100)

        fileSelectorLayout = QtGui.QGridLayout()
        fileSelectorLayout.addWidget(self.cbb, 0, 0, QtCore.Qt.AlignRight)
        fileSelectorLayout.addWidget(self.cbbEdit, 0, 1)
        fileSelectorLayout.addWidget(self.cbbButton, 0, 2)
        fileSelectorLayout.addWidget(self.wbb, 1, 0, QtCore.Qt.AlignRight)
        fileSelectorLayout.addWidget(self.wbbEdit, 1, 1)
        fileSelectorLayout.addWidget(self.wbbButton, 1, 2)
        fileSelectorLayout.addWidget(self.sam, 2, 0, QtCore.Qt.AlignRight)
        fileSelectorLayout.addWidget(self.samEdit, 2, 1)
        fileSelectorLayout.addWidget(self.samButton, 2, 2)
        fileSelectorLayout.addWidget(self.dwr, 3, 0, QtCore.Qt.AlignRight)
        fileSelectorLayout.addWidget(self.dwrEdit, 3, 1)
        fileSelectorLayout.addWidget(self.dwrButton, 3, 2)
        fileSelectorLayout.addWidget(self.plate, 4, 0, QtCore.Qt.AlignRight)
        fileSelectorLayout.addWidget(self.plateEdit, 4, 1)

        self.cbbButton.clicked.connect(self._handleCbbButton)
        self.wbbButton.clicked.connect(self._handleWbbButton)
        self.samButton.clicked.connect(self._handleSamButton)
        self.dwrButton.clicked.connect(self._handleDwrButton)

        return fileSelectorLayout

    def _handleCbbButton(self):
        """Open a file selection dialog to choose a .cbb (cold blackbody) file
        when the corresponding CBB button is pressed, and update the CBB text
        area to reflect the chosen file.
        """

        self.cbbEdit.setText(QtGui.QFileDialog.getOpenFileName(self,
            'Choose a cold blackbody file..', '', 'CBB (*.cbb)'))

    def _handleWbbButton(self):
        """Open a file selection dialog to choose a .wbb (warm blackbody) file
        when the corresponding WBB button is pressed, and update the WBB text
        area to reflect the chosen file.
        """

        self.wbbEdit.setText(QtGui.QFileDialog.getOpenFileName(self,
            'Choose a warm blackbody file..', '', 'WBB (*.wbb)'))

    def _handleSamButton(self):
        """Open a file selection dialog to choose a .sam (sample) file when the
        corresponding SAM button is pressed, and update the SAM text area to
        reflect the chosen file.
        """

        self.samEdit.setText(QtGui.QFileDialog.getOpenFileName(self,
            'Choose a sample file..', '', 'SAM (*.sam)'))

    def _handleDwrButton(self):
        """Open a file selection dialog to choose a .dwr (downwelling) file
        when the corresponding DWR button is pressed, and update the DWR text
        area to reflect the chosen file.
        """

        self.dwrEdit.setText(QtGui.QFileDialog.getOpenFileName(self,
            'Choose a downwelling file..', '', 'DWR (*.dwr)'))

    def _parseConfig(self):
        """
        """

        tree = et.parse('tes_config.xml')

        for method in tree.iterfind('method'):
            if (method.attrib['name'] == 'waterband'):
                self.wbTolerance = method.find('variationTolerance').text

                self.wbLowerTemp = method.find('temperatureLimits/lower').text
                self.wbUpperTemp = method.find('temperatureLimits/upper').text

                self.wbLowerWave = method.find('wavelengthLimits/lower').text
                self.wbUpperWave = method.find('wavelengthLimits/upper').text

            elif (method.attrib['name'] == 'standard'):
                self.stdTolerance = method.find('variationTolerance').text

                self.stdLowerTemp = method.find('temperatureLimits/lower').text
                self.stdUpperTemp = method.find('temperatureLimits/upper').text

                self.stdLowerWave = method.find('wavelengthLimits/lower').text
                self.stdUpperWave = method.find('wavelengthLimits/upper').text

            elif (method.attrib['name'] == 'moving window'):
                self.mwTolerance = method.find('variationTolerance').text

                self.mwLowerTemp = method.find('temperatureLimits/lower').text
                self.mwUpperTemp = method.find('temperatureLimits/upper').text

                self.mwLowerWave = method.find('wavelengthLimits/lower').text
                self.mwUpperWave = method.find('wavelengthLimits/upper').text

                self.mwWinWidth = method.find('windowWidth').text

            elif (method.attrib['name'] == 'variable moving window'):
                self.vmwTolerance = method.find('variationTolerance').text

                self.vmwLowerTemp = method.find('temperatureLimits/lower').text
                self.vmwUpperTemp = method.find('temperatureLimits/upper').text

                self.vmwLowerWave = method.find('wavelengthLimits/lower').text
                self.vmwUpperWave = method.find('wavelengthLimits/upper').text

                self.vmwLowerWinWidth = method.find('windowWidthLimits/lower').text
                self.vmwUpperWinWidth = method.find('windowWidthLimits/upper').text

                self.vmwWinStep = method.find('windowStep').text

            else:
                self.mmwTolerance = method.find('variationTolerance').text

                self.mmwLowerTemp = method.find('temperatureLimits/lower').text
                self.mmwUpperTemp = method.find('temperatureLimits/upper').text

                self.mmwLowerWave = method.find('wavelengthLimits/lower').text
                self.mmwUpperWave = method.find('wavelengthLimits/upper').text

                self.mmwLowerWinWidth = method.find('windowWidthLimits/lower').text
                self.mmwUpperWinWidth = method.find('windowWidthLimits/upper').text

                self.mmwWinStep = method.find('windowStep').text
                self.mmwNumWins = method.find('numWindows').text

    def _optionSelector(self):
        """Creates the layout for the option selection tab.
        """

        self._parseConfig()

        self.technique = QtGui.QLabel('Technique:')
        self.measurementTolerance = QtGui.QLabel('Coadd variation tolerance:')
        self.tempLimits = QtGui.QLabel('Search interval temperature limits:')
        self.waveLimits = QtGui.QLabel('Waterband wavelength limits:')
        self.windowLimits = QtGui.QLabel('Window width:')
        self.windowStep = QtGui.QLabel('Window step:')
        self.numWindows = QtGui.QLabel('Number of windows:')
        self.plots = QtGui.QLabel('Plots:')
        self.percent = QtGui.QLabel('%')
        self.k1 = QtGui.QLabel('K')
        self.k2 = QtGui.QLabel('K')
        self.micron1 = QtGui.QLabel('microns')
        self.micron2 = QtGui.QLabel('microns')
        self.micron3 = QtGui.QLabel('microns')
        self.micron4 = QtGui.QLabel('microns')
        self.micron5 = QtGui.QLabel('microns')

        # measurement tolerance
        self.measurementToleranceEdit = QtGui.QLineEdit()
        self.measurementToleranceEdit.setFixedWidth(75)
        self.measurementToleranceEdit.setText(self.wbTolerance)

        # temperature range
        self.minTempEdit = QtGui.QLineEdit()
        self.minTempEdit.setFixedWidth(75)
        self.minTempEdit.setText(self.wbLowerTemp)
        self.maxTempEdit = QtGui.QLineEdit()
        self.maxTempEdit.setFixedWidth(75)
        self.maxTempEdit.setText(self.wbUpperTemp)

        # wavelength range
        self.minWaveEdit = QtGui.QLineEdit()
        self.minWaveEdit.setFixedWidth(75)
        self.minWaveEdit.setText(self.wbLowerWave)
        self.maxWaveEdit = QtGui.QLineEdit()
        self.maxWaveEdit.setFixedWidth(75)
        self.maxWaveEdit.setText(self.wbUpperWave)

        # window size range
        self.minWinEdit = QtGui.QLineEdit()
        self.minWinEdit.setFixedWidth(75)
        self.maxWinEdit = QtGui.QLineEdit()
        self.maxWinEdit.setFixedWidth(75)

        # number of window steps
        self.windowStepEdit = QtGui.QLineEdit()
        self.windowStepEdit.setFixedWidth(75)

        # number of windows
        self.numWindowsEdit = QtGui.QLineEdit()
        self.numWindowsEdit.setFixedWidth(75)

        self.techniqueComboBox = QtGui.QComboBox(self)
        self.techniqueComboBox.addItem(
            'Waterband Temperature Emissivity Separation')
        self.techniqueComboBox.addItem(
            'Standard Temperature Emissivity Separation')
        self.techniqueComboBox.addItem(
            'Moving Window Temperature Emissivity Separation')
        self.techniqueComboBox.addItem(
            'Variable Moving Window Temperature Emissivity Separation')
        self.techniqueComboBox.addItem(
            'Multiple Moving Window Temperature Emissivity Separation')
        self.techniqueComboBox.currentIndexChanged.connect(
            self._handleTechnique)

        self.radiancePlotCheckBox = QtGui.QCheckBox('Calibrated radiance')
        self.emissivityPlotCheckBox = QtGui.QCheckBox('Calculated emissivity')
        self.emissivitySearchCheckBox = QtGui.QCheckBox('Emissivity search')
        self.metricPlotCheckBox = QtGui.QCheckBox('Variation criterea')

        # tooltips
        self.measurementTolerance.setToolTip('Maximum allowed error between coadds.')
        self.measurementToleranceEdit.setToolTip(self.measurementTolerance.toolTip())
        self.tempLimits.setToolTip('Upper and lower temperature limits on which to perform the emissivity search.')
        self.minTempEdit.setToolTip('Lower temperature limit')
        self.maxTempEdit.setToolTip('Upper temperature limit')
        self.waveLimits.setToolTip('Upper and lower waterband wavelength limits to be used in the temperature determination.')
        self.minWaveEdit.setToolTip('Lower waterband limit')
        self.maxWaveEdit.setToolTip('Upper waterband limit')
        self.windowLimits.setToolTip('Width of the wavelength window to examine across the spectrum.')
        self.minWinEdit.setToolTip(self.windowLimits.toolTip())
        self.maxWinEdit.setToolTip('Upper window limit')
        self.windowStep.setToolTip('The step to increase the window width within the limits.')
        self.windowStepEdit.setToolTip(self.windowStep.toolTip())
        self.numWindows.setToolTip('The total number of windows to examine at one time.')
        self.numWindowsEdit.setToolTip(self.numWindows.toolTip())
        self.radiancePlotCheckBox.setToolTip('Display a plot of the calibrated radiance curves for the sample, downwelling, cold blackbody and warm blackbody.')
        self.emissivityPlotCheckBox.setToolTip('Display a plot of the final calculated emissivity.')
        self.emissivitySearchCheckBox.setToolTip('Display a dynamic plot of the emissivity curve at each temperature examined.')
        self.metricPlotCheckBox.setToolTip('Display a plot of the variation metric used to determine the best temperature approximation.')

        checkBoxLayout = QtGui.QGridLayout()
        checkBoxLayout.addWidget(self.radiancePlotCheckBox, 0, 0)
        checkBoxLayout.addWidget(self.emissivityPlotCheckBox, 0, 1)
        checkBoxLayout.addWidget(self.emissivitySearchCheckBox, 1, 0)
        checkBoxLayout.addWidget(self.metricPlotCheckBox, 1, 1)
        checkBoxLayout.setContentsMargins(0, 0, 0, 0)

        checkBoxWidget = QtGui.QFrame()
        checkBoxWidget.setLayout(checkBoxLayout)

        self.measurementToleranceUnits = self._addUnits(self.measurementToleranceEdit, self.percent)
        self.tempLimitsUnits = self._addUnits(self.minTempEdit, self.k1, self.maxTempEdit, self.k2)
        self.waveLimitsUnits = self._addUnits(self.minWaveEdit, self.micron1, self.maxWaveEdit, self.micron2)
        self.windowLimitsUnits = self._addUnits(self.minWinEdit, self.micron3, self.maxWinEdit, self.micron4)
        self.windowStepUnits = self._addUnits(self.windowStepEdit, self.micron5)

        windowLimitsWidget = self._makeWidget(self.windowLimitsUnits)
        windowStepWidget = self._makeWidget(self.windowStepUnits)
        numWindowsWidget = self._makeWidget(self.numWindowsEdit)

        optionSelectorLayout = QtGui.QGridLayout()
        optionSelectorLayout.addWidget(self.technique, 0, 0,
            QtCore.Qt.AlignRight)
        optionSelectorLayout.addWidget(self.techniqueComboBox, 0, 1)
        optionSelectorLayout.addWidget(self.measurementTolerance, 1, 0, QtCore.Qt.AlignRight)
        optionSelectorLayout.addWidget(self.measurementToleranceUnits, 1, 1)
        optionSelectorLayout.addWidget(self.tempLimits, 2, 0,
            QtCore.Qt.AlignRight)
        optionSelectorLayout.addWidget(self.tempLimitsUnits, 2, 1)
        optionSelectorLayout.addWidget(self.waveLimits, 3, 0,
            QtCore.Qt.AlignRight)
        optionSelectorLayout.addWidget(self.waveLimitsUnits, 3, 1)
        optionSelectorLayout.addWidget(self.windowLimits, 4, 0, QtCore.Qt.AlignRight)
        optionSelectorLayout.addWidget(windowLimitsWidget, 4, 1)
        optionSelectorLayout.addWidget(self.windowStep, 5, 0, QtCore.Qt.AlignRight)
        optionSelectorLayout.addWidget(windowStepWidget, 5, 1)
        optionSelectorLayout.addWidget(self.numWindows, 6, 0, QtCore.Qt.AlignRight)
        optionSelectorLayout.addWidget(numWindowsWidget, 6, 1, QtCore.Qt.AlignLeft)
        optionSelectorLayout.addWidget(self.plots, 7, 0, QtCore.Qt.AlignRight)
        optionSelectorLayout.addWidget(checkBoxWidget, 7, 1)

        self._waterbandOptions()

        return optionSelectorLayout

    def _makeWidget(self, item):
        """
        """

        widget = QtGui.QFrame()
        layout = QtGui.QHBoxLayout()

        layout.addWidget(item)

        layout.setContentsMargins(0, 0, 0, 0)
        widget.setLayout(layout)

        return widget

    def _addUnits(self, edit1, label1, edit2=None, label2=None):
        """Helper function to create a sublayout.  For use in adding units to
        Qt Edit boxes.

        arguments:
            edit1 - First edit box.
            label1 - First label.
            edit2 - Second edit box (optional).
            label2 - Second label (optional).

        returns:
            A horizontal box layout containing the specified elements.
        """

        unitWidget = QtGui.QFrame()

        unitLayout = QtGui.QHBoxLayout()

        unitLayout.addWidget(edit1)
        unitLayout.addWidget(label1)

        if not edit2 is None:
            unitLayout.addWidget(edit2)

        if not label2 is None:
            unitLayout.addWidget(label2)

        unitLayout.setContentsMargins(0, 0, 0, 0)

        unitWidget.setLayout(unitLayout)

        return unitWidget

    def _handleTechnique(self):
        """Make necessary changes to wavelength range, window size range, and
        number of windows when a different temperature emissivity separation
        technique is chosen.
        """

        technique = str(self.techniqueComboBox.currentText())

        if ('Waterband' in technique):
            self._waterbandOptions()
        elif ('Standard' in technique):
            self._standardOptions()
        elif ('Variable' in technique):
            self._variableOptions()
        elif ('Multiple' in technique):
            self._multipleOptions()
        else:
            self._movingOptions()

    def _waterbandOptions(self):
        """
        """

        self.waveLimits.setText('Waterband wavelength limits:')

        self.measurementToleranceEdit.setText(self.wbTolerance)
        self.minTempEdit.setText(self.wbLowerTemp)
        self.maxTempEdit.setText(self.wbUpperTemp)
        self.minWaveEdit.setText(self.wbLowerWave)
        self.maxWaveEdit.setText(self.wbUpperWave)
        self.minWinEdit.setText('')
        self.maxWinEdit.setText('')
        self.windowStepEdit.setText('')
        self.numWindowsEdit.setText('')
        self.metricPlotCheckBox.setText('Variation criterea')

        self.waveLimits.setToolTip('Upper and lower waterband wavelength limits to be used in the temperature determination.')

        self.windowLimits.setVisible(False)
        self.windowLimitsUnits.setVisible(False)
        self.windowStep.setVisible(False)
        self.windowStepUnits.setVisible(False)
        self.numWindows.setVisible(False)
        self.numWindowsEdit.setVisible(False)
        self.emissivitySearchCheckBox.setVisible(True)
        self.metricPlotCheckBox.setVisible(True)

        self.waveLimits.setToolTip('Upper and lower waterband wavelength limits to be used in the temperature determination.')
        self.minWaveEdit.setToolTip('Lower waterband limit')
        self.maxWaveEdit.setToolTip('Upper waterband limit')
        self.metricPlotCheckBox.setToolTip('Display a plot of the variation metric used to determine the best temperature approximation.')

    def _standardOptions(self):
        """
        """

        self.waveLimits.setText('Wavelength limits:')

        self.measurementToleranceEdit.setText(self.stdTolerance)
        self.minTempEdit.setText(self.stdLowerTemp)
        self.maxTempEdit.setText(self.stdUpperTemp)
        self.minWaveEdit.setText(self.stdLowerWave)
        self.maxWaveEdit.setText(self.stdUpperWave)
        self.minWinEdit.setText('')
        self.maxWinEdit.setText('')
        self.windowStepEdit.setText('')
        self.numWindowsEdit.setText('')
        self.metricPlotCheckBox.setText('Smoothness criterea')

        self.metricPlotCheckBox.setChecked(False)

        self.windowLimits.setVisible(False)
        self.windowLimitsUnits.setVisible(False)
        self.windowStep.setVisible(False)
        self.windowStepUnits.setVisible(False)
        self.numWindows.setVisible(False)
        self.numWindowsEdit.setVisible(False)
        self.emissivitySearchCheckBox.setVisible(True)
        self.metricPlotCheckBox.setVisible(True)

        self.waveLimits.setToolTip('Upper and lower wavelength limits to be used in the temperature determination.')
        self.minWaveEdit.setToolTip('Lower wavelength limit')
        self.maxWaveEdit.setToolTip('Upper wavelength limit')
        self.metricPlotCheckBox.setToolTip('Display a plot of the smoothness metric used to determine the best temperature approximation.')

    def _movingOptions(self):
        """
        """

        self.waveLimits.setText('Search range:')
        self.windowLimits.setText('Window width:')

        self.measurementToleranceEdit.setText(self.mwTolerance)
        self.minTempEdit.setText(self.mwLowerTemp)
        self.maxTempEdit.setText(self.mwUpperTemp)
        self.minWaveEdit.setText(self.mwLowerWave)
        self.maxWaveEdit.setText(self.mwUpperWave)
        self.minWinEdit.setText(self.mwWinWidth)
        self.maxWinEdit.setText('')
        self.windowStepEdit.setText('')
        self.numWindowsEdit.setText('')

        self.emissivitySearchCheckBox.setChecked(False)
        self.metricPlotCheckBox.setChecked(False)

        self.maxWinEdit.setVisible(False)
        self.micron4.setVisible(False)
        self.windowLimits.setVisible(True)
        self.windowLimitsUnits.setVisible(True)
        self.windowStep.setVisible(False)
        self.windowStepUnits.setVisible(False)
        self.numWindows.setVisible(False)
        self.numWindowsEdit.setVisible(False)
        self.emissivitySearchCheckBox.setVisible(False)
        self.metricPlotCheckBox.setVisible(False)

        self.waveLimits.setToolTip('Upper and lower wavelength limits to be used in the temperature determination.')
        self.minWaveEdit.setToolTip('Lower wavelength limit')
        self.maxWaveEdit.setToolTip('Upper wavelength limit')
        self.windowLimits.setToolTip('Width of the wavelength window to examine across the spectrum.')
        self.minWinEdit.setToolTip(self.windowLimits.toolTip())

    def _variableOptions(self):
        """
        """

        self.waveLimits.setText('Search range:')
        self.windowLimits.setText('Window width limits:')
        self.windowStep.setText('Window step:')

        self.measurementToleranceEdit.setText(self.vmwTolerance)
        self.minTempEdit.setText(self.vmwLowerTemp)
        self.maxTempEdit.setText(self.vmwUpperTemp)
        self.minWaveEdit.setText(self.vmwLowerWave)
        self.maxWaveEdit.setText(self.vmwUpperWave)
        self.minWinEdit.setText(self.vmwLowerWinWidth)
        self.maxWinEdit.setText(self.vmwUpperWinWidth)
        self.windowStepEdit.setText(self.vmwWinStep)
        self.numWindowsEdit.setText('')

        self.emissivitySearchCheckBox.setChecked(False)
        self.metricPlotCheckBox.setChecked(False)

        self.maxWinEdit.setVisible(True)
        self.micron4.setVisible(True)
        self.windowLimits.setVisible(True)
        self.windowLimitsUnits.setVisible(True)
        self.windowStep.setVisible(True)
        self.windowStepUnits.setVisible(True)
        self.numWindows.setVisible(False)
        self.numWindowsEdit.setVisible(False)
        self.emissivitySearchCheckBox.setVisible(False)
        self.metricPlotCheckBox.setVisible(False)

        self.waveLimits.setToolTip('Upper and lower wavelength limits to be used in the temperature determination.')
        self.minWaveEdit.setToolTip('Lower wavelength limit')
        self.maxWaveEdit.setToolTip('Upper wavelength limit')
        self.windowLimits.setToolTip('Upper and lower limits of the wavelength window to examine across the spectrum.')
        self.minWinEdit.setToolTip('Lower window limit')
        self.maxWinEdit.setToolTip('Upper window limit')

    def _multipleOptions(self):
        """
        """

        self.waveLimits.setText('Search range:')
        self.windowLimits.setText('Window width limits:')
        self.windowStep.setText('Window step:')

        self.measurementToleranceEdit.setText(self.mmwTolerance)
        self.minTempEdit.setText(self.mmwLowerTemp)
        self.maxTempEdit.setText(self.mmwUpperTemp)
        self.minWaveEdit.setText(self.mmwLowerWave)
        self.maxWaveEdit.setText(self.mmwUpperWave)
        self.minWinEdit.setText(self.mmwLowerWinWidth)
        self.maxWinEdit.setText(self.mmwUpperWinWidth)
        self.windowStepEdit.setText(self.mmwWinStep)
        self.numWindowsEdit.setText(self.mmwNumWins)

        self.emissivitySearchCheckBox.setChecked(False)
        self.metricPlotCheckBox.setChecked(False)

        self.maxWinEdit.setVisible(True)
        self.micron4.setVisible(True)
        self.windowLimits.setVisible(True)
        self.windowLimitsUnits.setVisible(True)
        self.windowStep.setVisible(True)
        self.windowStepUnits.setVisible(True)
        self.numWindows.setVisible(True)
        self.numWindowsEdit.setVisible(True)
        self.emissivitySearchCheckBox.setVisible(False)
        self.metricPlotCheckBox.setVisible(False)

        self.waveLimits.setToolTip('Upper and lower wavelength limits to be used in the temperature determination.')
        self.minWaveEdit.setToolTip('Lower wavelength limit')
        self.maxWaveEdit.setToolTip('Upper wavelength limit')
        self.windowLimits.setToolTip('Upper and lower limits of the wavelength window to examine across the spectrum.')
        self.minWinEdit.setToolTip('Lower window limit')
        self.maxWinEdit.setToolTip('Upper window limit')

    def _about(self):
        """Creates the layout for the about tab.
        """

        self.aboutEdit = QtGui.QTextEdit()
        self.aboutEdit.setText('test')

        aboutLayout = QtGui.QVBoxLayout()
        aboutLayout.addWidget(self.aboutEdit)

        return aboutLayout

    def _temperatureBox(self):
        """Creates the layout for the temperature box used to display the
        estimated temperature after performing the specified temperature
        emissivity separation.
        """

        self.temperature = QtGui.QLabel('Sample temperature:')

        self.temperatureEdit = QtGui.QLabel(' ')

        temperatureGroup = QtGui.QGroupBox()

        temperatureBoxLayout = QtGui.QHBoxLayout()
        temperatureBoxLayout.addWidget(self.temperature)
        temperatureBoxLayout.addWidget(self.temperatureEdit, QtCore.Qt.AlignLeft)

        temperatureGroup.setLayout(temperatureBoxLayout)

        return temperatureGroup

    def _buttons(self):
        """Creates the layout for the set of OK and Cancel buttons.
        """

        self.okButton = QtGui.QPushButton('Ok')
        self.okButton.setFixedWidth(100)
        self.cancelButton = QtGui.QPushButton('Cancel')
        self.cancelButton.setFixedWidth(100)

        buttonLayout = QtGui.QHBoxLayout()
        buttonLayout.addStretch()
        buttonLayout.addWidget(self.okButton)
        buttonLayout.addWidget(self.cancelButton)
        buttonLayout.addStretch()

        self.okButton.clicked.connect(self._handleOkButton)
        self.cancelButton.clicked.connect(self._handleCancelButton)

        return buttonLayout

    def _handleOkButton(self):
        """Performs the specified separation when the OK button is pressed.
        """

        self.findTemperature()

    def _handleCancelButton(self):
        """Closes the program when the Cancel button is pressed.
        """

        self.close()

    def findTemperature(self):
        """Performs the temperature emissivity separation.
        """

        # open a progress dialog while the processing is being done
        progress = QtGui.QProgressDialog('Please wait..',
            QtCore.QString(), 0, 0)
        progress.show()

        # gather the information from the GUI needed for processing
        cbbFile = str(self.cbbEdit.text())
        wbbFile = str(self.wbbEdit.text())
        samFile = str(self.samEdit.text())
        dwrFile = str(self.dwrEdit.text())
        plateEmissivity = str(self.plateEdit.text())
        technique = str(self.techniqueComboBox.currentText())
        tolerance = float(self.measurementToleranceEdit.text())
        lowerTemp = float(self.minTempEdit.text())
        upperTemp = float(self.maxTempEdit.text())
        lowerWave = float(self.minWaveEdit.text())
        upperWave = float(self.maxWaveEdit.text())
        lowerWin = self.minWinEdit.text()
        upperWin = self.maxWinEdit.text()
        windowStep = self.windowStepEdit.text()
        numWindows = self.numWindowsEdit.text()

        if (plateEmissivity == ''):
            plateEmissivity = -1
        else:
            plateEmissivity = int(plateEmissivity)

        # read the user specified files
        cbb = dp.readDpFile(cbbFile)
        wbb = dp.readDpFile(wbbFile)
        sam = dp.readDpFile(samFile)

        if (dwrFile == ''):
            dwr = None
            toleranceTests = dp.calibrateDpData(plateEmissivity, cbb, wbb, sam)
        else:
            dwr = dp.readDpFile(dwrFile)
            toleranceTests = dp.calibrateDpData(plateEmissivity, cbb, wbb, sam, dwr)

        if (lowerWin == ''):
            lowerWin = upperWave - lowerWave
        else:
            lowerWin = float(lowerWin)

        if (upperWin == ''):
            upperWin = lowerWin
        else:
            upperWin = float(upperWin)

        if (windowStep == ''):
            windowStep = 1
        else:
            windowStep = float(windowStep)

        if (numWindows == ''):
            numWindows = 1
        else:
            numWindows = int(numWindows)

        if (upperWin == lowerWin):
            windowSteps = 1
        else:
            windowSteps = ((upperWin-lowerWin) / windowStep) + 1

        # perform temperature emissivity separation
        if ('Waterband' in technique):
            temp, diffs = tes.waterbandTes(sam, dwr, lowerTemp, upperTemp, lowerWave, upperWave)
            wave = [[lowerWave, upperWave]]
        else:
            assd, temp, wave, diffs =  tes.tes(sam, dwr, lowerTemp, upperTemp, lowerWave, upperWave, lowerWin, upperWin, windowSteps, numWindows)

        # display estimated temperature with 2 decimal places
        if (temp == 0):
            self.temperatureEdit.setText('Unknown')
        else:
            self.temperatureEdit.setText('{0:.1f} K'.format(temp))

        # hide the progress dialog upon completion
        progress.hide()

        radiance = self.radiancePlotCheckBox.isChecked()
        finalEmissivity = self.emissivityPlotCheckBox.isChecked()
        searchEmissivity = self.emissivitySearchCheckBox.isChecked()
        metric = self.metricPlotCheckBox.isChecked()

        # handle any plots specified by the user
        if radiance:
            self.radiancePlot = RadiancePlotWindow(cbb, wbb, sam, dwr)
        if metric:
            if ('Waterband' in technique):
                self.metricPlot = MetricPlotWindow(lowerTemp, upperTemp, diffs, True)
            else:
                self.metricPlot = MetricPlotWindow(lowerTemp, upperTemp, diffs, False)
        if finalEmissivity and not searchEmissivity:
            self.emissivityPlot = EmissivityPlotWindow(sam, dwr, lowerTemp, upperTemp, temp, wave)
        if searchEmissivity:
            self.emissivityPlot = EmissivityPlotWindow(sam, dwr, lowerTemp, upperTemp, temp, wave, True)

        # interferogram scan tolerance test
        displayWarning = False

        for test in toleranceTests:
            if ((100 - (test*100)) > tolerance):
                displayWarning = True

        if (displayWarning):
            self.warning = WarningWindow()

class WarningWindow(QtGui.QWidget):
    """
    """

    def __init__(self):
        """
        """

        super(WarningWindow, self).__init__()

        self.initUI()
        self.show()

    def initUI(self):
        """
        """

        self.warning = QtGui.QLabel('Interferogram scan measurements vary\nby more then the specified tolerance.\nData may be inconsistent.')

        self.okButton = QtGui.QPushButton('Ok')
        self.okButton.setFixedWidth(100)
        self.okButton.clicked.connect(self._handleOkButton)

        layout = QtGui.QGridLayout()

        layout.addWidget(self.warning, 0, 0)
        layout.addWidget(self.okButton, 1, 0, QtCore.Qt.AlignCenter)

        self.setLayout(layout)
        self.setWindowTitle('Warning!')

    def _handleOkButton(self):
        """Closes the popup window when the OK button is pressed.
        """

        self.close()

class RadiancePlotWindow(QtGui.QWidget):
    """A popup window used to display a plot of the CBB, WBB, SAM and DWR
    radiance.
    """

    def __init__(self, cbb, wbb, sam, dwr):
        """Constructor for the popup window.
        """

        super(RadiancePlotWindow, self).__init__()

        self.cbb = cbb
        self.wbb = wbb
        self.sam = sam
        self.dwr = dwr

        self.initUI()
        self.show()

    def initUI(self):
        """Initialize the top level of the popup window which consists of a plot
        of the radiance values for the specified files.
        """

        layout = QtGui.QVBoxLayout()

        layout.addLayout(self._plot())
        layout.addLayout(self._buttons())

        self.setLayout(layout)
        self.setWindowTitle('Radiance')

    def _buttons(self):
        """Creates an OK button at the bottom of the popup window.
        """

        self.okButton = QtGui.QPushButton('Ok')
        self.okButton.setFixedWidth(100)

        buttonLayout = QtGui.QHBoxLayout()
        buttonLayout.addWidget(self.okButton)

        self.okButton.clicked.connect(self._handleOkButton)

        return buttonLayout

    def _plot(self):
        """Creates the plot area of the popup window.
        """

        figure = plt.figure()
        canvas = FigureCanvas(figure)
        toolbar = NavigationToolbar(canvas, self)

        axis = figure.add_subplot(111)
        axis.plot(self.wbb.spectrum.wavelength, self.wbb.spectrum.value,
            label='Warm blackbody', color='r')
        axis.plot(self.cbb.spectrum.wavelength, self.cbb.spectrum.value,
            label='Cold blackbody', color='b')
        axis.plot(self.sam.spectrum.wavelength, self.sam.spectrum.value,
            label='Sample', color='k')
        if not self.dwr is None:
            axis.plot(self.dwr.spectrum.wavelength, self.dwr.spectrum.value,
                label='Downwelling', color='y')

        axis.axis([0, 20, 0, 30])
        axis.set_xlabel('Wavelength (microns)')
        axis.set_ylabel('Radiance (W/m^2/sr/micron)')
        axis.legend(loc=1, prop={'size':11})
        canvas.draw()

        plotLayout = QtGui.QVBoxLayout()
        plotLayout.addWidget(toolbar)
        plotLayout.addWidget(canvas)

        return plotLayout

    def _handleOkButton(self):
        """Closes the popup window when the OK button is pressed.
        """

        self.close()

class EmissivityPlotWindow(QtGui.QWidget):
    """A popup window used to display a plot of the emissivity at the sample
    temperature determined by the temperature emissivity separation.
    """

    def __init__(self, sam, dwr, lowerTemp, upperTemp, temp, wave, search=False):
        """Constructor for the popup window.
        """

        super(EmissivityPlotWindow, self).__init__()

        self.sam = sam
        self.dwr = dwr
        self.lowerTemp = lowerTemp
        self.upperTemp = upperTemp
        self.temp = temp
        self.wave = wave
        self.search = search

        self.initUI()
        self.show()
        self._drawPlot()

    def initUI(self):
        """Initialize the top level of the popup window which consists of a plot
        of the emissivity of the sample.
        """

        layout = QtGui.QVBoxLayout()

        layout.addLayout(self._initPlot())
        layout.addLayout(self._buttons())

        self.setLayout(layout)
        self.setWindowTitle('Emissivity')

    def _buttons(self):
        """Creates an OK button at the bottom of the popup window.
        """

        self.okButton = QtGui.QPushButton('Ok')
        self.okButton.setFixedWidth(100)

        buttonLayout = QtGui.QHBoxLayout()
        buttonLayout.addWidget(self.okButton)

        self.okButton.clicked.connect(self._handleOkButton)

        return buttonLayout

    def _initPlot(self):
        """Creates the plot area of the popup window.
        """

        self.figure = plt.figure()
        self.canvas = FigureCanvas(self.figure)
        toolbar = NavigationToolbar(self.canvas, self)

        self.axis = self.figure.add_subplot(111)

        self.axis.axis([8, 14, -0.2, 1.2])
        self.axis.set_xlabel('Wavelength (microns)')
        self.axis.set_ylabel('Emissivity')

        plotLayout = QtGui.QVBoxLayout()
        plotLayout.addWidget(toolbar)
        plotLayout.addWidget(self.canvas)

        return plotLayout

    def _drawPlot(self):
        """
        """

        samRadiance = self.sam.spectrum.value
        wavelength = self.sam.spectrum.wavelength

        line, = self.axis.plot([], [])
        title = self.axis.text(10.8, 1.3, '', va='top')

        if self.dwr is None:
            dwrRadiance = np.zeros(len(samRadiance))
        else:
            dwrRadiance = self.dwr.spectrum.value

        emissivity = []

        def _init():
            line.set_data([], [])
            title.set_text('')
            return line, title

        def _animate(i):
            line.set_data(wavelength, emissivity[i])
            title.set_text(str(temps[i]) + ' K')
            return line, title

        if self.search:
            temps = np.arange(self.lowerTemp, self.upperTemp+1, 0.1)

            for i in range(len(temps)):
                bb = bbRadiance(temps[i], wavelength)
                emissivity.append((samRadiance - dwrRadiance) / (bb - dwrRadiance))

            animatedPlot = ani.FuncAnimation(self.figure, _animate, np.arange(1, len(temps)), interval=100, blit=False, init_func=_init, repeat=False)

        finalEmissivity = ((samRadiance - dwrRadiance) /
                (bbRadiance(self.temp, wavelength) - dwrRadiance))

        self.axis.plot(wavelength, finalEmissivity, label='Final',
            color='k')
        for band in self.wave:
            plt.axvspan(band[0], band[1], color='r', alpha=0.5)

        self.canvas.draw()

    def _handleOkButton(self):
        """Closes the popup window when the OK button is pressed.
        """

        self.close()

class MetricPlotWindow(QtGui.QWidget):
    """
    """

    def __init__(self, lowerTemp, upperTemp, metric, waterband):
        """Constructor for the popup window.
        """

        super(MetricPlotWindow, self).__init__()

        self.lowerTemp = lowerTemp
        self.upperTemp = upperTemp
        self.metric = metric
        self.waterband = waterband

        self.initUI()
        self.show()

    def initUI(self):
        """
        """

        layout = QtGui.QVBoxLayout()

        layout.addLayout(self._plot())
        layout.addLayout(self._buttons())

        self.setLayout(layout)
        self.setWindowTitle('Metric')

    def _buttons(self):
        """Creates an OK button at the bottom of the popup window.
        """

        self.okButton = QtGui.QPushButton('Ok')
        self.okButton.setFixedWidth(100)

        buttonLayout = QtGui.QHBoxLayout()
        buttonLayout.addWidget(self.okButton)

        self.okButton.clicked.connect(self._handleOkButton)

        return buttonLayout

    def _plot(self):
        """Creates the plot area of the popup window.
        """

        temps = np.arange(self.lowerTemp, self.upperTemp+1, 0.1)
        index = np.argmin(self.metric)

        figure = plt.figure()
        canvas = FigureCanvas(figure)
        toolbar = NavigationToolbar(canvas, self)

        axis = figure.add_subplot(111)
        axis.plot(temps, self.metric)
        axis.plot(temps[index], self.metric[index], 'ro', label='Estimated temperature')

        axis.axis([self.lowerTemp, self.upperTemp, min(self.metric), max(self.metric)])
        axis.set_xlabel('Temperature (K)')
        if self.waterband:
            axis.set_ylabel('Standard deviation')
        else:
            axis.set_ylabel('Average squared second derivative')
        axis.set_yscale('log')
        canvas.draw()

        plotLayout = QtGui.QVBoxLayout()
        plotLayout.addWidget(toolbar)
        plotLayout.addWidget(canvas)

        return plotLayout

    def _handleOkButton(self):
        """Closes the popup window when the OK button is pressed.
        """

        self.close()

def main():
    """Initialize and display the GUI application.
    """

    app = QtGui.QApplication(sys.argv)
    mw = MainWindow()
    mw.raise_()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
