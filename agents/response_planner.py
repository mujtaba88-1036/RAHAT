import json
from typing import Any, Dict
from .base import BaseAgent
from services.gemini_services import call_gemini_json

RESPONSE_PLANNER_PROMPT="""
CRITICAL: Return ONLY valid JSON. No markdown. No backticks. 
No explanations outside the JSON. The ENTIRE response must be 
parseable by json.loads()

You are the Response Planner agent for RAHAT.
You receive a CrisisEvent from the Crisis Detector.

Your job:
1. Generate 3-5 specific, actionable response actions
2. Prioritize actions by urgency
3. Assign each action to a resource (Rescue 1122, Traffic Police, System, Notification Service)
4. Estimate expected impact of each action
5. Explain your planning reasoning

For Pakistani context: reference real emergency numbers (1122, 15), real roads, real sectors.

Output must match this exact JSON schema:
{
  "actions": [
    {
      "id": "ACT-001",
      "title": "string",
      "resource": "Rescue 1122|Traffic Police|System|Notification Service",
      "priority": "Critical|High|Medium|Low",
      "description": "string"
    }
  ],
  "priority_order": ["ACT-001", "ACT-002"],
  "expected_outcome": "string",
  "reasoning_steps": ["step 1...", "step 2..."]
}
"""

class ResponsePlannerAgent(BaseAgent):
    def __init__(self):
        super().__init__("ResponsePlanner")

    async def process(self, crisis_event: Dict[str, Any]) -> Dict[str, Any]:
        self.clear_reasoning()
        self.log_reasoning("Starting response planning based on crisis event via Gemini.")
        
        location = crisis_event.get("location", "Unknown")
        severity = crisis_event.get("severity", "UNKNOWN")
        self.log_reasoning(f"Planning for crisis at {location} with severity {severity}.")
        
        user_prompt = f"Generate a response plan for the following crisis event:\n{json.dumps(crisis_event, indent=2)}"
        
        self.log_reasoning("Calling Gemini API...")
        gemini_response = await call_gemini_json(RESPONSE_PLANNER_PROMPT, user_prompt)
        self.log_reasoning("Received response from Gemini API.")
        
        # Handle None (all API keys exhausted)
        if gemini_response is None:
            self.log_reasoning("API keys exhausted. Returning None for fallback.")
            return None
        
        plan = gemini_response if isinstance(gemini_response, dict) else {}
        
        self.log_reasoning("Response plan generated successfully.")
        return {
            "response_plan": plan,
            "reasoning_steps": self.reasoning_steps + plan.get("reasoning_steps", []),
            "raw_gemini_output": gemini_response
        }