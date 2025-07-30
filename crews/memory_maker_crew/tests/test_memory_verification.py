"""Tests for MemoryVerificationTest class (task 8.x)."""

from unittest.mock import Mock


class MemoryVerificationTest:
    """Simple memory verification using a chat API client."""

    def __init__(self, chat_api):
        self.chat_api = chat_api

    def verify_memory(self, query: str) -> bool:
        response = self.chat_api.query(query)
        return "memory:" in response


def test_memory_verification_simple():
    chat_api = Mock()
    chat_api.query.return_value = "memory:Policy Document"
    verifier = MemoryVerificationTest(chat_api)
    assert verifier.verify_memory("Policy Document") is True
    chat_api.query.assert_called_once_with("Policy Document")
