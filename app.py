import os
import streamlit as st
import pandas as pd
from chatbot import Chatbot
from engines.rag_engine import RagEngine
from config import CHROMA_PERSIST_DIR

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


def render_rag_ui():
    st.subheader("Document Q&A")

    # --- Config inputs ---
    default_session = st.session_state.get("user", {}).get("name", "default-session")
    session_id = st.text_input("Session ID", value=default_session, key="rag_session_id_input")
    if session_id:
        st.session_state.rag_session_id = session_id

    st.markdown("---")

    # --- PDF upload / load ---
    uploaded_files = st.file_uploader(
        "Upload PDFs", type="pdf", accept_multiple_files=True, key="rag_pdf_uploader"
    )

    col1, col2 = st.columns(2)

    with col1:
        if st.button("Process & Store PDFs", disabled=not uploaded_files, use_container_width=True):
            with st.spinner("Processing PDFs… (first run downloads the embedding model ~90 MB)"):
                from rag.ingest import ingest_pdfs
                from rag.pipeline import build_rag_chain
                vectorstore = ingest_pdfs(uploaded_files)
                chain, store = build_rag_chain(vectorstore)
                st.session_state.rag_chatbot = Chatbot(RagEngine(chain, store))
                st.session_state.rag_messages = []
            st.success(f"Processed {len(uploaded_files)} PDF(s). Ask away!")

    with col2:
        chroma_exists = os.path.exists(CHROMA_PERSIST_DIR)
        if st.button("Load Existing Documents", disabled=not chroma_exists, use_container_width=True):
            with st.spinner("Loading document store…"):
                from rag.ingest import load_vectorstore
                from rag.pipeline import build_rag_chain
                vectorstore = load_vectorstore()
                chain, store = build_rag_chain(vectorstore)
                st.session_state.rag_chatbot = Chatbot(RagEngine(chain, store))
                st.session_state.rag_messages = []
            st.success("Loaded existing documents. Ask away!")

    st.markdown("---")

    # --- Chat interface ---
    if "rag_messages" not in st.session_state:
        st.session_state.rag_messages = []

    if st.session_state.get("rag_chatbot"):
        for msg in st.session_state.rag_messages:
            with st.chat_message(msg["role"]):
                st.write(msg["content"])
                if msg.get("docs"):
                    with st.expander(f"Retrieved {len(msg['docs'])} chunks"):
                        for i, d in enumerate(msg["docs"]):
                            st.markdown(f"**Chunk {i+1}** — page {d['page']} — `{d['source']}`")
                            st.text(d["content"])

        question = st.chat_input("Ask a question about the documents…")
        if question:
            sid = st.session_state.get("rag_session_id", "default")
            st.session_state.rag_messages.append({"role": "user", "content": question})
            st.chat_message("user").write(question)
            with st.chat_message("assistant"):
                with st.spinner("Thinking…"):
                    result = st.session_state.rag_chatbot.ask(sid, question)
                st.write(result["answer"])
                with st.expander(f"Retrieved {len(result['docs'])} chunks"):
                    for i, d in enumerate(result["docs"]):
                        st.markdown(f"**Chunk {i+1}** — page {d.metadata.get('page', '?')} — `{d.metadata.get('source', '')}`")
                        st.text(d.page_content)
            st.session_state.rag_messages.append({
                "role": "assistant",
                "content": result["answer"],
                "docs": [
                    {
                        "content": d.page_content,
                        "page": d.metadata.get("page", "?"),
                        "source": d.metadata.get("source", ""),
                    }
                    for d in result["docs"]
                ],
            })
    else:
        st.info("Process PDFs or load existing documents to start chatting.")


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
        if st.button("Document Q&A", key="menu_DocQA", use_container_width=True):
            st.session_state.admin_page = "Document Q&A"
        st.markdown("---")
        if st.button("Logout", key="admin_logout", use_container_width=True):
            chatbot.logout(st.session_state)
            for key in ["rag_chatbot", "rag_messages", "rag_session_id"]:
                st.session_state.pop(key, None)
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

    elif choice == "Document Q&A":
        render_rag_ui()

# --- USER DASHBOARD ---
elif chatbot.check_is_user(st.session_state):
    st.title(f"User Dashboard ({st.session_state.user['name']})")

    if "user_page" not in st.session_state:
        st.session_state.user_page = "Chatbot"

    with st.sidebar:
        st.markdown("### Menu")
        if st.button("Chatbot", key="user_menu_chatbot", use_container_width=True):
            st.session_state.user_page = "Chatbot"
        if st.button("Document Q&A", key="user_menu_rag", use_container_width=True):
            st.session_state.user_page = "Document Q&A"
        st.markdown("---")
        if st.button("Logout", key="user_logout", use_container_width=True):
            chatbot.logout(st.session_state)
            for key in ["rag_chatbot", "rag_messages", "rag_session_id", "user_page"]:
                st.session_state.pop(key, None)
            st.rerun()

    if st.session_state.user_page == "Chatbot":
        st.subheader("Chatbot")
        query = st.chat_input("Type your message here...")
        if query:
            chatbot.add_message("user", {"type": "text", "data": query})
            response = chatbot.respond(query, role="user")
            chatbot.add_message("bot", response)
        render_chat_history()

    elif st.session_state.user_page == "Document Q&A":
        render_rag_ui()
