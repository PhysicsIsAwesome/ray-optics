#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright © 2018 Michael J. Hayford
""" Ray Optics GUI Application

Relies on PyQt5

.. Created on Mon Feb 12 09:24:01 2018

.. codeauthor: Michael J. Hayford
"""

import sys
import logging
from pathlib import Path

from PyQt5.QtCore import Qt as qt
from PyQt5.QtCore import QEvent
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import (QApplication, QAction, QMainWindow, QMdiArea,
                             QFileDialog, QTableView, QWidget, QMenu,
                             QVBoxLayout)
from PyQt5.QtCore import pyqtSlot
import qdarkstyle
from qdarkstyle.palette import DarkPalette

from traitlets.config.configurable import MultipleInstanceError

from rayoptics.raytr.trace import RaySeg
import rayoptics.gui.appcmds as cmds
from rayoptics.gui.appmanager import ModelInfo, AppManager
import rayoptics.qtgui.dockpanels as dock
from rayoptics.qtgui.ipyconsole import create_ipython_console

from rayoptics.parax import firstorder
from rayoptics.raytr import trace


class MainWindow(QMainWindow):
    count = 0

    def __init__(self, parent=None, qtapp=None):
        super().__init__(parent)
        self.qtapp = qtapp
        self.mdi = QMdiArea()
        self.setCentralWidget(self.mdi)

        self.app_manager = AppManager(None, gui_parent=self)
        self.mdi.subWindowActivated.connect(self.app_manager.
                                            on_view_activated)

        self.is_dark = self.light_or_dark(False)

        self.left = 100
        self.top = 50
        self.width = 1800
        self.height = 1200
        self.setGeometry(self.left, self.top, self.width, self.height)

        bar = self.menuBar()

        file_menu = bar.addMenu("File")
        file_menu.addAction("New")
        file_menu.addAction("Open...")
        file_menu.addSeparator()
        file_menu.addAction("Save")
        file_menu.addAction("Save As...")
        file_menu.addAction("Close")
        file_menu.triggered[QAction].connect(self.file_action)

        view_menu = bar.addMenu("View")
        view_menu.addAction("Spec Sheet")
        view_menu.addAction("Optical Layout")
        view_menu.addAction("Lens Table")
        view_menu.addAction("Element Table")
        # view_menu.addAction("Lens View")
        view_menu.triggered[QAction].connect(self.view_action)

        parax_menu = bar.addMenu("Paraxial Model")
        parax_menu.addAction("Paraxial Model")
        parax_menu.addAction("y-ybar View")
        parax_menu.addAction("nu-nubar View")
        parax_menu.addAction("yui Ray Table")
        parax_menu.addAction("3rd Order Aberrations")
        parax_menu.triggered[QAction].connect(self.view_action)

        analysis_menu = bar.addMenu("Analysis")
        view_menu.addAction("Ray Table")
        analysis_menu.addAction("Ray Fans")
        analysis_menu.addAction("OPD Fans")
        analysis_menu.addAction("Spot Diagram")
        analysis_menu.addAction("Wavefront Map")
        analysis_menu.addAction("Astigmatism Curves")
        analysis_menu.triggered[QAction].connect(self.view_action)

        wnd_menu = bar.addMenu("Window")
        wnd_menu.addAction("Cascade")
        wnd_menu.addAction("Tiled")
        wnd_menu.addSeparator()
        wnd_menu.addAction("Light UI")
        wnd_menu.addAction("Dark UI")
        wnd_menu.addSeparator()

        dock.create_dock_windows(self)
        for pi in dock.panels.values():
            wnd_menu.addAction(pi.menu_action)

        wnd_menu.triggered[QAction].connect(self.window_action)

        self.setWindowTitle("Ray Optics")
        self.show()

        if False:
            # create new model
            self.new_model()

        else:
            # restore a default model
            pth = Path(__file__).resolve()
            try:
                root_pos = pth.parts.index('rayoptics')
            except ValueError:
                logging.debug("Can't find rayoptics: path is %s", pth)
            else:
                path = Path(*pth.parts[:root_pos+1])
                # self.open_file(path / "codev/tests/asp46.seq")
                # self.open_file(path / "codev/tests/dar_test.seq")
                # self.open_file(path / "codev/tests/paraboloid.seq")
                # self.open_file(path / "codev/tests/paraboloid_f8.seq")
                # self.open_file(path / "codev/tests/schmidt.seq")
                # self.open_file(path / "codev/tests/questar35.seq")
                # self.open_file(path / "codev/tests/rc_f16.seq")
                # self.open_file(path / "codev/tests/ag_dblgauss.seq")
                # self.open_file(path / "codev/tests/threemir.seq")
                # self.open_file(path / "codev/tests/folded_lenses.seq")
                # self.open_file(path / "codev/tests/lens_reflection_test.seq")
                # self.open_file(path / "codev/tests/dec_tilt_test.seq")
                # self.open_file(path / "codev/tests/landscape_lens.seq")
                # self.open_file(path / "codev/tests/mangin.seq")
                # self.open_file(path / "optical/tests/cell_phone_camera.roa")
                # self.open_file(path / "optical/tests/singlet_f3.roa")

                # self.open_file(path / "models/Cassegrain.roa")
                # self.open_file(path / "models/collimator.roa")
                # self.open_file(path / "models/Dall-Kirkham.roa")
                # self.open_file(path / "models/petzval.roa")
                # self.open_file(path / "models/Ritchey_Chretien.roa")
                self.open_file(path / "models/Sasian Triplet.roa")
                # self.open_file(path / "models/singlet_f5.roa")
                # self.open_file(path / "models/thinlens.roa")
                # self.open_file(path / "models/telephoto.roa")
                # self.open_file(path / "models/thin_triplet.roa")
                # self.open_file(path / "models/TwoMirror.roa")
                # self.open_file(path / "models/TwoSphericalMirror.roa")

    def add_subwindow(self, widget, model_info):
        sub_wind = self.mdi.addSubWindow(widget)
        self.app_manager.add_view(sub_wind, widget, model_info)
        MainWindow.count += 1
        return sub_wind

    def delete_subwindow(self, sub_wind):
        self.app_manager.delete_view(sub_wind)
        self.mdi.removeSubWindow(sub_wind)
        MainWindow.count -= 1

    def add_ipython_subwindow(self):
        try:
            create_ipython_console(self, 'iPython console', 800, 600)
        except MultipleInstanceError:
            logging.debug("Unable to open iPython console. "
                          "MultipleInstanceError")
        except Exception as inst:
            print(type(inst))    # the exception instance
            print(inst.args)     # arguments stored in .args
            print(inst)          # __str__ allows args to be printed directly,
            pass                 # but may be overridden in exception subclasses

    def initial_window_offset(self):
        offset_x = 50
        offset_y = 25
        orig_x = (MainWindow.count - 1)*offset_x
        orig_y = (MainWindow.count - 1)*offset_y
        return orig_x, orig_y

    def file_action(self, q):
        if q.text() == "New":
            self.new_model()

        if q.text() == "Open...":
            options = QFileDialog.Options()
            # options |= QFileDialog.DontUseNativeDialog
            fileName, _ = QFileDialog.getOpenFileName(
                          self,
                          "QFileDialog.getOpenFileName()",
                          "",
                          "CODE V Files (*.seq);;Ray-Optics Files (*.roa)",
                          options=options)
            if fileName:
                logging.debug("open file: %s", fileName)
                self.open_file(fileName)

        if q.text() == "Save As...":
            options = QFileDialog.Options()
            # options |= QFileDialog.DontUseNativeDialog
            fileName, _ = QFileDialog.getSaveFileName(
                          self,
                          "QFileDialog.getSaveFileName()",
                          "",
                          "Ray-Optics Files (*.roa);;All Files (*)",
                          options=options)
            if fileName:
                logging.debug("save file: %s", fileName)
                self.save_file(fileName)

        if q.text() == "Close":
            self.close_model()

    def new_model(self):
        iid = cmds.create_new_ideal_imager(gui_parent=self,
                                           conjugate_type='infinite')

        self.add_ipython_subwindow()
        self.refresh_app_ui()

    def open_file(self, file_name):
        self.cur_filename = file_name
        self.app_manager.set_model(cmds.open_model(file_name))
        self.is_changed = True
        self.create_lens_table()
        cmds.create_live_layout_view(self.app_manager.model, gui_parent=self)
        self.add_ipython_subwindow()
        self.refresh_app_ui()

    def save_file(self, file_name):
        self.app_manager.model.save_model(file_name)
        self.cur_filename = file_name
        self.is_changed = False

    def close_model(self):
        """ NOTE: this does not check to save a modified model """
        self.app_manager.close_model(self.delete_subwindow)

    def view_action(self, q):
        opt_model = self.app_manager.model

        if q.text() == "Spec Sheet":
            cmds.create_new_ideal_imager(opt_model=opt_model, gui_parent=self)

        if q.text() == "Optical Layout":
            cmds.create_live_layout_view(opt_model, gui_parent=self)

        if q.text() == "Lens Table":
            self.create_lens_table()

        if q.text() == "Element Table":
            model = cmds.create_element_table_model(opt_model)
            self.create_table_view(model, "Element Table")

        if q.text() == "Ray Fans":
            cmds.create_ray_fan_view(opt_model, "Ray", gui_parent=self)

        if q.text() == "OPD Fans":
            cmds.create_ray_fan_view(opt_model, "OPD", gui_parent=self)

        if q.text() == "Spot Diagram":
            cmds.create_ray_grid_view(opt_model, gui_parent=self)

        if q.text() == "Wavefront Map":
            cmds.create_wavefront_view(opt_model, gui_parent=self)

        if q.text() == "Astigmatism Curves":
            cmds.create_field_curves(opt_model, gui_parent=self)

        if q.text() == "3rd Order Aberrations":
            cmds.create_3rd_order_bar_chart(opt_model, gui_parent=self)

        if q.text() == "y-ybar View":
            cmds.create_paraxial_design_view_v2(opt_model, 'ht',
                                                gui_parent=self)

        if q.text() == "nu-nubar View":
            cmds.create_paraxial_design_view_v2(opt_model, 'slp',
                                                gui_parent=self)

        if q.text() == "yui Ray Table":
            model = cmds.create_parax_table_model(opt_model)
            self.create_table_view(model, "Paraxial Ray Table")

        if q.text() == "Paraxial Model":
            model = cmds.create_parax_model_table(opt_model)
            self.create_table_view(model, "Paraxial Model")

        if q.text() == "Ray Table":
            self.create_ray_table(opt_model)

    def window_action(self, q):
        if q.text() == "Cascade":
            self.mdi.cascadeSubWindows()

        if q.text() == "Tiled":
            self.mdi.tileSubWindows()

        if q.text() == "Light UI":
            self.is_dark = self.light_or_dark(False)
            self.app_manager.sync_light_or_dark(self.is_dark)

        if q.text() == "Dark UI":
            self.is_dark = self.light_or_dark(True)
            self.app_manager.sync_light_or_dark(self.is_dark)

    def light_or_dark(self, is_dark):
        """ set the UI to a light or dark scheme.

        Qt doesn't seem to support controlling the MdiArea's background from a
        style sheet. Set the widget directly and save the original color
        to reset defaults.
        """
        if not hasattr(self, 'mdi_background'):
            self.mdi_background = self.mdi.background()

        if is_dark:
            self.qtapp.setStyleSheet(qdarkstyle.load_stylesheet_pyqt5())
            rgb = DarkPalette.color_palette()
            self.mdi.setBackground(QColor(rgb['COLOR_BACKGROUND_NORMAL']))
        else:
            self.qtapp.setStyleSheet('')
            self.mdi.setBackground(self.mdi_background)
        return is_dark

    def create_lens_table(self):
        seq_model = self.app_manager.model.seq_model

        def set_stop_surface(stop_surface):
            seq_model.stop_surface = stop_surface
            self.refresh_gui()

        def handle_context_menu(point):
            try:
                row = vheader.logicalIndexAt(point.y())
            except NameError:
                pass
            else:
                # show menu about the row
                menu = QMenu(self)
                if row != seq_model.stop_surface:
                    menu.addAction('Set Stop Surface',
                                   lambda: set_stop_surface(row))
                if seq_model.stop_surface is not None:
                    menu.addAction('Float Stop Surface',
                                   lambda: set_stop_surface(None))
                menu.popup(vheader.mapToGlobal(point))

        model = cmds.create_lens_table_model(seq_model)
        view = self.create_table_view(model, "Surface Data Table")
        vheader = view.verticalHeader()
        vheader.setContextMenuPolicy(qt.CustomContextMenu)
        vheader.customContextMenuRequested.connect(handle_context_menu)

    def create_ray_table(self, opt_model):
        osp = opt_model.optical_spec
        pupil = [0., 1.]
        fi = 0
        wl = osp.spectral_region.reference_wvl
        fld, wvl, foc = osp.lookup_fld_wvl_focus(fi, wl)
        ray, ray_op, wvl = trace.trace_base(opt_model, pupil, fld, wvl)
#        ray, ray_op, wvl, opd = trace.trace_with_opd(opt_model, pupil,
#                                                     fld, wvl, foc)

#        cr = trace.RayPkg(ray, ray_op, wvl)
#        s, t = trace.trace_coddington_fan(opt_model, cr, foc)

        ray = [RaySeg(*rs) for rs in ray]
        model = cmds.create_ray_table_model(opt_model, ray)
        self.create_table_view(model, "Ray Table")

    def create_table_view(self, table_model, table_title, close_callback=None):
        # construct the top level widget
        widget = QWidget()
        # construct the top level layout
        layout = QVBoxLayout(widget)

        tableView = QTableView()
        tableView.setAlternatingRowColors(True)

        # Add table to box layout
        layout.addWidget(tableView)

        # set the layout on the widget
        widget.setLayout(layout)

        sub = self.add_subwindow(widget, ModelInfo(self.app_manager.model,
                                                   cmds.update_table_view,
                                                   (tableView,)))
        sub.setWindowTitle(table_title)

        sub.installEventFilter(self)

        tableView.setModel(table_model)

        tableView.setMinimumWidth(tableView.horizontalHeader().length() +
                                  tableView.horizontalHeader().height())
#                                  The following line should work but returns 0
#                                  tableView.verticalHeader().width())

        view_width = tableView.width()
        view_ht = tableView.height()
        orig_x, orig_y = self.initial_window_offset()
        sub.setGeometry(orig_x, orig_y, view_width, view_ht)

        # table data updated successfully
        table_model.update.connect(self.on_data_changed)

        sub.show()

        return tableView

    def eventFilter(self, obj, event):
        """Used by table_view in response to installEventFilter."""
        if (event.type() == QEvent.Close):
            print('close event received:', obj)
        return False

    def refresh_gui(self, **kwargs):
        self.app_manager.refresh_gui(**kwargs)

    def refresh_app_ui(self):
        dock.update_dock_windows(self)

    def handle_ideal_imager_command(self, iid, command, specsheet):
        ''' link Ideal Imager Dialog buttons to model actions
        iid: ideal imager dialog
        command: text field with the action - same as button label
        specsheet: the input specsheet used to drive the actions
        '''
        if command == 'Apply':
            opt_model = self.app_manager.model
            opt_model.set_from_specsheet(specsheet)
            self.refresh_gui()
        elif command == 'Close':
            for view, info in self.app_manager.view_dict.items():
                if iid == info[0]:
                    self.delete_subwindow(view)
                    view.close()
                    break
        elif command == 'Update':
            opt_model = self.app_manager.model
            specsheet = opt_model.specsheet
            firstorder.specsheet_from_parax_data(opt_model, specsheet)
            iid.specsheet_dict[specsheet.conjugate_type] = specsheet
            iid.update_values()
        elif command == 'New':
            opt_model = cmds.create_new_optical_model_from_specsheet(specsheet)
            self.app_manager.set_model(opt_model)
            for view, info in self.app_manager.view_dict.items():
                if iid == info[0]:
                    w = iid
                    mi = info[1]
                    args = (iid, opt_model)
                    new_mi = ModelInfo(model=opt_model, fct=mi.fct,
                                       args=args, kwargs=mi.kwargs)
                    self.app_manager.view_dict[view] = w, new_mi
            self.refresh_gui()
            self.create_lens_table()
            cmds.create_live_layout_view(opt_model, gui_parent=self)
            cmds.create_paraxial_design_view_v2(opt_model, 'ht',
                                                gui_parent=self)
            self.refresh_gui()

    @pyqtSlot(object, int)
    def on_data_changed(self, rootObj, index):
        self.refresh_gui()


def main():
    logging.basicConfig(filename='rayoptics.log',
                        filemode='w',
                        level=logging.INFO)

    qtapp = QApplication(sys.argv)
    qtwnd = MainWindow(qtapp=qtapp)

    qtwnd.show()
    return qtapp.exec_()


if __name__ == '__main__':
    sys.exit(main())
