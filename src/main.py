import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3 as db
from create_tables import *

def init():
    """
    Initialises program.
    Establishes connection to database
    """
    global conn
    conn = db.connect('../database.db')
    create_tables(conn)


def fetch_active_assignments():
    """
    Fetch assignments that are not completed (status_id != 1) and not in history.
    """
    cursor = conn.cursor()
    # status_id: 1 = uncompleted, 2 = in progress, 3 = overdue
    query = """
            SELECT a.assignment_id, a.title, a.description, a.due_date, s.status
            FROM Assignments a
                     JOIN Status s ON a.status_id = s.status_id
            WHERE a.status_id != 1
        AND NOT EXISTS (
            SELECT 1 FROM History h WHERE h.assignment_id = a.assignment_id
        )
            ORDER BY a.due_date ASC \
            """
    cursor.execute(query)
    return cursor.fetchall()


def fetch_past_assignments():
    """
    Fetch past (completed) assignments from the History table.
    """
    cursor = conn.cursor()
    query = """
            SELECT title, description, due_date, completed_at
            FROM History
            ORDER BY completed_at DESC \
            """
    cursor.execute(query)
    return cursor.fetchall()


def create_tabs(root):
    notebook = ttk.Notebook(root)

    # Active Assignments Tab
    tab_active = ttk.Frame(notebook)
    notebook.add(tab_active, text='Active Assignments')
    tree_active = ttk.Treeview(tab_active, columns=('Title', 'Description', 'Due', 'Status'), show='headings')
    for col in ('Title', 'Description', 'Due', 'Status'):
        tree_active.heading(col, text=col)
        tree_active.column(col, width=120)
    tree_active.pack(expand=True, fill='both')
    for row in fetch_active_assignments():
        tree_active.insert('', 'end', values=row[1:])

    # Past Assignments Tab
    tab_past = ttk.Frame(notebook)
    notebook.add(tab_past, text='Past Assignments')
    tree_past = ttk.Treeview(tab_past, columns=('Title', 'Description', 'Due', 'Completed At'), show='headings')
    for col in ('Title', 'Description', 'Due', 'Completed At'):
        tree_past.heading(col, text=col)
        tree_past.column(col, width=120)
    tree_past.pack(expand=True, fill='both')
    for row in fetch_past_assignments():
        tree_past.insert('', 'end', values=row)

    notebook.pack(expand=True, fill='both')

    # Add "New Assignment" button in the top right
    btn_frame = tk.Frame(root)
    btn_frame.place(relx=1.0, x=-10, y=10, anchor='ne')
    tk.Button(btn_frame, text="New Assignment", command=lambda: add_assignment_popup(root, notebook, tree_active, tree_past)).pack()

    return notebook, tree_active, tree_past

def refresh_tabs(notebook, tree_active, tree_past):
    # Clear and repopulate the treeviews
    for i in tree_active.get_children():
        tree_active.delete(i)
    for row in fetch_active_assignments():
        tree_active.insert('', 'end', values=row[1:])
    for i in tree_past.get_children():
        tree_past.delete(i)
    for row in fetch_past_assignments():
        tree_past.insert('', 'end', values=row)


def add_assignment_popup(root, notebook, tree_active, tree_past):
    popup = tk.Toplevel(root)
    popup.title("New Assignment")
    popup.geometry("350x350")
    fields = ['Title', 'Description', 'Due Date (YYYY-MM-DD)', 'Status ID']
    entries = {}
    for idx, field in enumerate(fields):
        tk.Label(popup, text=field).grid(row=idx, column=0, padx=10, pady=5, sticky='w')
        entry = tk.Entry(popup, width=30)
        entry.grid(row=idx, column=1, padx=10, pady=5)
        entries[field] = entry

    def submit():
        title = entries['Title'].get()
        description = entries['Description'].get()
        due_date = entries['Due Date (YYYY-MM-DD)'].get()
        status_id = entries['Status ID'].get()
        if not title or not due_date or not status_id:
            messagebox.showerror("Error", "Title, Due Date, and Status ID are required.")
            return
        try:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO Assignments (title, description, due_date, status_id)
                VALUES (?, ?, ?, ?)
            """, (title, description, due_date, int(status_id)))
            conn.commit()
            popup.destroy()
            refresh_tabs(notebook, tree_active, tree_past)
        except Exception as e:
            messagebox.showerror("Error", str(e))

    tk.Button(popup, text="Add Assignment", command=submit).grid(row=len(fields), column=0, columnspan=2, pady=15)


if __name__ == '__main__':
    root = tk.Tk()
    root.title('Assignment Viewer')
    root.geometry('650x400')
    init()
    notebook, tree_active, tree_past = create_tabs(root)
    root.mainloop()