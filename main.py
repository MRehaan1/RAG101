# main.py

from CRUD import *

create_student("Ali", 22, "A")
bulk_insert_students("students.csv")

students = get_all_students()
for s in students:
    print(s)

update_student(1, "A+")

delete_student(3)

