import json
from typing import Any, Dict
from .base import BaseAgent
from services.gemini_services import call_gemini_json

ACTION_EXECUTOR_PROMPT="""
CRITICAL: Return ONLY valid JSON. No markdown. No backticks. 
No explanations outside the JSON. The ENTIRE response must be 
parseable by json.loads()

You are the Action Executor agent for RAHAT.
You receive a ResponsePlan from the Response Planner.

Simulate the execution of each action:
- For traffic rerouting: generate a mock route update object with before/after paths
- For emergency dispatch: create a ticket object with ticket_id, assigned_unit, ETA
- For citizen notification: generate the notification text in English and Roman Urdu
- For system alerts: create an alert log entry

For each action, log:
  - action_name
  - execution_status (SUCCESS / PARTIAL / FAILED)
  - timestamp
  - simulated_result (what changed in the system)
  - before_state vs after_state

Return a flat JSON object matching this exact schema. Do NOT wrap in an 'ExecutionReport' key:
{
  "executed_actions": [
    {
      "action_id": "ACT-001",
      "action_name": "string",
      "execution_status": "SUCCESS|PARTIAL|FAILED",
      "timestamp": "ISO string",
      "simulated_result": {},
      "before_state": "string",
      "after_state": "string"
    }
  ],
  "system_state_before": {},
  "system_state_after": {},
  "audit_log": ["timestamp - action description"]
}
"""

class ActionExecutorAgent(BaseAgent):
    def __init__(self):
        super().__init__("ActionExecutor")

    async def process(self, response_plan: Dict[str, Any]) -> Dict[str, Any]:
        self.clear_reasoning()
        self.log_reasoning("Starting action execution via Gemini simulation.")
        
        actions = response_plan.get("actions", [])
        self.log_reasoning(f"Simulating {len(actions)} actions from response plan.")
        
        user_prompt = f"Simulate execution for the following response plan:\n{json.dumps(response_plan, indent=2)}"
        
        self.log_reasoning("Calling Gemini API...")
        gemini_response = await call_gemini_json(ACTION_EXECUTOR_PROMPT, user_prompt)
        self.log_reasoning("Received response from Gemini API.")
        
        # Handle None (all API keys exhausted)
        if gemini_response is None:
            self.log_reasoning("API keys exhausted. Returning None for fallback.")
            return None
        
        if isinstance(gemini_response, dict):
            # Handle both {"ExecutionReport": {...}} and flat {...}
            execution_report = (
                gemini_response.get("ExecutionReport") or 
                gemini_response.get("execution_report") or 
                gemini_response
            )
        else:
            execution_report = {}
        
        self.log_reasoning("All actions executed in simulation.")
        return {
            "execution_report": execution_report,
            "reasoning_steps": self.reasoning_steps + execution_report.get("audit_log", []),
            "raw_gemini_output": gemini_response
        }
