from typing import List, Tuple


class SimpleFAQEngine:
    """Legacy engine from Project 1 — keyword-lookup FAQ bot."""

    def __init__(self, faq_map: dict):
        self.faq_map = faq_map
        self._histories: dict = {}

    def answer(self, session_id: str, question: str) -> str:
        ans = self.faq_map.get(question.strip().lower(), "Sorry, I don't know.")
        self._histories.setdefault(session_id, []).append(("user", question))
        self._histories[session_id].append(("assistant", ans))
        return ans

    def get_history(self, session_id: str) -> List[Tuple[str, str]]:
        return self._histories.get(session_id, [])
