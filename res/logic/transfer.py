# -*- coding: utf-8 -*-

from PyQt5 import QtCore, QtGui, QtWidgets
import mysql.connector
import sqlite3_to_mysql
import mysql_to_sqlite3
from res.logic.preview import run_preview
from res.pyui import transfer_ui
from res.logic import messages


def init(dialog, self, parent):
    """Initializing the transfer dialog.

    Args:
        parent: An instance of main_ui.Ui_main_win()

    Attributes:
        self.sqlite_database: The address of the
            sqlite_database.
        self.mode: A string, `sqlite_to_mysql` or `mysql_to_sqlite`.
    """
    self.preview_pushButton.setDisabled(True)
    self.sqlite_database = parent.sqlite_database
    self.mode = parent.mode
    self.mysql_conn = parent.mysql_conn
    self.mysql_cur = parent.mysql_cur
    self.sqlite_conn = parent.sqlite_conn
    self.sqlite_cur = parent.sqlite_cur
    if self.mode == 'sqlite_to_mysql':
        self.vacuum_checkBox.hide()
        self.buffered_checkBox.hide()
        self.tables_groupBox.setTitle('SQLite tables:')
        load_sqlite_tables(dialog, self)
    else:
        self.integer_type_label.hide()
        self.integer_type_comboBox.hide()
        self.string_type_label.hide()
        self.string_type_comboBox.hide()
        self.full_text_checkBox.hide()
        self.rowid_checkBox.hide()
        self.tables_groupBox.setTitle('MySQL tables:')
        fetch_mysql_tables(dialog, self)
    self.preview_pushButton.clicked.connect(
        lambda: preview(dialog, self)
        )
    self.transfer_pushButton.clicked.connect(
        lambda: transfer_thread(dialog, self, parent)
        )
    self.about_pushButton.clicked.connect(
        lambda: messages.about(dialog)
        )
    self.close_pushButton.clicked.connect(dialog.close)
    self.log_toolButton.clicked.connect(lambda: save_log(dialog, self))
    self.select_all_checkBox.clicked.connect(
        lambda: select_all(dialog, self)
        )
    self.tables_listWidget.doubleClicked.connect(
        lambda: preview(dialog, self)
        )


def preview(dialog, self):
    """Launches the preview dialog and shows 
    a preview of the chosen table.
    """
    self.preview_pushButton.setDisabled(True)
    table = self.tables_listWidget.currentItem().text()
    run_preview(dialog, self, table)
    self.preview_pushButton.setDisabled(False)


def save_log(dialog, self):
    """Launches a dialog and asks for the destination of the 
    log file.
    """
    destination = QtWidgets.QFileDialog.getSaveFileName(
        dialog, 
        caption='Save...',
        directory='log.txt',
        filter='All Files(*)',
        )[0].strip()
    if destination != '':
        self.log_lineEdit.setText(destination)
    

def load_sqlite_tables(dialog, self):
    """Fetches the names of the tables of the SQLite database.
    Also loads the names into the tables_listWidget.
    """
    self.preview_pushButton.setDisabled(False)
    sql = 'SELECT name FROM sqlite_master WHERE type = "table";'
    self.sqlite_cur.execute(sql)
    tables = self.sqlite_cur.fetchall()
    tables = list(map(lambda table: table[0], tables))
    if 'sqlite_sequence' in tables:
        tables.remove('sqlite_sequence')
    for table in tables:
        item = QtWidgets.QListWidgetItem()
        item.setText(table)
        item.setCheckState(QtCore.Qt.Unchecked)
        self.tables_listWidget.addItem(item)


def fetch_mysql_tables(dialog, self):
    """Fetches the table names of the MySQL database.
    I used a thread to do it, because it may freeze the GUI.
    """
    sql = 'SHOW TABLES;'
    self.fetch_mysql_tables_thread = SlowQuery(self.mysql_cur, sql)
    self.fetch_mysql_tables_thread.start()
    self.fetch_mysql_tables_thread.result.connect(
        lambda tables: load_mysql_tables(dialog, self, tables)
        )


def load_mysql_tables(dialog, self, tables):
    """Loads the table names of the MySQL database
    into the tables_listWidget.

    Args:
        tables: A list of the table names.

    Connected to:
        The result signal of the self.fetch_mysql_tables_thread
        object.
    """
    self.preview_pushButton.setDisabled(False)
    tables = list(map(lambda table: table[0], tables))
    for table in tables:
        item = QtWidgets.QListWidgetItem()
        item.setText(table)
        item.setCheckState(QtCore.Qt.Unchecked)
        self.tables_listWidget.addItem(item)


def transfer_thread(dialog, self, parent):
    """As transferring is an IO-bound process, 
    so in this function, I created an instance of 
    the Transfer class that handles the process in 
    a separate thread and prevents the GUI to freeze.

    Signals:
        status: Emits a string which might be a an error 
          or `transferred` which means, the process has 
          been successfully completed.
    """
    full_text = self.full_text_checkBox.isChecked()
    chunk = self.chunk_spinBox.value()
    foreign = self.foreign_keys_checkBox.isChecked()
    rowid = self.rowid_checkBox.isChecked()
    log = self.log_lineEdit.text().strip()
    integer = self.integer_type_comboBox.currentText().strip()
    string = self.string_type_comboBox.currentText().strip()
    tables = get_tables(dialog, self)
    vacuum = self.vacuum_checkBox.isChecked()
    buffered = self.buffered_checkBox.isChecked()
    if integer == 'Default':
        integer = 'INT(11)'
    if string == 'Default':
        string = ' VARCHAR(255)'
    if tables != []:
        info = {
            'full_text':full_text,
            'chunk':chunk,
            'foreign':foreign,
            'rowid':rowid,
            'log':log,
            'integer':integer,
            'string':string,
            'tables':tables,
            'vacuum':vacuum,
            'mode':self.mode,
            'username':parent.mysql_information['username'],
            'password':parent.mysql_information['password'],
            'database':parent.mysql_information['database'],
            'host':parent.mysql_information['host'],
            'port':parent.mysql_information['port'],
            'sqlite_database':self.sqlite_database,
            'buffered':buffered
            }
        self.transfer_thread = Transfer(info)
        self.transfer_thread.start()
        self.transfer_thread.status.connect(
            lambda status: transferred(dialog, self, status)
            )
    else:
        message = 'Please select at least one table.'
        messages.warning(dialog, 'Warning', message)


def transferred(dialog, self, status):
    """This function is called when the status signal 
    of the self.transfer_thread instance is emitted. 
    Shows a message which indicates the status of the 
    transferring process.
    """
    if status == 'transferred':
        message = 'Successful transferring!'
        messages.info(dialog, 'Info', message)
    else:
        messages.error(dialog, 'Error...', status)


def select_all(dialog, self):
    """Toggle checked/unchecked all the items in the list.
    Connected to:
        The clicked signal of the select_all_checkBox.
    """
    row_count = self.tables_listWidget.count()
    select_all = self.select_all_checkBox.isChecked()
    if select_all:
        state = QtCore.Qt.Checked
    else:
        state = QtCore.Qt.Unchecked
    for row in range(row_count):
        self.tables_listWidget.item(row).setCheckState(state)


def get_tables(dialog, self):
    """Returns a list of the selected tables."""
    tables = []
    row_count = self.tables_listWidget.count()
    for row in range(row_count):
        item = self.tables_listWidget.item(row)
        if item.checkState() == QtCore.Qt.Checked:
            tables.append(item.text())
    return tables


class Transfer(QtCore.QThread):
    """A separate thread that handles the process 
    of transferring and prevents the GUI to freeze.

    Args:
        info: A dictionary of information to create
          `converter` instances from the two classes 
          SQLite3toMySQL and MySQLtoSQLite.

    Methods:
        sqlite_to_mysql:
            Returns: A converter instance to transfer
              tables from a SQLite database to a MySQL
              database.
        mysql_to_sqlite:
            Returns: A converter instance to transfer
              tables from a MySQL database to a SQLite
              database.
        run: An overridden method, which runs by calling the 
          start method on an instance of the QThread class.

    Signals:
        status: Emits a string that indicates the status 
          of the transferring process.
    """
    status = QtCore.pyqtSignal(str)

    def __init__(self, info):
        super().__init__()
        self.full_text = info['full_text']
        self.chunk = info['chunk']
        self.foreign = info['foreign']
        self.rowid = info['rowid']
        self.log = info['log']
        self.integer = info['integer']
        self.string = info['string']
        self.tables = info['tables']
        self.vacuum = info['vacuum']
        self.mode = info['mode']
        self.username = info['username']
        self.password = info['password']
        self.database = info['database']
        self.host = info['host']
        self.port = info['port']
        self.sqlite_database = info['sqlite_database']
        self.buffered = info['buffered']

    def sqlite_to_mysql(self):
        converter = sqlite3_to_mysql.SQLite3toMySQL(
            sqlite_file=self.sqlite_database,
            sqlite_tables=self.tables,
            without_foreign_keys=self.foreign,
            mysql_user=self.username,
            mysql_password=self.password,
            mysql_database=self.database,
            mysql_host=self.host,
            mysql_port=self.port,
            mysql_integer_type=self.integer,
            mysql_string_type=self.string,
            use_fulltext=self.full_text,
            with_rowid=self.rowid,
            chunk=self.chunk,
            log_file=self.log
            )
        return converter
    
    def mysql_to_sqlite(self):
        converter = mysql_to_sqlite3.MySQLtoSQLite(
            sqlite_file=self.sqlite_database,
            mysql_tables=self.tables,
            without_foreign_keys=self.foreign,
            mysql_user=self.username,
            mysql_password=self.password,
            mysql_database=self.database,
            mysql_host=self.host,
            mysql_port=self.port,
            chunk=self.chunk,
            vacuum=self.vacuum,
            buffered=self.buffered,
            log_file=self.log
            )
        return converter

    def run(self):
        try:
            if self.mode == 'sqlite_to_mysql':
                self.converter = self.sqlite_to_mysql()
            else:
                self.converter = self.mysql_to_sqlite()
            self.converter.transfer()
            self.status.emit('transferred')
        except Exception as error:
            self.status.emit(str(error))


class SlowQuery(QtCore.QThread):
    """Fetches the result of the `SHOW TABLES` SQL command.

    Args:
        cur: The cursor of the MySQL connection.
        sql: `SHOW TABLES`

    Methods:
        run: An overridden method, which runs by calling the 
          start method on an instance of the QThread class.

    Signals:
        result: Emits a list of the table names.
        error: Emits a string when an error occurred.
    """
    result = QtCore.pyqtSignal(list)
    error = QtCore.pyqtSignal(str)

    def __init__(self, cur, sql):
        super().__init__()
        self.cur = cur
        self.sql = sql

    def run(self):
        try:
            self.cur.execute(self.sql)
            data = self.cur.fetchall()
            self.result.emit(data)
        except Exception as error:
            self.error.emit(str(error))


def run_transfer(parent_dialog, parent):
    dialog = QtWidgets.QDialog(parent=parent_dialog)
    ui = transfer_ui.Ui_dialog()
    ui.setupUi(dialog)
    init(dialog, ui, parent)
    dialog.show()
    dialog.exec_()
