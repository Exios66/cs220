"""
This module provides utilities for executing student code in a safe and controlled manner within our grading system. It includes functionality to run student code in a separate process with a timeout to prevent infinite loops, as well as checking student code against specified requirements without executing it in the grader's environment. The StudentProcessWorker class manages a long-lived child process that executes student code and checks requirements, allowing for isolation of the execution environment and better security when running untrusted code. The idea is to have a client in our grader that communicates with this worker process via JSON messages over stdin/stdout, sending code to execute or check and receiving results back. This design helps ensure that any side effects from running student code do not affect the grader's environment and allows us to enforce execution time limits effectively.
"""

import builtins
import json
import os
import select
import subprocess
import sys
import threading
from contextlib import contextmanager
from typing import Any, Dict, List
import matplotlib
import matplotlib.pyplot as plt
from shared.config import MODE


CODE_MAX_EXECUTION_TIME = 360  # in seconds
STUDENT_RUNNER_USER = "studentrunner"


def timeout_handler() -> None:
    """Helper function for execute_code to trigger when code has taken too long"""

    raise RuntimeError(
        "Execution timed out in our grader system. Please modify your code so it runs faster."
    )


def execute_code(
    code: str,
    global_vars: Dict[str, Any],
    warnings_list: List[str],
    errors_list: List[str],
    error_prefix: str,
) -> None:
    """Execute the code and record any warnings or errors.

    Detects and warns about changes to pre-existing global and builtin
    variables when running student code. This helps prevent unintended
    side effects later in the notebook. Uses a timeout to prevent execution
    from lasting too long.

    Parameters:
        code: Python code to run that potentially contains errors
        global_vars: Dictionary mapping names of global variables to their values
        warnings_list: Records any detected warning messages
        errors_list: Records strings with error_msg and exception text if any occur
        error_prefix: Start of error message to display to the student. Example:
            if desired message is f"Test case failed: {e}", then prefix is "Test case failed: "
    """
    before_exec_globals = global_vars.copy()
    builtin_identifiers = dir(builtins)

    timer = threading.Timer(CODE_MAX_EXECUTION_TIME, timeout_handler)
    timer.start()

    try:
        exec(code, global_vars)
    except Exception as e:
        errors_list.append(f"{error_prefix}{e}")
    finally:
        timer.cancel()  # code finished before alarm went off, cancel the alarm

    after_exec_globals = global_vars.copy()

    variables_defined_by_exec = set(after_exec_globals) - set(before_exec_globals)
    for var_name in variables_defined_by_exec:
        if var_name in builtin_identifiers:
            warnings_list.append(
                f"Built-in function '{var_name}' was modified. You should never overwrite these."
            )


class StudentProcessWorker:
    """Runs student code in a separate long-lived Python process."""

    def __init__(self, cwd: str):
        # here we will spawn a long-lives python child exprocess that will execute student code for us, and we will communicate with it via stdin/stdout using json messages. We do this to isolate the execution environment and ensure that any changes to global variables or imports in student code do not affect our grader's execution environment. We also enforce a timeout on code execution to prevent infinite loops or excessively long-running code from hanging our grader system.
        # Build a minimal environment for the worker process.
        # Only pass what's needed for Python to run (PATH, PYTHONPATH, HOME).
        # This prevents student code from reading sensitive env vars like
        # Canvas API tokens, Google Sheets credentials, etc. via os.environ.
        popen_kwargs: Dict[str, Any] = {
            # sys.executable ensures that the same python interpreter is used to run the child process, which is important for consistency in package availability and behavior.
            "args": [sys.executable, "-m", "grader_utils.student_process_worker"],
            "stdin": subprocess.PIPE,
            "stdout": subprocess.PIPE,
            "stderr": subprocess.PIPE,
            "text": True,
            "cwd": cwd,
            "bufsize": 1,  # line-buffered to ensure timely communication between processes
        }

        if MODE == "deploy" and not os.environ.get("CI"):
            safe_env = {
                "PATH": os.environ.get("PATH", "/usr/bin:/bin"),
                "HOME": f"/home/{STUDENT_RUNNER_USER}",
                "MPLCONFIGDIR": "/tmp/matplotlib_config",
                "PYTHONPATH": os.environ.get("PYTHONPATH", ""),
            }
            for key in os.environ:
                if key.startswith(("CONDA_", "PIXI_")) or key == "VIRTUAL_ENV":
                    safe_env[key] = os.environ[key]
            popen_kwargs["env"] = safe_env
            popen_kwargs["user"] = STUDENT_RUNNER_USER
            popen_kwargs["group"] = STUDENT_RUNNER_USER
            popen_kwargs["extra_groups"] = []

        self.proc = subprocess.Popen(**popen_kwargs)

    # just so we can make our class a context manager and ensure the subprocess is cleaned up properly
    def __enter__(self) -> "StudentProcessWorker":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()

    def execute_code(
        self,
        code: str,
        error_prefix: str,
    ) -> tuple[List[str], List[str]]:
        """Execute the given code in the child process and return any warnings or errors. The error_prefix is used to provide context in the error message about where the error occurred, for example if the code being executed is part of a test case, the prefix could be "Test case 1 failed: ", so that when we append the exception text to it and return it to the student, they get a clear and informative error message."""
        response = self._send_request(
            {
                "command": "execute_code",
                "code": code,
                "error_prefix": error_prefix,
            }
        )
        return response["warnings"], response["errors"]

    def check_code(
        self,
        student_code: str,
        required_functions: List[str],
        required_vars: List[str],
        assertions: str,
    ) -> tuple[bool, List[str]]:
        """
        Check the given student code against the requirements and return whether it passed and any messages. This is used for our core check functionality, where we check if student code defines required functions and variables and satisfies assertions without actually running the student's code in our grader environment.
        """
        response = self._send_request(
            {
                "command": "check_code",
                "student_code": student_code,
                "required_functions": required_functions,
                "required_vars": required_vars,
                "assertions": assertions,
            }
        )
        return response["passed"], response["messages"]

    def close(self) -> None:
        """Terminate the child process. First we check if it's still running, and if so we attempt a graceful termination. If the process does not exit within a reasonable time, we forcefully kill it to ensure it does not linger and consume resources."""

        if self.proc.poll() is None:
            self.proc.terminate()
            try:
                self.proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.proc.kill()
                self.proc.wait(timeout=5)

    def _send_request(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        if self.proc.poll() is not None:
            stderr = ""
            if self.proc.stderr is not None:
                stderr = self.proc.stderr.read().strip()
            raise RuntimeError(
                "Student execution worker exited unexpectedly."
                + (f" stderr: {stderr}" if stderr else "")
            )

        if self.proc.stdin is None or self.proc.stdout is None:
            raise RuntimeError("Student execution worker pipes are unavailable.")

        self.proc.stdin.write(json.dumps(payload) + "\n")
        self.proc.stdin.flush()

        ready, _, _ = select.select([self.proc.stdout], [], [], CODE_MAX_EXECUTION_TIME)
        if not ready:
            self.close()
            raise RuntimeError(
                "Execution timed out in our grader system. Please modify your code so it runs faster."
            )

        response_line = self.proc.stdout.readline()
        if not response_line:
            stderr = ""
            if self.proc.stderr is not None:
                stderr = self.proc.stderr.read().strip()
            raise RuntimeError(
                "Student execution worker returned no response."
                + (f" stderr: {stderr}" if stderr else "")
            )

        response = json.loads(response_line)
        if not response.get("ok", False):
            raise RuntimeError(response["error"])
        return response["result"]


@contextmanager
def suppress_output():
    """Temporarily suppresses stdout, stderr, and MatplolLib output.

    Redirects stdout and stderr to os.devnull, effectively silencing
    any print statements or error messages within the context. Once
    the context is exited, the original stdout and stderr are restored.
    Also sets Matplotlib to a non-interactive backend to suppress plot
    displays and closes any lingering figures after execution.

    This is useful when running executing code in cells above the current
    grader.check call, since we don't want that output to show up
    when the user is expecting information related to the current question.

    Usage:
        with suppress_output():
            # Code with suppressed output
    """

    with open(os.devnull, "w", encoding="utf-8") as devnull:
        old_stdout = sys.stdout
        old_stderr = sys.stderr
        old_backend = matplotlib.get_backend()
        try:
            sys.stdout = devnull
            sys.stderr = devnull
            matplotlib.use("Agg")
            yield
        finally:
            sys.stdout = old_stdout
            sys.stderr = old_stderr
            matplotlib.use(old_backend)
            plt.close("all")
