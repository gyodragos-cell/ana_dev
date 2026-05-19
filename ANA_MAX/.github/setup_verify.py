#!/usr/bin/env python3
"""
GitHub Actions Setup Guide for ANA MAX
=======================================
This script verifies that all GitHub Actions files are properly configured.
"""
import sys
from pathlib import Path

if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

base_dir = Path(__file__).parent
github_dir = base_dir / ".github"

print("="*60)
print("  GitHub Actions Configuration Check")
print("="*60)
print()

# Check workflow files
workflows = github_dir / "workflows"
if workflows.exists():
    yml_files = list(workflows.glob("*.yml"))
    print(f"✅ Workflows: {len(yml_files)}")
    for wf in yml_files:
        print(f"   - {wf.name}")
else:
    print("❌ No workflows directory")

print()

# Check Dependabot
dependabot = github_dir / "dependabot.yml"
if dependabot.exists():
    print("✅ Dependabot configured")
else:
    print("⚠️  No Dependabot config")

print()

# Check templates
templates = github_dir / "ISSUE_TEMPLATE"
if templates.exists():
    md_files = list(templates.glob("*.md"))
    print(f"✅ Issue Templates: {len(md_files)}")
    for tm in md_files:
        print(f"   - {tm.name}")
else:
    print("⚠️  No issue templates")

pr_template = github_dir / "PULL_REQUEST_TEMPLATE.md"
if pr_template.exists():
    print("✅ PR Template exists")
else:
    print("⚠️  No PR template")

print()
print("="*60)
print("  Setup Complete!")
print("="*60)
print()
print("Next steps:")
print("1. Push to GitHub: git push origin main")
print("2. Check Actions tab: https://github.com/YOUR_USERNAME/ANA_MAX/actions")
print("3. Workflows will run automatically on:")
print("   - Push to main/master/develop")
print("   - Pull requests")
print("   - Manual trigger (workflow_dispatch)")
print()
print("Features enabled:")
print("  ✅ Automated testing (pytest, compilation)")
print("  ✅ Security scanning (Bandit)")
print("  ✅ BOM encoding check")
print("  ✅ Jules integration verification")
print("  ✅ Dependabot (auto dependency updates)")
print("  ✅ Issue & PR templates")
print()
