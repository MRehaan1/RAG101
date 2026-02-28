# Student Management System

A Python-based student management system with a chatbot interface, built using Streamlit and MySQL.

## Features

- **Authentication** — Role-based login for admins and regular users
- **Admin Dashboard** — Full CRUD operations (Create, Read, Update, Delete) through a sidebar menu
- **Chatbot Interface** — Natural language commands to query and manage student data
- **Bulk Import** — Upload a CSV file to insert multiple students at once
- **Grade Validation** — Supports grades: A+, A, B+, B, C+, C, D, F

## Project Structure

```
├── app.py             # Streamlit UI (login, admin dashboard, user chatbot)
├── chatbot.py         # Chatbot logic and command parsing
├── CRUD.py            # Database operations (create, read, update, delete)
├── database.py        # MySQL connection setup
├── config.py          # Loads database config from .env
├── auth.py            # Authentication and role checking
├── student.py         # Student class with grade validation
├── main.py            # CLI entry point for quick testing
├── students.csv       # Sample student data for bulk import
├── admins.json        # Admin credentials
├── users.json         # User credentials
├── .env.example       # Environment variable template
└── requirements.txt   # Python dependencies
```

## Setup

### 1. Clone the repository

```bash
git clone <your-repo-url>
cd projectone
```

### 2. Create a virtual environment

```bash
python -m venv venv
venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure the database

Create a `.env` file based on the template:

```bash
cp .env.example .env
```

Fill in your MySQL credentials:

```
DB_USER=root
DB_PASSWORD=yourpassword
DB_NAME=student_db
DB_HOST=localhost
DB_PORT=3306
```

Make sure the MySQL database and a `students` table exist:

```sql
CREATE DATABASE IF NOT EXISTS student_db;

USE student_db;

CREATE TABLE IF NOT EXISTS students (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100),
    age INT,
    grade VARCHAR(5)
);
```

### 5. Set up credentials

Add admin and user accounts in `admins.json` and `users.json`:

```json
[
  { "name": "Admin", "email": "admin@example.com", "password": "admin123" }
]
```

## Usage

### Run the Streamlit app

```bash
streamlit run app.py
```

### Run via CLI

```bash
python main.py
```

## Chatbot Commands

| Command | Role | Description |
|---|---|---|
| `all students` | All | View all students |
| `student id 3` | All | Find student by ID |
| `search name Ali` | All | Search students by name |
| `grade A+` | All | Filter by grade |
| `age 22` | All | Filter by age |
| `top students` | All | List students sorted by grade |
| `passing students` | All | List non-failing students |
| `count students` | All | Total number of students |
| `average age` | All | Average age of all students |
| `add student Ali 20 A+` | Admin | Add a new student |
| `delete student 3` | Admin | Delete student by ID |
| `update student 3 grade B+` | Admin | Update a student's grade |

## Tech Stack

- **Python**
- **Streamlit** — Web UI
- **MySQL** — Database
- **mysql-connector-python** — Database driver
- **pandas** — Data display
