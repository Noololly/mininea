def create_tables(conn):
    """
    Creates the Assignments, Status, and History tables if they do not exist.
    :param conn: SQLite connection object
    """
    cursor = conn.cursor()

    # Create Status table
    cursor.execute("""
                   CREATE TABLE IF NOT EXISTS Status
                   (
                       status_id
                       INTEGER
                       PRIMARY
                       KEY,
                       status
                       INTEGER
                       NOT
                       NULL
                   );
                   """)

    # Create Assignments table
    cursor.execute("""
                   CREATE TABLE IF NOT EXISTS Assignments
                   (
                       assignment_id
                       INTEGER
                       PRIMARY
                       KEY,
                       title
                       TEXT
                       NOT
                       NULL,
                       description
                       TEXT,
                       due_date
                       DATE,
                       status_id
                       INTEGER,
                       created_at
                       TIMESTAMP
                       DEFAULT
                       CURRENT_TIMESTAMP,
                       updated_at
                       TIMESTAMP
                       DEFAULT
                       CURRENT_TIMESTAMP,
                       FOREIGN
                       KEY
                   (
                       status_id
                   ) REFERENCES Status
                   (
                       status_id
                   )
                       );
                   """)

    cursor.execute("""
                   CREATE TABLE IF NOT EXISTS History
                   (
                       history_id
                       INTEGER
                       PRIMARY
                       KEY,
                       assignment_id
                       INTEGER,
                       title
                       TEXT,
                       description
                       TEXT,
                       due_date
                       DATE,
                       completed_at
                       TIMESTAMP,
                       status_id
                       INTEGER,
                       FOREIGN
                       KEY
                   (
                       assignment_id
                   ) REFERENCES Assignments
                   (
                       assignment_id
                   ),
                       FOREIGN KEY
                   (
                       status_id
                   ) REFERENCES Status
                   (
                       status_id
                   )
                       );
                   """)

    conn.commit()
