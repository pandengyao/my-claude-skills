#!/usr/bin/env python3
"""
Analyze experiment code dependencies in JavaScript/TypeScript projects.

This script identifies all code locations that reference a specific experiment ID or whitelist name,
helping to understand the full scope of code that needs to be cleaned up.
"""

import os
import re
import json
import argparse
from pathlib import Path
from typing import List, Dict, Set, Tuple


class ExperimentAnalyzer:
    """Analyzes experiment dependencies in JavaScript/TypeScript codebases."""

    def __init__(self, root_dir: str, experiment_id: str):
        self.root_dir = Path(root_dir)
        self.experiment_id = experiment_id
        self.results = {
            "experiment_id": experiment_id,
            "total_files": 0,
            "affected_files": [],
            "dependency_graph": {},
            "patterns_found": {}
        }

        # Common patterns for experiment checks in JavaScript/TypeScript
        self.patterns = [
            # Function calls
            (r'isExpEnabled\s*\(\s*[\'"]' + re.escape(experiment_id) + r'[\'"]\s*\)', "function_call"),
            (r'getExpValue\s*\(\s*[\'"]' + re.escape(experiment_id) + r'[\'"]\s*\)', "function_call"),
            (r'checkExp\s*\(\s*[\'"]' + re.escape(experiment_id) + r'[\'"]\s*\)', "function_call"),
            (r'expConfig\s*\(\s*[\'"]' + re.escape(experiment_id) + r'[\'"]\s*\)', "function_call"),

            # Config object access
            (r'config\.experiments\.' + re.escape(experiment_id), "config_access"),
            (r'expConfig\[[\'"]' + re.escape(experiment_id) + r'[\'"]\]', "config_access"),
            (r'experiments\[[\'"]' + re.escape(experiment_id) + r'[\'"]\]', "config_access"),

            # Environment variables
            (r'process\.env\.' + re.escape(experiment_id.upper()), "env_var"),
            (r'import\.meta\.env\.' + re.escape(experiment_id.upper()), "env_var"),

            # Global variables
            (r'window\.__EXP_CONFIG__\.' + re.escape(experiment_id), "global_var"),
            (r'globalThis\.' + re.escape(experiment_id), "global_var"),

            # Comments and annotations
            (r'@exp[:\s]+' + re.escape(experiment_id), "comment"),
            (r'experiment:\s*' + re.escape(experiment_id), "comment"),

            # String literals (direct references)
            (r'[\'"]' + re.escape(experiment_id) + r'[\'"]', "string_literal"),
        ]

    def is_code_file(self, file_path: Path) -> bool:
        """Check if file is a code file we should analyze."""
        extensions = {'.js', '.jsx', '.ts', '.tsx', '.vue', '.mjs', '.cjs'}
        return file_path.suffix in extensions

    def should_skip_dir(self, dir_name: str) -> bool:
        """Check if directory should be skipped."""
        skip_dirs = {'node_modules', '.git', 'dist', 'build', 'coverage', '.next', '.nuxt'}
        return dir_name in skip_dirs

    def analyze_file(self, file_path: Path) -> List[Dict]:
        """Analyze a single file for experiment references."""
        matches = []

        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()

            for pattern, pattern_type in self.patterns:
                for match in re.finditer(pattern, content, re.IGNORECASE):
                    line_num = content[:match.start()].count('\n') + 1
                    line_start = content.rfind('\n', 0, match.start()) + 1
                    line_end = content.find('\n', match.end())
                    if line_end == -1:
                        line_end = len(content)

                    line_content = content[line_start:line_end].strip()

                    matches.append({
                        "line": line_num,
                        "pattern_type": pattern_type,
                        "matched_text": match.group(),
                        "line_content": line_content,
                        "start_pos": match.start(),
                        "end_pos": match.end()
                    })

                    # Track pattern types
                    if pattern_type not in self.results["patterns_found"]:
                        self.results["patterns_found"][pattern_type] = 0
                    self.results["patterns_found"][pattern_type] += 1

        except Exception as e:
            print(f"Error analyzing {file_path}: {e}")

        return matches

    def scan_directory(self):
        """Recursively scan directory for experiment references."""
        for root, dirs, files in os.walk(self.root_dir):
            # Filter out directories to skip
            dirs[:] = [d for d in dirs if not self.should_skip_dir(d)]

            for file_name in files:
                file_path = Path(root) / file_name

                if not self.is_code_file(file_path):
                    continue

                self.results["total_files"] += 1
                matches = self.analyze_file(file_path)

                if matches:
                    relative_path = file_path.relative_to(self.root_dir)
                    self.results["affected_files"].append({
                        "file": str(relative_path),
                        "matches": matches,
                        "match_count": len(matches)
                    })

    def generate_report(self) -> str:
        """Generate a human-readable report of findings."""
        report = []
        report.append(f"\n{'='*80}")
        report.append(f"Experiment Dependency Analysis Report")
        report.append(f"{'='*80}")
        report.append(f"\nExperiment ID: {self.experiment_id}")
        report.append(f"Root Directory: {self.root_dir}")
        report.append(f"\nTotal files scanned: {self.results['total_files']}")
        report.append(f"Files with references: {len(self.results['affected_files'])}")

        if self.results["patterns_found"]:
            report.append(f"\nPattern types found:")
            for pattern_type, count in sorted(self.results["patterns_found"].items()):
                report.append(f"  - {pattern_type}: {count} occurrence(s)")

        if self.results["affected_files"]:
            report.append(f"\n{'='*80}")
            report.append("Affected Files:")
            report.append(f"{'='*80}\n")

            for file_info in sorted(self.results["affected_files"], key=lambda x: x["match_count"], reverse=True):
                report.append(f"\n{file_info['file']} ({file_info['match_count']} match(es))")
                report.append("-" * 80)

                for match in file_info["matches"]:
                    report.append(f"  Line {match['line']:4d} [{match['pattern_type']}]:")
                    report.append(f"    {match['line_content'][:100]}")
        else:
            report.append("\nNo references found for this experiment.")

        report.append(f"\n{'='*80}\n")
        return "\n".join(report)

    def save_json(self, output_path: str):
        """Save results as JSON."""
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False)


def main():
    parser = argparse.ArgumentParser(
        description="Analyze experiment code dependencies in JavaScript/TypeScript projects"
    )
    parser.add_argument(
        "experiment_id",
        help="The experiment ID or whitelist name to search for"
    )
    parser.add_argument(
        "--root",
        default=".",
        help="Root directory to search (default: current directory)"
    )
    parser.add_argument(
        "--output",
        help="Output JSON file path (optional)"
    )

    args = parser.parse_args()

    # Run analysis
    analyzer = ExperimentAnalyzer(args.root, args.experiment_id)
    analyzer.scan_directory()

    # Print report
    print(analyzer.generate_report())

    # Save JSON if requested
    if args.output:
        analyzer.save_json(args.output)
        print(f"JSON report saved to: {args.output}")


if __name__ == "__main__":
    main()
