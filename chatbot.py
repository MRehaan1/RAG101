# chatbot.py
from auth import login, is_admin, is_user
from CRUD import get_all_students, create_student, update_student, delete_student, delete_all_students, bulk_insert_students
from student import Student


class Chatbot:
    def __init__(self, engine=None):
        self.messages = []
        self.engine = engine

    def ask(self, session_id: str, question: str) -> dict:
        """Delegate to the injected RAG engine. Returns {'answer': str, 'docs': list}."""
        return self.engine.answer(session_id, question)

    # --- AUTH ---
    def login(self, email: str, password: str):
        """Attempt login; returns auth result dict or None."""
        return login(email, password)

    def logout(self, session_state):
        """Clear all session state fields."""
        session_state.logged_in = False
        session_state.role = None
        session_state.user = None
        self.messages = []

    def check_is_admin(self, session_state) -> bool:
        return is_admin(session_state)

    def check_is_user(self, session_state) -> bool:
        return is_user(session_state)

    # --- CHAT HISTORY ---
    def add_message(self, sender: str, content):
        self.messages.append({"sender": sender, "content": content})

    def get_messages(self):
        return self.messages

    # --- HELPERS ---
    def _load_students(self) -> list[Student]:
        """Convert raw DB tuples into Student objects."""
        return [Student(ID=row[0], name=row[1], age=row[2], grade=row[3]) for row in get_all_students()]

    def _to_table_data(self, students: list[Student]) -> list:
        """Convert Student objects back to tuples for table rendering."""
        return [[s.ID, s.name, s.age, s.grade] for s in students]

    def _text_response(self, text: str) -> dict:
        return {"type": "text", "data": text}

    def _table_response(self, students: list[Student]) -> dict:
        if not students:
            return self._text_response("No students found.")
        return {"type": "table", "data": self._to_table_data(students)}

    # --- CHATBOT RESPONSE ---
    def respond(self, query: str, role: str = "user") -> dict:
        query_lower = query.strip().lower()
        is_admin = role == "admin"

        # all students
        if "all students" in query_lower:
            return self._table_response(self._load_students())

        # student id <n>
        elif "student id" in query_lower:
            try:
                student_id = int(query_lower.split()[-1])
                result = [s for s in self._load_students() if s.ID == student_id]
                return self._table_response(result) if result else self._text_response("Student not found!")
            except Exception:
                return self._text_response("Invalid ID format. Example: 'student id 3'")

        # search name <name>
        elif "search name" in query_lower:
            name = query_lower.replace("search name", "").strip()
            result = [s for s in self._load_students() if name in s.name.lower()]
            return self._table_response(result) if result else self._text_response("No students found with that name.")

        # average age — must come before plain "age" check
        elif "average age" in query_lower:
            students = self._load_students()
            if not students:
                return self._text_response("No students found.")
            avg = sum(s.age for s in students) / len(students)
            return self._text_response(f"Average age of students: **{avg:.1f}**")

        # age <n>
        elif "age" in query_lower:
            try:
                age = int(query_lower.replace("age", "").strip())
                result = [s for s in self._load_students() if s.age == age]
                return self._table_response(result) if result else self._text_response(f"No students found with age {age}.")
            except Exception:
                return self._text_response("Invalid age format. Example: 'age 22'")

        # top students — sorted by grade rank
        elif "top students" in query_lower:
            grade_rank = {"A+": 1, "A": 2, "B+": 3, "B": 4, "C+": 5, "C": 6, "D": 7, "F": 8}
            students = sorted(self._load_students(), key=lambda s: grade_rank.get(s.grade.upper(), 99))
            return self._table_response(students)

        # passing students
        elif "passing" in query_lower:
            result = [s for s in self._load_students() if s.is_passing()]
            return self._table_response(result)

        # count students
        elif "count" in query_lower:
            students = self._load_students()
            return self._text_response(f"Total number of students: **{len(students)}**")

        # add student <name> <age> <grade>  — admin only
        elif "add student" in query_lower:
            if not is_admin:
                return self._text_response("You don't have permission to add students.")
            try:
                parts = query.strip().split()
                name, age, grade = parts[2], int(parts[3]), parts[4].upper()
                if grade not in Student.valid_grades:
                    return self._text_response(f"Invalid grade **{grade}**. Valid grades: {', '.join(Student.valid_grades)}")
                s = Student(name=name, age=age, grade=grade, ID=None)
                create_student(s.name, s.age, s.grade)
                return self._text_response(f"Student **{s.name}** added successfully!")
            except Exception:
                return self._text_response("Invalid format. Example: 'add student John 20 A+'")

        # delete student <id>  — admin only
        elif "delete student" in query_lower:
            if not is_admin:
                return self._text_response("You don't have permission to delete students.")
            try:
                student_id = int(query_lower.split()[-1])
                target = next((s for s in self._load_students() if s.ID == student_id), None)
                if not target:
                    return self._text_response(f"No student found with ID {student_id}.")
                delete_student(student_id)
                return self._text_response(f"Student **{target.name}** (ID {student_id}) deleted successfully!")
            except Exception:
                return self._text_response("Invalid format. Example: 'delete student 3'")

        # update student <id> grade <grade>  — admin only
        elif "update student" in query_lower:
            if not is_admin:
                return self._text_response("You don't have permission to update students.")
            try:
                parts = query.strip().split()
                student_id = int(parts[2])
                new_grade = parts[-1].upper()
                target = next((s for s in self._load_students() if s.ID == student_id), None)
                if not target:
                    return self._text_response(f"No student found with ID {student_id}.")
                target.update_grade(new_grade)
                update_student(student_id, target.grade)
                return self._text_response(f"Student **{target.name}** grade updated to **{target.grade}**!")
            except ValueError as e:
                return self._text_response(str(e))
            except Exception:
                return self._text_response("Invalid format. Example: 'update student 3 grade B+'")

        # grade <letter>
        elif "grade" in query_lower:
            grade = query_lower.replace("grade", "").strip().upper()
            result = [s for s in self._load_students() if s.grade.upper() == grade]
            return self._table_response(result) if result else self._text_response(f"No students found with grade {grade}.")

        else:
            user_commands = (
                "- `all students`\n"
                "- `student id 3`\n"
                "- `search name Rehaan`\n"
                "- `grade A+`\n"
                "- `age 22`\n"
                "- `top students`\n"
                "- `passing students`\n"
                "- `count students`\n"
                "- `average age`"
            )
            admin_commands = (
                "\n\n**Admin only:**\n"
                "- `add student Mousa 20 A+`\n"
                "- `delete student 3`\n"
                "- `update student 3 grade B+`"
            )
            help_text = "I don't understand. Try commands like:\n" + user_commands
            if is_admin:
                help_text += admin_commands
            return self._text_response(help_text)

    # --- ADMIN CRUD ---
    def get_students(self):
        return get_all_students()

    def add_student(self, name: str, age: int, grade: str):
        create_student(name, age, grade)

    def modify_student(self, student_id: int, new_grade: str):
        update_student(student_id, new_grade)

    def remove_student(self, student_id: int):
        delete_student(student_id)

    def remove_all_students(self):
        delete_all_students()

    def bulk_insert(self, file):
        bulk_insert_students(file)
