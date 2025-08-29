# logs_generator.py

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
```

---

## Quick start

```bash
# 100 text logs to stdout (default)
python logs_generator.py

# 1,000 JSONL logs to a file
python logs_generator.py -n 1000 -f jsonl -o logs.jsonl

# 500 logs with 25% chance of fake PII
python logs_generator.py -n 500 -r 0.25

# Reproducible output using a seed
python logs_generator.py -n 50 --seed 42
```

---

## Command-line usage

```bash
python logs_generator.py [OPTIONS]
```

### Options

| Option | Long | Type | Default | Description |
|---|---|---|---|---|
| `-n` | `--count` | int | `100` | Number of log lines to generate. |
| `-r` | `--pii-rate` | float | `0.1` | Fraction of logs that include *fake* PII (`0.0`–`1.0`). |
| `-f` | `--format` | choice | `text` | Output format: `text` or `jsonl` (one JSON object per line). |
| `-o` | `--outfile` | str | `-` | Output file path or `-` for stdout. |
|  | `--seed` | int | `None` | Random seed for reproducibility. |

**Exit codes**  
- Returns non‑zero if `--pii-rate` is outside `[0.0, 1.0]` or on unexpected errors.

---

## Examples

### 1) Text format (stdout)
```bash
python logs_generator.py -n 2 -f text
```
Example output (wrapped for readability):
```
2025-05-18T12:34:56.789Z INFO  svc=search req_id=abc123... sid=QwErTy... ip=203.0.113.7 GET /api/v1/search status=200 latency_ms=87 bytes=2456 ua="Mozilla/5.0 ..." pii=False msg="GET /api/v1/search -> 200 in 87ms"
2025-05-18T12:34:55.432Z ERROR svc=orders req_id=def456... sid=AsDfGh... ip=2001:db8:85a3:... POST /api/v1/orders status=500 latency_ms=421 bytes=4096 ua="curl/8.1.2" pii=True msg="NullReference in orders.handler at orders.py:317 | user=Alex Johnson email=alex.johnson@synthetic.dev phone=+1 555-123-4567"
```

### 2) JSONL format (file)
```bash
python logs_generator.py -n 2 -f jsonl -o logs.jsonl
head -n 2 logs.jsonl
```
Example output (one JSON per line):
```json
{"timestamp":"2025-05-18T12:34:56.789Z","level":"INFO","service":"search","remote_addr":"203.0.113.7","method":"GET","path":"/api/v1/search","status":200,"latency_ms":87,"response_bytes":2456,"user_agent":"Mozilla/5.0 ...","request_id":"abc123...","session_id":"QwErTy...","pii":false,"message":"GET /api/v1/search -> 200 in 87ms"}
{"timestamp":"2025-05-18T12:34:55.432Z","level":"ERROR","service":"orders","remote_addr":"2001:db8:85a3:...","method":"POST","path":"/api/v1/orders","status":500,"latency_ms":421,"response_bytes":4096,"user_agent":"curl/8.1.2","request_id":"def456...","session_id":"AsDfGh...","pii":true,"pii_details":{"name":"Alex Johnson","email":"alex.johnson@synthetic.dev","phone":"+1 555-123-4567","address":"123 Elm St, Springfield","payment_card":"4xxx-xxxx-xxxx-xxxx"},"message":"NullReference in orders.handler at orders.py:317 | user=Alex Johnson email=alex.johnson@synthetic.dev phone=+1 555-123-4567"}
```

---

## Useful pipelines

### Filter by HTTP status with `jq`
```bash
python logs_generator.py -n 1000 -f jsonl | jq 'select(.status >= 500)'
```

### Extract latency histogram (JSONL)
```bash
python logs_generator.py -n 10000 -f jsonl | jq -r '.latency_ms' | awk '{bucket=int($1/50)*50; h[bucket]++} END{for (b in h) printf "%d-%d ms: %d
", b, b+49, h[b]}'
```

### Send to `logger` / syslog
```bash
python logs_generator.py -n 200 | logger -t synthetic-logs
```

### Tail-like behavior
```bash
# Generate continuously (press Ctrl+C to stop)
while true; do python logs_generator.py -n 50 --seed $RANDOM; sleep 1; done
```

---

## Programmatic use (import)

Although designed as a CLI tool, you can import selected helpers:

```python
from logs_generator import generate_logs

# 10 jsonl strings with 5% PII
for line in generate_logs(count=10, pii_rate=0.05, fmt="jsonl", seed=123):
    print(line)
```

---

## Data model (JSONL)

Top-level fields include:
- `timestamp` (ISO8601, UTC, ms precision)
- `level` (`DEBUG`|`INFO`|`WARN`|`ERROR`)
- `service` (e.g., `auth`, `orders`, `search`, ...)
- `remote_addr` (IPv4 or IPv6)
- `method`, `path`, `status`, `latency_ms`, `response_bytes`
- `user_agent`, `request_id`, `session_id`
- `pii` (boolean), and when `true`: `pii_details` with `name`, `email`, `phone`, `address`, `payment_card`
- `message` (human-readable one-liner)
