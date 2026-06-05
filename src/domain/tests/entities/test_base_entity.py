from dataclasses import dataclass
from unittest import TestCase

from src.domain.entities.base_entity import BaseEntity


class TestBaseEntity(TestCase):
    def test_as_dict_returns_plain_dictionary(self):
        @dataclass
        class SampleEntity(BaseEntity):
            name: str
            value: int

        self.assertEqual(
            SampleEntity(name="item", value=42).as_dict(),
            {"name": "item", "value": 42},
        )

    def test_as_dict_recursively_converts_nested_entities(self):
        @dataclass
        class InnerEntity(BaseEntity):
            count: int

        @dataclass
        class OuterEntity(BaseEntity):
            inner: InnerEntity

        self.assertEqual(
            OuterEntity(inner=InnerEntity(count=5)).as_dict(),
            {"inner": {"count": 5}},
        )
