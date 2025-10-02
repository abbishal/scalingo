import subprocess
import os
from flask import Flask, request, jsonify

app = Flask(__name__)

HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Python Web Interpreter</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; }
        .container { max-width: 1200px; margin: 0 auto; }
        .editor { width: 100%; height: 300px; margin: 10px 0; }
        .output { background: #f5f5f5; padding: 15px; margin: 10px 0; min-height: 200px; }
        button { padding: 10px 20px; margin: 5px; }
    </style>
</head>
<body>
    <div class="container">
        <h1>Python Web Interpreter</h1>
        <p><strong>Warning:</strong> This can run arbitrary Python code and system commands.</p>
        
        <div>
            <button onclick="runPython()">Run Python Code</button>
            <button onclick="runCommand()">Run System Command</button>
            <button onclick="clearOutput()">Clear Output</button>
        </div>
        
        <textarea id="code" class="editor">print("Hello, World!")
for i in range(5):
    print(f"Number: {i}")</textarea>
        
        <div id="output" class="output">Output will appear here...</div>
    </div>

    <script>
        function runPython() {
            const code = document.getElementById('code').value;
            fetch('/run_python', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({code: code})
            })
            .then(r => r.json())
            .then(data => {
                document.getElementById('output').textContent = data.output || data.error;
            });
        }

        function runCommand() {
            const cmd = prompt("Enter system command:");
            if (cmd) {
                fetch('/run_command', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({command: cmd})
                })
                .then(r => r.json())
                .then(data => {
                    document.getElementById('output').textContent = data.output || data.error;
                });
            }
        }

        function clearOutput() {
            document.getElementById('output').textContent = '';
        }
    </script>
</body>
</html>
"""

def run_python_code(code):
    """Execute Python code safely"""
    try:
        # Write code to temporary file
        with open('/tmp/temp_code.py', 'w') as f:
            f.write(code)
        
        # Execute the code
        result = subprocess.run(
            ['python', '/tmp/temp_code.py'],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        output = result.stdout
        if result.stderr:
            output += "\nErrors:\n" + result.stderr
            
        # Clean up
        if os.path.exists('/tmp/temp_code.py'):
            os.remove('/tmp/temp_code.py')
            
        return output or "Code executed successfully (no output)"
        
    except subprocess.TimeoutExpired:
        return "Error: Execution timed out after 30 seconds"
    except Exception as e:
        return f"Error: {str(e)}"

def run_system_command(command):
    """Execute system command safely"""
    try:
        # Block dangerous commands
        dangerous = ['rm -rf', 'format', 'mkfs', 'dd', 'shutdown', 'reboot', '>', '>>']
        if any(cmd in command for cmd in dangerous):
            return "Error: Dangerous command blocked"
            
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        output = result.stdout
        if result.stderr:
            output += "\nErrors:\n" + result.stderr
            
        return output or "Command executed successfully (no output)"
        
    except subprocess.TimeoutExpired:
        return "Error: Command timed out after 30 seconds"
    except Exception as e:
        return f"Error: {str(e)}"

@app.route('/')
def index():
    return HTML

@app.route('/run_python', methods=['POST'])
def execute_python():
    data = request.get_json()
    code = data.get('code', '')
    
    if not code:
        return jsonify({'error': 'No code provided'})
        
    output = run_python_code(code)
    return jsonify({'output': output})

@app.route('/run_command', methods=['POST'])
def execute_command():
    data = request.get_json()
    command = data.get('command', '')
    
    if not command:
        return jsonify({'error': 'No command provided'})
        
    output = run_system_command(command)
    return jsonify({'output': output})

if __name__ == '__main__':
    print("Warning: This application can execute arbitrary code!")
    print("Running on http://localhost:5000")
    app.run(host='0.0.0.0', port=5000, debug=False)
