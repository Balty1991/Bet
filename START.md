# Analyst Sports

Repo pentru analiză sportivă peste exporturi JSON de tip OddsHarvester.

## Instalare

```bash
pip install -e .
```

## Rulare

```bash
analyst --input examples/sample_upcoming.json --top 10 --output analysis.json
```

sau:

```bash
python -m analyst --input examples/sample_upcoming.json --output analysis.csv --output-format csv
```
