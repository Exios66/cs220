# CS 220 - Data Science Programming 1

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
├── projects/
│   └── p1/            # Assignment 1
│       ├── p1.ipynb
│       ├── student_grader/
│       ├── grader_utils/
│       └── shared/
```

## Submitting Assignments

1. Complete all questions in the notebook
2. Run all cells to verify tests pass
3. Submit `p1.ipynb` to Gradescope
