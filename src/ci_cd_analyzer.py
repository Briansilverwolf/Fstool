import os
import subprocess
from typing import List
import ast
import yaml
from pathlib import Path
from typing import List, Dict, Set, Optional

class CICDAnalyzer:
    """
    Analyzes code dependencies and CI/CD pipeline configuration to determine
    which test jobs should run based on changed code files.
    """
    def __init__(self, project_root: str, workflows_dir: Optional[str] = None):
        self.project_root = Path(project_root).resolve()
        # Directory containing CI workflow YAML files (e.g. .github/workflows)
        self.workflows_dir = Path(workflows_dir) if workflows_dir else self.project_root / '.github' / 'workflows'
        # Mapping: module_name -> set of test file paths
        self._test_import_map: Dict[str, Set[Path]] = {}
        # Mapping: module_name -> set of modules that import it (reverse dependency)
        self._reverse_dep_graph: Dict[str, Set[str]] = {}

    def build_import_maps(self) -> None:
        """
        Walk the project, parse Python files, and build maps of imports for tests and modules.
        """
        module_to_imports: Dict[str, Set[str]] = {}
        for py_file in self.project_root.rglob('*.py'):
            rel = py_file.relative_to(self.project_root)
            module_name = '.'.join(rel.with_suffix('').parts)
            imports = self._extract_imports(py_file)
            module_to_imports[module_name] = imports

            # If it's a test file, record imports
            if py_file.name.startswith('test_'):
                for imp in imports:
                    self._test_import_map.setdefault(imp, set()).add(py_file)

        # Build reverse dependency graph
        for mod, deps in module_to_imports.items():
            for dep in deps:
                self._reverse_dep_graph.setdefault(dep, set()).add(mod)

    def _extract_imports(self, file_path: Path) -> Set[str]:
        """
        Parse a Python file and extract top-level imported module names.
        """
        imports: Set[str] = set()
        try:
            tree = ast.parse(file_path.read_text(encoding='utf-8'))
        except (SyntaxError, UnicodeDecodeError):
            return imports

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.add(alias.name)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.add(node.module)
        return imports

    def get_changed_files(self, commit_range: str = 'HEAD~1..HEAD') -> List[str]:
        """
        Fetch the list of files changed between two commits (or one commit and HEAD).
        Default is HEAD~1 (previous commit) to HEAD (latest commit).

        :param commit_range: A Git commit range (e.g., HEAD~1..HEAD, or a branch comparison)
        :return: List of changed files
        """
        try:
            # Run git diff to get the list of changed files
            result = subprocess.run(
                ['git', 'diff', '--name-only', commit_range],
                cwd=self.project_root,
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )

            # Split the output into a list of changed files
            changed_files = result.stdout.strip().split('\n')
            return changed_files

        except subprocess.CalledProcessError as e:
            print(f"Error fetching changed files: {e}")
            return []


    def get_impacted_tests(self, changed_files: List[str]) -> Set[Path]:
        """
        Given a list of changed file paths (relative or absolute), return a set of test files
        that directly or transitively depend on them.
        """
        # Ensure maps are built
        if not self._reverse_dep_graph:
            self.build_import_maps()

        # Convert changed files to module names
        changed_modules = set()
        for f in changed_files:
            p = Path(f)
            if p.is_absolute():
                try:
                    rel = p.relative_to(self.project_root)
                except ValueError:
                    continue
            else:
                rel = Path(f)
            mod = '.'.join(rel.with_suffix('').parts)
            changed_modules.add(mod)

        # BFS to find all modules depending on changed modules
        impacted_modules = set()
        queue = list(changed_modules)
        while queue:
            current = queue.pop()
            if current in impacted_modules:
                continue
            impacted_modules.add(current)
            for parent in self._reverse_dep_graph.get(current, []):
                queue.append(parent)

        # Collect tests
        impacted_tests: Set[Path] = set()
        for mod in impacted_modules:
            impacted_tests.update(self._test_import_map.get(mod, set()))

        return impacted_tests

    def parse_workflows(self) -> Dict[str, List[str]]:
        """
        Parse CI/CD workflow YAML files and extract job names and their test commands.
        Returns a mapping of workflow file to list of job names.
        """
        workflows: Dict[str, List[str]] = {}
        for wf in self.workflows_dir.glob('*.yml'):
            try:
                data = yaml.safe_load(wf.read_text(encoding='utf-8'))
            except Exception:
                continue
            jobs = []
            for job_name, job_def in (data or {}).get('jobs', {}).items():
                jobs.append(job_name)
            workflows[str(wf)] = jobs
        return workflows

    def suggest_jobs_to_run(self, changed_files: List[str]) -> Dict[str, List[str]]:
        """
        Suggest CI/CD jobs to run based on changed files.
        Returns a mapping: workflow_file -> list of job names to trigger.
        """
        impacted_tests = self.get_impacted_tests(changed_files)
        workflows = self.parse_workflows()

        # Naively suggest that any workflow with 'test' in job name runs if tests impacted
        suggestions: Dict[str, List[str]] = {}
        for wf_file, jobs in workflows.items():
            suggested = [job for job in jobs if 'test' in job.lower()]
            if suggested and impacted_tests:
                suggestions[wf_file] = suggested
        return suggestions

# Example usage:
# analyzer = CICDAnalyzer(project_root='.', workflows_dir='.github/workflows')\#
# changed = ['src/app.py']
# tests = analyzer.get_impacted_tests(changed)
# jobs = analyzer.suggest_jobs_to_run(changed)
# print(tests, jobs)
