"""
Authentication integration for LiteLLM proxy server.
Adds Claude CLI authentication UI directly to the LiteLLM interface.
"""

import os
import asyncio
import subprocess
import json
import pty
import select
import fcntl
from pathlib import Path
from fastapi import WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, JSONResponse
import aiofiles

# HTML template for authentication page
AUTH_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Claude Authentication - LiteLLM</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            max-width: 800px;
            margin: 0 auto;
            padding: 2rem;
            background: #f5f5f5;
        }
        .container {
            background: white;
            border-radius: 8px;
            padding: 2rem;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        h1 {
            color: #333;
            margin-bottom: 1rem;
        }
        .status {
            padding: 1rem;
            border-radius: 4px;
            margin-bottom: 1rem;
        }
        .status.authenticated {
            background: #d4edda;
            color: #155724;
            border: 1px solid #c3e6cb;
        }
        .status.unauthenticated {
            background: #f8d7da;
            color: #721c24;
            border: 1px solid #f5c6cb;
        }
        .terminal {
            background: #1e1e1e;
            color: #d4d4d4;
            padding: 1rem;
            border-radius: 4px;
            font-family: 'Consolas', 'Monaco', monospace;
            font-size: 14px;
            height: 400px;
            overflow-y: auto;
            display: none;
        }
        .terminal.active {
            display: block;
        }
        button {
            background: #007bff;
            color: white;
            border: none;
            padding: 0.75rem 1.5rem;
            border-radius: 4px;
            font-size: 16px;
            cursor: pointer;
            margin-right: 1rem;
        }
        button:hover {
            background: #0056b3;
        }
        button:disabled {
            background: #6c757d;
            cursor: not-allowed;
        }
        .oauth-link {
            display: none;
            padding: 1rem;
            background: #e7f3ff;
            border: 1px solid #b3d9ff;
            border-radius: 4px;
            margin: 1rem 0;
        }
        .oauth-link a {
            color: #004085;
            font-weight: bold;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Claude Authentication</h1>
        
        <div id="status" class="status">
            Checking authentication status...
        </div>
        
        <div id="oauth-link" class="oauth-link">
            <p>Please visit the following URL to authenticate:</p>
            <a id="oauth-url" href="#" target="_blank"></a>
        </div>
        
        <button id="auth-btn" onclick="startAuth()" disabled>
            Start Authentication
        </button>
        
        <button onclick="window.location='/docs'">
            Back to API Documentation
        </button>
        
        <div id="terminal" class="terminal"></div>
    </div>
    
    <script>
        let ws = null;
        let isAuthenticating = false;
        
        async function checkAuthStatus() {
            try {
                const response = await fetch('/auth/status');
                const data = await response.json();
                updateStatus(data.authenticated);
                return data.authenticated;
            } catch (e) {
                console.error('Failed to check auth status:', e);
                return false;
            }
        }
        
        function updateStatus(authenticated) {
            const statusEl = document.getElementById('status');
            const authBtn = document.getElementById('auth-btn');
            
            if (authenticated) {
                statusEl.className = 'status authenticated';
                statusEl.textContent = 'Authenticated successfully! You can now use the API.';
                authBtn.disabled = true;
                authBtn.textContent = 'Already Authenticated';
            } else {
                statusEl.className = 'status unauthenticated';
                statusEl.textContent = 'Not authenticated. Please click the button below to authenticate.';
                authBtn.disabled = false;
                authBtn.textContent = 'Start Authentication';
            }
        }
        
        function addTerminalLine(text) {
            const terminal = document.getElementById('terminal');
            const line = document.createElement('div');
            line.textContent = text;
            terminal.appendChild(line);
            terminal.scrollTop = terminal.scrollHeight;
        }
        
        function submitAuthCode() {
            const input = document.getElementById('auth-code-input');
            const code = input.value.trim();
            if (code && ws && ws.readyState === WebSocket.OPEN) {
                ws.send(JSON.stringify({
                    type: 'input',
                    text: code
                }));
                input.disabled = true;
                input.placeholder = 'Code submitted...';
            }
        }
        
        function startAuth() {
            if (isAuthenticating) return;
            
            isAuthenticating = true;
            const terminal = document.getElementById('terminal');
            const authBtn = document.getElementById('auth-btn');
            
            terminal.className = 'terminal active';
            terminal.innerHTML = '';
            authBtn.disabled = true;
            authBtn.textContent = 'Authenticating...';
            
            // Connect WebSocket
            ws = new WebSocket(`ws://${window.location.host}/auth/ws`);
            
            ws.onopen = () => {
                addTerminalLine('Starting Claude authentication...');
                ws.send(JSON.stringify({action: 'start'}));
            };
            
            ws.onmessage = (event) => {
                const data = JSON.parse(event.data);
                
                if (data.type === 'output') {
                    addTerminalLine(data.text);
                    
                    // Check for OAuth URL
                    const urlMatch = data.text.match(/https:\/\/[^\s]+/);
                    if (urlMatch) {
                        const oauthLink = document.getElementById('oauth-link');
                        const oauthUrl = document.getElementById('oauth-url');
                        oauthLink.style.display = 'block';
                        oauthUrl.href = urlMatch[0];
                        oauthUrl.textContent = urlMatch[0];
                        
                        // Add input field for auth code if not already present
                        if (!document.getElementById('auth-code-input')) {
                            const inputDiv = document.createElement('div');
                            inputDiv.style.marginTop = '1rem';
                            inputDiv.innerHTML = `
                                <label for="auth-code-input">After authorizing, paste your code here:</label>
                                <div style="display: flex; gap: 0.5rem; margin-top: 0.5rem;">
                                    <input type="text" id="auth-code-input" 
                                           style="flex: 1; padding: 0.5rem; font-family: monospace;"
                                           placeholder="Paste authorization code">
                                    <button onclick="submitAuthCode()" 
                                            style="padding: 0.5rem 1rem; background: #007bff; color: white; border: none; border-radius: 4px; cursor: pointer;">
                                        Submit
                                    </button>
                                </div>
                            `;
                            oauthLink.appendChild(inputDiv);
                        }
                    }
                } else if (data.type === 'complete') {
                    addTerminalLine('\\nAuthentication complete!');
                    isAuthenticating = false;
                    setTimeout(() => checkAuthStatus(), 1000);
                } else if (data.type === 'error') {
                    addTerminalLine(`\\nError: ${data.message}`);
                    isAuthenticating = false;
                    authBtn.disabled = false;
                    authBtn.textContent = 'Retry Authentication';
                }
            };
            
            ws.onclose = () => {
                if (isAuthenticating) {
                    addTerminalLine('\\nConnection closed unexpectedly.');
                    isAuthenticating = false;
                    authBtn.disabled = false;
                    authBtn.textContent = 'Retry Authentication';
                }
            };
        }
        
        // Check auth status on load
        checkAuthStatus();
    </script>
</body>
</html>
"""

def add_auth_routes(app):
    """Add authentication routes to the LiteLLM FastAPI app."""
    
    @app.get("/auth")
    async def auth_page():
        """Serve the authentication UI."""
        return HTMLResponse(content=AUTH_HTML)
    
    @app.get("/auth/status")
    async def auth_status():
        """Check if Claude CLI is authenticated."""
        creds_path = Path("/root/.claude/.credentials.json")
        authenticated = creds_path.exists() and creds_path.stat().st_size > 0
        return JSONResponse({"authenticated": authenticated})
    
    @app.websocket("/auth/ws")
    async def websocket_endpoint(websocket: WebSocket):
        """Handle interactive Claude CLI authentication via WebSocket."""
        await websocket.accept()
        
        master_fd = None
        slave_fd = None
        
        try:
            # Wait for start signal
            data = await websocket.receive_json()
            if data.get("action") != "start":
                return
            
            # Create a pseudo-terminal
            master_fd, slave_fd = pty.openpty()
            
            # Set terminal to non-blocking mode
            flags = fcntl.fcntl(master_fd, fcntl.F_GETFL)
            fcntl.fcntl(master_fd, fcntl.F_SETFL, flags | os.O_NONBLOCK)
            
            # Start Claude CLI with the PTY
            process = await asyncio.create_subprocess_exec(
                "claude",
                stdin=slave_fd,
                stdout=slave_fd,
                stderr=slave_fd,
                env={**os.environ, "TERM": "xterm"}
            )
            
            # Close slave_fd in parent process
            os.close(slave_fd)
            slave_fd = None
            
            # Track state for the interactive flow
            state = "waiting_for_theme"
            
            async def send_input_when_ready():
                """Send input based on current state"""
                await asyncio.sleep(2)  # Initial wait for prompt
                
                if state == "waiting_for_theme":
                    # Select default theme
                    os.write(master_fd, b"\n")
                    return "waiting_for_login"
                elif state == "waiting_for_login":
                    # Select OAuth login (option 1)
                    os.write(master_fd, b"\n")
                    return "waiting_for_url"
                return state
            
            # Initial input sending
            state = await send_input_when_ready()
            
            # Main loop to handle output and input
            buffer = b""
            while True:
                # Check for output from PTY
                try:
                    output = os.read(master_fd, 4096)
                    if output:
                        buffer += output
                        # Try to decode and send complete lines
                        while b'\n' in buffer or b'\r' in buffer:
                            line_end = buffer.find(b'\n')
                            if line_end == -1:
                                line_end = buffer.find(b'\r')
                            if line_end == -1:
                                break
                            
                            line = buffer[:line_end]
                            buffer = buffer[line_end+1:]
                            
                            try:
                                text = line.decode('utf-8', errors='replace')
                                # Clean ANSI escape sequences for cleaner output
                                await websocket.send_json({
                                    "type": "output",
                                    "text": text
                                })
                                
                                # State transitions based on output
                                if state == "waiting_for_theme" and "Choose the text style" in text:
                                    await asyncio.sleep(0.5)
                                    os.write(master_fd, b"\n")
                                    state = "waiting_for_login"
                                elif state == "waiting_for_login" and "Select login method" in text:
                                    await asyncio.sleep(0.5)
                                    os.write(master_fd, b"\n")
                                    state = "waiting_for_url"
                                elif "authenticated" in text.lower() or "success" in text.lower():
                                    await websocket.send_json({"type": "complete"})
                                    break
                            except:
                                pass
                        
                        # Send remaining buffer if it looks complete
                        if buffer and len(buffer) > 100:
                            try:
                                text = buffer.decode('utf-8', errors='replace')
                                await websocket.send_json({
                                    "type": "output", 
                                    "text": text
                                })
                                buffer = b""
                            except:
                                pass
                                
                except OSError:
                    await asyncio.sleep(0.1)
                
                # Check for input from WebSocket
                try:
                    data = await asyncio.wait_for(websocket.receive_json(), timeout=0.1)
                    if data.get("type") == "input":
                        code = data.get("text", "")
                        os.write(master_fd, f"{code}\n".encode())
                except asyncio.TimeoutError:
                    pass
                except WebSocketDisconnect:
                    break
                
                # Check if process ended
                if process.returncode is not None:
                    if process.returncode == 0:
                        await websocket.send_json({"type": "complete"})
                    else:
                        await websocket.send_json({
                            "type": "error",
                            "message": f"Process exited with code {process.returncode}"
                        })
                    break
                
        except WebSocketDisconnect:
            pass
        except Exception as e:
            await websocket.send_json({
                "type": "error",
                "message": str(e)
            })
        finally:
            # Cleanup
            if master_fd is not None:
                try:
                    os.close(master_fd)
                except:
                    pass
            if slave_fd is not None:
                try:
                    os.close(slave_fd)
                except:
                    pass
            if process and process.returncode is None:
                try:
                    process.terminate()
                    await process.wait()
                except:
                    pass
    
    # Add a note in the main docs
    original_description = app.description or ""
    app.description = f"""
{original_description}

### Authentication Required

This LiteLLM instance uses Claude Code which requires authentication.

**First-time setup:**
1. Visit [/auth](/auth) to authenticate with Claude
2. Follow the OAuth flow in your browser
3. Once authenticated, you can use all API endpoints

**Note:** Authentication persists across container restarts.
"""
    
    return app