# JARVIS - OpenCode, Hermes & 9Router Integrated Pipeline
import sys
import os
from pathlib import Path

hermes_dir = Path(__file__).parent
sys.path.append(str(hermes_dir))

from hermes_9router_bridge import Hermes9RouterBridge

class OpenCodeHermesExecutor:
    def __init__(self):
        self.bridge = Hermes9RouterBridge()
        print("[JARVIS OpenCode] Initialized connection with Hermes & 9router.")

    def execute_task(self, task_description, model=None):
        print(f"[OpenCode Pipeline] Menerima tugasan: {task_description}")
        response = self.bridge.route_prompt(
            prompt=f"Jalankan tugasan OpenCode berikut sebagai pembangun perisian pakar (Karpathy guidelines): {task_description}",
            model=model
        )
        return response

if __name__ == "__main__":
    executor = OpenCodeHermesExecutor()
    res = executor.execute_task("Verify Opencode-Hermes-9Router pipeline status")
    print("Hasil Eksekusi:", res)
