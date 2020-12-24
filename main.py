# -*- coding: utf-8 -*-

from PyQt5 import QtCore, QtGui, QtWidgets
import mysql.connector
import sqlite3
import os
from res.logic.transfer import run_transfer
from res.logic import messages
from res.pyui import main_ui


def init(dialog, self):
    """Initializing the main dialog.
    Args:
        dialog: an instance of QMianWidget.
        self: an instace of Ui_main_win class.
    Attributes:
        self.visible: to show/hide password
    Returns:
        Nothing.
    """
    self.visible = False
    load_icons(dialog, self)
    show_hide_password(dialog, self)
    self.sqlite_toolButton.clicked.connect(
        lambda: open_sqlite(dialog, self)
        )
    self.show_hide_password_pushButton.clicked.connect(
        lambda: show_hide_password(dialog, self)
        )
    self.connect_pushButton.clicked.connect(
        lambda: connect_to_mysql(dialog, self)
        )
    self.about_pushButton.clicked.connect(
        lambda: messages.about(dialog)
        )
    self.close_pushButton.clicked.connect(dialog.close)


def load_icons(dialog, self):
    """Loads the sqlite_mysql.png file.
    Maybe later, I need to load some
    more icons, so I named the function `load_icons`.
    """
    logo = "res/icons/sqlite_mysql.png"
    self.logo_label.setPixmap(QtGui.QPixmap(logo))


def show_hide_password(dialog, self):
    """Alters the echo mode of password_lineEdit to
        normal/password.
    Connected to:
        clicked signal of show_hide_password_pushButton.
    """
    if self.visible:
        icon_path = "res/icons/visibility_on.png"
        self.password_lineEdit.setEchoMode(QtWidgets.QLineEdit.Normal)
        self.visible = False
    else:
        icon_path = "res/icons/visibility_off.png"
        self.password_lineEdit.setEchoMode(QtWidgets.QLineEdit.Password)
        self.visible = True
    icon = QtGui.QIcon()
    icon.addPixmap(
        QtGui.QPixmap(icon_path), 
        QtGui.QIcon.Normal, 
        QtGui.QIcon.Off
        )
    self.show_hide_password_pushButton.setIcon(icon)


def open_sqlite(dialog, self):
    """Opens a dialog for choosing the SQLite database.
    Connected to:
        clicked signal of sqlite_toolButton.
    """
    sqlite_database = QtWidgets.QFileDialog.getOpenFileName(
        dialog, 
        caption='Open Image',
        filter='All Files(*)',
        )[0].strip()
    if sqlite_database != '':
        self.sqlite_lineEdit.setText(sqlite_database)


def connect_to_mysql(dialog, self):
    """Trying to connect to the MySQL database using the provided data.
    For connecting to the MySQL database, I used a thread because, 
    in low-speed connections or when providing wrong data, 
    the GUI will be frozen.
    
    Connected to:
        clicked signal of connect_pushButton.

    Signals:
        connected: After a successful connection, 
          this signal emits a list with two objects: [conn, cur].
        error: When an error occurred during connection to the server, 
          this signal is emitted.
    """
    self.connect_pushButton.setDisabled(True)
    host = self.host_lineEdit.text()
    port = self.port_spinBox.value()
    username = self.username_lineEdit.text()
    password = self.password_lineEdit.text()
    database = self.database_lineEdit.text()
    self.mysql_information = {
        'host':host,
        'port':port,
        'username':username,
        'password':password,
        'database':database
        }
    self.mysql_thread = ConnectToMySQL(self.mysql_information)
    self.mysql_thread.start()
    self.mysql_thread.connected.connect(
        lambda conn_cur: 
        connected_to_mysql(dialog, self, conn_cur)
        )
    self.mysql_thread.error.connect(
        lambda error: mysql_error_handler(dialog, self, error)
        )


def mysql_error_handler(dialog, self, error):
    """
    Args:
        error: A string which is passed to this functuion
          by the error signal of the self.mysql_thread instance.
    """
    self.connect_pushButton.setDisabled(False)
    messages.error(dialog, 'Error...', error)


def connected_to_mysql(dialog, self, conn_cur):
    """This function runs when a successful 
    MySQL database connection is established.
    Then calls the connect_to_sqlite function,
    in order to validate the SQLite database.

    Connected to:
        The connected signal of the self.mysql_thread instance.
    """
    self.connect_pushButton.setDisabled(False)
    self.mysql_conn = conn_cur[0]
    self.mysql_cur = conn_cur[1]
    connect_to_sqlite(dialog, self)


def connect_to_sqlite(dialog, self):
    """This function runs when a successful
    MySQL database connection is established.
    Then validates the SQLite database, after a successful
    validation, the main dialog will be disappeared and the
    transfer dialog will be opened.

    Connected to:
        connected_to_mysql function.
    """
    self.sqlite_database = self.sqlite_lineEdit.text()
    valid_sqlite_database = check_sqlite(self.sqlite_database)
    if valid_sqlite_database:
        self.sqlite_conn = sqlite3.connect(self.sqlite_database)
        self.sqlite_cur = self.sqlite_conn.cursor()
        sqlite_to_mysql = self.sqlite_to_mysql_radioButton.isChecked()
        if sqlite_to_mysql:
            self.mode = 'sqlite_to_mysql'
        else:
            self.mode = 'mysql_to_sqlite'
        dialog.hide()
        run_transfer(dialog, self)
    else:
        message = "It's not a valid SQLite database."
        messages.error(dialog, 'Error...', message)


def check_sqlite(sqlite_database):
    """Validates the opened SQLite database.
    Args:
        sqlite_database: The address of the opened SQLite database.
    Returns:
        True: If the provided address is a valid SQLite
          database.
        False: If the provided address is not a valid SQLite
          database.
    Details:
        I inspired from https://stackoverflow.com/a/46048804
    """
    if os.path.isfile(sqlite_database):
        if os.path.getsize(sqlite_database) > 100:
            with open(sqlite_database,'r', encoding="ISO-8859-1") \
                 as sqlite_file:
                header = sqlite_file.read(100)
                if header.startswith('SQLite format 3'):
                    return True
                else:
                    return False


class ConnectToMySQL(QtCore.QThread):
    """A sub-class of the QThread class which establishes
    a MySQL connection, as connecting to a remote server 
    might be a slow process, I used a thread to handle it 
    and prevent the GUI to freeze.

    Signals:
        connected: When a successful connection is established.
          Emits a list with two objects: [conn, cur].
        error: Emits an error string when the connecting process
          is failed.
    """
    connected = QtCore.pyqtSignal(list)
    error = QtCore.pyqtSignal(str)

    def __init__(self, mysql_information):
        super().__init__()
        self.host = mysql_information['host']
        self.port = int(mysql_information['port'])
        self.username = mysql_information['username']
        self.password = mysql_information['password']
        self.database = mysql_information['database']
        self.timeout = 5
        self.conn = ''
    
    def run(self):
        try:
            self.conn = mysql.connector.connect(
                host = self.host,
                port = self.port,
                user = self.username,
                password = self.password,
                database = self.database,
                connection_timeout= self.timeout
                )
            if self.conn.is_connected():
                self.cur = self.conn.cursor()
                self.connected.emit([self.conn, self.cur])
            else:
                self.error.emit("Can't connect to the database!")
        except Exception as error:
            self.error.emit(str(error))


if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    main_win = QtWidgets.QMainWindow()
    ui = main_ui.Ui_main_win()
    ui.setupUi(main_win)
    init(main_win, ui)
    main_win.show()
    sys.exit(app.exec_())
