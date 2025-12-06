# Claude Code SDK Authentication Architecture

## Visual Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                        ANTHROPIC API                             │
│                    (Direct API Access)                           │
│                                                                  │
│  Client Code  ──── API Key ───→  Anthropic API                 │
│                   (x-api-key)     - Models: claude-3-*          │
│                                   - Direct HTTP/REST            │
│                                   - Requires ANTHROPIC_API_KEY  │
└─────────────────────────────────────────────────────────────────┘

                            vs.

┌─────────────────────────────────────────────────────────────────┐
│                     CLAUDE CODE SDK                              │
│                  (CLI-Based Architecture)                        │
│                                                                  │
│  Python Code                                                     │
│      ↓                                                          │
│  claude_code_sdk.query()                                        │
│      ↓                                                          │
│  SubprocessCLITransport                                         │
│      ↓                                                          │
│  Spawns: claude --output-format stream-json                    │
│      ↓                                                          │
│  Claude Code CLI                                                │
│      ├── Reads: ~/.claude.json (OAuth tokens)                  │
│      └── Connects to: Claude Code Service                      │
│                                                                  │
│  Authentication: OAuth (via browser)                            │
│  Login Command: claude                                          │
│  No API Keys!                                                   │
└─────────────────────────────────────────────────────────────────┘
```

## Data Flow Diagram

```
1. Initial Setup (One-time)
   ┌──────────┐     ┌──────────────┐     ┌────────────────┐
   │   User   │────→│ claude login │────→│ OAuth Browser  │
   └──────────┘     └──────────────┘     └────────────────┘
                            │                      │
                            ↓                      ↓
                    ┌───────────────┐     ┌────────────────┐
                    │ ~/.claude.json│←────│ OAuth Tokens   │
                    └───────────────┘     └────────────────┘

2. SDK Usage (Every Request)
   ┌─────────────┐     ┌──────────────┐     ┌──────────────┐
   │ Python Code │────→│ SDK query()  │────→│ Subprocess   │
   └─────────────┘     └──────────────┘     └──────────────┘
                                                     │
                                                     ↓
   ┌─────────────┐     ┌──────────────┐     ┌──────────────┐
   │   Response  │←────│ Parse Output │←────│ Claude CLI   │
   └─────────────┘     └──────────────┘     └──────────────┘
                                                     │
                                             Uses stored OAuth
                                             from ~/.claude.json
```

## Key Differences Summary

```
┌──────────────────────┬─────────────────────┬──────────────────────┐
│      Feature         │   Anthropic API     │   Claude Code SDK    │
├──────────────────────┼─────────────────────┼──────────────────────┤
│ Authentication       │ API Keys            │ OAuth                │
│ Credential Storage   │ Environment/Code    │ ~/.claude.json       │
│ Setup Command        │ None                │ claude login         │
│ Architecture         │ Direct HTTP         │ CLI Subprocess       │
│ Programmatic Auth    │ Yes                 │ No                   │
│ CI/CD Friendly       │ Yes                 │ Limited              │
│ Security Model       │ API Key Based       │ OAuth Token Based    │
└──────────────────────┴─────────────────────┴──────────────────────┘
```