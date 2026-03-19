import anthropic
import openai
from google import genai
from google.genai import types
from config import (
    CLAUDE_API_KEY,
    OPENAI_API_KEY,
    GOOGLE_API_KEY,
)
import time
from datetime import datetime

class Agent:
    def __init__(self, name, model="claude-sonnet-4-20250514", system_prompt=""):
        """
        Initialize an agent with a name, model, and optional system prompt.

        Args:
            name (str): The name of the agent (e.g., "refactoring", "analysis")
            model (str): The model to use (Claude, GPT, or Gemini)
            system_prompt (str): Optional system prompt for the agent
        """
        self.name = name
        self.model = model
        self.system_prompt = system_prompt
        self.query_log = []  # Store query history

        # Determine provider and initialize appropriate client
        if self._is_claude_model(model):
            self.provider = "claude"
            self.client = anthropic.Anthropic(api_key=CLAUDE_API_KEY)
        elif self._is_gpt_model(model):
            self.provider = "openai"
            self.client = openai.OpenAI(api_key=OPENAI_API_KEY)
        elif self._is_gemini_model(model):
            self.provider = "google"
            self.client = genai.Client(api_key=GOOGLE_API_KEY)
        else:
            raise ValueError(f"Unsupported model: {model}")

    def _is_claude_model(self, model):
        """Check if the model is a Claude model"""
        return "claude" in model.lower()

    def _is_gpt_model(self, model):
        """Check if the model is a GPT model"""
        return any(gpt_name in model.lower() for gpt_name in ["gpt", "o1", "o3", "o3-mini", "o4-mini"])

    def _is_gemini_model(self, model):
        """Check if the model is a Gemini model"""
        return "gemini" in model.lower()

    def query(self, user_prompt):
        """
        Send a query to the agent and return the response.

        Args:
            user_prompt (str): The user's prompt/question

        Returns:
            str: The agent's response
        """
        # Record the query
        query_record = {
            'timestamp': datetime.now().isoformat(),
            'agent_name': self.name,
            'model': self.model,
            'provider': self.provider,
            'execution_time': 0,
        }

        # Execute the query based on provider
        start_time = time.time()

        if self.provider == "claude":
            response = self._query_claude(user_prompt)
        elif self.provider == "openai":
            response = self._query_openai(user_prompt)
        elif self.provider == "google":
            response = self._query_gemini(user_prompt)
        else:
            raise ValueError(f"Unsupported provider: {self.provider}")

        # Complete the record
        query_record['execution_time'] = time.time() - start_time

        # Store the record
        self.query_log.append(query_record)

        return response

    def _get_base_model_name(self):
        """Get the base model name by removing thinking-related suffixes"""
        thinking_off_suffixes = ["thinkingoff", "thinking-off", "without-thinking", "no-thinking"]
        model_name = self.model

        for suffix in thinking_off_suffixes:
            if suffix in model_name.lower():
                # Remove the suffix (and any preceding hyphen)
                model_name = model_name.replace(f"-{suffix}", "").replace(suffix, "")

        return model_name

    def _is_claude_thinking_enabled(self):
        """Check if Claude thinking should be enabled based on model name"""
        thinking_off_suffixes = ["thinkingoff", "thinking-off", "without-thinking", "no-thinking"]
        model_lower = self.model.lower()

        return not any(suffix in model_lower for suffix in thinking_off_suffixes)

    def _query_claude_with_thinking(self, user_prompt):
        """Query Claude API with thinking enabled"""
        messages = [{"role": "user", "content": [{"type": "text", "text": user_prompt}]}]

        response = self.client.messages.create(
            model=self._get_base_model_name(),
            max_tokens=20000,
            thinking={
                "type": "enabled",
                "budget_tokens": 10000,
            },
            temperature=1,
            system=self.system_prompt,
            messages=messages,
        )

        if isinstance(response.content, list):
            text_content = ""
            for content_block in response.content:
                if hasattr(content_block, 'text'):
                    text_content += content_block.text
        else:
            text_content = response.content

        return text_content

    def _query_claude_standard(self, user_prompt):
        """Query Claude API without thinking (for models with thinking disabled)"""
        messages = [{"role": "user", "content": [{"type": "text", "text": user_prompt}]}]

        response = self.client.messages.create(
            model=self._get_base_model_name(),
            max_tokens=20000,
            temperature=1,
            system=self.system_prompt,
            messages=messages,
        )

        if isinstance(response.content, list):
            text_content = ""
            for content_block in response.content:
                if hasattr(content_block, 'text'):
                    text_content += content_block.text
        else:
            text_content = response.content

        return text_content

    def _query_claude(self, user_prompt):
        """Query Claude API using the appropriate method based on model name"""
        if self._is_claude_thinking_enabled():
            return self._query_claude_with_thinking(user_prompt)
        else:
            return self._query_claude_standard(user_prompt)

    def _query_openai_reasoning(self, user_prompt):
        """Query OpenAI API for O-series reasoning models (o3, o3-mini)"""
        merged = f"{self.system_prompt}\n\n{user_prompt}" if self.system_prompt else user_prompt

        resp = self.client.responses.create(
            model=self.model,
            input=[{
                "role": "user",
                "content": [{"type": "input_text", "text": merged}]
            }],
            reasoning={"effort": "medium"},
        )
        return resp.output_text

    def _query_openai_standard(self, user_prompt):
        """Query OpenAI API for standard models (gpt-4, gpt-4.1, etc.)"""
        messages = [{"role": "user", "content": user_prompt}]

        if self.system_prompt:
            messages.insert(0, {"role": "system", "content": self.system_prompt})

        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=1
        )

        return response.choices[0].message.content

    def _is_reasoning_model(self):
        """Check if the current model is an O-series reasoning model"""
        reasoning_models = ["o3", "o3-mini", "o1", "o1-preview", "o1-mini", "gpt-5.4"]
        return any(self.model.startswith(model) for model in reasoning_models)

    def _query_openai(self, user_prompt):
        """Query OpenAI API using the appropriate method based on model type"""
        if self._is_reasoning_model():
            return self._query_openai_reasoning(user_prompt)
        else:
            return self._query_openai_standard(user_prompt)

    def _query_gemini(self, user_prompt):
        """Query Google Gemini API with thinking budget based on model name"""
        thinking_off_suffixes = ["thinkingoff", "thinking-off", "without-thinking", "no-thinking"]
        model_lower = self.model.lower()

        thinking_budget = 0 if any(suffix in model_lower for suffix in thinking_off_suffixes) else 10000

        if self.system_prompt:
            config = types.GenerateContentConfig(
                temperature=1,
                system_instruction=self.system_prompt,
                thinking_config=types.ThinkingConfig(thinkingBudget=thinking_budget)
            )
        else:
            config = types.GenerateContentConfig(
                temperature=1,
                thinking_config=types.ThinkingConfig(thinkingBudget=thinking_budget)
            )

        response = self.client.models.generate_content(
            model=self._get_base_model_name(),
            config=config,
            contents=user_prompt
        )

        return response.text

    def set_system_prompt(self, system_prompt):
        """Update the system prompt for this agent."""
        self.system_prompt = system_prompt

    def set_model(self, model):
        """Update the model for this agent."""
        self.model = model
        # Re-initialize client if provider changed
        if self._is_claude_model(model):
            if self.provider != "claude":
                self.provider = "claude"
                self.client = anthropic.Anthropic(api_key=CLAUDE_API_KEY)
        elif self._is_gpt_model(model):
            if self.provider != "openai":
                self.provider = "openai"
                self.client = openai.OpenAI(api_key=OPENAI_API_KEY)
        elif self._is_gemini_model(model):
            if self.provider != "google":
                self.provider = "google"
                self.client = genai.Client(api_key=GOOGLE_API_KEY)

    def record_latest_usage(self):
        """
        Record the latest query usage and return it as a simplified record.

        Returns:
            dict: Usage record with agent_name and execution_time, or None if no queries
        """
        if self.query_log:
            latest_record = self.query_log[-1]
            return {
                'agent_name': latest_record['agent_name'],
                'execution_time': latest_record['execution_time']
            }
        return None

    def get_query_history(self):
        """Return the query history for this agent"""
        return self.query_log
