# app.py
import streamlit as st
import pandas as pd
from chatbot import Chatbot

# --- SESSION STATE INITIALIZATION ---
if "chatbot" not in st.session_state:
    st.session_state.chatbot = Chatbot()
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "role" not in st.session_state:
    st.session_state.role = None
if "user" not in st.session_state:
    st.session_state.user = None

chatbot = st.session_state.chatbot


def render_chat_history():
    for msg in chatbot.get_messages():
        content = msg["content"]
        if msg["sender"] == "user":
            _, right = st.columns([2, 0.2])
            with right:
                st.markdown(f"**You:** {content['data']}")
        else:
            left, _ = st.columns([3, 0.2])
            with left:
                if content["type"] == "table":
                    df = pd.DataFrame(content["data"], columns=["ID", "Name", "Age", "Grade"])
                    st.dataframe(df, use_container_width=True, hide_index=True)
                else:
                    st.markdown(f"**Bot:** {content['data']}")


# --- LOGIN SCREEN ---
if not st.session_state.logged_in:
    st.title("Login")
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        auth_result = chatbot.login(email, password)
        if auth_result:
            st.session_state.logged_in = True
            st.session_state.role = auth_result["role"]
            st.session_state.user = auth_result["user"]
            st.rerun()
        else:
            st.error("Invalid credentials!")

# --- ADMIN DASHBOARD ---
elif chatbot.check_is_admin(st.session_state):
    st.title("Admin Dashboard")
    st.write(f"Hello Admin: {st.session_state.user['name']}")

    if "admin_page" not in st.session_state:
        st.session_state.admin_page = "View Students"

    st.markdown("""
    <style>
    div[data-testid="stSidebarContent"] .chatbot-btn button {
        background-color: #7B2FBE !important;
        color: white !important;
        border: none !important;
    }
    div[data-testid="stSidebarContent"] .chatbot-btn button:hover {
        background-color: #5a1f8f !important;
    }
    </style>
    """, unsafe_allow_html=True)

    with st.sidebar:
        st.markdown("### Menu")
        for item in ["View Students", "Add Student", "Update Student", "Delete Student", "Bulk Insert"]:
            if st.button(item, key=f"menu_{item}", use_container_width=True):
                st.session_state.admin_page = item
        st.markdown('<div class="chatbot-btn">', unsafe_allow_html=True)
        if st.button("Chatbot", key="menu_Chatbot", use_container_width=True):
            st.session_state.admin_page = "Chatbot"
        st.markdown('</div>', unsafe_allow_html=True)
        st.markdown("---")
        if st.button("Logout", key="admin_logout", use_container_width=True):
            chatbot.logout(st.session_state)
            st.rerun()

    choice = st.session_state.admin_page

    if choice == "View Students":
        students = chatbot.get_students()
        if students:
            df = pd.DataFrame(students, columns=["ID", "Name", "Age", "Grade"])
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.info("No students found.")

    elif choice == "Add Student":
        name = st.text_input("Name", key="add_name")
        age = st.number_input("Age", min_value=1, max_value=100, step=1, key="add_age")
        grade = st.text_input("Grade", key="add_grade")
        if st.button("Add Student"):
            chatbot.add_student(name, age, grade)
            st.success(f"Student {name} added!")

    elif choice == "Update Student":
        student_id = st.number_input("Student ID", min_value=1, step=1, key="upd_id")
        new_grade = st.text_input("New Grade", key="upd_grade")
        if st.button("Update Student"):
            chatbot.modify_student(student_id, new_grade)
            st.success(f"Student ID {student_id} updated!")

    elif choice == "Delete Student":
        student_id = st.number_input("Student ID", min_value=1, step=1, key="del_id")
        if st.button("Delete Student"):
            chatbot.remove_student(student_id)
            st.success(f"Student ID {student_id} deleted!")

        st.markdown("---")
        st.warning("Danger Zone")
        confirm = st.checkbox("I confirm I want to delete ALL students")
        if st.button("Delete All Students", disabled=not confirm):
            chatbot.remove_all_students()
            st.success("All students deleted!")

    elif choice == "Bulk Insert":
        file = st.file_uploader("Upload CSV", type="csv")
        if file is not None:
            chatbot.bulk_insert(file)
            st.success("Data Improted Succesfully !")

    elif choice == "Chatbot":
        st.subheader("Chatbot")
        query = st.chat_input("Type your message here...", key="admin_chat_input")
        if query:
            chatbot.add_message("user", {"type": "text", "data": query})
            response = chatbot.respond(query, role="admin")
            chatbot.add_message("bot", response)
        render_chat_history()

# --- USER DASHBOARD (Chatbot) ---
elif chatbot.check_is_user(st.session_state):
    st.title(f"User Dashboard - Chatbot ({st.session_state.user['name']})")
    with st.sidebar:
        if st.button("Logout", key="user_logout", use_container_width=True):
            chatbot.logout(st.session_state)
            st.rerun()

    query = st.chat_input("Type your message here...")
    if query:
        chatbot.add_message("user", {"type": "text", "data": query})
        response = chatbot.respond(query, role="user")
        chatbot.add_message("bot", response)
    render_chat_history()
