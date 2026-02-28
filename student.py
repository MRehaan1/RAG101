class Student:
    student_count = 0 #class variable
    valid_grades = ["A+", "A", "B+", "B", "C+", "C", "D", "F"]

    def __init__(self, name, age, grade,ID):
        self.name = name
        self.age = age
        self.grade = grade
        self.ID = ID
        Student.student_count += 1


    @classmethod
    def get_student_count(cls):
        return cls.student_count
    
    def __str__(self):
        return f"{self.name} (ID: {self.ID}) - Age: {self.age} - Grade: {self.grade}"

    def is_passing(self):
        return self.grade != "F"

    def update_grade(self, new_grade):
        if new_grade in Student.valid_grades:
            self.grade = new_grade
        else:
            raise ValueError(f"Invalid grade: {new_grade}")
