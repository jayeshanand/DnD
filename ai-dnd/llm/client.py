"""LLM client wrapper for Ollama."""

import requests
import json
from typing import Optional
from datetime import datetime


class OllamaClient:
    """Client for communicating with Ollama local LLM."""

    def __init__(self, base_url: str = "http://localhost:11434", model: str = "llama2"):
        self.base_url = base_url
        self.model = model
        self.api_endpoint = f"{self.base_url}/api/generate"

    def generate(
        self,
        prompt: str,
        temperature: float = 0.8,
        top_p: float = 0.9,
        max_tokens: int = 1024,
        system: Optional[str] = None,
    ) -> str:
        """
        Generate text from the LLM.

        Args:
            prompt: User prompt text
            temperature: Controls randomness (0.0-1.0)
            top_p: Nucleus sampling parameter
            max_tokens: Max length of response
            system: System prompt to set context

        Returns:
            Generated text response
        """
        full_prompt = prompt
        if system:
            full_prompt = f"{system}\n\n{prompt}"

        payload = {
            "model": self.model,
            "prompt": full_prompt,
            "stream": False,
            "temperature": temperature,
            "top_p": top_p,
            "num_predict": max_tokens,
        }

        try:
            response = requests.post(self.api_endpoint, json=payload, timeout=60)
            response.raise_for_status()
            data = response.json()
            return data.get("response", "").strip()
        except requests.exceptions.ConnectionError:
            return "[ERROR] Cannot connect to Ollama. Is it running on {}?".format(
                self.base_url
            )
        except Exception as e:
            return f"[ERROR] LLM generation failed: {str(e)}"

    def generate_dm_response_with_retry(
        self,
        system_prompt: str,
        game_context: str,
        player_input: str,
        temperature: float = 0.8,
        max_retries: int = 2,
    ) -> str:
        """
        Generate a DM response with retry logic for malformed JSON.
        
        Args:
            system_prompt: System prompt defining DM behavior
            game_context: Current game state description
            player_input: What the player said/did
            temperature: Sampling temperature
            max_retries: Number of retry attempts on JSON failure
            
        Returns:
            DM's response (ideally valid JSON)
        """
        user_prompt = f"{game_context}\n\nPlayer action: {player_input}\n\nDM response (JSON):"
        
        for attempt in range(max_retries + 1):
            response = self.generate(
                prompt=user_prompt,
                system=system_prompt,
                temperature=temperature,
                max_tokens=1024,
            )
            
            # Check if it looks like an error
            if response.startswith("[ERROR]"):
                return self._fallback_response(player_input)
            
            # Try to validate JSON
            try:
                import re
                json_match = re.search(r'\{.*\}', response, re.DOTALL)
                if json_match:
                    json.loads(json_match.group(0))  # Validate JSON
                    return response  # Success!
            except json.JSONDecodeError:
                if attempt < max_retries:
                    # Retry with lower temperature for more deterministic output
                    temperature *= 0.7
                    print(f"[Retry {attempt + 1}/{max_retries}: Invalid JSON, retrying with temp={temperature:.2f}]")
                    continue
                else:
                    # Final attempt failed, return fallback
                    print(f"[All retries exhausted, using fallback response]")
                    return self._fallback_response(player_input)
        
        return self._fallback_response(player_input)

    def _fallback_response(self, player_action: str) -> str:
        """
        Generate a fallback response when LLM fails or returns invalid JSON.
        
        Returns valid JSON that won't crash the parser.
        """
        return json.dumps({
            "narration": f"You attempt to {player_action}. The world shimmers mysteriously as reality adjusts. Perhaps you should try a different approach.",
            "npc_speeches": [],
            "effects": {
                "location": None,
                "time_delta": 5,
                "hp_change": 0,
                "gold_change": 0,
                "new_items": [],
                "new_quests": [],
                "completed_quests": [],
                "npc_relationship_changes": {}
            },
            "suggested_options": [
                "Look around",
                "Try something else",
                "Wait and observe"
            ],
            "timestamp": datetime.now().isoformat()
        })

    def generate_dm_response(
        self,
        system_prompt: str,
        game_context: str,
        player_input: str,
        temperature: float = 0.8,
    ) -> str:
        """
        Generate a DM response given game context and player input.
        
        DEPRECATED: Use generate_dm_response_with_retry instead for Phase 2+

        Args:
            system_prompt: System prompt defining DM behavior
            game_context: Current game state description
            player_input: What the player said/did
            temperature: Sampling temperature

        Returns:
            DM's narrative response
        """
        # Delegate to retry version with single attempt
        return self.generate_dm_response_with_retry(
            system_prompt, game_context, player_input, temperature, max_retries=0
        )

    def is_available(self) -> bool:
        """Check if Ollama is available and responsive."""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            return response.status_code == 200
        except:
            return False
