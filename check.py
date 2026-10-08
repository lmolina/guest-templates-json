#!/usr/bin/env python3
import glob
import json
import unittest

from jsonschema.validators import validator_for

from guesttemplates import loader

class MockLoader(loader.Loader):
    def __init__(self):
        self._confs = {}
        self._by_uuid = {}
        self._by_reflabel = {}

class TestLoader(unittest.TestCase):
    def test_load_templates(self):
        """Tests that the templates can be loaded and converted to XML successfully."""

        loader = MockLoader()
        loader.find_config_files("json/")

        # Loading templates can fail if inconsistencies are found (e.g. uefi and device-model)
        loader.load_templates()

        # Check that we were able to load some templates successfully
        # The exact number depends on how many base templates there are that are skipped.
        self.assertLessEqual(len(loader._by_uuid), len(loader._confs))
        self.assertGreaterEqual(len(loader._by_uuid), 3)

        for i in loader._by_uuid.values():
            i.toxml({})

        all_uuids = []
        all_reflabels = []
        for i in glob.glob("json/*"):
            with open(i, 'r') as f:
                template = json.load(f)
                if 'uuid' in template:
                    all_uuids.append(template['uuid'])
                if 'reference_label' in template:
                    all_reflabels.append(template['reference_label'])

        self.assertEqual(sorted(loader._by_uuid.keys()), sorted(all_uuids))
        self.assertEqual(sorted(loader._by_reflabel.keys()), sorted(all_reflabels))


class TestJsonFiles(unittest.TestCase):
    def test_strict_json(self):
        """Tests that the templates are strict JSON: no duplicated keys, no NaN/Infinity."""

        def reject_duplicates(pairs):
            keys = [k for k, _ in pairs]
            duplicates = [k for k in keys if keys.count(k) > 1]
            self.assertEqual(duplicates, [])
            return dict(pairs)

        def reject_constant(name):
            self.fail(f"non-standard JSON constant: {name}")

        for path in sorted(glob.glob("json/*.json")):
            with self.subTest(path=path), open(path) as f:
                json.load(f, object_pairs_hook=reject_duplicates,
                          parse_constant=reject_constant)

    def test_schema(self):
        """Tests that every template matches schema/template.schema.json."""
        with open("schema/template.schema.json") as f:
            schema = json.load(f)
        validator_cls = validator_for(schema)
        validator_cls.check_schema(schema)
        validator = validator_cls(schema)
        for path in sorted(glob.glob("json/*.json")):
            with self.subTest(path=path), open(path) as f:
                errors = [
                    f"{e.json_path}: {e.message}"
                    for e in validator.iter_errors(json.load(f))
                ]
                self.assertEqual(errors, [])


if __name__ == '__main__':
    unittest.main()
