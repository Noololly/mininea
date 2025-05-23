import tkinter as tk
import sqlite3 as db

def init():
    """
    Initialises program.
    Checks to see if database exists.
    Runs table_creator if it doesn't exist.
    :return:
    """
    global conn
    conn = db.connect('mininea.db')

if __name__ == '__main__':
    root = tk.Tk()
    init()
