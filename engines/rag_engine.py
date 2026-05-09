from typing import List, Tuple


class RagEngine:
    """RAG engine — wraps a LangChain history-aware chain."""

    def __init__(self, chain, history_store: dict):
        self.chain = chain
        self.history_store = history_store

    def answer(self, session_id: str, question: str) -> dict:
        result = self.chain.invoke(
            {"input": question},
            config={"configurable": {"session_id": session_id}},
        )
        return {"answer": result["answer"], "docs": result["docs"]}

    def get_history(self, session_id: str) -> List[Tuple[str, str]]:
        h = self.history_store.get(session_id)
        if not h:
            return []
        return [
            ("user", m.content) if m.type == "human" else ("assistant", m.content)
            for m in h.messages
        ]
