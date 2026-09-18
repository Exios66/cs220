"""
Information about the server that can be safely shared with students.
Confidential information about the server and its deployment should go
in master_grader/server.py, not here.
"""

import os
from enum import Enum
from shared.config import MODE


class RequiredRequestFields(Enum):
    """All must be in body to make a valid request to the gpt220 server."""

    PROJECT_ID = "project_id"
    QUESTION_ID = "question_id"
    EXPECTED_ANSWER = "expected_answer"
    PROMPT = "prompt"
    TEMPLATE_CODE = "template_code"
    STUDENT_CODE = "student_code"
    AUTOGRADER_OUTPUT = "autograder_output"
    LANGUAGE = "language"


# The URL to hit to access our LLM feedback service. This is
# viewable in the top center of the screen when viewing the
# gpt220 service. Uncomment the line below when running tests
# using the locally running docker container for the server.
# Otherwise, all requests should route to the deployed server.
# Can be overridden via GPT_SERVICE_URL env var (used in CI for blue-green deploys).

_DEPLOY_URL = "https://prod.cs220-feedback-server.cs.wisc.edu/"
_DEV_URL = "http://0.0.0.0:8080/"

if os.environ.get("GPT_SERVICE_URL"):
    GPT_SERVICE_PUBLIC_URL = os.environ["GPT_SERVICE_URL"]
elif MODE == "deploy":
    GPT_SERVICE_PUBLIC_URL = _DEPLOY_URL
elif MODE == "dev":
    GPT_SERVICE_PUBLIC_URL = _DEV_URL
else:
    raise ValueError(f"Unknown mode: {MODE}. Expected 'deploy' or 'dev'.")
