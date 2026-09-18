"""Worker process that executes student code in a separate interpreter."""

import json
import sys
from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
from grader_utils import check_student_code_against_requirements, execute_code


def _emit(payload: dict) -> None:
    sys.stdout.write(json.dumps(payload) + "\n")
    sys.stdout.flush()


def main() -> None:
    global_vars = {"__name__": "__main__"}

    for line in sys.stdin:
        if not line.strip():
            continue

        try:
            request = json.loads(line)
            command = request["command"]
            fake_stdout = StringIO()
            fake_stderr = StringIO()
            # we redirect becuase tudent code might call print(). Without this, those prints would go to the worker's real stdout, which is the pipe back to the grader. That would corrupt the JSON protocol — the grader would try to parse "Hello World" as JSON and crash. So student output is captured into StringIO objects and effectively discarded.
            with redirect_stdout(fake_stdout), redirect_stderr(fake_stderr):
                if command == "execute_code":
                    warnings_list = []
                    errors_list = []
                    execute_code(
                        request["code"],
                        global_vars,
                        warnings_list,
                        errors_list,
                        request["error_prefix"],
                    )
                    result = {
                        "warnings": warnings_list,
                        "errors": errors_list,
                    }
                elif command == "check_code":
                    warnings_list = []
                    errors_list = []
                    check_student_code_against_requirements(
                        request["student_code"],
                        request["required_functions"],
                        request["required_vars"],
                        request["assertions"],
                        warnings_list,
                        errors_list,
                        global_vars,
                    )
                    result = {
                        "passed": not (warnings_list or errors_list),
                        "messages": errors_list + warnings_list,
                    }
                else:
                    raise ValueError(f"Unknown worker command: {command}")
        except Exception as exc:
            _emit({"ok": False, "error": str(exc)})
            continue

        _emit({"ok": True, "result": result})


# just so we can run it as. amodule otherwise importing this module would execute the main function and start the worker process immediately, which we don't want when we're importing the StudentProcessWorker class in our grader code.
if __name__ == "__main__":
    main()
