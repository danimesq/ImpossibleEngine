# Construct reference semantic fixtures

These fixtures record semantic requirements found while studying:

- https://github.com/danimesq/Alien-Parcor
- https://github.com/danimesq/Flappy-Ramon

They are **not** input projects for the Impossible importer. In particular,
they do not make C2 XML a supported production format. Their role is to give
the ACE registry, expression parser, Selection System and runtime tests a
source-backed vocabulary.

The full original projects remain at their source repositories. No game media,
audio, fonts, addon binaries or full event-sheet source files are vendored
here. This avoids copying assets with unverified redistribution rights.

## Fixture lifecycle

1. Keep a semantic case here with its C2 source provenance.
2. Convert the full C2 project using the separately selected C2-to-C3 project
   converter.
3. Record converter repository, immutable commit/version, license, command,
   source checksum, output checksum and warnings.
4. Keep the generated C3 project as an end-to-end importer fixture in the
   appropriate test corpus, subject to source-project rights.
5. Import the C3 project, compare its typed AST/IR to the semantic case and
   report every unsupported or changed behavior.

The C2 semantic catalogue and C3 importer fixtures are deliberately different
artifacts. Do not feed this directory to the C3 importer.

See `cases.json` for the initial source-backed case index.
