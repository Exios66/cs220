"""
Functions for grading student code for a given question. Includes
the actual grader.check function and a way to tell if studentcode
calls a given function.
"""

import ast
from typing import List, Dict, Any
from grader_utils.assert_helpers import *
from grader_utils.grader_messages import (
    CUR_QUESTION_ERROR_PREFIX,
    MISSED_REQ_FUNC_FORMAT,
    MISSED_REQ_VAR_FORMAT,
    ASSERTION_FAILED_PREFIX,
)
import re
from grader_utils.code_execution import execute_code
import time


def strip_standalone_output_calls(code: str) -> str:
    """Replace standalone print/dir/help calls with ``pass`` and remove magic lines.

    If a non-Python cell magic (e.g. ``%%bash``) is present, skip the whole cell
    because the remaining lines are not valid Python once the magic header is
    removed. For ``%%capture``, keep the cell body since it is still Python code.
    """
    standalone_output_call_re = re.compile(
        r"^(\s*)(?:print|dir|help)\s*\(.*\)\s*(?:#.*)?$"
    )
    magic_line_re = re.compile(r"^\s*[%!]")
    transformed_lines = []
    for line in code.splitlines():
        stripped = line.lstrip()
        if stripped.startswith("%%"):
            magic_name = stripped[2:].split(maxsplit=1)[0].lower()
            if magic_name in ("capture", "time", "timeit"):
                continue
            return ""
        if magic_line_re.match(line):
            continue
        m = standalone_output_call_re.match(line)
        if m:
            transformed_lines.append(f"{m.group(1)}pass")
        else:
            transformed_lines.append(line)

    try:
        ast.parse("\n".join(transformed_lines))
    except SyntaxError:
        # If the transformed code is not syntactically valid, return the original code
        return code

    return "\n".join(transformed_lines)


def check_student_code_against_requirements(
    student_code: str,
    required_functions: List[str],
    required_vars: List[str],
    assertions: str,
    current_question_warnings: List[str],
    current_question_errors: List[str],
    global_vars: Dict[str, Any],
) -> float:
    """Helper function for packages' grader check functions

    Executes student's code then checks that student code has:
    - used all required functions
    - defined all necessary variables
    - passes all test cases

    and then appends to the list of warnings and/or errors for the
    current question. Used to enforce consistency across all check
    functions in grader packages.
    """

    start = time.perf_counter()
    execute_code(
        student_code,
        global_vars,
        current_question_warnings,
        current_question_errors,
        CUR_QUESTION_ERROR_PREFIX,
    )
    time_to_run_code = time.perf_counter() - start

    for function_name in required_functions:
        if not _does_code_use(student_code, function_name):
            current_question_errors.append(MISSED_REQ_FUNC_FORMAT.format(function_name))

    for required_var in required_vars:
        if required_var not in global_vars:
            current_question_errors.append(MISSED_REQ_VAR_FORMAT.format(required_var))

    execute_code(
        assertions,
        global_vars,
        current_question_warnings,
        current_question_errors,
        ASSERTION_FAILED_PREFIX,
    )

    return time_to_run_code


def _does_code_use(code_snippet: str, name: str) -> bool:
    """Uses ast to tell if code contains a call to a specific function or operator.

    For a list of usable operator names, check
    https://docs.python.org/3/library/ast.html

    Parameters:
        code_snippet: A string containing Python code to be analyzed
        name: The name of the function or ast operator to look for in the code snippet
    """

    class CustomNodeVisitor(ast.NodeVisitor):
        """Extends ast's NoteVisitor to look for functions or operators"""

        def __init__(self):
            self.found = False

        def visit(self, node):
            """Traverse the abstract syntax tree to check for the function call or operator or variable access"""

            if isinstance(node, ast.Call):

                full_name = self.get_full_name(node.func)
                if full_name == name:
                    self.found = True
                if isinstance(node.func, ast.Attribute) and node.func.attr == name:
                    self.found = True

            elif (
                isinstance(node, ast.BinOp)
                or isinstance(node, ast.BoolOp)
                or isinstance(node, ast.UnaryOp)
            ):
                op_name = node.op.__class__.__name__
                if op_name == name:
                    self.found = True
            elif isinstance(node, ast.Name):
                if node.id == name:
                    self.found = True
            elif isinstance(node, ast.Attribute):
                if node.attr == name:
                    self.found = True
            self.generic_visit(node)

        def get_full_name(self, node):
            """Recursively retrieves the full name of a function being called

            This inclues attribute accesses (e.g., "module.function").
            """

            if isinstance(node, ast.Attribute):
                return self.get_full_name(node.value) + "." + node.attr
            elif isinstance(node, ast.Name):
                return node.id
            return ""

    tree = ast.parse(code_snippet)
    visitor = CustomNodeVisitor()
    visitor.visit(tree)
    return visitor.found


def get_imports(code_snippet: str) -> set[str]:
    """
    Returns a set of top-level module names imported in a particular code cell.
    """
    replaced_code = strip_standalone_output_calls(code_snippet)
    tree = ast.parse(replaced_code)
    imports = set()

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.add(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom):
            if node.module is not None:
                imports.add(node.module.split(".")[0])

    return imports


def get_disallowed_constructs(
    code_snippet: str, disallowed_constructs: List[str]
) -> tuple[bool, str]:
    """
    Returns a list of disallowed constructs or functions found in the code snippet.
    """
    replaced_code = strip_standalone_output_calls(code_snippet)
    tree = ast.parse(replaced_code)
    for node in ast.walk(tree):
        if isinstance(node, ast.ListComp) and "ListComp" in disallowed_constructs:
            return True, "list comprehension"
        if isinstance(node, ast.Lambda) and "Lambda" in disallowed_constructs:
            return True, "lambda expression"
        if isinstance(node, ast.SetComp) and "SetComp" in disallowed_constructs:
            return True, "set comprehension"
        if isinstance(node, ast.DictComp) and "DictComp" in disallowed_constructs:
            return True, "dict comprehension"
        if (
            isinstance(node, ast.GeneratorExp)
            and "GeneratorExp" in disallowed_constructs
        ):
            return True, "generator expression"

        if isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Attribute):
                if isinstance(func.value, ast.Name):
                    if func.value.id + "." + func.attr in disallowed_constructs:
                        return True, func.value.id + "." + func.attr

            if isinstance(func, ast.Name) and func.id in disallowed_constructs:
                return True, func.id

    return False, "No disallowed constructs or functions found"
