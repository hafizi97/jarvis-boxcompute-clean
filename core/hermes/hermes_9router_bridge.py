import os
import json
import requests

class Hermes9RouterBridge:
    def __init__(self, base_url="http://127.0.0.1:20128/v1"):
        self.base_url = base_url
        self.api_key = os.environ.get("NINEROUTER_KEY", "sk-eba49bed4ad933fe-3ux51u-e90d2ed3")

    def route_prompt(self, prompt, model=None):
        if not model:
            model = "recommended"
        try:
            headers = {"Content-Type": "application/json"}
            if self.api_key:
                headers["Authorization"] = f"Bearer {self.api_key}"
            resp = requests.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json={
                    "model": model,
                    "messages": [{"role": "user", "content": prompt}],
                    "stream": False
                },
                timeout=60
            )
            if resp.status_code == 200:
                try:
                    data = resp.json()
                    return data.get("choices", [{}])[0].get("message", {}).get("content", "No content returned")
                except Exception as json_err:
                    return f"Error parsing JSON: {str(json_err)}, Response text: {resp.text}"
            else:
                return f"Error from 9Router: {resp.status_code} - {resp.text}"
        except Exception as e:
            return f"Exception connecting to 9Router: {str(e)}"
