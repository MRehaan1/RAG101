from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_community.chat_message_histories import ChatMessageHistory
from config import GROQ_API_KEY, GROQ_MODEL, RETRIEVAL_K, LLM_TEMPERATURE

_CONTEXTUALIZE_PROMPT = (
    "Given a chat history and the latest user question which might reference "
    "context in the chat history, formulate a standalone question which can be "
    "understood without the chat history. Do NOT answer the question, just "
    "reformulate it if needed and otherwise return it as is."
)

_QA_PROMPT = (
    "You are an assistant for question-answering tasks. "
    "Use the following pieces of retrieved context to answer the question. "
    "If you don't know the answer, say that you don't know. "
    "Keep the answer concise.\n\n{context}"
)


def build_rag_chain(vectorstore):
    """Build and return (chain_with_history, history_store).

    The chain output is a dict containing 'answer' (str) and 'docs' (list[Document]).
    """
    llm = ChatGroq(
        model=GROQ_MODEL,
        temperature=LLM_TEMPERATURE,
        api_key=GROQ_API_KEY,
    )

    retriever = vectorstore.as_retriever(search_kwargs={"k": RETRIEVAL_K})

    contextualize_prompt = ChatPromptTemplate.from_messages([
        ("system", _CONTEXTUALIZE_PROMPT),
        MessagesPlaceholder("chat_history"),
        ("human", "{input}"),
    ])

    qa_prompt = ChatPromptTemplate.from_messages([
        ("system", _QA_PROMPT),
        MessagesPlaceholder("chat_history"),
        ("human", "{input}"),
    ])

    def _retrieve(inputs: dict) -> list:
        if inputs.get("chat_history"):
            rewrite = contextualize_prompt | llm | StrOutputParser()
            query = rewrite.invoke(inputs)
        else:
            query = inputs["input"]
        return retriever.invoke(query)

    answer_chain = qa_prompt | llm | StrOutputParser()

    rag_chain = (
        RunnablePassthrough.assign(docs=_retrieve)
        .assign(context=lambda x: "\n\n".join(d.page_content for d in x["docs"]))
        .assign(answer=answer_chain)
    )

    store: dict = {}

    def _get_session_history(session_id: str) -> ChatMessageHistory:
        if session_id not in store:
            store[session_id] = ChatMessageHistory()
        return store[session_id]

    chain_with_history = RunnableWithMessageHistory(
        rag_chain,
        _get_session_history,
        input_messages_key="input",
        history_messages_key="chat_history",
        output_messages_key="answer",
    )

    return chain_with_history, store
