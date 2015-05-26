"""JSON Schema utilities

Attributes:
    _cache: Cache of previously loaded schemas

Resources:
    http://json-schema.org/
    http://json-schema.org/latest/json-schema-core.html
    http://spacetelescope.github.io/understanding-json-schema/index.html

"""

import os
import json

from vendor import jsonschema

_cache = {}
module_dir = os.path.dirname(__file__)
schema_dir = os.path.join(module_dir, "schema")


def load(schema):
    if schema not in _cache:
        path = os.path.join(module_dir, "schema",
                            "%s.json" % schema)
        with open(path, "r") as f:
            _cache[schema] = f.read()

    return json.loads(_cache[schema])


def validate(data, schema):
    if isinstance(schema, basestring):
        schema = load(schema)

    base_uri = "file:///%s/" % schema_dir.replace("\\", "/")
    resolver = jsonschema.RefResolver(base_uri, None, cache_remote=True)
    return jsonschema.validate(data, schema, types={"array": (list, tuple)},
                               resolver=resolver)


ValidationError = jsonschema.ValidationError

__all__ = ["validate",
           "ValidationError"]


if __name__ == '__main__':
    data = {
        "success": True,
        "instance": {
            "name": "MyName",
            "data": {
                "family": "MyFamily"
            }
        },
        "plugin": {
            "name": "string",
            "data": {
                "families": ["family"]
            }
        },
        "error": {
            "message": "My message"
        }
    }

    validate(data, "result")
