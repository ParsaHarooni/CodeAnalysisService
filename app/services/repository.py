import os
import uuid
import ast
from typing import Optional, Tuple
from git import Repo
from git.exc import GitCommandError
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)


class FunctionVisitor(ast.NodeVisitor):
    """AST visitor to find functions by name."""

    def __init__(self, target_name: str):
        self.target_name = target_name
        self.found_node = None
        self.found_lines = None

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        """Visit a function definition node."""
        if node.name == self.target_name:
            self.found_node = node
            # Get the actual source lines for the function
            self.found_lines = (node.lineno, node.end_lineno)
        self.generic_visit(node)


class RepositoryService:
    def __init__(self):
        self.storage_path = settings.REPO_STORAGE_PATH
        os.makedirs(self.storage_path, exist_ok=True)

    def generate_job_id(self) -> str:
        return str(uuid.uuid4())

    def get_repo_path(self, job_id: str) -> str:
        return os.path.join(self.storage_path, job_id)

    async def clone_repository(self, repo_url: str, job_id: str) -> bool:
        repo_path = self.get_repo_path(job_id)
        try:
            Repo.clone_from(str(repo_url), repo_path)
            return True
        except GitCommandError as e:
            logger.error(f"Failed to clone repository: {str(e)}")
            return False

    def _find_function_in_file(
        self, file_path: str, function_name: str
    ) -> Optional[Tuple[str, int, int]]:
        """Find a function in a Python file using AST.

        Args:
            file_path: Path to the Python file
            function_name: Name of the function to find

        Returns:
            Tuple of (source code, start line, end line) if found, None otherwise
        """
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                source = f.read()

            tree = ast.parse(source)
            visitor = FunctionVisitor(function_name)
            visitor.visit(tree)

            if visitor.found_node and visitor.found_lines:
                with open(file_path, "r", encoding="utf-8") as f:
                    lines = f.readlines()
                    start_line, end_line = visitor.found_lines
                    # Include function body and any decorators
                    function_source = "".join(lines[start_line - 1 : end_line])
                    return function_source, start_line, end_line

        except (SyntaxError, UnicodeDecodeError) as e:
            logger.warning(f"Error parsing {file_path}: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error processing {file_path}: {str(e)}")

        return None

    def _find_module_file(self, repo_path: str, module_name: str) -> Optional[str]:
        """Find a Python module file in the repository.

        Args:
            repo_path: Path to the repository
            module_name: Name of the module (can include path)

        Returns:
            Full path to the module file if found, None otherwise
        """
        # Convert module name to possible file paths
        possible_paths = [
            # Direct file name
            f"{module_name}.py",
            # Module path conversion (e.g., foo.bar -> foo/bar.py)
            f"{module_name.replace('.', '/')}.py",
            # Handle __init__.py files
            f"{module_name.replace('.', '/')}/__init__.py",
        ]

        for path in possible_paths:
            full_path = os.path.join(repo_path, path)
            if os.path.isfile(full_path):
                return full_path

        # If not found, try searching recursively
        for root, _, files in os.walk(repo_path):
            for file in files:
                if file == f"{module_name.split('.')[-1]}.py":
                    return os.path.join(root, file)

        return None

    def get_function_code(self, job_id: str, function_name: str) -> Optional[str]:
        """Get the source code of a function from the repository.

        Args:
            job_id: ID of the repository analysis job
            function_name: Name of the function to find, can be in formats:
                         - "function_name"
                         - "module.function_name"
                         - "path/to/module:function_name"

        Returns:
            Source code of the function if found, None otherwise
        """
        repo_path = self.get_repo_path(job_id)
        if not os.path.exists(repo_path):
            return None

        # Handle different function name formats
        if ":" in function_name:
            # Format: path/to/module:function_name
            module_path, func_name = function_name.split(":")
            module_path = module_path.replace("/", ".")
        elif "." in function_name:
            # Format: module.submodule.function_name
            *module_parts, func_name = function_name.split(".")
            module_path = ".".join(module_parts)
        else:
            # Format: function_name (search all files)
            module_path = None
            func_name = function_name

        if module_path:
            # If module is specified, look only in that module
            module_file = self._find_module_file(repo_path, module_path)
            if not module_file:
                logger.warning(f"Module {module_path} not found in repository {job_id}")
                return None

            result = self._find_function_in_file(module_file, func_name)
            if result:
                source_code, start_line, end_line = result
                logger.info(
                    f"Found function {func_name} in {module_file} "
                    f"(lines {start_line}-{end_line})"
                )
                return source_code
        else:
            # Search all Python files
            for root, _, files in os.walk(repo_path):
                for file in files:
                    if not file.endswith(".py"):
                        continue

                    file_path = os.path.join(root, file)
                    result = self._find_function_in_file(file_path, func_name)

                    if result:
                        source_code, start_line, end_line = result
                        logger.info(
                            f"Found function {func_name} in {file_path} "
                            f"(lines {start_line}-{end_line})"
                        )
                        return source_code

        logger.warning(f"Function {function_name} not found in repository {job_id}")
        return None
