"""
This file is part of OpenSesame.

OpenSesame is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

OpenSesame is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with OpenSesame.  If not, see <http://www.gnu.org/licenses/>.
"""

from libopensesame import item, exceptions, debug
from libqtopensesame import qtplugin
import os.path
import imp
from PyQt4 import QtGui, QtCore

class eyelink_calibrate(item.item):

	"""
	This class (the class with the same name as the module)
	handles the basic functionality of the item. It does
	not deal with GUI stuff.
	"""

	def __init__(self, name, experiment, string = None):

		"""
		Constructor
		"""

		self.version = 0.23

		# The item_typeshould match the name of the module
		self.item_type = "eyelink_calibrate"

		self._text_attached = "Yes"
		self._text_not_attached = "No (dummy mode)"
		self.tracker_attached = self._text_attached
		self.sacc_vel_thresh = 35
		self.sacc_acc_thresh = 9500
		self.cal_target_size = 16
		self.cal_beep = 'yes'
		self.force_drift_correct = 'no'

		# This options makes OpenSesame restart automatically after each session,
		# but this is not necessary anymore
		self.restart = "No"

		# Provide a short accurate description of the items functionality
		self.description = "Calibration/ initialization plugin for the Eyelink series of eye trackers (SR-Research)"

		# The parent handles the rest of the contruction
		item.item.__init__(self, name, experiment, string)

	def prepare(self):

		"""
		Prepare the item. In this case this means to initialize
		the eyelink object.
		"""

		# Pass the word on to the parent
		item.item.prepare(self)

		# Create an eyelink instance if it doesn't exist yet. Libeyelink is
		# dynamically loaded
		path = os.path.join(os.path.dirname(__file__), "libeyelink.py")
		libeyelink = imp.load_source("libeyelink", path)

		if self.get("tracker_attached") == self._text_attached:

			# The edf logfile has the same name as the opensesame log, but with a different extension
			# We also filter out characters that are not supported
			data_file = ""
			for c in os.path.splitext(os.path.basename(self.get("logfile")))[0]:
				if c.isalnum():
					data_file += c
			data_file = data_file + ".edf"

			# Automatically rename common filenames that are too long
			if data_file[:8] == 'subject-':
				data_file = 'S' + data_file[8:]
			if data_file == 'defaultlog.edf':
				data_file = 'default.edf'

			print "eyelink_calibrate(): logging tracker data as %s" % data_file
			debug.msg("loading libeyelink")
			self.experiment.eyelink = libeyelink.libeyelink(self.experiment, \
				(self.get("width"), self.get("height")), data_file=data_file, \
				saccade_velocity_threshold=self.get("sacc_vel_thresh"), \
				saccade_acceleration_threshold=self.get("sacc_acc_thresh"), \
				force_drift_correct=self.get('force_drift_correct')== \
				'yes')
			self.experiment.cleanup_functions.append(self.close)
			if self.get("restart") == "Yes":
				self.experiment.restart = True
		else:
			debug.msg("loading libeyelink (dummy mode)")
			self.experiment.eyelink = libeyelink.libeyelink_dummy(self.experiment, \
				(self.get("width"), self.get("height")))

		# Report success
		return True

	def close(self):

		"""
		Perform some cleanup functions to make sure that we don't leave
		OpenSesame and the eyelink in a mess
		"""

		debug.msg("starting eyelink deinitialisation")
		self.sleep(100)
		self.experiment.eyelink.close()
		self.experiment.eyelink = None
		debug.msg("finished eyelink deinitialisation")
		self.sleep(100)

	def run(self):

		"""
		Run the item. In this case this means putting the offline canvas
		to the display and waiting for the specified duration.
		"""

		self.set_item_onset()

		self.experiment.eyelink.calibrate(beep=self.get('cal_beep')== \
			'yes', target_size=self.get('cal_target_size'))

		# Report success
		return True

class qteyelink_calibrate(eyelink_calibrate, qtplugin.qtplugin):

	"""
	This class (the class named qt[name of module] handles
	the GUI part of the plugin. For more information about
	GUI programming using PyQt4, see:
	<http://www.riverbankcomputing.co.uk/static/Docs/PyQt4/html/classes.html>
	"""

	def __init__(self, name, experiment, string = None):

		"""
		Constructor
		"""

		# Pass the word on to the parents
		eyelink_calibrate.__init__(self, name, experiment, string)
		qtplugin.qtplugin.__init__(self, __file__)

	def init_edit_widget(self):

		"""
		This function creates the controls for the edit
		widget.
		"""

		# Lock the widget until we're doing creating it
		self.lock = True

		# Pass the word on to the parent
		qtplugin.qtplugin.init_edit_widget(self, False)
		self.add_combobox_control("tracker_attached", "Tracker attached", [self._text_attached, self._text_not_attached], \
			tooltip = "Indicates if the tracker is attached")
		if hasattr(self, 'add_checkbox_control'):
			self.add_checkbox_control("cal_beep", "Calibration beep", \
				tooltip = "Indicates whether a beep sounds when the calibration target jumps")
			self.add_checkbox_control("force_drift_correct", \
				"Enable drift correction if disabled (Eyelink 1000)", \
				tooltip = "Indicates whether drift correction should be enabled, if it is disabled in the Eyelink configuration.")
		else:
			self.add_combobox_control("cal_beep", "Calibration beep", ['yes', 'no'], \
				tooltip = "Indicates whether a beep sounds when the calibration target jumps")
			self.add_combobox_control("force_drift_correct", \
				"Enable drift correction if disabled (Eyelink 1000)", ['yes', 'no'], \
				tooltip = "Indicates whether drift correction should be enabled, if it is disabled in the Eyelink configuration.")				
		self.add_spinbox_control("cal_target_size", "Calibration target size", 0, 256,
			tooltip = "The size of the calibration target in pixels")
		self.add_line_edit_control("sacc_vel_thresh", "Saccade velocity threshold", default = self.get("sacc_vel_thresh"), \
			tooltip = "Saccade detection parameter")
		self.add_line_edit_control("sacc_acc_thresh", "Saccade acceleration threshold", default = self.get("sacc_acc_thresh"), \
			tooltip = "Saccade detection parameter")
		self.add_text("<small><b>Eyelink OpenSesame plug-in v%.2f</b></small>" % self.version)

		# Add a stretch to the edit_vbox, so that the controls do not
		# stretch to the bottom of the window.
		self.edit_vbox.addStretch()

		# Unlock
		self.lock = True

	def apply_edit_changes(self):

		"""
		Set the variables based on the controls
		"""

		# Abort if the parent reports failure of if the controls are locked
		if not qtplugin.qtplugin.apply_edit_changes(self, False) or self.lock:
			return False

		# Refresh the main window, so that changes become visible everywhere
		self.experiment.main_window.refresh(self.name)

		# Report success
		return True

	def edit_widget(self):

		"""
		Set the controls based on the variables
		"""

		# Lock the controls, otherwise a recursive loop might aris
		# in which updating the controls causes the variables to be
		# updated, which causes the controls to be updated, etc...
		self.lock = True

		# Let the parent handle everything
		qtplugin.qtplugin.edit_widget(self)

		# Unlock
		self.lock = False

		# Return the _edit_widget
		return self._edit_widget

