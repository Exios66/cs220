# CS 220 - Data Science Programming I

## Course Information

- **Credits:** 4
- **Semester:** Fall 2026
- **Prerequisite:** Satisfied Quantitative Reasoning (QR) A requirement or declared in the Professional Capstone Program in Computer Sciences
- **Course Page:** https://cs220.cs.wisc.edu/f26/

## Instructors

- Mike Doescher (mdoescher@wisc.edu)
- Blerina Gkotse (gkotse@wisc.edu)

## Communication Tools

| Tool | Purpose |
|------|---------|
| [Piazza](https://piazza.com/wisc/fall2026/fa26compsci220001/home) | Discussion (no code snippets > 5 lines) |
| [Canvas](https://canvas.wisc.edu/courses/531185) | Grades, quizzes, announcements |
| [Gradescope](https://www.gradescope.com/courses/1372769) | Project submissions |
| [Office Hours](https://calendar.google.com/calendar/u/1?cid=Y19kYzQ0OGNlYzFjMjI4ZmQwYjc4ZWJkMDZmZjlhZGZhMzc2MTcwZmY4NGZmNWY2ZTc4NWI2ODhhOTk1OWNmNTk0Qdyb3VwLmNhbGVuZGFyLmdvb2dsZS5jb20) | TA/PM/Instructor help |
| [Office Hour Sign-Up](https://apps.cs.wisc.edu/glc/check-in/) | Schedule appointments |
| [Old Exams](https://git.doit.wisc.edu/cdis/cs/courses/cs220/cs220-lecture-material/-/tree/main/Common/old_exams) | Practice for exams |

## Grading Breakdown

| Component | Weight | Details |
|-----------|--------|---------|
| Class Surveys | 1% | Start/end of semester + 2 midsemester |
| Labs | 4% | 13 labs, lowest 3 dropped |
| Projects | 47% | 13 projects (P1=1%, P2-P8,P10-P13=4% each, P9=2%) |
| Quizzes | 16% | 10 quizzes (2% each), lowest 2 dropped |
| Exams | 32% | Exam1=10%, Exam2=10%, Final=12% |

## Letter Grades

| Range | Grade |
|-------|-------|
| 93% - 100% | A |
| 88% - 92.99% | AB |
| 80% - 87.99% | B |
| 75% - 79.99% | BC |
| 70% - 74.99% | C |
| 60% - 69.99% | D |

## Project Policies

### Submission Requirements

1. Run all auto-grader tests locally before submitting
2. Submit via Gradescope — you may submit as many times as you wish
3. Verify the auto-grader completed successfully
4. Syntax errors crash the auto-grader; inefficient code may timeout (you get a 0)
5. Both partners must upload the project
6. Additional tests may run after submission — fix any errors identified

### Late Policy

- 12 late days banked for the semester
- After 12 days used: 5% deduction per day late
- Projects > 7 days late not accepted
- Late days do not apply to quizzes
- Late days are applied automatically
- Cannot use late days on P13

### Partnership Rules

- P2-P13: work alone or with one partner
- Partners must not work on alternating projects
- Partners must not split the project and work on separate halves
- Pair programming recommended (two people, one screen)
- **Generative AI is NOT allowed on projects**

### Grading Philosophy

- Results-oriented: only your code's output matters
- Code that doesn't run = 0 points
- Code is never manually fixed or graded higher for "looking correct"
- Forbidden constructs result in 0 points (auto-grader enforces this)

## Quizzes

- Open notes, computer/Internet, and Python interpreter allowed
- **No collaboration** allowed
- Multiple choice format on Canvas
- No time limit
- Must complete before 11:59:00 PM on due date
- No extensions (answers released when quiz closes)

## Exams

- In-person, closed-book, closed-laptop
- Multiple-choice scantron (#2 pencil)
- Cumulative content
- One 8.5x11 note sheet allowed (both sides, turned in with exam)
- Missed exam policies:
  - Miss Exam1 → Exam2 score replaces it
  - Miss Exam2 → Final % replaces it
  - Miss both → Final replaces both
  - Miss Final → Online makeup available

## Readings

- [Python for Everybody](https://runestone.academy/ns/books/published/py4e-int/index.html)
- [Think Python 2nd Edition](https://greenteapress.com/wp/think-python-2e/)
- [Automate the Boring Stuff](https://automatetheboringstuff.com/)
- Course Notes (posted on website)

## Academic Integrity

### Acceptable

- Collaboration with project partner
- Doing worksheets with non-partners
- Copying online examples NOT specific to your project (must cite)

### NOT Acceptable

- Code sharing with non-partner (including algorithm sharing)
- Using generative AI to write code
- Looking at/copying non-partner's code
- Partners working on alternating projects
- Partners splitting the project

## Setup

### Prerequisites

Install [pixi](https://pixi.sh) following the [installation instructions](https://cs220.cs.wisc.edu/installation_instructions/index.html).

### Getting Started

```bash
# Clone the repository
git clone https://github.com/Exios66/cs220.git
cd cs220

# Install dependencies
pixi install

# Launch JupyterLab
pixi run jupyterlab
```

### Downloading Projects

```bash
pixi run get_project p1
```

## Repository Structure

```
cs220/
├── pixi.toml          # Environment configuration
├── pixi.lock          # Locked dependencies
├── .gitignore         # Git ignore rules
├── .gitattributes     # Git attributes
├── README.md          # This file
└── projects/
    └── p1/            # Assignment 1
        ├── p1.ipynb   # Notebook
        ├── student_grader/  # Autograder
        ├── grader_utils/    # Grader utilities
        ├── shared/          # Shared config
        └── images/          # Notebook images
```

## Pre-Submission Checklist

- [ ] All code cells have correct answers
- [ ] No `%whos` or magic commands in submitted cells
- [ ] All cells run without syntax errors
- [ ] Auto-grader tests pass locally
- [ ] Notebook is saved (Cmd+S / Ctrl+S)
- [ ] Name is in the notebook header
- [ ] Submit to Gradescope
- [ ] Verify Gradescope auto-grader completed successfully

## How to Succeed

1. Attend in-person lectures
2. Attend and complete all labs
3. Complete projects by deadlines
4. Take weekly quizzes
5. Practice old exam questions
6. Use office hours (fastest way to get help)
