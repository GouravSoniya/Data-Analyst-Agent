import sys
import io
import ast
import traceback
import builtins
import re

BLOCKED_MODULES = {
    "os", "subprocess", "shutil", "socket", "requests", "httpx",
    "urllib", "ftplib", "smtplib", "telnetlib", "asyncio",
    "multiprocessing", "threading", "ctypes", "cffi",
    "importlib", "pickle", "shelve", "dbm",
}

BLOCKED_ATTRIBUTES = {
    "os.system", "os.popen", "os.remove", "os.unlink",
    "subprocess.run", "subprocess.Popen",
}

BLOCKED_BUILTINS = {
    "eval", "exec", "compile", "breakpoint",
}


class HarmfulCodeError(Exception):
    pass


# 🔥 NEW: sanitize LLM output
def sanitize_code(code: str) -> str:
    code = code.strip()

    # Remove markdown ``` blocks
    code = re.sub(r"```[\w]*", "", code)
    code = code.replace("```", "")

    # Remove weird unicode pipes and artifacts
    code = code.replace("｜", "|")

    return code.strip()


class _SafetyVisitor(ast.NodeVisitor):
    def visit_Import(self, node):
        for alias in node.names:
            if alias.name.split(".")[0] in BLOCKED_MODULES:
                raise HarmfulCodeError(f"Blocked import: {alias.name}")
        self.generic_visit(node)

    def visit_ImportFrom(self, node):
        if node.module and node.module.split(".")[0] in BLOCKED_MODULES:
            raise HarmfulCodeError(f"Blocked import: {node.module}")
        self.generic_visit(node)

    def visit_Attribute(self, node):
        if isinstance(node.value, ast.Name):
            pattern = f"{node.value.id}.{node.attr}"
            if pattern in BLOCKED_ATTRIBUTES:
                raise HarmfulCodeError(f"Blocked attribute: {pattern}")
        self.generic_visit(node)

    def visit_Call(self, node):
        if isinstance(node.func, ast.Name):
            name = node.func.id
            if name in BLOCKED_BUILTINS:
                raise HarmfulCodeError(f"Blocked builtin: {name}")
            if name == "__import__":
                raise HarmfulCodeError("Blocked: __import__")
            if name == "open":
                raise HarmfulCodeError("Use pandas instead of open()")
        self.generic_visit(node)


def _build_safe_builtins():
    safe = vars(builtins).copy()
    for name in BLOCKED_BUILTINS:
        safe.pop(name, None)
    return safe


def check_code_safety(code: str):
    try:
        tree = ast.parse(code)
    except SyntaxError as e:
        raise HarmfulCodeError(f"Syntax error: {e}")

    _SafetyVisitor().visit(tree)


def execute_python_code(code: str, globals_dict=None) -> str:
    if globals_dict is None:
        globals_dict = {}

    code = sanitize_code(code)

    # Safety check
    try:
        check_code_safety(code)
    except HarmfulCodeError as e:
        return f"[BLOCKED] {e}\n"

    if "__builtins__" not in globals_dict:
        globals_dict["__builtins__"] = _build_safe_builtins()

    buffer = io.StringIO()
    old_stdout, old_stderr = sys.stdout, sys.stderr
    sys.stdout = buffer
    sys.stderr = buffer

    try:
        tree = ast.parse(code)

        if tree.body and isinstance(tree.body[-1], ast.Expr):
            *body, last = tree.body

            if body:
                exec(compile(ast.Module(body=body, type_ignores=[]), "<string>", "exec"), globals_dict)

            result = eval(compile(ast.Expression(last.value), "<string>", "eval"), globals_dict)

            if result is not None:
                print(result)
        else:
            exec(compile(tree, "<string>", "exec"), globals_dict)

    except Exception:
        traceback.print_exc()

    finally:
        sys.stdout = old_stdout
        sys.stderr = old_stderr

    return buffer.getvalue()