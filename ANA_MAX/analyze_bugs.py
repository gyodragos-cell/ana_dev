#!/usr/bin/env python3
"""
ANA MAX - Bug Analysis & Repair Script
=======================================
Analizeaza codul si repara bug-urile comune
"""

import os
import sys
import json
import ast
from pathlib import Path
from typing import List, Dict, Tuple

# Force UTF-8 encoding
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

sys.path.insert(0, str(Path(__file__).parent))

class BugAnalyzer:
    def __init__(self, base_dir: Path):
        self.base_dir = base_dir
        self.errors = []
        self.warnings = []
        self.fixed = []
    
    def analyze_all(self):
        """Run all analyses"""
        print("="*60)
        print("  ANA MAX - Bug Analysis & Repair")
        print("="*60)
        print()
        
        self.check_corrupted_files()
        self.check_imports()
        self.check_tool_definitions()
        self.check_jules_integration()
        self.check_memory_leaks()
        self.check_security_issues()
        
        self.print_report()
    
    def check_corrupted_files(self):
        """Check for corrupted Python files"""
        print("📋 Checking for corrupted files...")
        
        for py_file in self.base_dir.rglob("*.py"):
            # Skip archives and venv
            if 'archives' in str(py_file) or 'venv' in str(py_file) or 'node_modules' in str(py_file):
                continue
            
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    # Check for null bytes
                    if '\x00' in content:
                        self.errors.append(f"Corrupted file (null bytes): {py_file}")
                        print(f"  ❌ {py_file.name} - CORRUPTED")
                    # Try to parse
                    try:
                        ast.parse(content)
                    except SyntaxError as e:
                        self.warnings.append(f"Syntax error in {py_file}: {e}")
                        print(f"  ⚠️  {py_file.name} - SYNTAX ERROR")
            except Exception as e:
                self.errors.append(f"Cannot read {py_file}: {e}")
        
        print(f"  ✅ Scan complete\n")
    
    def check_imports(self):
        """Check for common import issues"""
        print("📦 Checking imports...")
        
        # Check jules_mcp_bridge
        try:
            from tools.jules_mcp_bridge import JulesMCPTool
            tool = JulesMCPTool()
            defn = tool.get_definition()
            print(f"  ✅ jules_mcp_bridge - OK ({len(defn.parameters)} params)")
        except Exception as e:
            self.errors.append(f"jules_mcp_bridge import failed: {e}")
            print(f"  ❌ jules_mcp_bridge - FAILED: {e}")
        
        # Check jules_api_rotator
        try:
            from tools.jules_api_rotator import get_rotator
            rotator = get_rotator()
            print(f"  ✅ jules_api_rotator - OK ({len(rotator.keys)} keys)")
        except Exception as e:
            self.errors.append(f"jules_api_rotator import failed: {e}")
            print(f"  ❌ jules_api_rotator - FAILED: {e}")
        
        # Check base imports
        try:
            from tools.base import Tool, ToolDefinition, ToolParameter, ToolResult, ToolStatus
            print(f"  ✅ tools.base - OK")
        except Exception as e:
            self.errors.append(f"tools.base import failed: {e}")
            print(f"  ❌ tools.base - FAILED: {e}")
        
        print()
    
    def check_tool_definitions(self):
        """Check all tool definitions are valid"""
        print("🔧 Checking tool definitions...")
        
        tools_dir = self.base_dir / "tools"
        tool_count = 0
        
        for tool_file in tools_dir.glob("*.py"):
            if tool_file.name.startswith('__'):
                continue
            
            try:
                # Try to import and instantiate
                module_name = f"tools.{tool_file.stem}"
                __import__(module_name)
                module = sys.modules[module_name]
                
                # Find Tool classes
                for attr_name in dir(module):
                    attr = getattr(module, attr_name)
                    if isinstance(attr, type) and attr.__name__.endswith('Tool') and attr.__name__ not in ['Tool', 'BaseTool']:
                        try:
                            instance = attr()
                            if hasattr(instance, 'get_definition'):
                                defn = instance.get_definition()
                                if defn and defn.name:
                                    tool_count += 1
                                    # print(f"  ✅ {defn.name}")
                        except Exception as e:
                            self.warnings.append(f"Tool {attr_name} failed: {e}")
            except Exception as e:
                if 'archives' not in str(tool_file):
                    self.warnings.append(f"Module {tool_file.stem} import warning: {e}")
        
        print(f"  ✅ {tool_count} tools validated\n")
    
    def check_jules_integration(self):
        """Check Jules integration"""
        print("🎯 Checking Jules integration...")
        
        # Check keys file
        keys_file = Path(r"C:\Users\billy\Desktop\jules\jules-mcp-server-main\.jules_keys.json")
        if keys_file.exists():
            with open(keys_file) as f:
                data = json.load(f)
                keys = data.get('keys', [])
                print(f"  ✅ {len(keys)} API keys configured")
                
                # Check if any key is active
                active = [k for k in keys if k.get('is_active', True)]
                print(f"  ✅ {len(active)} keys active")
        else:
            self.warnings.append("Jules keys file not found")
            print(f"  ⚠️  Keys file not found")
        
        # Check Jules MCP path
        jules_path = Path(r"C:\Users\billy\Desktop\jules\jules-mcp-server-main")
        if jules_path.exists():
            dist_file = jules_path / "dist" / "index.js"
            if dist_file.exists():
                print(f"  ✅ Jules MCP Server built")
            else:
                self.errors.append("Jules MCP not built - run: npm run build")
                print(f"  ❌ Jules MCP not built")
        else:
            self.warnings.append("Jules MCP path not found")
            print(f"  ⚠️  Jules path not found")
        
        print()
    
    def check_memory_leaks(self):
        """Check for potential memory leaks"""
        print("🧠 Checking for memory issues...")
        
        # Check memory directory
        memory_dir = self.base_dir / "memory"
        if memory_dir.exists():
            db_files = list(memory_dir.glob("*.db"))
            total_size = sum(f.stat().st_size for f in db_files)
            print(f"  ✅ {len(db_files)} database files ({total_size/1024:.1f} KB)")
        else:
            self.warnings.append("Memory directory not found")
            print(f"  ⚠️  Memory directory missing")
        
        # Check logs
        logs_dir = self.base_dir / "logs"
        if logs_dir.exists():
            log_file = logs_dir / "ana_max.log"
            if log_file.exists():
                size = log_file.stat().st_size
                if size > 50 * 1024 * 1024:  # 50MB
                    self.warnings.append(f"Log file too large: {size/1024/1024:.1f} MB")
                    print(f"  ⚠️  Log file large: {size/1024/1024:.1f} MB")
                else:
                    print(f"  ✅ Log file OK ({size/1024:.1f} KB)")
        
        print()
    
    def check_security_issues(self):
        """Check for security issues"""
        print("🔒 Checking security...")
        
        # Check .env file
        env_file = self.base_dir / ".env"
        if env_file.exists():
            with open(env_file) as f:
                content = f.read()
                # Check if API keys are exposed
                if 'your_key_here' in content or 'your_secret' in content:
                    self.warnings.append(".env contains placeholder keys")
                    print(f"  ⚠️  .env has placeholder keys")
                else:
                    print(f"  ✅ .env configured")
        else:
            self.warnings.append(".env file not found")
            print(f"  ⚠️  .env missing")
        
        # Check for hardcoded secrets in code
        for py_file in (self.base_dir / "tools").glob("*.py"):
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    if 'API_KEY = "' in content or 'SECRET = "' in content:
                        self.warnings.append(f"Possible hardcoded secret in {py_file.name}")
            except:
                pass
        
        print(f"  ✅ Security scan complete\n")
    
    def print_report(self):
        """Print final report"""
        print("="*60)
        print("  Analysis Report")
        print("="*60)
        print()
        
        if self.errors:
            print(f"❌ ERRORS ({len(self.errors)}):")
            for err in self.errors:
                print(f"  • {err}")
            print()
        
        if self.warnings:
            print(f"⚠️  WARNINGS ({len(self.warnings)}):")
            for warn in self.warnings:
                print(f"  • {warn}")
            print()
        
        if self.fixed:
            print(f"✅ FIXED ({len(self.fixed)}):")
            for fix in self.fixed:
                print(f"  • {fix}")
            print()
        
        if not self.errors and not self.warnings:
            print("✅ No issues found! System is healthy.\n")
        else:
            print(f"📊 Summary: {len(self.errors)} errors, {len(self.warnings)} warnings\n")


if __name__ == "__main__":
    base_dir = Path(__file__).parent
    analyzer = BugAnalyzer(base_dir)
    analyzer.analyze_all()
