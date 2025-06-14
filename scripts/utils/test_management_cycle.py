#!/usr/bin/env python3
"""
Automated Test Management Cycle (S-A-C-V-C)

Implements the weekly test management cycle:
- Scan: Find new/changed scripts in debug folder
- Analyze: Understand script purpose and find existing tests  
- Convert: Transform logic into proper tests
- Validate: Run full test suite + linters
- Clean: Archive processed scripts and commit changes

Usage:
    python scripts/utils/test_management_cycle.py --action scan
    python scripts/utils/test_management_cycle.py --action analyze
    python scripts/utils/test_management_cycle.py --action validate  
    python scripts/utils/test_management_cycle.py --action clean
    python scripts/utils/test_management_cycle.py --action full-cycle
"""

import argparse
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Tuple
import json
import glob


class TestManagementCycle:
    """Automated test management cycle implementation."""
    
    def __init__(self, workspace_root: str = "."):
        self.workspace_root = Path(workspace_root)
        self.debug_dir = self.workspace_root / "scripts" / "debug"
        self.archive_dir = self.workspace_root / "scripts" / "archive"
        self.tests_dir = self.workspace_root / "tests"
        
        # Ensure directories exist
        self.debug_dir.mkdir(parents=True, exist_ok=True)
        self.archive_dir.mkdir(parents=True, exist_ok=True)
        
    def scan_phase(self) -> List[Dict[str, str]]:
        """
        SCAN: Find new/changed scripts in debug folder and recent commits.
        Returns list of candidates for conversion.
        """
        print("🔍 SCAN Phase: Looking for scripts to convert...")
        
        candidates = []
        
        # 1. Scan debug directory for Python files
        debug_files = list(self.debug_dir.glob("*.py"))
        
        for file_path in debug_files:
            if file_path.name == "__init__.py":
                continue
                
            stat = file_path.stat()
            candidates.append({
                'type': 'debug_script',
                'path': str(file_path),
                'name': file_path.name,
                'lines': self._count_lines(file_path),
                'modified': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                'size_kb': round(stat.st_size / 1024, 2)
            })
        
        # 2. Scan recent git commits for fix:/feat: commits
        try:
            result = subprocess.run([
                'git', 'log', '--since=1 week ago', 
                '--pretty=format:%h|%s|%ci', '--grep=fix:', '--grep=feat:'
            ], capture_output=True, text=True, cwd=self.workspace_root)
            
            if result.returncode == 0:
                for line in result.stdout.strip().split('\n'):
                    if line:
                        commit_hash, subject, date = line.split('|', 2)
                        candidates.append({
                            'type': 'recent_commit',
                            'hash': commit_hash,
                            'subject': subject,
                            'date': date,
                            'needs_regression_test': 'fix:' in subject
                        })
        except Exception as e:
            print(f"⚠️  Could not scan git commits: {e}")
        
        print(f"✅ Found {len(candidates)} candidates")
        for candidate in candidates:
            if candidate['type'] == 'debug_script':
                print(f"  📄 {candidate['name']} ({candidate['lines']} lines, {candidate['size_kb']} KB)")
            elif candidate['type'] == 'recent_commit':
                print(f"  🔧 {candidate['hash']}: {candidate['subject'][:50]}...")
                
        return candidates
    
    def analyze_phase(self, candidates: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """
        ANALYZE: Understand script purpose and search for existing tests.
        Returns candidates with analysis results.
        """
        print("🔬 ANALYZE Phase: Understanding candidates...")
        
        analyzed = []
        
        for candidate in candidates:
            if candidate['type'] == 'debug_script':
                analysis = self._analyze_debug_script(candidate)
                analyzed.append({**candidate, **analysis})
            elif candidate['type'] == 'recent_commit':
                analysis = self._analyze_commit(candidate)
                analyzed.append({**candidate, **analysis})
        
        return analyzed
    
    def validate_phase(self) -> bool:
        """
        VALIDATE: Run full test suite + linters.
        Returns True if all tests pass.
        """
        print("✅ VALIDATE Phase: Running tests and linters...")
        
        commands = [
            (['uv', 'run', 'python', '-m', 'pytest', 'tests/', '-v', '--tb=short'], "Running pytest"),
            (['uv', 'run', 'ruff', 'check', 'src/', 'tests/'], "Running ruff linter"),
            (['uv', 'run', 'mypy', 'src/'], "Running mypy type check")
        ]
        
        all_passed = True
        
        for cmd, description in commands:
            print(f"🔧 {description}...")
            try:
                result = subprocess.run(cmd, cwd=self.workspace_root, capture_output=True, text=True)
                if result.returncode == 0:
                    print(f"  ✅ {description} - PASSED")
                else:
                    print(f"  ❌ {description} - FAILED")
                    print(f"  Output: {result.stdout[-200:]}")  # Last 200 chars
                    print(f"  Error: {result.stderr[-200:]}")   # Last 200 chars
                    all_passed = False
            except Exception as e:
                print(f"  ❌ {description} - ERROR: {e}")
                all_passed = False
        
        return all_passed
    
    def clean_phase(self, processed_files: List[str]) -> bool:
        """
        CLEAN: Archive processed scripts and commit changes.
        Returns True if cleanup successful.
        """
        print("🧹 CLEAN Phase: Archiving and committing...")
        
        if not processed_files:
            print("  ℹ️  No files to clean up")
            return True
        
        # Create archive directory with current month
        archive_month = self.archive_dir / datetime.now().strftime("%Y-%m")
        archive_month.mkdir(parents=True, exist_ok=True)
        
        # Archive processed files
        for file_path in processed_files:
            source = Path(file_path)
            if source.exists():
                # Rename to indicate it was converted
                archive_name = f"{source.stem}_converted_to_test{source.suffix}"
                target = archive_month / archive_name
                
                try:
                    # Use git mv to maintain history
                    subprocess.run(['git', 'mv', str(source), str(target)], 
                                 cwd=self.workspace_root, check=True)
                    print(f"  📦 Archived: {source.name} → {target}")
                except subprocess.CalledProcessError as e:
                    print(f"  ⚠️  Could not archive {source.name}: {e}")
        
        # Commit changes
        try:
            # Add new test files
            subprocess.run(['git', 'add', 'tests/'], cwd=self.workspace_root, check=True)
            
            # Commit with proper format
            commit_msg = f"test(conversion): convert {len(processed_files)} debug scripts to tests\n\nWeekly S-A-C-V-C cycle - {datetime.now().strftime('%Y-%m-%d')}"
            subprocess.run(['git', 'commit', '-m', commit_msg], 
                         cwd=self.workspace_root, check=True)
            print(f"  ✅ Committed changes")
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"  ⚠️  Could not commit changes: {e}")
            return False
    
    def run_full_cycle(self):
        """Run complete S-A-C-V-C cycle."""
        print("🚀 Starting Full Test Management Cycle (S-A-C-V-C)")
        print("=" * 60)
        
        # SCAN
        candidates = self.scan_phase()
        if not candidates:
            print("✨ No candidates found - repository is clean!")
            return
        
        print("\n" + "=" * 60)
        
        # ANALYZE
        analyzed = self.analyze_phase(candidates)
        
        # Show analysis results
        conversion_candidates = [c for c in analyzed 
                               if c.get('recommendation') == 'convert']
        
        if not conversion_candidates:
            print("✨ No scripts need conversion - analysis complete!")
            return
        
        print(f"\n📋 Conversion Plan:")
        for candidate in conversion_candidates:
            print(f"  🔄 {candidate['name']} → {candidate.get('target_test', 'TBD')}")
        
        print("\n⚠️  Manual conversion required. Use convert_script() method for each file.")
        print("   After conversion, run with --action validate and --action clean")
        
        print("\n" + "=" * 60)
        print("🎯 Next Steps:")
        print("1. Review conversion candidates above")
        print("2. Convert scripts manually or use convert_script() helper")
        print("3. Run: python scripts/utils/test_management_cycle.py --action validate")
        print("4. Run: python scripts/utils/test_management_cycle.py --action clean")
    
    def _analyze_debug_script(self, candidate: Dict[str, str]) -> Dict[str, str]:
        """Analyze a debug script to understand its purpose."""
        file_path = Path(candidate['path'])
        
        try:
            content = file_path.read_text()
            
            # Simple heuristics to determine purpose
            purpose = "general_debug"
            target_test_type = "integration"
            
            if 'test' in content.lower() or 'assert' in content.lower():
                purpose = "test_verification"
                target_test_type = "integration"
            elif 'mcp' in content.lower() or 'tool' in content.lower():
                purpose = "mcp_testing"
                target_test_type = "integration"  
            elif 'performance' in content.lower() or 'benchmark' in content.lower():
                purpose = "performance_check"
                target_test_type = "performance"
            elif 'error' in content.lower() or 'exception' in content.lower():
                purpose = "error_testing"
                target_test_type = "regression"
            
            # Check if similar test already exists
            existing_test = self._find_similar_test(candidate['name'])
            
            recommendation = "convert" if not existing_test else "extend_existing"
            
            return {
                'purpose': purpose,
                'target_test_type': target_test_type,
                'existing_test': existing_test,
                'recommendation': recommendation,
                'target_test': f"tests/{target_test_type}/test_{file_path.stem}.py"
            }
            
        except Exception as e:
            return {
                'purpose': 'unknown',
                'error': str(e),
                'recommendation': 'manual_review'
            }
    
    def _analyze_commit(self, candidate: Dict[str, str]) -> Dict[str, str]:
        """Analyze a commit to determine if it needs a regression test."""
        if candidate.get('needs_regression_test'):
            return {
                'purpose': 'regression_test_needed',
                'recommendation': 'create_regression_test',
                'target_test': f"tests/regression/test_fix_{candidate['hash']}.py"
            }
        else:
            return {
                'purpose': 'feature_addition', 
                'recommendation': 'create_feature_test',
                'target_test': f"tests/integration/test_feature_{candidate['hash']}.py"
            }
    
    def _find_similar_test(self, script_name: str) -> str:
        """Find existing test that might be similar to the script."""
        # Remove common prefixes/suffixes
        clean_name = script_name.replace('debug_', '').replace('.py', '')
        
        # Search in all test directories
        for test_dir in ['unit', 'integration', 'regression', 'e2e', 'performance']:
            test_path = self.tests_dir / test_dir
            if test_path.exists():
                for test_file in test_path.glob(f"*{clean_name}*.py"):
                    return str(test_file)
                    
        return ""
    
    def _count_lines(self, file_path: Path) -> int:
        """Count lines in a file."""
        try:
            return len(file_path.read_text().splitlines())
        except:
            return 0


def main():
    parser = argparse.ArgumentParser(description="Test Management Cycle (S-A-C-V-C)")
    parser.add_argument('--action', choices=['scan', 'analyze', 'validate', 'clean', 'full-cycle'],
                       default='full-cycle', help='Action to perform')
    parser.add_argument('--workspace', default='.', help='Workspace root directory')
    
    args = parser.parse_args()
    
    cycle = TestManagementCycle(args.workspace)
    
    if args.action == 'scan':
        candidates = cycle.scan_phase()
        print(f"\n📊 Summary: {len(candidates)} candidates found")
        
    elif args.action == 'analyze':
        candidates = cycle.scan_phase()
        analyzed = cycle.analyze_phase(candidates)
        print(f"\n📊 Summary: {len(analyzed)} candidates analyzed")
        
    elif args.action == 'validate':
        success = cycle.validate_phase()
        sys.exit(0 if success else 1)
        
    elif args.action == 'clean':
        # This would typically be called with specific files
        print("⚠️  Clean phase requires processed files list")
        print("   Use programmatically or after conversion")
        
    elif args.action == 'full-cycle':
        cycle.run_full_cycle()


if __name__ == "__main__":
    main() 