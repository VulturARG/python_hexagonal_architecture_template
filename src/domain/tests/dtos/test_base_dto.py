from dataclasses import FrozenInstanceError, dataclass
from typing import Any, get_type_hints
from unittest import TestCase

from src.domain.dtos.base_dto import BaseDTO


class TestBaseDTO(TestCase):
    def test_as_dict_returns_plain_dictionary(self):
        @dataclass(frozen=True)
        class SampleDTO(BaseDTO):
            name: str
            age: int

        self.assertEqual(SampleDTO(name="Alice", age=30).as_dict(), {"name": "Alice", "age": 30})

    def test_from_dict_creates_instance_from_dictionary(self):
        @dataclass(frozen=True)
        class SampleDTO(BaseDTO):
            name: str
            age: int

        dto = SampleDTO.from_dict({"name": "Bob", "age": 25})
        self.assertEqual(dto.name, "Bob")
        self.assertEqual(dto.age, 25)

    def test_from_dict_raises_type_error_on_unexpected_keys(self):
        @dataclass(frozen=True)
        class SampleDTO(BaseDTO):
            name: str

        with self.assertRaises(TypeError):
            SampleDTO.from_dict({"name": "Bob", "unexpected": "value"})

    def test_is_immutable(self):
        @dataclass(frozen=True)
        class SampleDTO(BaseDTO):
            name: str

        with self.assertRaises(FrozenInstanceError):
            SampleDTO(name="Alice").name = "Bob"

    def test_equality_based_on_field_values(self):
        @dataclass(frozen=True)
        class SampleDTO(BaseDTO):
            name: str

        self.assertEqual(SampleDTO(name="Alice"), SampleDTO(name="Alice"))
        self.assertNotEqual(SampleDTO(name="Alice"), SampleDTO(name="Bob"))

    def test_from_dict_data_annotation(self):
        hints = get_type_hints(BaseDTO.from_dict)
        self.assertEqual(hints["data"], dict[str, Any])
