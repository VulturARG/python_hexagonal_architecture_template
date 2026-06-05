from unittest import TestCase
from unittest.mock import patch

from src.domain.exceptions.base_src_error import (
    BaseSrcError,
    SrcBaseNotAuthorized,
    SrcBaseNotFound,
    SrcBaseWarning,
    SrcGenericError,
)
from src.domain.exceptions.decorators.generic_error_handler import (
    generic_error_handler,
    logger_error_details,
)


class TestGenericErrorHandler(TestCase):
    def test_returns_value_when_no_exception_raised(self):
        class Subject:
            @generic_error_handler
            def run(self):
                return 42

        self.assertEqual(Subject().run(), 42)

    def test_reraises_src_base_warning_unchanged(self):
        class Subject:
            @generic_error_handler
            def run(self):
                raise SrcBaseWarning()

        with self.assertRaises(SrcBaseWarning):
            Subject().run()

    def test_reraises_src_base_not_authorized_unchanged(self):
        class Subject:
            @generic_error_handler
            def run(self):
                raise SrcBaseNotAuthorized()

        with self.assertRaises(SrcBaseNotAuthorized):
            Subject().run()

    def test_reraises_src_base_not_found_unchanged(self):
        class Subject:
            @generic_error_handler
            def run(self):
                raise SrcBaseNotFound()

        with self.assertRaises(SrcBaseNotFound):
            Subject().run()

    def test_wraps_unexpected_exception_in_src_generic_error(self):
        class Subject:
            @generic_error_handler
            def run(self):
                raise ValueError("unexpected")

        with self.assertRaises(SrcGenericError):
            Subject().run()

    def test_sets_was_error_logged_when_wrapping_unexpected_exception(self):
        class Subject:
            @generic_error_handler
            def run(self):
                raise ValueError("unexpected")

        try:
            Subject().run()
        except SrcGenericError as exc:
            self.assertTrue(exc.was_error_logged)

    def test_reraises_base_src_error_subclass_and_marks_as_logged(self):
        class DomainError(BaseSrcError):
            pass

        class Subject:
            @generic_error_handler
            def run(self):
                raise DomainError()

        try:
            Subject().run()
        except DomainError as exc:
            self.assertTrue(exc.was_error_logged)

    def test_handles_standalone_function_without_class_name(self):
        @generic_error_handler
        def standalone():
            raise RuntimeError("oops")

        with patch(
            "src.domain.exceptions.decorators.generic_error_handler.logger_error_details"
        ) as mock_details:
            with self.assertRaises(SrcGenericError):
                standalone()
            _, kwargs = mock_details.call_args
            self.assertIsNone(kwargs.get("class_name"))

    def test_does_not_relog_base_src_error_when_already_logged(self):
        class DomainError(BaseSrcError):
            pass

        class Subject:
            @generic_error_handler
            def run(self):
                err = DomainError()
                err.was_error_logged = True
                raise err

        with patch(
            "src.domain.exceptions.decorators.generic_error_handler.base_exception_logger"
        ) as mock_logger:
            with self.assertRaises(DomainError):
                Subject().run()
            mock_logger.assert_not_called()

    def test_reraises_base_src_error_subclass_as_is(self):
        class DomainError(BaseSrcError):
            pass

        class Subject:
            @generic_error_handler
            def run(self):
                raise DomainError()

        with self.assertRaises(DomainError):
            Subject().run()


class TestLoggerErrorDetails(TestCase):
    def test_logger_error_details_handles_empty_traceback(self):
        with patch(
            "src.domain.exceptions.decorators.generic_error_handler.extract_tb",
            return_value=[],
        ):
            with patch(
                "src.domain.exceptions.decorators.generic_error_handler.logger"
            ) as mock_logger:
                logger_error_details(exc=RuntimeError("x"), method_name="run")
                mock_logger.error.assert_called_once()
                call_args = mock_logger.error.call_args[0]
                self.assertIn("unknown", call_args)
