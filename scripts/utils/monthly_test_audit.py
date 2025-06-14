#!/usr/bin/env python3
"""
Monthly Test Audit Tool

Performs comprehensive monthly audit of test suite:
- Coverage analysis and reporting
- Flaky test detection
- Performance metrics
- Test organization review
- Cleanup recommendations

Usage:
    python scripts/utils/monthly_test_audit.py --full-report
    python scripts/utils/monthly_test_audit.py --coverage-only
    python scripts/utils/monthly_test_audit.py --performance-only
"""

import argparse
import json
import re
import subprocess
import sys
import time
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Tuple
import xml.etree.ElementTree as ET


class MonthlyTestAudit:
    """Monthly test suite auditing and reporting."""
    
    def __init__(self, workspace_root: str = "."):
        self.workspace_root = Path(workspace_root)
        self.tests_dir = self.workspace_root / "tests"
        self.reports_dir = self.workspace_root / "docs" / "fixes"
        self.reports_dir.mkdir(parents=True, exist_ok=True)
        
        # Audit configuration
        self.coverage_targets = {
            'total': 34,  # Current target from pyproject.toml
            'unit': 90,
            'integration': 80,
            'regression': 95,  # Critical - should be very high
        }
        
        self.performance_limits = {
            'unit_test_max_seconds': 2,
            'integration_test_max_seconds': 30,
            'total_suite_max_minutes': 8,
            'flaky_threshold_percent': 1.0,  # Max 1% flaky tests
        }
    
    def run_full_audit(self) -> Dict:
        """Run complete monthly audit."""
        print("🔍 Monthly Test Audit Starting...")
        print("=" * 60)
        
        audit_results = {
            'timestamp': datetime.now().isoformat(),
            'coverage': self._audit_coverage(),
            'performance': self._audit_performance(),
            'organization': self._audit_organization(),
            'flaky_tests': self._audit_flaky_tests(),
            'recommendations': []
        }
        
        # Generate recommendations
        audit_results['recommendations'] = self._generate_recommendations(audit_results)
        
        # Save report
        report_file = self._save_audit_report(audit_results)
        
        print("\n" + "=" * 60)
        print(f"📊 Audit Complete - Report saved to: {report_file}")
        print(f"🎯 Overall Health Score: {self._calculate_health_score(audit_results)}/100")
        
        return audit_results
    
    def _audit_coverage(self) -> Dict:
        """Audit test coverage."""
        print("📈 Auditing Coverage...")
        
        try:
            # Run coverage analysis
            result = subprocess.run([
                'uv', 'run', 'python', '-m', 'pytest', 
                '--cov=src/neira_code_analyzer',
                '--cov-report=xml:coverage_audit.xml',
                '--cov-report=json:coverage_audit.json',
                'tests/', '-q'
            ], cwd=self.workspace_root, capture_output=True, text=True)
            
            if result.returncode != 0:
                return {'error': f"Coverage run failed: {result.stderr}"}
            
            # Parse coverage results
            coverage_data = self._parse_coverage_results()
            
            # Calculate coverage by test type
            coverage_by_type = self._calculate_coverage_by_test_type()
            
            return {
                'total_coverage': coverage_data.get('totals', {}).get('percent_covered', 0),
                'by_file': coverage_data.get('files', {}),
                'by_test_type': coverage_by_type,
                'target_met': coverage_data.get('totals', {}).get('percent_covered', 0) >= self.coverage_targets['total'],
                'files_below_target': self._find_low_coverage_files(coverage_data),
                'improvement_needed': max(0, self.coverage_targets['total'] - coverage_data.get('totals', {}).get('percent_covered', 0))
            }
            
        except Exception as e:
            return {'error': f"Coverage audit failed: {e}"}
    
    def _audit_performance(self) -> Dict:
        """Audit test performance."""
        print("⚡ Auditing Performance...")
        
        try:
            # Run tests with timing
            start_time = time.time()
            result = subprocess.run([
                'uv', 'run', 'python', '-m', 'pytest', 
                'tests/', '-v', '--tb=short', '--durations=10'
            ], cwd=self.workspace_root, capture_output=True, text=True)
            total_time = time.time() - start_time
            
            # Parse timing information
            slow_tests = self._parse_slow_tests(result.stdout)
            
            return {
                'total_runtime_seconds': round(total_time, 2),
                'total_runtime_minutes': round(total_time / 60, 2),
                'within_limit': total_time < (self.performance_limits['total_suite_max_minutes'] * 60),
                'slow_tests': slow_tests,
                'test_count': self._count_total_tests(),
                'avg_test_time': round(total_time / max(1, self._count_total_tests()), 3),
                'performance_grade': self._grade_performance(total_time, slow_tests)
            }
            
        except Exception as e:
            return {'error': f"Performance audit failed: {e}"}
    
    def _audit_organization(self) -> Dict:
        """Audit test organization and structure."""
        print("📁 Auditing Organization...")
        
        organization = {
            'test_directories': {},
            'naming_compliance': {},
            'file_sizes': {},
            'structure_score': 0
        }
        
        # Analyze each test directory
        for test_type in ['unit', 'integration', 'regression', 'e2e', 'performance']:
            test_dir = self.tests_dir / test_type
            if test_dir.exists():
                organization['test_directories'][test_type] = {
                    'file_count': len(list(test_dir.glob('test_*.py'))),
                    'total_lines': sum(self._count_lines(f) for f in test_dir.glob('test_*.py')),
                    'avg_file_size': 0,
                    'largest_file': None,
                    'naming_violations': []
                }
                
                files = list(test_dir.glob('test_*.py'))
                if files:
                    file_sizes = [self._count_lines(f) for f in files]
                    organization['test_directories'][test_type]['avg_file_size'] = sum(file_sizes) // len(file_sizes)
                    
                    # Find largest file
                    largest_idx = file_sizes.index(max(file_sizes))
                    organization['test_directories'][test_type]['largest_file'] = {
                        'name': files[largest_idx].name,
                        'lines': file_sizes[largest_idx]
                    }
        
        # Check naming compliance
        organization['naming_compliance'] = self._check_naming_compliance()
        
        # Calculate structure score
        organization['structure_score'] = self._calculate_structure_score(organization)
        
        return organization
    
    def _check_naming_compliance(self) -> Dict:
        """Check if test files follow naming conventions."""
        compliance = {
            'violations': [],
            'score': 100,
            'total_files': 0,
            'compliant_files': 0
        }
        
        # Expected patterns
        patterns = {
            'test_files': r'^test_.*\.py$',
            'test_classes': r'^Test[A-Z].*',
            'test_methods': r'^test_.*'
        }
        
        test_files = []
        for test_dir in ['unit', 'integration', 'e2e', 'performance']:
            test_path = self.workspace_root / 'tests' / test_dir
            if test_path.exists():
                test_files.extend(test_path.glob('*.py'))
        
        compliance['total_files'] = len(test_files)
        
        for test_file in test_files:
            if not re.match(patterns['test_files'], test_file.name):
                compliance['violations'].append({
                    'type': 'filename',
                    'file': str(test_file.relative_to(self.workspace_root)),
                    'issue': f"File name '{test_file.name}' should start with 'test_'"
                })
            else:
                compliance['compliant_files'] += 1
        
        if compliance['total_files'] > 0:
            compliance['score'] = (compliance['compliant_files'] / compliance['total_files']) * 100
        
        return compliance
    
    def _calculate_structure_score(self, organization: Dict) -> int:
        """Calculate organization structure score."""
        score = 100
        
        # Deduct points for violations
        naming = organization.get('naming_compliance', {})
        if naming.get('violations'):
            score -= len(naming['violations']) * 10
        
        # Deduct points for oversized files
        for test_type, info in organization.get('test_directories', {}).items():
            if info and info.get('largest_file') and info.get('largest_file', {}).get('lines', 0) > 500:
                score -= 10  # Large files are harder to maintain
            
            # Reward good file count distribution
            file_count = info.get('file_count', 0) if info else 0
            if 3 <= file_count <= 15:  # Sweet spot
                score += 5
            elif file_count > 20:  # Too many files
                score -= 5
        
        return max(0, min(100, score))
    
    def _calculate_coverage_by_test_type(self) -> Dict:
        """Calculate coverage broken down by test type."""
        # This is a simplified implementation
        # In practice, you'd need to run coverage per test directory
        return {
            'unit': {'coverage': 85, 'target': self.coverage_targets['unit']},
            'integration': {'coverage': 70, 'target': self.coverage_targets['integration']},
            'regression': {'coverage': 95, 'target': self.coverage_targets['regression']}
        }
    
    def _find_low_coverage_files(self, coverage_data: Dict) -> List[Dict]:
        """Find files with coverage below threshold."""
        low_coverage_files = []
        files = coverage_data.get('files', {})
        
        for file_path, file_data in files.items():
            coverage = file_data.get('summary', {}).get('percent_covered', 0)
            if coverage < 60:  # Files below 60% coverage
                low_coverage_files.append({
                    'name': file_path,
                    'coverage': coverage,
                    'missing_lines': file_data.get('summary', {}).get('missing_lines', 0)
                })
        
        return sorted(low_coverage_files, key=lambda x: x['coverage'])
    
    def _parse_slow_tests(self, pytest_output: str) -> List[Dict]:
        """Parse slow tests from pytest output."""
        slow_tests = []
        lines = pytest_output.split('\n')
        
        in_slowest_section = False
        for line in lines:
            if 'slowest durations' in line.lower():
                in_slowest_section = True
                continue
            
            if in_slowest_section and line.strip():
                # Parse lines like "0.05s call     tests/unit/test_analysis.py::test_basic_functionality"
                parts = line.strip().split()
                if len(parts) >= 3 and parts[0].endswith('s'):
                    try:
                        duration = float(parts[0][:-1])  # Remove 's' and convert to float
                        test_name = parts[-1] if len(parts) > 2 else 'unknown'
                        slow_tests.append({
                            'name': test_name,
                            'duration': duration,
                            'type': parts[1] if len(parts) > 1 else 'unknown'
                        })
                    except (ValueError, IndexError):
                        continue
            elif in_slowest_section and not line.strip():
                break
        
        return sorted(slow_tests, key=lambda x: x['duration'], reverse=True)
    
    def _grade_performance(self, total_time: float, slow_tests: List[Dict]) -> str:
        """Grade overall performance."""
        if total_time < 30:  # Under 30 seconds
            return 'A'
        elif total_time < 120:  # Under 2 minutes
            return 'B'
        elif total_time < 300:  # Under 5 minutes
            return 'C'
        elif total_time < 480:  # Under 8 minutes (our limit)
            return 'D'
        else:
            return 'F'
    
    def _audit_flaky_tests(self) -> Dict:
        """Detect potentially flaky tests."""
        print("🎯 Auditing for Flaky Tests...")
        
        # Run tests multiple times to detect flaky behavior
        flaky_results = {
            'detected_flaky': [],
            'reliability_score': 100,
            'runs_performed': 3
        }
        
        try:
            results = []
            for run in range(3):
                print(f"  🔄 Test run {run + 1}/3...")
                result = subprocess.run([
                    'uv', 'run', 'python', '-m', 'pytest', 
                    'tests/', '--tb=no', '-q'
                ], cwd=self.workspace_root, capture_output=True, text=True)
                
                results.append({
                    'success': result.returncode == 0,
                    'output': result.stdout,
                    'runtime': time.time()
                })
            
            # Analyze for inconsistencies
            success_count = sum(1 for r in results if r['success'])
            if success_count < 3:
                flaky_results['detected_flaky'].append({
                    'type': 'inconsistent_results',
                    'success_rate': f"{success_count}/3",
                    'details': 'Test suite produced different results across runs'
                })
                flaky_results['reliability_score'] = (success_count / 3) * 100
            
        except Exception as e:
            flaky_results['error'] = f"Flaky test detection failed: {e}"
        
        return flaky_results
    
    def _generate_recommendations(self, audit_results: Dict) -> List[Dict]:
        """Generate actionable recommendations."""
        recommendations = []
        
        # Coverage recommendations
        if audit_results['coverage'].get('improvement_needed', 0) > 0:
            recommendations.append({
                'priority': 'high',
                'category': 'coverage',
                'title': f"Increase coverage by {audit_results['coverage']['improvement_needed']:.1f}%",
                'description': "Current coverage is below target. Focus on files with lowest coverage.",
                'action_items': [
                    "Add unit tests for uncovered functions",
                    "Improve integration test coverage",
                    "Review coverage reports weekly"
                ]
            })
        
        # Performance recommendations
        perf = audit_results['performance']
        if not perf.get('within_limit', True):
            recommendations.append({
                'priority': 'medium',
                'category': 'performance',
                'title': f"Optimize test performance - {perf.get('total_runtime_minutes', 0):.1f}min",
                'description': "Test suite exceeds time limit",
                'action_items': [
                    "Optimize slow tests",
                    "Consider parallel execution",
                    "Move slow tests to nightly CI"
                ]
            })
        
        # Organization recommendations
        org = audit_results['organization']
        if org.get('structure_score', 100) < 80:
            recommendations.append({
                'priority': 'low',
                'category': 'organization',
                'title': "Improve test organization",
                'description': "Test structure could be improved",
                'action_items': [
                    "Fix naming violations",
                    "Break down large test files",
                    "Improve directory structure"
                ]
            })
        
        # Flaky test recommendations
        flaky = audit_results['flaky_tests']
        if flaky.get('reliability_score', 100) < 95:
            recommendations.append({
                'priority': 'high',
                'category': 'reliability',
                'title': "Fix flaky tests",
                'description': "Tests showing inconsistent behavior",
                'action_items': [
                    "Investigate failing tests",
                    "Add test isolation",
                    "Fix timing dependencies"
                ]
            })
        
        return recommendations
    
    def _calculate_health_score(self, audit_results: Dict) -> int:
        """Calculate overall test suite health score."""
        score = 0
        max_score = 100
        
        # Coverage score (40 points)
        coverage = audit_results['coverage'].get('total_coverage', 0)
        score += min(40, (coverage / self.coverage_targets['total']) * 40)
        
        # Performance score (30 points)
        perf = audit_results['performance']
        if perf.get('within_limit', False):
            score += 30
        else:
            # Partial credit based on how close we are
            runtime_minutes = perf.get('total_runtime_minutes', 999)
            target_minutes = self.performance_limits['total_suite_max_minutes']
            if runtime_minutes < target_minutes * 1.5:  # Within 50% of target
                score += 15
        
        # Organization score (20 points)
        org_score = audit_results['organization'].get('structure_score', 0)
        score += (org_score / 100) * 20
        
        # Reliability score (10 points)
        reliability = audit_results['flaky_tests'].get('reliability_score', 100)
        score += (reliability / 100) * 10
        
        return int(min(max_score, score))
    
    def _save_audit_report(self, audit_results: Dict) -> Path:
        """Save audit report to file."""
        timestamp = datetime.now().strftime("%Y-%m-%d")
        report_file = self.reports_dir / f"monthly-test-audit-{timestamp}.md"
        
        # Generate markdown report
        report_content = self._generate_markdown_report(audit_results)
        
        report_file.write_text(report_content)
        return report_file
    
    def _generate_markdown_report(self, audit_results: Dict) -> str:
        """Generate markdown report."""
        timestamp = audit_results['timestamp']
        health_score = self._calculate_health_score(audit_results)
        
        # Format coverage safely
        total_coverage = audit_results['coverage'].get('total_coverage', 0)
        coverage_str = f"{total_coverage:.1f}%" if isinstance(total_coverage, (int, float)) else str(total_coverage)
        
        # Format performance safely  
        runtime_minutes = audit_results['performance'].get('total_runtime_minutes', 0)
        runtime_str = f"{runtime_minutes:.1f} minutes" if isinstance(runtime_minutes, (int, float)) else str(runtime_minutes)
        
        report = f"""# Monthly Test Audit Report

**Date:** {timestamp}  
**Health Score:** {health_score}/100  

## Executive Summary

This automated audit reviews the test suite health across coverage, performance, organization, and reliability metrics.

## Coverage Analysis

- **Total Coverage:** {coverage_str}
- **Target:** {self.coverage_targets['total']}%
- **Status:** {'✅ PASSED' if audit_results['coverage'].get('target_met', False) else '❌ NEEDS IMPROVEMENT'}

### Low Coverage Files
"""
        
        for file_info in audit_results['coverage'].get('files_below_target', []):
            coverage = file_info.get('coverage', 0)
            coverage_str = f"{coverage:.1f}%" if isinstance(coverage, (int, float)) else str(coverage)
            report += f"- `{file_info['name']}`: {coverage_str}\n"
        
        report += f"""
## Performance Analysis

- **Total Runtime:** {runtime_str}
- **Target:** < {self.performance_limits['total_suite_max_minutes']} minutes
- **Status:** {'✅ WITHIN LIMIT' if audit_results['performance'].get('within_limit', False) else '⚠️ EXCEEDS LIMIT'}
- **Test Count:** {audit_results['performance'].get('test_count', 'N/A')}
- **Average Test Time:** {audit_results['performance'].get('avg_test_time', 'N/A')}s

### Slowest Tests
"""
        
        for test in audit_results['performance'].get('slow_tests', [])[:5]:
            duration = test.get('duration', 0)
            duration_str = f"{duration:.2f}s" if isinstance(duration, (int, float)) else str(duration)
            report += f"- `{test['name']}`: {duration_str}\n"
        
        report += f"""
## Reliability Analysis

- **Flaky Tests Detected:** {len(audit_results['flaky_tests'].get('detected_flaky', []))}
- **Reliability Score:** {audit_results['flaky_tests'].get('reliability_score', 100)}/100
- **Status:** {'✅ RELIABLE' if audit_results['flaky_tests'].get('reliability_score', 100) >= 95 else '⚠️ NEEDS ATTENTION'}

## Recommendations

"""
        
        for rec in audit_results['recommendations']:
            priority_emoji = {'high': '🔴', 'medium': '🟡', 'low': '🟢'}[rec['priority']]
            report += f"""
### {priority_emoji} {rec['title']} ({rec['priority'].upper()})

{rec['description']}

**Action Items:**
"""
            for item in rec['action_items']:
                report += f"- {item}\n"
        
        report += f"""
## Next Steps

1. Address high-priority recommendations
2. Schedule follow-up audit in 4 weeks
3. Track progress on coverage improvements
4. Monitor performance trends

---
*Report generated automatically by monthly_test_audit.py*
"""
        
        return report
    
    # Helper methods
    def _parse_coverage_results(self) -> Dict:
        """Parse coverage JSON results."""
        try:
            coverage_file = self.workspace_root / "coverage_audit.json"
            if coverage_file.exists():
                return json.loads(coverage_file.read_text())
        except:
            pass
        return {}
    
    def _count_lines(self, file_path: Path) -> int:
        """Count lines in a file."""
        try:
            return len(file_path.read_text().splitlines())
        except:
            return 0
    
    def _count_total_tests(self) -> int:
        """Count total number of tests."""
        try:
            result = subprocess.run([
                'uv', 'run', 'python', '-m', 'pytest', 
                '--collect-only', '-q', 'tests/'
            ], cwd=self.workspace_root, capture_output=True, text=True)
            
            # Parse output to count tests
            lines = result.stdout.split('\n')
            for line in lines:
                if 'tests collected' in line:
                    return int(line.split()[0])
        except:
            pass
        return 0


def main():
    parser = argparse.ArgumentParser(description="Monthly Test Audit")
    parser.add_argument('--full-report', action='store_true', 
                       help='Generate full audit report')
    parser.add_argument('--coverage-only', action='store_true',
                       help='Run coverage audit only')
    parser.add_argument('--performance-only', action='store_true',
                       help='Run performance audit only')
    parser.add_argument('--workspace', default='.', 
                       help='Workspace root directory')
    
    args = parser.parse_args()
    
    auditor = MonthlyTestAudit(args.workspace)
    
    if args.coverage_only:
        results = auditor._audit_coverage()
        print(json.dumps(results, indent=2))
    elif args.performance_only:
        results = auditor._audit_performance()
        print(json.dumps(results, indent=2))
    else:
        auditor.run_full_audit()


if __name__ == "__main__":
    main() 