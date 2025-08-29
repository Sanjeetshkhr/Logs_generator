# Create a README.md file for the provided logs_generator.py script
readme_content = """# logs_generator.py

Generate realistic-looking, synthetic server logs — optionally including fake PII — for demos, testing pipelines, log parsers, SIEM exercises, and performance/load scenarios.

> **Note**: All generated data is synthetic. Payment card strings are random and **not** guaranteed to pass Luhn checks. Do not treat any generated value as real PII.

---

## Features

- Text or JSON Lines (`jsonl`) output
- Configurable number of lines
- Adjustable probability of including **fake** PII fields
- Deterministic runs via `--seed`
- Built-in variety of services, endpoints, methods, user agents, status codes, and error templates
- IPv4/IPv6 mix, latency, response size, request/session IDs

---

## Requirements

- Python 3.8+ (standard library only — no extra dependencies)

---

## Installation

```bash
# Option 1: copy the script into your project
cp logs_generator.py /path/to/your/project/

# Option 2: curl or wget the raw file
curl -O https://example.com/path/to/logs_generator.py  # replace with your location
