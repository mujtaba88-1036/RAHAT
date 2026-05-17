import json
from typing import Any, Dict, List
from .base import BaseAgent
from services.gemini_services import call_gemini_json

CRISIS_DETECTOR_PROMPT = """
CRITICAL: Return ONLY valid JSON. No markdown. No backticks. 
No explanations outside the JSON. The ENTIRE response must be 
parseable by json.loads()

You are the Crisis Detector agent for RAHAT.
You receive an array of Signal objects from the Signal Collector.

Your job:
1. Cluster signals by location (within 2km radius = same cluster)
2. Cross-reference signal types (do they agree on the same crisis?)
3. Assess severity: CRITICAL / HIGH / MEDIUM / LOW
4. Calculate confidence percentage
5. Write a situation summary in plain English

Think step by step. Show your clustering logic explicitly.
Show why confidence is what it is (which signals corroborate).

Return a SINGLE JSON object (not an array) matching this exact schema:
{
  "location": "string",
  "crisis_type": "string",
  "severity": "CRITICAL|HIGH|MEDIUM|LOW",
  "confidence": number (0-100),
  "situation_summary": "string",
  "affected_population": "estimated number",
  "reasoning_steps": ["step 1...", "step 2..."]
}
"""

class CrisisDetectorAgent(BaseAgent):
    def __init__(self):
        super().__init__("CrisisDetector")

    async def process(self, signals: List[Dict[str, Any]]) -> Dict[str, Any]:
        self.clear_reasoning()
        self.log_reasoning("Starting crisis detection process.")
        self.log_reasoning(f"Analyzing {len(signals)} signals for clustering via Gemini.")
        
        user_prompt = f"Analyze the following signals to detect crisis events:\n{json.dumps(signals, indent=2)}"
        
        self.log_reasoning("Calling Gemini API...")
        gemini_response = await call_gemini_json(CRISIS_DETECTOR_PROMPT, user_prompt)
        self.log_reasoning("Received response from Gemini API.")
        
        # Handle None (all API keys exhausted)
        if gemini_response is None:
            self.log_reasoning("API keys exhausted. Returning None for fallback.")
            return None
        
        # We expect a CrisisEvent JSON object
        if isinstance(gemini_response, list) and len(gemini_response) > 0:
            crisis_event = gemini_response[0]
        elif isinstance(gemini_response, dict) and "error" not in gemini_response:
            crisis_event = gemini_response
        else:
            crisis_event = {}

        if isinstance(gemini_response, dict) and "error" in gemini_response:
            self.log_reasoning(f"Error from Gemini API: {gemini_response['error']}")
        
        self.log_reasoning("Crisis clustered and severity assessed successfully.")
        return {
            "crisis_event": crisis_event,
            "reasoning_steps": self.reasoning_steps + crisis_event.get("reasoning_steps", []),
            "raw_gemini_output": gemini_response
        }