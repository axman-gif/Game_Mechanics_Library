# -*- coding: utf-8 -*-
"""
Deterministic Gatekeeper & AST Auditor for Loop Engineering (audit_minigame.py)
Checks:
1. Mandatory template headers, imports, and 5-block anatomy from AGENTS.md.
2. Strict C++-transferable AST rules (zero comprehensions, lambdas, decorators, generators, or walrus operators).
3. Headless execution verification (--smoke-test) with zero bytecode generation (-B).
"""
import sys
import os
import ast
import subprocess

sys.dont_write_bytecode = True

REQUIRED_STRINGS = [
    "sys.dont_write_bytecode = True",
    "from pyray import *",
    "from utils import *",
    "BLOCK 1: CORE PATTERN IMPLEMENTATION",
    "BLOCK 2: WORLD SIMULATION & ENTITIES",
    "BLOCK 3: TELEMETRY & X-RAY DEBUG OVERLAY",
    "draw_gamepad_status_badge",
    "draw_ui_settings_bar",
    "--smoke-test"
]

MIN_LINES = 300
HARD_CEILING_LINES = 1800

def check_ast_cpp_rules(filepath, source):
    try:
        tree = ast.parse(source, filename=filepath)
    except SyntaxError as e:
        return [f"Line {e.lineno}: SyntaxError: {e.msg}"]

    errors = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.ListComp, ast.DictComp, ast.SetComp, ast.GeneratorExp)):
            errors.append(f"Line {node.lineno}: Comprehension/Generator expression forbidden (Rule 4: use explicit C++-style for loops).")
        elif isinstance(node, ast.Lambda):
            errors.append(f"Line {node.lineno}: 'lambda' forbidden (Rule 4).")
        elif isinstance(node, (ast.Yield, ast.YieldFrom, ast.AsyncFunctionDef, ast.Await)):
            errors.append(f"Line {node.lineno}: Generator 'yield' or 'async/await' forbidden (Rule 4).")
        elif isinstance(node, ast.NamedExpr):
            errors.append(f"Line {node.lineno}: Walrus operator (:=) forbidden (Rule 4).")
        elif isinstance(node, (ast.FunctionDef, ast.ClassDef)):
            if node.decorator_list:
                errors.append(f"Line {node.lineno}: Decorators (@) forbidden (Rule 4).")
            if isinstance(node, ast.FunctionDef) and node.name.startswith("__") and node.name != "__init__":
                errors.append(f"Line {node.lineno}: Dunder method '{node.name}' forbidden (only __init__ is allowed).")
    return errors

def main():
    if len(sys.argv) < 2:
        print("Usage: python -B audit_minigame.py minigames/<script_name>.py")
        sys.exit(1)

    filepath = sys.argv[1]
    if not os.path.exists(filepath):
        print(f"[FAIL] File not found: {filepath}")
        sys.exit(1)

    with open(filepath, "r", encoding="utf-8") as f:
        source = f.read()

    # 1. Check mandatory AGENTS.md structural requirements
    missing = []
    has_asset_loader = ("from assets.asset_loader import *" in source) or ("from assets.audio.asset_loader import *" in source)
    if not has_asset_loader:
        missing.append("from assets.asset_loader import *")
    for req in REQUIRED_STRINGS:
        if req not in source:
            missing.append(req)
    # Check for canonical game loop block (Block 4 or Block 5)
    has_loop_block = ("BLOCK 4: MAIN GAME LOOP" in source) or ("BLOCK 5: MAIN GAME LOOP" in source)
    if not has_loop_block:
        missing.append("BLOCK 4/5: MAIN GAME LOOP & AUTOMATED SMOKE TEST")
    if missing:
        print(f"[FAIL] {filepath} - Missing mandatory AGENTS.md elements:")
        for m in missing:
            print(f"  - {m}")
        sys.exit(1)

    # 2. Check AST for C++ Transferability (Rule 4)
    ast_errors = check_ast_cpp_rules(filepath, source)
    if ast_errors:
        print(f"[FAIL] {filepath} - Rule 4 (C++ Transferable Code) violations detected:")
        for err in ast_errors[:15]:
            print(f"  - {err}")
        sys.exit(1)

    # 3. Check line count bounds (600 to 1,500 lines target, 1,800 maximum hard ceiling)
    line_count = len(source.splitlines())
    if line_count < MIN_LINES:
        print(f"[FAIL] {filepath} - Script is undersized ({line_count} lines < {MIN_LINES} minimum).")
        print(f"  Every minigame must provide thorough pedagogical comments, full 5-block anatomy, dual input, and X-Ray overlay.")
        sys.exit(1)
    if line_count > HARD_CEILING_LINES:
        print(f"[FAIL] {filepath} - Script exceeds hard ceiling ({line_count} lines > {HARD_CEILING_LINES} maximum).")
        print(f"  Scripts must remain strictly within 600 to 1,500 lines (hard ceiling of 1,800) to avoid token bloat.")
        sys.exit(1)

    # 4. Run headless Raylib smoke test (catches CFFI float/int and Color errors)
    env = os.environ.copy()
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    res = subprocess.run([sys.executable, "-B", filepath, "--smoke-test"], capture_output=True, text=True, env=env)
    if res.returncode != 0:
        print(f"[FAIL] {filepath} - Runtime crash during --smoke-test:\n{res.stderr}\n{res.stdout}")
        sys.exit(1)

    print(f"[PASS] {filepath} passed Template + AST C++ Check + Raylib Smoke Test (0 errors).")
    sys.exit(0)

if __name__ == "__main__":
    main()

