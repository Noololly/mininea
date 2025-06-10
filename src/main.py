import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3 as db
from create_tables import *
import datetime

def init():
	"""
	Initialises program.
	Establishes connection to database
	"""
	global conn
	conn = db.connect('database.db')
	create_tables(conn) # moved this subroutine to another file to make code cleaner

def mark_complete(tree_active, tree_past, notebook):
	selected = tree_active.selection()
	if not selected:
		messagebox.showwarning("No Selection", "Please select an assignment to mark as complete.")
		return
	item = tree_active.item(selected[0])
	values = item['values']

	cursor = conn.cursor()
	cursor.execute("""
			   SELECT assignment_id FROM Assignments WHERE title = ? AND due_date = ?
			   """, (values[0], values[2]))
	result = cursor.fetchone()
	if not result:
		messagebox.showerror("Error", "Assignment not found.")
		return
	assignment_id = result[0]
	try:
		time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
		cursor.execute("""
				 INSERT INTO History (assignment_id, title, description, due_date, completed_at)
				 SELECT assignment_id, title, description, due_date, ?
				 FROM Assignments WHERE assignment_id = ?
				 """, (time, assignment_id))
		cursor.execute("""DELETE FROM Assignments WHERE assignment_id = ?""", (assignment_id,))
		conn.commit()
		refresh_tabs(notebook, tree_active, tree_past)
	except Exception as e:
		messagebox.showerror("Error", str(e))
	

def mark_uncomplete(tree_past, tree_active, notebook):
	selected = tree_past.selection()
	if not selected:
		messagebox.showwarning("No Selection", "Please select an assignment to mark as uncompleted.")
		return
	item = tree_past.item(selected[0])
	values = item['values']

	cursor = conn.cursor()
	cursor.execute("""
			   SELECT assignment_id FROM History WHERE title = ? AND due_date = ? AND completed_at = ?
			   """, (values[0], values[2], values[3]))
	result = cursor.fetchone()
	if not result:
		messagebox.showerror("Error", "Assignment not found.")
		return
	assignment_id = result[0]
	try:
		cursor.execute("""
				 INSERT INTO Assignments (assignment_id, title, description, due_date)
				 SELECT assignment_id, title, description, due_date FROM History WHERE assignment_id = ?
				 """, (assignment_id,))
		cursor.execute("""DELETE FROM History WHERE assignment_id = ?""", (assignment_id,))
		conn.commit()
		refresh_tabs(notebook, tree_active, tree_past)
	except Exception as e:
		messagebox.showerror("Error", str(e))


def edit_assignment(root, notebook, tree_active, tree_past, is_active=True):
    tree = tree_active if is_active else tree_past
    selected = tree.selection()
    if not selected:
        messagebox.showwarning("No Selection", "Please select an assignment to edit.")
        return
    item = tree.item(selected[0])
    values = item['values']

    title, description, due_date = values[:3]
    completed_at = values[3] if not is_active else None

    popup = tk.Toplevel(root)
    popup.title("Edit Assignment")
    popup.geometry("450x250")
    fields = ['Title', 'Description', 'Due Date (YYYY-MM-DD)']
    if not is_active:
        fields.append('Completed At')
    entries = {}

    for idx, field in enumerate(fields):
        tk.Label(popup, text=field).grid(row=idx, column=0, padx=10, pady=5, sticky='w')
        entry = tk.Entry(popup, width=30)
        entry.grid(row=idx, column=1, padx=10, pady=5)
        if field == 'Title':
            entry.insert(0, title)
        elif field == 'Description':
            entry.insert(0, description)
        elif field == 'Due Date (YYYY-MM-DD)':
            entry.insert(0, due_date)
        elif field == 'Completed At' and completed_at is not None:
            entry.insert(0, completed_at)
        entries[field] = entry
    
    def submit():
        new_title = entries['Title'].get()
        new_description = entries['Description'].get()
        new_due_date = entries['Due Date (YYYY-MM-DD)'].get()
        if not new_title or not new_due_date:
            messagebox.showerror("Error", "Title and Due Date are required.")
            return
        try:
            cursor = conn.cursor()
            if is_active:
                # Find assignment_id for active assignment
                cursor.execute("""
                    SELECT assignment_id FROM Assignments
                    WHERE title = ? AND description = ? AND due_date = ?
                """, (title, description, due_date))
                result = cursor.fetchone()
                if not result:
                    messagebox.showerror("Error", "Assignment not found.")
                    return
                assignment_id = result[0]
                cursor.execute("""
                    UPDATE Assignments
                    SET title = ?, description = ?, due_date = ?
                    WHERE assignment_id = ?
                """, (new_title, new_description, new_due_date, assignment_id))
            else:
                # Find assignment_id for past assignment
                new_completed_at = entries['Completed At'].get()
                cursor.execute("""
                    SELECT assignment_id FROM History
                    WHERE title = ? AND description = ? AND due_date = ? AND completed_at = ?
                """, (title, description, due_date, completed_at))
                result = cursor.fetchone()
                if not result:
                    messagebox.showerror("Error", "Assignment not found.")
                    return
                assignment_id = result[0]
                cursor.execute("""
                    UPDATE History
                    SET title = ?, description = ?, due_date = ?, completed_at = ?
                    WHERE assignment_id = ?
                """, (new_title, new_description, new_due_date, new_completed_at, assignment_id))
            conn.commit()
            popup.destroy()
            refresh_tabs(notebook, tree_active, tree_past)
        except Exception as e:
            messagebox.showerror("Error", str(e))
    
    tk.Button(popup, text="Save Changes", command=submit).grid(row=len(fields), column=0, columnspan=2, pady=15)


def fetch_active_assignments():
	"""
	Fetch assignments that are not completed (status_id != 1) and not in history.
	"""
	cursor = conn.cursor()
	# status_id: 1 = uncompleted, 2 = in progress, 3 = overdue
	query = """
			SELECT a.assignment_id, a.title, a.description, a.due_date, s.status
			FROM Assignments a, Status s
			WHERE s.status_id = a.assignment_id AND s.status = 1
			  AND NOT EXISTS (SELECT 1
							  FROM History h
							  WHERE h.assignment_id = a.assignment_id)
			ORDER BY a.due_date \
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
	main_frame = ttk.Frame(root)
	main_frame.pack(expand=True, fill='both')

	btn_frame = ttk.Frame(main_frame)
	btn_frame.pack(fill='x', pady=(5, 0))
	new_assignment_btn = ttk.Button(
		btn_frame,
		text="New Assignment",
		command=lambda: add_assignment_popup(root, notebook, tree_active, tree_past)
	)
	new_assignment_btn.pack(side='right', padx=10)

	notebook = ttk.Notebook(main_frame)
	notebook.pack(expand=True, fill='both', pady=(5, 10), padx=10)

	tab_active = ttk.Frame(notebook)
	notebook.add(tab_active, text='Active Assignments')
	tree_active = ttk.Treeview(tab_active, columns=('Title', 'Description', 'Due', 'Status'), show='headings')
	for col in ('Title', 'Description', 'Due', 'Status'):
		tree_active.heading(col, text=col)
		tree_active.column(col, width=120)
	tree_active.pack(expand=True, fill='both')
	for row in fetch_active_assignments():
		tree_active.insert('', 'end', values=row[1:])
	
	edit_active_btn = ttk.Button(
		tab_active,
		text="Edit Assignment",
		command=lambda: edit_assignment(root, notebook, tree_active, tree_past, is_active=True)
	)
	edit_active_btn.pack(side='right', pady=10)

	tab_past = ttk.Frame(notebook)
	notebook.add(tab_past, text='Past Assignments')
	tree_past = ttk.Treeview(tab_past, columns=('Title', 'Description', 'Due', 'Completed At'), show='headings')
	for col in ('Title', 'Description', 'Due', 'Completed At'):
		tree_past.heading(col, text=col)
		tree_past.column(col, width=120)
	tree_past.pack(expand=True, fill='both')
	for row in fetch_past_assignments():
		tree_past.insert('', 'end', values=row)

	edit_past_btn = ttk.Button(
		tab_past,
		text="Edit Assignment",
		command=lambda: edit_assignment(root, notebook, tree_active, tree_past, is_active=False)
	)
	edit_past_btn.pack(side='right', pady=10)

	refresh_btn = ttk.Button(
		btn_frame,
		text="Refresh",
		command=lambda: refresh_tabs(notebook, tree_active, tree_past)
	)
	refresh_btn.pack(side='right', padx=10)

	complete_button = ttk.Button(
		tab_active,
		text="Mark as Complete",
		command=lambda: mark_complete(tree_active, tree_past, notebook)
	)
	complete_button.pack(side='right', pady=10)

	mark_uncomplete_button = ttk.Button(
		tab_past,
		text="Mark as Uncompleted",
		command=lambda: mark_uncomplete(tree_past, tree_active, notebook)
	)
	mark_uncomplete_button.pack(side='right', pady=10)

	return notebook, tree_active, tree_past

def refresh_tabs(notebook, tree_active, tree_past):
	# Clear active assignments treeview
	for i in tree_active.get_children():
		tree_active.delete(i)
	for row in fetch_active_assignments():
		tree_active.insert('', 'end', values=row[1:])

	# Clear past assignments treeview
	for i in tree_past.get_children():
		tree_past.delete(i)
	for row in fetch_past_assignments():
		tree_past.insert('', 'end', values=row)

def add_assignment_popup(root, notebook, tree_active, tree_past):
	popup = tk.Toplevel(root)
	popup.title("New Assignment")
	popup.geometry("450x200")
	fields = ['Title', 'Description', 'Due Date (YYYY-MM-DD)']
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
		if not title or not due_date:
			messagebox.showerror("Error", "Title and Due Date are required.")
			return
		try:
			cursor = conn.cursor()
			cursor.execute("""
						   INSERT INTO Assignments (title, description, due_date)
						   VALUES (?, ?, ?)
						   """, (title, description, due_date))
			assignment_id = cursor.lastrowid
			cursor.execute("""
						   INSERT INTO Status (status_id, status)
						   VALUES (?, ?)
						   """, (assignment_id, 1)) # makes it uncompleted

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