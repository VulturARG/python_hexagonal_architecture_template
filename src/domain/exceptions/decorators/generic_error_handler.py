from inspect import isclass
from logging import getLogger
from sys import exc_info
from traceback import extract_tb
from typing import Callable

from src.domain.exceptions.base_src_error import (
    BaseSrcError,
    SrcBaseNotAuthorized,
    SrcBaseNotFound,
    SrcBaseWarning,
    SrcGenericError,
)

logger = getLogger(__name__)


def generic_error_handler(func: Callable) -> Callable:
    """Wrap a method to handle domain exceptions and log infrastructure errors."""

    def wrapper(*args, **kwargs):
        try:
            if isclass(args[0]):
                class_name = args[0].__name__
            else:
                class_name = args[0].__class__.__name__
        except IndexError:
            class_name = None
        method_name = func.__name__
        try:
            return func(*args, **kwargs)
        except (SrcBaseWarning, SrcBaseNotAuthorized, SrcBaseNotFound) as exc:
            raise exc
        except BaseSrcError as exc:
            if not exc.was_error_logged:
                base_exception_logger(class_name=class_name, method_name=method_name, exception=exc)
                exc.was_error_logged = True
            raise exc
        except Exception as exc:
            logger_error_details(exc=exc, method_name=method_name, class_name=class_name)
            error = SrcGenericError(exc)
            error.was_error_logged = True
            raise error from exc

    return wrapper


def logger_error_details(exc: Exception, method_name: str, class_name: str | None = None) -> None:
    """Log exception details including traceback and context information."""
    traceback_frames = extract_tb(exc_info()[2])
    if not traceback_frames:
        line_number = "unknown"
    else:
        _, line_number, _, _ = traceback_frames[-1]

    if class_name is None:
        logger.error(
            "ERROR: '%s' exception was raised in line %s in '%s' function/method.",
            exc.__class__.__name__,
            line_number,
            method_name,
        )
        return

    logger.error(
        "ERROR: '%s' exception was raised in line %s in '%s' method of the '%s' class.",
        exc.__class__.__name__,
        line_number,
        method_name,
        class_name,
    )
    logger.exception("Unhandled exception")


def base_exception_logger(
    class_name: str | None, method_name: str, exception: BaseSrcError
) -> None:
    """Log a domain exception with its error message."""
    logger_error_details(exc=exception, method_name=method_name, class_name=class_name)
    message = exception.dict().get("error", "No error message received")
    logger.exception("ERROR MESSAGE: %s", message)
