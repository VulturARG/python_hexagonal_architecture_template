# Python Pre-Commit Hooks Template

---

### How to set up the pre-commit hooks
You need to install some python packages (install them in your system python, not in the container):

```
pip install pre-commit ruff
```
Ruff replaces black, isort and flake8, providing linting, import sorting and formatting in a single faster tool.

Once you have installed all the dependencies, you can execute the following command, being in the root of the project.

```
pre-commit install
```
