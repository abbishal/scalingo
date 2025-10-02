import os
import subprocess
import sys
import tempfile
from io import StringIO
from flask import Flask, request, jsonify, render_template_string
import html

app = Flask(__name__)

# Security configuration
MAX_EXECUTION_TIME = 5  # seconds
MAX_OUTPUT_LENGTH = 10000  # characters

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Python Web Interpreter</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 15px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            overflow: hidden;
        }
        
        .header {
            background: #2c3e50;
            color: white;
            padding: 30px;
            text-align: center;
        }
        
        .header h1 {
            font-size: 2.5em;
            margin-bottom: 10px;
        }
        
        .header p {
            opacity: 0.8;
            font-size: 1.1em;
        }
        
        .warning {
            background: #e74c3c;
            color: white;
            padding: 15px;
            text-align: center;
            font-weight: bold;
            border-bottom: 3px solid #c0392b;
        }
        
        .content {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 0;
            min-height: 600px;
        }
        
        @media (max-width: 768px) {
            .content {
                grid-template-columns: 1fr;
            }
        }
        
        .editor-section, .output-section {
            padding: 25px;
        }
        
        .editor-section {
            background: #f8f9fa;
            border-right: 2px solid #e9ecef;
        }
        
        .output-section {
            background: #1a1a1a;
            color: #00ff00;
            font-family: 'Courier New', monospace;
        }
        
        .section-title {
            font-size: 1.3em;
            margin-bottom: 15px;
            color: #2c3e50;
            font-weight: 600;
        }
        
        .output-title {
            color: #00ff00;
        }
        
        textarea {
            width: 100%;
            height: 400px;
            padding: 15px;
            border: 2px solid #ddd;
            border-radius: 8px;
            font-family: 'Courier New', monospace;
            font-size: 14px;
            resize: vertical;
            background: #ffffff;
            transition: border-color 0.3s;
        }
        
        textarea:focus {
            outline: none;
            border-color: #667eea;
        }
        
        .button-group {
            display: flex;
            gap: 10px;
            margin-top: 20px;
            flex-wrap: wrap;
        }
        
        button {
            padding: 12px 25px;
            border: none;
            border-radius: 6px;
            font-size: 14px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        
        .run-btn {
            background: #27ae60;
            color: white;
        }
        
        .run-btn:hover {
            background: #219a52;
            transform: translateY(-2px);
        }
        
        .clear-btn {
            background: #e74c3c;
            color: white;
        }
        
        .clear-btn:hover {
            background: #c0392b;
            transform: translateY(-2px);
        }
        
        .example-btn {
            background: #3498db;
            color: white;
        }
        
        .example-btn:hover {
            background: #2980b9;
            transform: translateY(-2px);
        }
        
        .command-btn {
            background: #9b59b6;
            color: white;
        }
        
        .command-btn:hover {
            background: #8e44ad;
            transform: translateY(-2px);
        }
        
        #output {
            background: #1a1a1a;
            color: #00ff00;
            padding: 15px;
            border-radius: 8px;
            height: 400px;
            overflow-y: auto;
            white-space: pre-wrap;
            word-wrap: break-word;
            font-size: 14px;
            line-height: 1.4;
        }
        
        .loading {
            display: none;
            text-align: center;
            padding: 20px;
            color: #667eea;
        }
        
        .spinner {
            border: 4px solid #f3f3f3;
            border-top: 4px solid #667eea;
            border-radius: 50%;
            width: 40px;
            height: 40px;
            animation: spin 1s linear infinite;
            margin: 0 auto 10px;
        }
        
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        
        .error {
            color: #ff6b6b;
        }
        
        .success {
            color: #51cf66;
        }
        
        .command-input {
            width: 100%;
            padding: 10px;
            margin-top: 10px;
            border: 2px solid #ddd;
            border-radius: 6px;
            font-family: 'Courier New', monospace;
            display: none;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🐍 Python Web Interpreter</h1>
            <p>Execute Python code and system commands in your browser</p>
        </div>
        
        <div class="warning">
            ⚠️ WARNING: This tool can execute arbitrary commands on the host system. Use with extreme caution!
        </div>
        
        <div class="content">
            <div class="editor-section">
                <div class="section-title">Code Editor</div>
                <textarea id="code" placeholder="Enter your Python code here...">print("Hello, World!")
for i in range(5):
    print(f"Number: {i}")</textarea>
                
                <input type="text" id="command" class="command-input" placeholder="Enter system command...">
                
                <div class="button-group">
                    <button class="run-btn" onclick="runCode()">Run Python Code</button>
                    <button class="command-btn" onclick="toggleCommand()">Run System Command</button>
                    <button class="example-btn" onclick="loadExample()">Load Example</button>
                    <button class="clear-btn" onclick="clearAll()">Clear All</button>
                </div>
            </div>
            
            <div class="output-section">
                <div class="section-title output-title">Output</div>
                <div class="loading" id="loading">
                    <div class="spinner"></div>
                    <div>Executing code...</div>
                </div>
                <pre id="output">Ready to execute code...</pre>
            </div>
        </div>
    </div>

    <script>
        let commandMode = false;
        
        function toggleCommand() {
            commandMode = !commandMode;
            const commandInput = document.getElementById('command');
            const codeTextarea = document.getElementById('code');
            
            if (commandMode) {
                commandInput.style.display = 'block';
                codeTextarea.style.display = 'none';
                commandInput.focus();
            } else {
                commandInput.style.display = 'none';
                codeTextarea.style.display = 'block';
            }
        }
        
        function runCode() {
            const loading = document.getElementById('loading');
            const output = document.getElementById('output');
            const code = commandMode ? 
                document.getElementById('command').value : 
                document.getElementById('code').value;
            
            if (!code.trim()) {
                output.innerHTML = '<span class="error">Please enter some code or a command to execute.</span>';
                return;
            }
            
            loading.style.display = 'block';
            output.innerHTML = '';
            
            const endpoint = commandMode ? '/run_command' : '/run_python';
            
            fetch(endpoint, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    code: code,
                    command: commandMode ? code : ''
                })
            })
            .then(response => response.json())
            .then(data => {
                loading.style.display = 'none';
                if (data.error) {
                    output.innerHTML = `<span class="error">${data.error}</span>`;
                } else {
                    output.innerHTML = `<span class="success">${data.output}</span>`;
                }
            })
            .catch(error => {
                loading.style.display = 'none';
                output.innerHTML = `<span class="error">Error: ${error.message}</span>`;
            });
        }
        
        function loadExample() {
            const exampleCode = `import os
import sys

# System information
print("Python version:", sys.version)
print("Current directory:", os.getcwd())
print("Platform:", sys.platform)

# List files in current directory
print("\\nFiles in current directory:")
for file in os.listdir('.'):
    print(f"  - {file}")

# Simple calculation
result = sum(i**2 for i in range(10))
print(f"\\nSum of squares from 0 to 9: {result}")`;
            
            document.getElementById('code').value = exampleCode;
            if (commandMode) toggleCommand();
        }
        
        function clearAll() {
            document.getElementById('code').value = '';
            document.getElementById('command').value = '';
            document.getElementById('output').innerHTML = 'Ready to execute code...';
            if (commandMode) toggleCommand();
        }
        
        // Handle Enter key in command mode
        document.getElementById('command').addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                runCode();
            }
        });
        
        // Handle Ctrl+Enter in code editor
        document.getElementById('code').addEventListener('keydown', function(e) {
            if (e.ctrlKey && e.key === 'Enter') {
                runCode();
            }
        });
    </script>
</body>
</html>
"""

def execute_python_code(code):
    """Execute Python code and capture output"""
    try:
        # Create a temporary file to execute the code
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(code)
            temp_file = f.name
        
        try:
            # Execute the code with timeout
            result = subprocess.run(
                [sys.executable, temp_file],
                capture_output=True,
                text=True,
                timeout=MAX_EXECUTION_TIME,
                cwd=os.getcwd()
            )
            
            output = result.stdout + result.stderr
            if len(output) > MAX_OUTPUT_LENGTH:
                output = output[:MAX_OUTPUT_LENGTH] + "\n... (output truncated)"
                
            return output.strip() or "Code executed successfully (no output)"
            
        except subprocess.TimeoutExpired:
            return f"Error: Code execution timed out after {MAX_EXECUTION_TIME} seconds"
        finally:
            # Clean up temporary file
            if os.path.exists(temp_file):
                os.unlink(temp_file)
                
    except Exception as e:
        return f"Error: {str(e)}"

def execute_system_command(command):
    """Execute system command and capture output"""
    try:
        # Security: Limit dangerous commands (customize this list as needed)
        dangerous_commands = ['rm -rf', 'format', 'mkfs', 'dd', 'shutdown', 'reboot']
        if any(cmd in command.lower() for cmd in dangerous_commands):
            return "Error: This command is not allowed for security reasons"
        
        # Execute command with timeout
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=MAX_EXECUTION_TIME,
            cwd=os.getcwd()
        )
        
        output = result.stdout + result.stderr
        if len(output) > MAX_OUTPUT_LENGTH:
            output = output[:MAX_OUTPUT_LENGTH] + "\n... (output truncated)"
            
        return output.strip() or "Command executed successfully (no output)"
        
    except subprocess.TimeoutExpired:
        return f"Error: Command execution timed out after {MAX_EXECUTION_TIME} seconds"
    except Exception as e:
        return f"Error: {str(e)}"

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/run_python', methods=['POST'])
def run_python():
    """Endpoint to execute Python code"""
    try:
        data = request.get_json()
        code = data.get('code', '')
        
        if not code:
            return jsonify({'error': 'No code provided'})
        
        output = execute_python_code(code)
        return jsonify({'output': html.escape(output)})
        
    except Exception as e:
        return jsonify({'error': f'Server error: {str(e)}'})

@app.route('/run_command', methods=['POST'])
def run_command():
    """Endpoint to execute system commands"""
    try:
        data = request.get_json()
        command = data.get('command', '')
        
        if not command:
            return jsonify({'error': 'No command provided'})
        
        output = execute_system_command(command)
        return jsonify({'output': html.escape(output)})
        
    except Exception as e:
        return jsonify({'error': f'Server error: {str(e)}'})

if __name__ == '__main__':
    # Warning message
    print("⚠️  WARNING: This application can execute arbitrary commands on the host system!")
    print("⚠️  Only run this in a secure, isolated environment!")
    print("🚀 Starting server on http://localhost:5000")
    
    app.run(host='0.0.0.0', port=5000, debug=False)
