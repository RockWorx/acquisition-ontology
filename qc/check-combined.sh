#!/usr/bin/env bash
# Combined ELK consistency pass (Red Team N1): the SysML-link demo A-Box (model instances +
# the derived program risk/assessment) reasoned against the FULL T-Box -- base + transform +
# bridge + BFO 2020 + CCO 2.1 + IAO -- fully offline via import-catalog.xml.
#
# Prereqs: run setup-offline-imports.sh first; ROBOT on PATH; a Python with rdflib + pySHACL.
#   export PYTHON=/path/to/venv/bin/python   ROBOT=/path/to/robot
# Self-contained: run_demo.py is loaded BY FILE PATH from this release (<release>/sysml_link/,
# beside qc/); no package import and no dependency outside this repository.
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
PYTHON="${PYTHON:-python}"
ROBOT="${ROBOT:-robot}"
DEMO="$HERE/../sysml_link/run_demo.py"
if [ ! -f "$DEMO" ]; then
  echo "check-combined: run_demo.py not found at $DEMO (expected <release>/sysml_link/ beside qc/)" >&2
  exit 2
fi
OUT="$(mktemp -d)"
trap 'rm -rf "$OUT"' EXIT

"$PYTHON" - "$DEMO" "$OUT/rwx-check.ttl" <<'PY'
import importlib.util
import sys
from rdflib import RDF, URIRef
from rdflib.namespace import OWL

spec = importlib.util.spec_from_file_location("sysml_link_run_demo", sys.argv[1])
run_demo = importlib.util.module_from_spec(spec)
spec.loader.exec_module(run_demo)
g = run_demo.derive_risk(run_demo.load_model())
onto = URIRef("https://w3id.org/rockworx/demo/check")
g.add((onto, RDF.type, OWL.Ontology))
for module in ("https://w3id.org/rockworx/acq",
               "https://w3id.org/rockworx/acq/transform",
               "https://w3id.org/rockworx/acq/sysml"):
    g.add((onto, OWL.imports, URIRef(module)))
g.serialize(destination=sys.argv[2], format="turtle")
PY

"$ROBOT" reason --reasoner ELK --catalog "$HERE/import-catalog.xml" \
  --input "$OUT/rwx-check.ttl" --output "$OUT/rwx-combined-reasoned.ttl"
echo "Combined A-Box + full T-Box: ELK-consistent (exit 0, 0 unsatisfiable classes)."
