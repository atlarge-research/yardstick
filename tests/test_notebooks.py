"""Static smoke checks for the notebooks under version control.

Running a notebook for real needs a deployment (apptainer, container pulls,
a DAS reservation), so CI cannot execute one. But the bug that motivated
these tests did not need execution to be caught: ``example.ipynb`` carried
``MinecraftServer("minecraft")`` long after the constructor's first
parameter became a ``Node``. Nothing noticed, because the only notebook
check in CI was that outputs had been stripped.

So this module reads the notebooks as source and checks the parts that can
be checked without infrastructure:

  * every code cell parses;
  * every ``yardstick_benchmark`` import in them still resolves;
  * every call into ``yardstick_benchmark`` still matches the signature it
    is calling -- which is exactly the class of error above.

Third-party imports that are missing (matplotlib, pandas, seaborn -- the
``notebooks`` extra) are stepped over rather than failed on, so a checkout
installed with a plain ``uv sync`` still runs these. A missing or renamed
``yardstick_benchmark`` name is always a failure.
"""

import ast
import importlib
import inspect
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union, get_args, get_origin

import pytest


REPO_ROOT = Path(__file__).resolve().parent.parent
EXPERIMENTS = REPO_ROOT / "experiments"

NOTEBOOKS = [REPO_ROOT / "example.ipynb", *sorted(EXPERIMENTS.glob("*.ipynb"))]
NOTEBOOK_IDS = [str(p.relative_to(REPO_ROOT)) for p in NOTEBOOKS]

#: Stands in for an argument value when binding a call against a signature.
#: Only the shape of the call (how many positionals, which keywords) is
#: checked here -- the values are never evaluated.
ARG = object()


def _cell_source(cell: Dict[str, Any]) -> Optional[str]:
    """The cell's source with IPython line magics neutralised, or None if
    the cell is not Python this module can reason about (a cell magic like
    ``%%bash`` makes the whole cell something else)."""
    source = "".join(cell["source"])
    lines = source.splitlines()
    if any(line.lstrip().startswith("%%") for line in lines):
        return None
    kept = []
    for line in lines:
        stripped = line.lstrip()
        # `%load_ext autoreload`, `!pip install ...`: valid in Jupyter,
        # syntax errors to Python.
        kept.append("" if stripped.startswith(("%", "!")) else line)
    return "\n".join(kept)


def _code_cells(path: Path) -> List[Tuple[int, str]]:
    notebook = json.loads(path.read_text())
    cells = []
    for index, cell in enumerate(notebook["cells"]):
        if cell["cell_type"] != "code":
            continue
        source = _cell_source(cell)
        if source is not None and source.strip():
            cells.append((index, source))
    return cells


def _trees(path: Path) -> List[Tuple[int, ast.Module]]:
    return [(index, ast.parse(src)) for index, src in _code_cells(path)]


def _is_yardstick(module: str) -> bool:
    return module.split(".")[0] == "yardstick_benchmark"


@pytest.mark.parametrize("notebook", NOTEBOOKS, ids=NOTEBOOK_IDS)
def test_every_code_cell_parses(notebook: Path):
    """A notebook is JSON, so a syntax error in one sits in git happily."""
    cells = _code_cells(notebook)
    assert cells, f"{notebook.name} has no code cells to check"
    for index, source in cells:
        try:
            ast.parse(source)
        except SyntaxError as exc:
            pytest.fail(f"{notebook.name} cell {index} does not parse: {exc}")


@pytest.mark.parametrize("notebook", NOTEBOOKS, ids=NOTEBOOK_IDS)
def test_imports_resolve(notebook: Path):
    """Execute just the import statements: the cheapest execution that
    still catches a module or name that moved."""
    namespace: Dict[str, Any] = {}
    # Jupyter puts the notebook's own directory on sys.path, which is how
    # the experiment notebooks reach `_lib`.
    sys.path.insert(0, str(notebook.parent))
    try:
        for index, tree in _trees(notebook):
            for node in ast.walk(tree):
                if not isinstance(node, (ast.Import, ast.ImportFrom)):
                    continue
                statement = ast.unparse(node)
                try:
                    exec(compile(statement, str(notebook), "exec"), namespace)
                except ModuleNotFoundError as exc:
                    missing = exc.name or ""
                    if _is_yardstick(missing):
                        pytest.fail(
                            f"{notebook.name} cell {index}: {statement!r} -> {exc}"
                        )
                    # matplotlib & friends come from the `notebooks` extra.
                    continue
                except ImportError as exc:
                    # The name is gone from a module that does exist -- a
                    # rename the notebook was not updated for.
                    pytest.fail(f"{notebook.name} cell {index}: {statement!r} -> {exc}")
    finally:
        sys.path.remove(str(notebook.parent))


def _imported_yardstick_names(trees: List[Tuple[int, ast.Module]]) -> Dict[str, Any]:
    """Local name -> the ``yardstick_benchmark`` object it refers to."""
    names: Dict[str, Any] = {}
    for _, tree in trees:
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if _is_yardstick(alias.name) and alias.asname is None:
                        names[alias.name.split(".")[0]] = importlib.import_module(
                            alias.name.split(".")[0]
                        )
                    elif _is_yardstick(alias.name):
                        names[alias.asname] = importlib.import_module(alias.name)
            elif isinstance(node, ast.ImportFrom):
                if node.module is None or not _is_yardstick(node.module):
                    continue
                module = importlib.import_module(node.module)
                for alias in node.names:
                    obj = getattr(module, alias.name, None)
                    assert obj is not None, (
                        f"{node.module} has no {alias.name!r} any more"
                    )
                    names[alias.asname or alias.name] = obj
    return names


def _variable_types(
    trees: List[Tuple[int, ast.Module]], names: Dict[str, Any]
) -> Dict[str, type]:
    """Variables assigned straight from a constructor call, so that method
    calls on them (``minecraft.set_world_spawn(...)``) can be checked too."""
    types: Dict[str, type] = {}
    for _, tree in trees:
        for node in ast.walk(tree):
            if not isinstance(node, ast.Assign) or not isinstance(node.value, ast.Call):
                continue
            func = node.value.func
            if not isinstance(func, ast.Name):
                continue
            obj = names.get(func.id)
            if not inspect.isclass(obj):
                continue
            for target in node.targets:
                if isinstance(target, ast.Name):
                    types[target.id] = obj
    return types


def _annotation_accepts(annotation: Any, value: Any) -> Optional[bool]:
    """Whether `annotation` can accept the literal `value`, or None when the
    annotation is not a plain class this can decide on."""
    origin = get_origin(annotation)
    if origin is Union:
        verdicts = [_annotation_accepts(a, value) for a in get_args(annotation)]
        if any(v is True for v in verdicts):
            return True
        return False if all(v is False for v in verdicts) else None
    if not inspect.isclass(annotation) or annotation is Any:
        return None
    if annotation in (float, complex) and isinstance(value, (int, float)):
        return True  # the numeric tower: an int literal is a fine float
    return isinstance(value, annotation)


def _check_literal_types(what: str, call: ast.Call, bound: inspect.BoundArguments):
    """Catch a literal handed to a parameter that cannot hold it.

    This is the check that ``MinecraftServer("minecraft")`` needed: it has
    the right *arity* -- the string binds happily to ``node`` -- and only
    the annotation says it cannot be a ``Node``.
    """
    for name, value in bound.arguments.items():
        parameter = bound.signature.parameters[name]
        if parameter.kind in (parameter.VAR_POSITIONAL, parameter.VAR_KEYWORD):
            continue
        if not isinstance(value, ast.Constant):
            continue  # not a literal: nothing can be decided statically
        if _annotation_accepts(parameter.annotation, value.value) is False:
            pytest.fail(
                f"{what}: {ast.unparse(call)[:120]} passes "
                f"{value.value!r} as {name}, which is {parameter.annotation}"
            )


def _check_call(what: str, obj: Any, call: ast.Call, implicit_self: bool) -> bool:
    """Bind `call`'s shape against `obj`'s signature. Returns False when the
    call cannot be checked (``*args``/``**kwargs`` hide its shape)."""
    if any(isinstance(a, ast.Starred) for a in call.args):
        return False
    if any(kw.arg is None for kw in call.keywords):
        return False
    try:
        signature = inspect.signature(obj)
    except (TypeError, ValueError):
        return False
    # Bind the argument *expressions*, so a literal can be type-checked
    # afterwards; everything else is just a placeholder.
    positional: List[Any] = list(call.args)
    if implicit_self:
        positional.insert(0, ARG)
    keywords = {kw.arg: kw.value for kw in call.keywords}
    try:
        bound = signature.bind(*positional, **keywords)
    except TypeError as exc:
        pytest.fail(
            f"{what}: {ast.unparse(call)[:120]} does not fit {signature}: {exc}"
        )
    _check_literal_types(what, call, bound)
    return True


@pytest.mark.parametrize("notebook", NOTEBOOKS, ids=NOTEBOOK_IDS)
def test_calls_into_yardstick_match_their_signatures(notebook: Path):
    """The check that would have caught ``MinecraftServer("minecraft")``."""
    trees = _trees(notebook)
    names = _imported_yardstick_names(trees)
    assert names, f"{notebook.name} imports nothing from yardstick_benchmark"
    types = _variable_types(trees, names)

    checked = 0
    for index, tree in trees:
        where = f"{notebook.name} cell {index}"
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            func = node.func
            if isinstance(func, ast.Name):
                obj = names.get(func.id)
                if obj is None:
                    continue
                checked += _check_call(where, obj, node, implicit_self=False)
            elif isinstance(func, ast.Attribute) and isinstance(func.value, ast.Name):
                owner = func.value.id
                if owner in names and inspect.ismodule(names[owner]):
                    obj = getattr(names[owner], func.attr, None)
                    assert obj is not None, (
                        f"{where}: {owner} has no {func.attr!r} any more"
                    )
                    checked += _check_call(where, obj, node, implicit_self=False)
                elif owner in types:
                    method = getattr(types[owner], func.attr, None)
                    assert method is not None, (
                        f"{where}: {types[owner].__name__} has no "
                        f"{func.attr!r} any more ({owner}.{func.attr})"
                    )
                    if inspect.isfunction(method):
                        checked += _check_call(where, method, node, implicit_self=True)

    assert checked, (
        f"{notebook.name}: no call into yardstick_benchmark was checked -- "
        "this test would pass no matter what the notebook contained"
    )
