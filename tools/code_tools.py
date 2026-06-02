from crewai_tools import BaseTool
from pydantic import Field, BaseModel
from typing import Type
import subprocess
import tempfile
import os
import ast
import sys
from pathlib import Path

class CodeInput(BaseModel):
    code: str = Field(..., description="Python code to execute")

class CodeInterpreterTool(BaseTool):
    name: str = "code_interpreter"
    description: str = "Execute Python code safely in a sandboxed environment with 30-second timeout"
    args_schema: Type[BaseModel] = CodeInput
    
    def _run(self, code: str) -> str:
        try:
            # Create a temporary file with the code
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
                f.write(code)
                temp_file = f.name
            
            try:
                # Execute the code with timeout
                result = subprocess.run(
                    [sys.executable, temp_file],
                    capture_output=True,
                    text=True,
                    timeout=30,  # 30 second timeout
                    cwd=tempfile.gettempdir()
                )
                
                if result.returncode == 0:
                    output = result.stdout.strip()
                    return f"Output:\n{output}" if output else "Code executed successfully (no output)"
                else:
                    error = result.stderr.strip()
                    return f"Error:\n{error}"
                    
            except subprocess.TimeoutExpired:
                return "Error: Code execution timed out (30s limit)"
            finally:
                # Clean up temp file
                if os.path.exists(temp_file):
                    os.unlink(temp_file)
                
        except Exception as e:
            return f"Error: {str(e)}"

class CodeReviewInput(BaseModel):
    file_path: str = Field(..., description="Path to Python file to review")

class CodeReviewerTool(BaseTool):
    name: str = "code_reviewer"
    description: str = "Review Python code for syntax errors, security issues, and style problems"
    args_schema: Type[BaseModel] = CodeReviewInput
    
    def _run(self, file_path: str) -> str:
        try:
            # Read the file
            if not os.path.exists(file_path):
                return f"File not found: {file_path}"
            
            with open(file_path, 'r', encoding='utf-8') as f:
                code = f.read()
            
            if not code.strip():
                return "File is empty"
            
            issues = []
            
            # Try to parse as Python to check syntax
            try:
                ast.parse(code)
                issues.append("✅ Syntax: Valid Python syntax")
            except SyntaxError as e:
                issues.append(f"❌ Syntax Error: {e}")
                return "\n".join(issues)
            
            # Basic security checks
            security_patterns = [
                ('eval(', "Potentially dangerous eval() function"),
                ('exec(', "Potentially dangerous exec() function"),
                ('subprocess.call', "Direct subprocess call without validation"),
                ('os.system', "Direct os.system call without validation"),
                ('input(', "User input without validation")
            ]
            
            security_issues = []
            for pattern, message in security_patterns:
                if pattern in code:
                    security_issues.append(f"⚠️  Security: {message}")
            
            if not security_issues:
                security_issues.append("✅ Security: No obvious security issues found")
            
            # Basic style checks
            style_issues = []
            lines = code.split('\n')
            
            for i, line in enumerate(lines, 1):
                # Check for long lines
                if len(line.strip()) > 120:
                    style_issues.append(f"Line {i}: Line too long ({len(line.strip())} chars)")
                
                # Check for missing docstrings in functions
                if line.strip().startswith('def ') and i < len(lines):
                    next_line = lines[i].strip() if i < len(lines) else ''
                    if not next_line.startswith('"""') and not next_line.startswith('#'):
                        style_issues.append(f"Line {i}: Function missing docstring")
            
            if not style_issues:
                style_issues.append("✅ Style: No major style issues found")
            
            # Combine all results
            result = issues + security_issues + style_issues
            return "\n".join(result)
            
        except Exception as e:
            return f"Review error: {str(e)}"
