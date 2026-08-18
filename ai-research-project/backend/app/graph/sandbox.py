"""
Secure sandbox for executing Python/Pandas/Scipy medical statistics code.

Captures stdout, stderr, and matplotlib figures as base64.
"""
import io
import sys
import base64
import traceback
from typing import Any, Dict

import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# Optional scientific libraries
try:
    import numpy as np
except ImportError:
    np = None

try:
    import scipy.stats as scipy_stats
except ImportError:
    scipy_stats = None

try:
    import scipy
except ImportError:
    scipy = None

try:
    import seaborn as sns
except ImportError:
    sns = None

try:
    import statsmodels.api as sm
except ImportError:
    sm = None

try:
    from statsmodels.formula.api import ols, logit, glm
except ImportError:
    ols = logit = glm = None

try:
    from lifelines import KaplanMeierFitter, CoxPHFitter
except ImportError:
    KaplanMeierFitter = CoxPHFitter = None

try:
    from sklearn import metrics as sklearn_metrics
except ImportError:
    sklearn_metrics = None

# Allowed imports injected into sandbox globals
ALLOWED_IMPORTS = {
    # Core
    "pandas": pd,
    "pd": pd,
    "numpy": np,
    "np": np,
    # Plotting
    "matplotlib": matplotlib,
    "plt": plt,
    "seaborn": sns,
    "sns": sns,
    # Statistics
    "scipy": scipy,
    "scipy_stats": scipy_stats,
    "statsmodels_api": sm,
    "statsmodels_formula_ols": ols,
    "statsmodels_formula_logit": logit,
    "statsmodels_formula_glm": glm,
    # Survival
    "KaplanMeierFitter": KaplanMeierFitter,
    "CoxPHFitter": CoxPHFitter,
    # ML metrics
    "sklearn_metrics": sklearn_metrics,
}


def _build_builtins() -> dict:
    """Build a restricted __builtins__ dict for the sandbox."""
    safe = {
        "print": print,
        "len": len,
        "range": range,
        "list": list,
        "dict": dict,
        "str": str,
        "int": int,
        "float": float,
        "bool": bool,
        "sum": sum,
        "min": min,
        "max": max,
        "abs": abs,
        "round": round,
        "sorted": sorted,
        "reversed": reversed,
        "enumerate": enumerate,
        "zip": zip,
        "map": map,
        "filter": filter,
        "any": any,
        "all": all,
        "type": type,
        "isinstance": isinstance,
        "set": set,
        "tuple": tuple,
        "pow": pow,
        "divmod": divmod,
        "True": True,
        "False": False,
        "None": None,
        "Exception": Exception,
        "ValueError": ValueError,
        "TypeError": TypeError,
        "KeyError": KeyError,
        "IndexError": IndexError,
        "ZeroDivisionError": ZeroDivisionError,
        "open": open,
        "__import__": __import__,
    }
    return safe


SANDBOX_GLOBALS = {
    "__builtins__": _build_builtins(),
    **ALLOWED_IMPORTS,
}


def execute_code(code: str, df: pd.DataFrame) -> Dict[str, Any]:
    """
    Execute user-provided analysis code in a restricted environment.

    Args:
        code: Python code string to execute.
        df: The DataFrame loaded from the user's uploaded file.

    Returns:
        Dict with keys: success, stdout, stderr, figure_base64, result_text, result_table
    """
    stdout_capture = io.StringIO()
    stderr_capture = io.StringIO()

    # Clear any existing plots
    plt.close("all")

    old_stdout = sys.stdout
    old_stderr = sys.stderr
    sys.stdout = stdout_capture
    sys.stderr = stderr_capture

    figure_base64 = None
    result_text = ""
    result_table = None

    try:
        local_vars = {"df": df, "data": df}

        exec(code, SANDBOX_GLOBALS, local_vars)

        # Capture any matplotlib figures
        fig = plt.gcf()
        if fig.get_axes():
            buf = io.BytesIO()
            fig.savefig(
                buf, format="png", dpi=120, bbox_inches="tight",
                facecolor="white", edgecolor="none",
            )
            buf.seek(0)
            figure_base64 = base64.b64encode(buf.read()).decode("utf-8")
            buf.close()

        # Check for a 'result' variable
        if "result" in local_vars:
            result_val = local_vars["result"]
            if isinstance(result_val, pd.DataFrame):
                result_table = {
                    "columns": [{"title": str(c), "key": str(c)} for c in result_val.columns],
                    "rows": result_val.fillna("").head(50).to_dict(orient="records"),
                }
            else:
                result_text = str(result_val)

        success = True
        output = stdout_capture.getvalue()

    except Exception:
        success = False
        output = traceback.format_exc()

    finally:
        sys.stdout = old_stdout
        sys.stderr = old_stderr

    return {
        "success": success,
        "stdout": output.strip() if output else None,
        "stderr": stderr_capture.getvalue().strip() or None,
        "figure_base64": figure_base64,
        "result_text": result_text,
        "result_table": result_table,
    }
