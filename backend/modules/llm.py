"""
LLM integration using OpenRouter for GPT-4o with custom tag parsing.
"""

import re
from openai import OpenAI
from typing import Dict, List, Tuple
import logging

logger = logging.getLogger(__name__)


class LLMService:
    def __init__(
        self,
        api_key: str,
        model: str = "openai/gpt-5.1-chat",
        temperature: float = 0.7,
        max_tokens: int = 1000
    ):
        """
        Initialize LLM service with OpenRouter.
        
        Args:
            api_key: OpenRouter API key
            model: Model to use (e.g., openai/gpt-5.1-chat)
            temperature: Sampling temperature
            max_tokens: Maximum tokens in response
        """
        self.client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=api_key
        )
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        
        logger.info(f"LLM service initialized with model: {model}")
    
    def generate_response(
        self,
        system_prompt: str,
        messages: List[Dict[str, str]],
        user_message: str
    ) -> str:
        """
        Generate response from LLM.
        
        Args:
            system_prompt: System prompt with interviewer instructions
            messages: Previous conversation messages
            user_message: Current user message
        
        Returns:
            Raw LLM response with tags
        """
        try:
            # Build full message list
            full_messages = [{"role": "system", "content": system_prompt}]
            full_messages.extend(messages)
            full_messages.append({"role": "user", "content": user_message})
            
            logger.info(f"Sending request to LLM with {len(full_messages)} messages")
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=full_messages,
                temperature=self.temperature,
                max_tokens=self.max_tokens
            )
            
            content = response.choices[0].message.content
            logger.info(f"Received response: {len(content)} characters")
            
            return content
        
        except Exception as e:
            logger.error(f"Error generating LLM response: {e}")
            raise
    
    def parse_response(self, response: str) -> Tuple[str, str]:
        """
        Parse LLM response to extract <falar> and <codigo> tags.
        
        Args:
            response: Raw LLM response
        
        Returns:
            Tuple of (falar_content, codigo_content)
        """
        # Extract <falar> content
        falar_match = re.search(r'<falar>(.*?)</falar>', response, re.DOTALL)
        falar_content = falar_match.group(1).strip() if falar_match else ""
        
        # Extract <codigo> content
        codigo_match = re.search(r'<codigo>(.*?)</codigo>', response, re.DOTALL)
        codigo_content = codigo_match.group(1).strip() if codigo_match else ""
        
        logger.debug(f"Parsed - Falar: {len(falar_content)} chars, Codigo: {len(codigo_content)} chars")
        
        return falar_content, codigo_content
    
    def generate_evaluation(
        self,
        messages: List[Dict[str, str]],
        profile: str,
        stack: str
    ) -> Dict[str, any]:
        """
        Generate final interview evaluation.
        
        Args:
            messages: All conversation messages
            profile: Interviewer profile used
            stack: Technology stack
        
        Returns:
            Evaluation dict with strengths, weaknesses, suggestions, and score
        """
        evaluation_prompt = f"""Baseado na entrevista completa para a vaga de {profile} em {stack}, gere uma avaliação final do candidato.

FORMATO DE RESPOSTA:
<codigo>
## Avaliação Final - {profile.title()} {stack.title()}

### ✅ Pontos Fortes
- [Liste os pontos fortes demonstrados]

### ⚠️ Pontos Fracos
- [Liste áreas que precisam melhorar]

### 💡 Sugestões de Melhoria
- [Sugestões concretas e acionáveis]

### 📊 Nota Final
**[X]/10** - [Justificativa breve]
</codigo>"""
        
        try:
            eval_messages = messages + [{"role": "user", "content": evaluation_prompt}]
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=eval_messages,
                temperature=0.3,  # Lower temperature for more consistent evaluation
                max_tokens=1500
            )
            
            content = response.choices[0].message.content
            _, codigo_content = self.parse_response(content)
            
            return {
                "evaluation": codigo_content,
                "profile": profile,
                "stack": stack
            }
        
        except Exception as e:
            logger.error(f"Error generating evaluation: {e}")
            raise
