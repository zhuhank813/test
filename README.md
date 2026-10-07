# Football decision lab

A reproducible, synthetic American football fourth-down analysis in Python.
All data and possession values are simulated; no real NFL data or calibrated EPA.

## Run

Python 3.10+; no external dependencies:

```bash
python analysis.py
```

Read [the Chinese report](REPORT.md), or download and open `report.html` for a self-contained offline version.

- `synthetic_plays.csv`: 12,000 generated fourth-down situations.
- `analysis.py`: data generation, analysis, checks and SVG/HTML authoring.
- `summary.json`: machine-readable findings.
- Three SVG charts: decision map, downside risk, and conversion luck.

The simulation is an educational experiment, not an NFL tactical recommendation.
