# Resume CLI (no Poetry)

Requires Python 3.11+; no external dependencies.

Run:

```bash
python3 main.py
```

`roles.json` stores each role as an ID-to-technology mapping.
For each experience or project, select only technologies you actually used.
Example input: `1,3,8` (or Enter for none). The CLI validates IDs, ignores repeated IDs, and writes technology names to `output/input.json`.

The generator is a mock. It returns text fragments as JSON, not AI-written resume bullets.
