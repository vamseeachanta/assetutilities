"""
Function decorator for automatic documentation.
"""

import logging
from functools import wraps
from inspect import signature
from typing import Callable, Optional

import sympy

from .dom import DocumentDOM

"""
- [ ] #todo - i have to review , tweak implementation and use it
"""


def explain_function(purpose: Optional[str] = None) -> Callable:
    """
    Decorator to document function execution in the report.

    Args:
        purpose: Optional description of function's purpose
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            dom = DocumentDOM()

            # Add purpose if provided
            logging.debug("inside wrapper function")
            if purpose:
                dom.add_paragraph(f"\n{purpose}")
                logging.debug(f"appended purpose: {purpose}")

            # Document input parameters
            sig = signature(func)
            bound_args = sig.bind(*args, **kwargs)
            bound_args.apply_defaults()

            # - [ ] #todo #11_siva #acma_consultation have to clean up inputs processing
            params_text = (
                "no input parameters\n" if not bound_args.arguments else "- Inputs : \n"
            )

            if bound_args.arguments:
                for param_name, param_value in bound_args.arguments.items():
                    if isinstance(param_value, (sympy.Expr, sympy.Symbol)):
                        param_value = (
                            DocumentDOM.LATEX_DELIM
                            + sympy.latex(param_value)
                            + DocumentDOM.LATEX_DELIM
                        )
                    params_text += f"\t- {param_name}: {param_value}\n"

            # - [ ] #todo #11_siva #acma_consultation not really sure this ought to be
            # converted to latex here . i think i should be able to just add a sympy expression or
            # sympy symbol to dom directly.
            # let the writers figure out how to flush to docx or markdown as appropriate.
            # but, probably not a viable idea since dom, when persisted has to be plain text..
            # sympy to latex, latex to sympy ? damn it.

            dom.add_paragraph(params_text)

            # Execute function and capture result
            result = func(*args, **kwargs)

            # - [ ] #todo #11_siva #acma_consultation - review this.. this is not exactly like the input value printing above.
            # Document output with multiple return values support
            output_text = "- Output : \n"
            if isinstance(result, tuple):
                for i, value in enumerate(result):
                    if isinstance(value, (sympy.Expr, sympy.Symbol)):
                        value = (
                            DocumentDOM.LATEX_DELIM
                            + sympy.latex(value)
                            + DocumentDOM.LATEX_DELIM
                        )
                    output_text += f"\t- return_{i}: {value}\n"
            else:
                if isinstance(result, (sympy.Expr, sympy.Symbol)):
                    result = (
                        DocumentDOM.LATEX_DELIM
                        + sympy.latex(result)
                        + DocumentDOM.LATEX_DELIM
                    )
                output_text += f"\t- return: {result}\n"

            dom.add_paragraph(output_text)

            return result

        return wrapper

    return decorator
