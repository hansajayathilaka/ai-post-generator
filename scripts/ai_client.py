import os

import anthropic
import google.generativeai as genai


class ClaudeClient:
    def __init__(self):
        self.client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

    def generate(self, system_prompt: str, user_prompt: str) -> str:
        msg = self.client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=4096,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
        )
        return msg.content[0].text


class GeminiClient:
    def __init__(self):
        genai.configure(api_key=os.environ["GEMINI_API_KEY"])
        self.model = genai.GenerativeModel("gemini-2.0-flash")

    def generate(self, system_prompt: str, user_prompt: str) -> str:
        response = self.model.generate_content(f"{system_prompt}\n\n{user_prompt}")
        return response.text


def get_ai_client():
    if os.environ.get("ANTHROPIC_API_KEY"):
        return ClaudeClient()
    if os.environ.get("GEMINI_API_KEY"):
        return GeminiClient()
    raise EnvironmentError("Set ANTHROPIC_API_KEY or GEMINI_API_KEY")
