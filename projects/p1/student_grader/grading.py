"""
This version of the grader is used by students
when completing their assignments. It is very similar to the
master version used by TAs/PMs except that it makes HTTP requests to
our server to get feedback from the LLM, and it uses the metadata
file to inform grader.check about test cases to run
"""

import os
import nbformat
from ipylab import JupyterFrontEnd
from IPython import get_ipython
from grader_utils.assert_helpers import *
from grader_utils import (
    CHECK_START_FORMAT,
    SUCCESS_MSG,
    POINTS_POSSIBLE_PREFIX,
    ABOVE_QUESTION_ERROR_PREFIX,
    NO_CODE_FOR_QID_FORMAT,
    METADATA_REQUIRED_VARS_KEY,
    METADATA_REQUIRED_FUNCS_KEY,
    METADATA_ASSERTIONS_KEY,
    METADATA_LLM_FEEDBACK_KEY,
    METADATA_ALLOWED_IMPORTS_KEY,
    get_nb_path,
    load_metadata_dict,
    check_student_code_against_requirements,
    print_feedback,
    strip_standalone_output_calls,
    StudentProcessWorker,
)
from dataclasses import dataclass
from typing import Optional, Tuple

import time
import functools


def _retry(max_attempts=6, multiplier=2, min_wait=0.5, max_wait=120, reraise=True):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            wait = min_wait
            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except Exception:
                    if attempt == max_attempts:
                        if reraise:
                            raise
                        return None
                    time.sleep(min(wait, max_wait))
                    wait *= multiplier

        return wrapper

    return decorator


_GRADER_CHECK_STUB = "student_grader.check"

_JUPYTER_FRONTEND = JupyterFrontEnd()


@dataclass
class CheckContext:
    notebook: nbformat.NotebookNode
    question_id: str
    assignment_metadata: dict
    project_id: str
    should_get_llm_feedback: bool
    global_vars: dict
    notebook_execution: bool  # True if running inside IPython kernel w/ globals


def check(question_id: str, should_get_llm_feedback: bool = False) -> bool | dict:
    _save_notebook_best_effort()

    print(CHECK_START_FORMAT.format(question_id))

    student_nb_path = get_nb_path()
    dir_path = os.path.dirname(student_nb_path)
    project_file_name = os.path.split(student_nb_path)[-1]
    project_id = project_file_name.split(".")[0]

    assignment_metadata = load_metadata_dict(dir_path)

    notebook = _load_notebook(student_nb_path)
    global_vars, notebook_execution = _get_execution_context_globals()

    ctx = CheckContext(
        notebook=notebook,
        question_id=question_id,
        assignment_metadata=assignment_metadata,
        project_id=project_id,
        should_get_llm_feedback=should_get_llm_feedback,
        global_vars=global_vars,
        notebook_execution=notebook_execution,
    )

    if ctx.notebook_execution:
        return _run_notebook_mode(
            ctx
        )  # returns bool because we do not need scores here
    else:
        return _run_script_mode(
            ctx
        )  # returns dict of {q_id: (score, feedback)} for all q_ids in metadata, which is used by autograder to assign scores and feedback


def _save_notebook_best_effort() -> None:
    if _JUPYTER_FRONTEND:
        _JUPYTER_FRONTEND.commands.execute("docmanager:save")
        # time.sleep(0.05)


@_retry(reraise=True, max_attempts=6, multiplier=2, min_wait=0.5, max_wait=120)
def _load_notebook(student_nb_path: str) -> nbformat.NotebookNode:
    with open(student_nb_path, "r", encoding="utf-8") as f:
        return nbformat.read(f, as_version=4)


def _get_execution_context_globals() -> Tuple[dict, bool]:
    try:
        ip = get_ipython()
        if not ip:
            return {}, False
        return ip.user_global_ns, True
    except Exception:
        return {}, False


def _find_question_code_cell(
    notebook: nbformat.NotebookNode, question_id: str
) -> Optional[nbformat.NotebookNode]:
    tag = f"{question_id}-code"
    for c in notebook.cells:
        if tag in c.get("metadata", {}).get("tags", []):
            return c
    return None


def _run_core_check(
    *,
    student_code: str,
    question_id: str,
    assignment_metadata: dict,
    global_vars: dict,
    project_id: str,
    should_get_llm_feedback: bool,
) -> bool | dict:
    llm_feedback_allowed = assignment_metadata[question_id][METADATA_LLM_FEEDBACK_KEY]

    required_functions = assignment_metadata[question_id][METADATA_REQUIRED_FUNCS_KEY]
    required_vars = assignment_metadata[question_id][METADATA_REQUIRED_VARS_KEY]
    assertions = assignment_metadata[question_id][METADATA_ASSERTIONS_KEY]

    current_question_errors = []
    current_question_warnings = []

    time_to_run_code = check_student_code_against_requirements(
        student_code,
        required_functions,
        required_vars,
        assertions,
        current_question_warnings,
        current_question_errors,
        global_vars,
    )

    print(
        f"Time to run student code: {time_to_run_code:.2f} seconds"
        + ("\n" if time_to_run_code < 200 else " (consider optimizing your code!)\n")
    )

    if current_question_warnings or current_question_errors:
        print_feedback(
            current_question_warnings,
            current_question_errors,
            project_id,
            question_id,
            should_get_llm_feedback,
            student_code,
            llm_feedback_allowed=llm_feedback_allowed,
        )
        return False, current_question_errors + current_question_warnings

    print(f"{SUCCESS_MSG}\n")
    if should_get_llm_feedback:
        print_feedback(
            [],
            [],
            project_id,
            question_id,
            should_get_llm_feedback,
            student_code,
            llm_feedback_allowed=llm_feedback_allowed,
        )
    return True, []


def _run_notebook_mode(ctx: CheckContext) -> bool:
    cell = _find_question_code_cell(ctx.notebook, ctx.question_id)
    if not cell:
        print(NO_CODE_FOR_QID_FORMAT.format(ctx.question_id))
        return False

    check, errors = _run_core_check(
        student_code=cell.source,
        question_id=ctx.question_id,
        assignment_metadata=ctx.assignment_metadata,
        global_vars=ctx.global_vars.copy(),
        project_id=ctx.project_id,
        should_get_llm_feedback=ctx.should_get_llm_feedback,
    )

    return check


def _run_script_mode(ctx: CheckContext) -> dict:
    try:
        errors_in_previous_cells = []
        warnings_in_previous_cells = []
        q_ids = [
            q_id
            for q_id in ctx.assignment_metadata
            if q_id != METADATA_ALLOWED_IMPORTS_KEY
        ]  # using list comp here as list comp is known to be faster than for loop appends
        check = {}
        all_tags = [f"{q_id}-code" for q_id in q_ids]
        with StudentProcessWorker(os.getcwd()) as worker:
            for cell in ctx.notebook.cells:
                tags = cell.metadata.get("tags", [])
                # this is a code cell with points associated
                found_cell = set(tags).intersection(set(all_tags))
                q_id = list(found_cell)[0].replace("-code", "") if found_cell else None
                if q_id in check.keys():
                    return {
                        q_id: (
                            0.0,
                            f"FAILURE REASON: Duplicate question ID code cells found in notebook. Each question should have exactly one question tag, but {q_id} appears more than once. Please fix and resubmit.",
                        )
                        for q_id in q_ids
                    }

                replace_dir_print_help = strip_standalone_output_calls(
                    cell.source
                ).strip()
                if found_cell:
                    question_metadata = ctx.assignment_metadata[q_id]
                    check_passed, check_errors = worker.check_code(
                        student_code=replace_dir_print_help,
                        required_functions=question_metadata[
                            METADATA_REQUIRED_FUNCS_KEY
                        ],
                        required_vars=question_metadata[METADATA_REQUIRED_VARS_KEY],
                        assertions=question_metadata[METADATA_ASSERTIONS_KEY],
                    )

                    points_possible = question_metadata[POINTS_POSSIBLE_PREFIX]

                    check[q_id] = (
                        (points_possible, "")
                        if check_passed
                        else (0.0, "FAILURE REASON(s):\n- " + "\n- ".join(check_errors))
                    )
                # execute non-check code cells before question cell with suppressed output
                if cell.cell_type == "code" and _GRADER_CHECK_STUB not in cell.source:
                    if replace_dir_print_help:
                        curr_warnings, curr_errors = worker.execute_code(
                            replace_dir_print_help,
                            ABOVE_QUESTION_ERROR_PREFIX,
                        )
                        warnings_in_previous_cells.extend(curr_warnings)
                        errors_in_previous_cells.extend(curr_errors)
        return check
    except Exception as exc:
        raise RuntimeError(f"Error while running _run_script_mode: {exc}") from exc
