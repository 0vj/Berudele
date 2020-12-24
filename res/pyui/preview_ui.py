# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'preview.ui'
#
# Created by: PyQt5 UI code generator 5.12
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_dialog(object):
    def setupUi(self, dialog):
        dialog.setObjectName("dialog")
        dialog.resize(873, 593)
        self.gridLayout_2 = QtWidgets.QGridLayout(dialog)
        self.gridLayout_2.setObjectName("gridLayout_2")
        self.table_groupBox = QtWidgets.QGroupBox(dialog)
        self.table_groupBox.setObjectName("table_groupBox")
        self.gridLayout = QtWidgets.QGridLayout(self.table_groupBox)
        self.gridLayout.setObjectName("gridLayout")
        self.table_tableWidget = QtWidgets.QTableWidget(self.table_groupBox)
        self.table_tableWidget.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.table_tableWidget.setAlternatingRowColors(True)
        self.table_tableWidget.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.table_tableWidget.setObjectName("table_tableWidget")
        self.table_tableWidget.setColumnCount(0)
        self.table_tableWidget.setRowCount(0)
        self.table_tableWidget.horizontalHeader().setHighlightSections(False)
        self.table_tableWidget.horizontalHeader().setStretchLastSection(True)
        self.table_tableWidget.verticalHeader().setVisible(False)
        self.table_tableWidget.verticalHeader().setDefaultSectionSize(21)
        self.table_tableWidget.verticalHeader().setHighlightSections(False)
        self.gridLayout.addWidget(self.table_tableWidget, 0, 0, 1, 1)
        self.gridLayout_2.addWidget(self.table_groupBox, 0, 0, 1, 1)

        self.retranslateUi(dialog)
        QtCore.QMetaObject.connectSlotsByName(dialog)

    def retranslateUi(self, dialog):
        _translate = QtCore.QCoreApplication.translate
        dialog.setWindowTitle(_translate("dialog", "Preview"))
        self.table_groupBox.setTitle(_translate("dialog", "Table Name:"))


