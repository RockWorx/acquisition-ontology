#!/usr/bin/env bash
# Combined ELK consistency pass (Red Team N1): the SysML-link demo A-Box (model instances +
# the derived program risk/assessment) reasoned against the FULL T-Box -- base + transform +
# bridge + BFO 2020 + CCO 2.1 + IAO -- fully offline via import-catalog.xml.
#
# Prereqs: run setup-offline-imports.sh first; ROBOT on PATH; a Python with rwx importable.
#   export PYTHON=/path/to/venv/bin/python   ROBOT=/path/to/robot
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
REPO="$(cd "$HERE/.." && pwd)"
PYTHON="${PYTHON:-python}"
ROBOT="${ROBOT:-robot}"

"$PYTHON" - "$REPO" <<'PY'
import sys
sys.path.insert(0, sys.argv[1])
from rdflib import RDF, URIRef
from rdflib.namespace import OWL
from sysml_link.run_demo import derive_risk, load_model

g = derive_risk(load_model())
onto = URIRef("https://w3id.org/rockworx/demo/check")
g.add((onto, RDF.type, OWL.Ontology))
for module in ("https://w3id.org/rockworx/acq",
               "https://w3id.org/rockworx/acq/transform",
               "https://w3id.org/rockworx/acq/sysml"):
    g.add((onto, OWL.imports, URIRef(module)))
g.serialize(destination="/tmp/rwx-check.ttl", format="turtle")
PY

"$ROBOT" reason --reasoner ELK --catalog "$HERE/import-catalog.xml" \
  --input /tmp/rwx-check.ttl --output /tmp/rwx-combined-reasoned.ttl
echo "Combined A-Box + full T-Box: ELK-consistent (exit 0, 0 unsatisfiable classes)."
