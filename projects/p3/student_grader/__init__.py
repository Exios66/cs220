"""Init file for student_grader package.

Imports everything from all child files so that everything inside of the student_grader
is importable with a simple `from student_grader import thing`. Doing it this way
means dependents of the student_grader package don't need to know where inside the
student_grader package a given constant/function is located.
"""

from .grading import *
from grader_utils import initialize
