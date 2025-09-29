import unittest
from backend.entities.minister import Minister
from backend.exceptions import EmptyMinisterNameError


class TestMinister(unittest.TestCase):
    def test_minister_name(self):
        minister = Minister(name="Alice")
        self.assertEqual(minister.name, "Alice")
        self.assertEqual(minister.id, None)  # Assuming id is None before saving to DB

    def test_minister_id(self):
        minister = Minister(name="Bob", id=1)
        self.assertEqual(minister.id, 1)
        self.assertEqual(minister.name, "Bob")

    def test_minister_name_empty(self):
        with self.assertRaises(EmptyMinisterNameError):
            Minister(name="")


if __name__ == "__main__":
    unittest.main()
