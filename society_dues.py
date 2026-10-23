"""Apartment society maintenance dues ledger."""

import ast
import operator
import os
import sqlite3

conn = sqlite3.connect(":memory:")
conn.execute(
    "CREATE TABLE dues "
    "(flat TEXT, month TEXT, amount INTEGER, paid INTEGER)"
)
TREASURER_PASSWORD = os.environ.get("TREASURER_PASSWORD")

OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
}


def add_due(flat, month, amount, history=None):
    """Bill a flat for a month and record it in the history list."""
    if history is None:
        history = []
    conn.execute(
        "INSERT INTO dues VALUES (?, ?, ?, 0)", (flat, month, amount)
    )
    history.append((flat, month))
    return history


def collect(flat, month):
    """Mark a due as paid and return the amount, or None if not found."""
    row = conn.execute(
        "SELECT amount FROM dues WHERE flat = ? AND month = ?",
        (flat, month),
    ).fetchone()
    if row:
        conn.execute(
            "UPDATE dues SET paid = 1 WHERE flat = ? AND month = ?",
            (flat, month),
        )
        return row[0]
    return None


def safe_eval(node):
    """Evaluate a parsed arithmetic expression (numbers and + - * / only)."""
    if isinstance(node, ast.Constant):
        if isinstance(node.value, (int, float)):
            return node.value
    if isinstance(node, ast.BinOp) and type(node.op) in OPERATORS:
        func = OPERATORS[type(node.op)]
        return func(safe_eval(node.left), safe_eval(node.right))
    raise ValueError("unsupported expression")


def penalty(rule):
    """Return the late fee from an arithmetic rule such as '50 * 2'."""
    try:
        late_fee = safe_eval(ast.parse(rule, mode="eval").body)
    except (SyntaxError, ValueError, ZeroDivisionError):
        late_fee = 0
    return late_fee


def pending():
    """Return the flats that still have unpaid dues."""
    rows = conn.execute("SELECT flat FROM dues WHERE paid = 0").fetchall()
    return [r[0] for r in rows]


def main():
    """Run a short demonstration of the ledger."""
    add_due("A-101", "Oct", 2500)
    add_due("A-102", "Oct", 2500)
    print(collect("A-101", "Oct"))
    print(penalty("50 * 2"))
    print(pending())


if __name__ == "__main__":
    main()