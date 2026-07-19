# SysML v2 AST Toolchain (headless, real) -- reproducible recipe

Turns a `.sysml` source into a genuine OMG-Systems-Modeling-API AST JSON with **no
Eclipse GUI and no Jupyter**. This is what makes the demonstrator's AST a real
tool-export (not hand-authored). Stood up + proven 2026-07-18.

**Key simplification:** the Pilot needs NO Maven / per-jar resolution. The official
release ships a single fat jar bundling all dependencies, plus a version-matched
`sysml.library/`. We use release `2026-05`, kernel `0.60.1`.

## Toolchain (user-provided; set these once)

The SysML v2 pilot + Java 21 are user-provided; point the placeholders below at your install.

```
TOOLS="$HOME/tools/sysml"          # wherever you unpack the pilot + build ASTGenerator
JDK21="$HOME/tools/jdk-21"          # a Java 21 home (e.g. an Adoptium/Temurin 21 tarball)
JAR="$TOOLS/jupyter-sysml-kernel-0.60.1-all.jar"   # the pilot release fat jar
LIB="$TOOLS/sysml.library"          # the version-matched standard library from the same release
ASTGEN="$TOOLS/astgen"              # compiled-classes output dir for org.stu.ast.ASTGenerator
```

- Pilot fat jar (`$JAR`): the single all-in-one jar from the SysML v2 pilot release (`2026-05`,
  kernel `0.60.1`) -- bundles all dependencies, so no Maven is needed.
- ASTGenerator source (pattern credit: max-thoma/semantic-tag-utility, BSD-3):
  `.../semantic-tag-utility/semantic_tag_utility/ci/org/stu/ast/ASTGenerator.java`.

## Compile (once)

```
"$JDK21/bin/javac" -cp "$JAR" -d "$ASTGEN" /path/to/ASTGenerator.java
```

## Run (any model -> AST JSON)

Args: `[0]=stdlib dir  [1]=tag-lib .sysml  [2]=model .sysml  [3]=package name  [4]=out .json`.
If the model uses no tags, pass a 0-byte file as arg 1. Runtime ~2 s; the log4j
"no appenders" stderr lines are harmless.

```
"$JDK21/bin/java" -Dfile.encoding=UTF-8 \
  -cp "$ASTGEN:$JAR" org.stu.ast.ASTGenerator \
  "$LIB" /path/to/tags.sysml /path/to/Model.sysml ModelPackageName /path/to/out.ast.json
```

## AST shape (0.60.1)

A compact single-line JSON **array of element envelopes**:
`{ "identity": {"@id": <uuid>}, "payload": { "@type": <Metaclass>, "elementId": <uuid>,
"qualifiedName": ..., "name": ..., ...full API metamodel fields... } }`.
NOTE: `@type`/`elementId` live INSIDE `payload`, and only the exported package's own
elements are serialized (referenced library elements appear as `@id` refs). The
`gen-jsonld` / `ast_to_jsonld` enrichment (Task 6) must read the `payload` envelope --
verify this shape against the tag-utility's expected input, which was written against an
earlier release.
