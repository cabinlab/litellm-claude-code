"""Module to expose the custom handler for YAML configuration"""
# Import and create the handler instance
from .claude_code_provider import ClaudeCodeSDKProvider

# Create instance that YAML can reference
my_custom_llm = ClaudeCodeSDKProvider()