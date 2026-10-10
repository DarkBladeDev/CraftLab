# craftlab-security

Canonical security event contract, universal data sanitization, and WAL-mode SQLite audit persistence for the CraftLab monorepo.

---

## Monorepo Installation

To install in editable development or release mode:

```bash
pip install -e packages/craftlab_security
```

## Package Structure

- `src/craftlab_security/models.py`: Canonical security event models (`SecurityEvent`, enums).
- `src/craftlab_security/sanitizer.py`: Universal data sanitizer (`DataSanitizer`).
- `src/craftlab_security/sink.py`: Isolated SQLite audit sink (`SecurityAuditSink`).
- `src/craftlab_security/validation.py`: Fail-fast production environment validation.

## Running Tests

```bash
pytest packages/craftlab_security/tests -v
```

## Documentation

For architecture details, integration guides, and API specifications, see:
- [CraftLab Packages Registry](../../docs/packages/README.md)
- [craftlab-security Package Documentation](../../docs/packages/craftlab-security.md)
