import json
from typing import Any, Dict, List
from .base import BaseAgent
from services.gemini_services import call_gemini_json

SIGNAL_COLLECTOR_PROMPT = """
CRITICAL: Return ONLY valid JSON. No markdown. No backticks. 
No explanations outside the JSON. The ENTIRE response must be 
parseable by json.loads()

You are the Signal Collector agent for RAHAT crisis system.
Your job is to process raw, noisy inputs from 3 sources:
1. Social media text (Roman Urdu / Urdu / English)
2. Weather API data (JSON)
3. Traffic API data (JSON)

For each input you receive, extract:
- location (specific area/sector in Islamabad or Rawalpindi)
- signal_type (flood / fire / accident / road_block / heat / unknown)
- urgency_hint (high / medium / low — based on language tone)
- raw_text (normalized to English)
- source (social / weather / traffic)

Output must match this exact JSON schema:
{
  "signals": [
    {
      "location": "string — specific sector name",
      "signal_type": "flood|fire|accident|road_block|heat|unknown",
      "urgency_hint": "high|medium|low",
      "raw_text": "string — English version",
      "source": "social|weather|traffic",
      "reasoning": "string — why you extracted this"
    }
  ],
  "reasoning_steps": ["step 1...", "step 2...", "step 3..."]
}
"""

class SignalCollectorAgent(BaseAgent):
    def __init__(self):
        super().__init__("SignalCollector")

    async def process(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        self.clear_reasoning()
        self.log_reasoning("Starting signal collection process.")
        
        inputs = payload.get("inputs", [])
        self.log_reasoning(f"Received {len(inputs)} inputs to process via Gemini.")
        
        user_prompt = f"Extract signals from the following inputs:\n{json.dumps(inputs, indent=2)}"
        
        self.log_reasoning("Calling Gemini API...")
        gemini_response = await call_gemini_json(SIGNAL_COLLECTOR_PROMPT, user_prompt)
        self.log_reasoning("Received response from Gemini API.")
        
        # Handle None (all API keys exhausted)
        if gemini_response is None:
            self.log_reasoning("API keys exhausted. Returning None for fallback.")
            return None
        
        # We expect a JSON array of signals
        signals = gemini_response if isinstance(gemini_response, list) else gemini_response.get("signals", [])
        
        self.log_reasoning(f"Finished signal collection. Extracted {len(signals)} signals.")
        return {
            "signals": signals,
            "reasoning_steps": self.reasoning_steps,
            "raw_gemini_output": gemini_response
        }