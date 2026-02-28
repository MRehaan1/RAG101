# crud.py

from database import get_connection
import csv



def create_student(name, age, grade):
    conn = get_connection()
    cursor = conn.cursor()

    query = "INSERT INTO students (name, age, grade) VALUES (%s, %s, %s)"
    cursor.execute(query, (name, age, grade))

    conn.commit()
    cursor.close()
    conn.close()


def get_all_students():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM students")
    results = cursor.fetchall()

    cursor.close()
    conn.close()

    return results


def update_student(student_id, new_grade):
    conn = get_connection()
    cursor = conn.cursor()

    query = "UPDATE students SET grade = %s WHERE id = %s"
    cursor.execute(query, (new_grade, student_id))

    conn.commit()
    cursor.close()
    conn.close()


def delete_student(student_id):
    conn = get_connection()
    cursor = conn.cursor()

    query = "DELETE FROM students WHERE id = %s"
    cursor.execute(query, (student_id,))

    conn.commit()
    cursor.close()
    conn.close()


def delete_all_students():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM students")

    conn.commit()
    cursor.close()
    conn.close()

import csv
import io

def bulk_insert_students(file):
    """
    Inserts students from a CSV file into the database.
    `file` can be a Streamlit UploadedFile or a string path.
    """
    conn = get_connection()
    cursor = conn.cursor()

    # If file is a string path, open normally
    if isinstance(file, str):
        csvfile = open(file, newline='', encoding='utf-8')
    else:
        # UploadedFile: wrap in TextIOWrapper to read text instead of bytes
        # IMPORTANT: set newline='' to work with csv correctly
        csvfile = io.TextIOWrapper(file, encoding='utf-8', newline='')

    with csvfile:
        reader = csv.DictReader(csvfile)
        data = [(row['name'], int(row['age']), row['grade']) for row in reader]

    query = "INSERT INTO students (name, age, grade) VALUES (%s, %s, %s)"
    cursor.executemany(query, data)

    conn.commit()
    cursor.close()
    conn.close()

    print(f"{len(data)} records inserted successfully!")