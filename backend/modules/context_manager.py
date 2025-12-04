"""
Context management for interview conversations.
Keeps a rolling window of the last N exchanges to optimize token usage.
"""

from typing import List, Dict
from collections import deque


class ContextManager:
    def __init__(self, max_exchanges: int = 6):
        """
        Initialize context manager.
        
        Args:
            max_exchanges: Maximum number of exchanges to keep in context
        """
        self.max_exchanges = max_exchanges
        self.context = deque(maxlen=max_exchanges)
    
    def add_exchange(self, user_message: str, assistant_message: str):
        """Add a user-assistant exchange to the context."""
        self.context.append({
            "user": user_message,
            "assistant": assistant_message
        })
    
    def get_messages(self) -> List[Dict[str, str]]:
        """
        Get formatted messages for LLM API.
        
        Returns:
            List of message dicts in OpenAI format
        """
        messages = []
        for exchange in self.context:
            messages.append({"role": "user", "content": exchange["user"]})
            messages.append({"role": "assistant", "content": exchange["assistant"]})
        return messages
    
    def clear(self):
        """Clear all context."""
        self.context.clear()
    
    def get_context_summary(self) -> str:
        """Get a text summary of the current context."""
        if not self.context:
            return "Nenhum contexto ainda."
        
        summary = []
        for i, exchange in enumerate(self.context, 1):
            summary.append(f"Troca {i}:")
            summary.append(f"  Candidato: {exchange['user'][:100]}...")
            summary.append(f"  Entrevistador: {exchange['assistant'][:100]}...")
        
        return "\n".join(summary)
    
    def get_exchange_count(self) -> int:
        """Get the number of exchanges in context."""
        return len(self.context)
