# -*- coding: utf-8 -*-

from PyQt5 import QtCore, QtGui, QtWidgets
from res.pyui import preview_ui
from res.logic import messages


def init(dialog, self, parent, table):
    """Initializing the preview dialog.
    Args:
        parent: An instance of transfer_ui.Ui_dialog()
        table: The selected table from the tables_listWidget.
    """
    self.table_groupBox.setTitle(table)
    self.mode = parent.mode
    self.mysql_conn = parent.mysql_conn
    self.mysql_cur = parent.mysql_cur
    self.sqlite_conn = parent.sqlite_conn
    self.sqlite_cur = parent.sqlite_cur
    dialog.setModal(True)
    dialog.setWindowModality(QtCore.Qt.ApplicationModal)
    fetch_table(dialog, self, table)


def fetch_table(dialog, self, table):
    """Based on the chosen table name, fetches the 
    corresponding data. I used a separate thread to 
    fetch data from the MySQL database, as it might be 
    an IO-bound process.
    """
    sql_fetch_all = 'select * from {};'.format(table)
    if self.mode == 'sqlite_to_mysql':
        sql = 'SELECT name FROM PRAGMA_TABLE_INFO("{}");'.format(table)
        self.sqlite_cur.execute(sql)
        headers = self.sqlite_cur.fetchall()
        self.sqlite_cur.execute(sql_fetch_all)
        rows = self.sqlite_cur.fetchall()
        load_table(dialog, self, (headers, rows))
    else:
        sql = 'SHOW COLUMNS FROM {};'.format(table)
        self.fetch_table_thread = FetchTable(
            self.mysql_cur, 
            sql, 
            sql_fetch_all
            )
        self.fetch_table_thread.start()
        self.fetch_table_thread.result.connect(
            lambda result: load_table(dialog, self, result)
            )
        self.fetch_table_thread.error.connect(
            lambda error: thread_error_handler(dialog, self, error)
            )


def thread_error_handler(dialog, self, error):
    """Shows an error message if a problem occurred
    during fetching data in the thread.
    """
    messages.error(dialog, 'Error...', error)


def load_table(dialog, self, result):
    """Loads the result into the table_tableWidget.
    Args:
        result: A list of the database rows.
    """
    headers = result[0]
    rows = result[1]
    headers = list(map(lambda header: header[0], headers))
    self.table_tableWidget.setColumnCount(len(headers))
    self.table_tableWidget.setHorizontalHeaderLabels(headers)
    rows = list(map(lambda row: list(row), rows))
    row_count = len(rows)
    self.table_tableWidget.setRowCount(row_count)
    for row in range(row_count):
        for column in range(len(headers)):
            text = str(rows[row][column])
            item = QtWidgets.QTableWidgetItem(text)
            self.table_tableWidget.setItem(row, column, item)


class FetchTable(QtCore.QThread):
    """Fetches the headers and the rows of a table.

    Args:
        cur: The cursor of the MySQL connection.
        header_sql: The SQL command to fetch the column names.
        rows_sql: The SQL command to fetch the rows of the table.

    Methods:
        run: An overridden method, which runs by calling the 
          start method on an instance of the QThread class.

    Signals:
        result: A tuple with two lists, the first one contains the 
          names of the columns and the second one, contains the rows of the 
          table => ([h0, h1, ..., hN], [(c1, c2, ..., cN)])
        error: A string that reports the problems of the process.
    """
    result = QtCore.pyqtSignal(tuple)
    error = QtCore.pyqtSignal(str)

    def __init__(self, cur, header_sql, rows_sql):
        super().__init__()
        self.cur = cur
        self.header_sql = header_sql
        self.rows_sql = rows_sql
    
    def run(self):
        try:
            self.cur.execute(self.header_sql)
            headers = self.cur.fetchall()
            self.cur.execute(self.rows_sql)
            rows = self.cur.fetchall()
            self.result.emit((headers, rows))
        except Exception as error:
            self.error.emit(str(error))


def run_preview(parent_dialog, parent, table):
    dialog = QtWidgets.QDialog(parent=parent_dialog)
    ui = preview_ui.Ui_dialog()
    ui.setupUi(dialog)
    init(dialog, ui, parent, table)
    dialog.show()
    dialog.exec_()
