#!/usr/bin/env python3
"""
Verification script to demonstrate that Claude Code SDK 
does not support standard LLM parameters.
"""

from claude_code_sdk import ClaudeCodeOptions
import inspect

def verify_parameters():
    """Check which parameters are available in ClaudeCodeOptions."""
    
    print("=== Claude Code SDK Parameter Verification ===\n")
    
    # Get all fields from ClaudeCodeOptions
    options_fields = [field for field in dir(ClaudeCodeOptions) if not field.startswith('_')]
    
    # Parameters we're looking for
    target_params = ['temperature', 'max_tokens', 'stop_sequences', 'top_p', 'top_k']
    
    print("ClaudeCodeOptions available fields:")
    for field in sorted(options_fields):
        if not field.startswith('__'):
            print(f"  ✓ {field}")
    
    print("\nChecking for standard LLM parameters:")
    for param in target_params:
        if param in options_fields:
            print(f"  ✓ {param} - FOUND")
        else:
            print(f"  ✗ {param} - NOT FOUND")
    
    # Show the actual dataclass definition
    print("\nClaudeCodeOptions dataclass signature:")
    print(inspect.signature(ClaudeCodeOptions))
    
    # Try to create options with unsupported parameters
    print("\nAttempting to create ClaudeCodeOptions with unsupported parameters...")
    try:
        # This will fail because these parameters don't exist
        options = ClaudeCodeOptions(
            temperature=0.7,  # This will cause TypeError
            max_tokens=1000
        )
    except TypeError as e:
        print(f"  ❌ Error (as expected): {e}")
    
    # Show what IS supported
    print("\nCreating ClaudeCodeOptions with supported parameters:")
    options = ClaudeCodeOptions(
        system_prompt="Test prompt",
        max_thinking_tokens=5000,  # Note: thinking tokens, not output tokens
        model="claude-3-5-sonnet-20241022",
        allowed_tools=["Read", "Write"]
    )
    print(f"  ✓ Successfully created with: {options}")

if __name__ == "__main__":
    verify_parameters()