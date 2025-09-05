#!/usr/bin/env python3
import sys
from pathlib import Path
from src.ci_cd_analyzer import CICDAnalyzer

def main():
    # 1) Determine the project root (you can also pass this in via argv)
    project_root = Path(__file__).parent.resolve()
    workflows_dir = project_root / '.github' / 'workflows'

    # 2) Initialize the analyzer
    analyzer = CICDAnalyzer(
        project_root=str(project_root),
        workflows_dir=str(workflows_dir)
    )

    # 3) Fetch changed files from Git
    changed_files = analyzer.get_changed_files('HEAD~1..HEAD')
    print("Changed files:")
    for f in changed_files:
        print(f"  - {f}")
    print()

    # 4) Build import maps (tests ↔ modules)
    analyzer.build_import_maps()

    # 5) Compute which tests are impacted by those changes
    impacted_tests = analyzer.get_impacted_tests(changed_files)
    print("Impacted tests:")
    for t in impacted_tests:
        print(f"  - {t}")
    print()

    # 6) Parse your workflows and get all job names
    workflows = analyzer.parse_workflows()
    print("Workflows and their jobs:")
    for wf, jobs in workflows.items():
        print(f"  {wf}:")
        for job in jobs:
            print(f"    • {job}")
    print()

    # 7) Finally, get suggestions of which jobs to run
    suggestions = analyzer.suggest_jobs_to_run(changed_files)
    print("Suggested CI jobs to run:")
    for wf, jobs in suggestions.items():
        print(f"  {wf}:")
        for job in jobs:
            print(f"    ✔ {job}")
    print()

if __name__ == "__main__":
    main()
