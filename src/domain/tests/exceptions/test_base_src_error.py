from typing import get_type_hints
from unittest import TestCase

from src.domain.exceptions.base_src_error import (
    BaseSrcError,
    SrcBaseNotAuthorized,
    SrcBaseNotFound,
    SrcBaseWarning,
    SrcGenericError,
)


class TestBaseSrcError(TestCase):
    def test_is_subclass_of_exception(self):
        self.assertTrue(issubclass(BaseSrcError, Exception))

    def test_dict_returns_error_key_with_class_name_when_message_is_none(self):
        result = BaseSrcError().dict()
        self.assertIn("error", result)
        self.assertIn("BaseSrcError", result["error"])

    def test_dict_returns_message_when_message_is_set(self):
        class ConcreteError(BaseSrcError):
            MESSAGE = "something went wrong"

        self.assertEqual(ConcreteError().dict(), {"error": "something went wrong"})

    def test_was_error_logged_defaults_to_false(self):
        self.assertFalse(BaseSrcError().was_error_logged)

    def test_was_error_logged_is_per_instance(self):
        a = BaseSrcError()
        b = BaseSrcError()
        a.was_error_logged = True
        self.assertFalse(b.was_error_logged)


class TestSrcGenericError(TestCase):
    def test_inherits_from_base_src_error(self):
        self.assertTrue(issubclass(SrcGenericError, BaseSrcError))

    def test_dict_returns_generic_error_key_when_given_exception(self):
        self.assertEqual(SrcGenericError(ValueError("boom")).dict(), {"error": "boom"})

    def test_dict_returns_string_message_when_given_string(self):
        self.assertEqual(SrcGenericError("oops").dict(), {"error": "oops"})

    def test_dict_return_type_annotation(self):
        hints = get_type_hints(SrcGenericError.dict)
        self.assertEqual(hints["return"], dict[str, str])


class TestSrcBaseSubclasses(TestCase):
    def test_src_base_warning_inherits_from_base_src_error(self):
        self.assertTrue(issubclass(SrcBaseWarning, BaseSrcError))

    def test_src_base_not_authorized_inherits_from_base_src_error(self):
        self.assertTrue(issubclass(SrcBaseNotAuthorized, BaseSrcError))

    def test_src_base_not_found_inherits_from_base_src_error(self):
        self.assertTrue(issubclass(SrcBaseNotFound, BaseSrcError))

    def test_warning_is_catchable_as_base_src_error(self):
        with self.assertRaises(BaseSrcError):
            raise SrcBaseWarning()

    def test_not_found_is_catchable_as_base_src_error(self):
        with self.assertRaises(BaseSrcError):
            raise SrcBaseNotFound()
