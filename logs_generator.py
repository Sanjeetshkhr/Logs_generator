"""
logs_generator.py

"""

import argparse
import json
import os
import random
import string
import sys
from datetime import datetime, timedelta

LEVELS = ["DEBUG", "INFO", "WARN", "ERROR"]
SERVICES = ["auth", "billing", "gateway", "catalog", "orders", "search", "notifications"]
METHODS = ["GET", "POST", "PUT", "PATCH", "DELETE"]
PATHS = [
    "/api/v1/login", "/api/v1/logout", "/api/v1/users", "/api/v1/users/{id}",
    "/api/v1/orders", "/api/v1/orders/{id}", "/api/v1/catalog/items",
    "/healthz", "/metrics", "/api/v1/search"
]
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124.0.0.0 Safari/537.36",
    "curl/8.1.2", "okhttp/4.11.0", "PostmanRuntime/7.35.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_5) AppleWebKit/605.1.15 Version/16.5 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) Gecko/20100101 Firefox/126.0"
]
STATUS_CHOICES = [200, 200, 200, 201, 204, 301, 302, 400, 401, 403, 404, 409, 422, 429, 500, 502, 503]
FIRST_NAMES = ["Alex", "Jordan", "Taylor", "Casey", "Riley", "Avery", "Morgan", "Sam", "Jamie", "Cameron"]
LAST_NAMES = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Miller", "Davis", "Garcia", "Clark", "Lopez"]
STREETS = ["Oak St", "Maple Ave", "Cedar Rd", "Pine Ln", "Birch Blvd", "Willow Way", "Elm St"]
CITIES = ["Springfield", "Riverton", "Lakeside", "Fairview", "Greenville", "Kingston", "Georgetown"]
DOMAINS = ["example.com", "mail.test", "synthetic.dev", "no-reply.fake"]
ERROR_TEMPLATES = [
    "NullReference in {service}.handler at {file}:{line}",
    "Timeout connecting to {dependency}: operation=upstream_call",
    "Failed to deserialize JSON: unexpected token near '{token}'",
    "Permission denied for user={user} on resource={path}",
    "Deadletter processing failed: message_id={msgid}"
]

def rand_ts(now=None, jitter_seconds = 600):
    now = now or datetime.utcnow()
    return (now - timedelta(seconds=random.randint(0, jitter_seconds))).isoformat(timespec="milliseconds") + "Z"

def rand_ip():
    return ".".join(str(random.randint(1, 254)) for _ in range(4))

def rand_ipv6():
    return ":".join("".join(random.choices("0123456789abcdef", k=4)) for _ in range(8))

def rand_request_id():
    return "".join(random.choices(string.ascii_lowercase + string.digits, k=16))

def rand_session_id():
    return "".join(random.choices(string.ascii_letters + string.digits, k=24))

def choose_path():
    p = random.choice(PATHS)
    if "{id}" in p:
        return p.replace("{id}", str(random.randint(1000, 9999)))
    return p

def rand_name():
    return f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"

def rand_email(name=None):
    if not name:
        name = rand_name()
    handle = name.lower().replace(" ", ".")
    return f"{handle}@{random.choice(DOMAINS)}"

def rand_phone():
    # Simple international-ish format: +<country><area><number>
    return f"+{random.randint(1, 99)} {random.randint(100,999)}-{random.randint(100,999)}-{random.randint(1000,9999)}"

def rand_address():
    return f"{random.randint(10, 9999)} {random.choice(STREETS)}, {random.choice(CITIES)}"

def rand_token(n=12):
    return "".join(random.choices(string.ascii_lowercase + string.digits, k=n))

def maybe_ipv6():
    return rand_ipv6() if random.random() < 0.1 else rand_ip()

def build_pii_payload():
    name = rand_name()
    return {
        "name": name,
        "email": rand_email(name),
        "phone": rand_phone(),
        "address": rand_address(),
        # A clearly fake card-like string (does NOT guarantee Luhn validity; for safety, do not treat as real)
        "payment_card": f"{random.randint(4000,4999)}-{random.randint(1000,9999)}-{random.randint(1000,9999)}-{random.randint(1000,9999)}"
    }

def build_log(with_pii=False, fmt="text", now=None):
    ts = rand_ts(now)
    level = random.choices(LEVELS, weights=[0.1, 0.55, 0.2, 0.15])[0]
    service = random.choice(SERVICES)
    ip = maybe_ipv6()
    method = random.choice(METHODS)
    path = choose_path()
    status = random.choice(STATUS_CHOICES)
    latency_ms = max(1, int(random.gauss(120, 80)))
    ua = random.choice(USER_AGENTS)
    req_id = rand_request_id()
    sess_id = rand_session_id()
    size = max(128, int(abs(random.gauss(2048, 1500))))

    base = {
        "timestamp": ts,
        "level": level,
        "service": service,
        "remote_addr": ip,
        "method": method,
        "path": path,
        "status": status,
        "latency_ms": latency_ms,
        "response_bytes": size,
        "user_agent": ua,
        "request_id": req_id,
        "session_id": sess_id,
        "pii": with_pii
    }

    # Message content
    if level in ("ERROR", "WARN") and random.random() < 0.6:
        tmpl = random.choice(ERROR_TEMPLATES)
        msg = tmpl.format(
            service=service,
            file=f"{service}.py",
            line=random.randint(10, 400),
            dependency=random.choice(SERVICES),
            token=random.choice(["{", "}", ":", ",", "]"]),
            user=rand_email(),
            path=path,
            msgid=rand_token(10)
        )
    elif method == "POST" and status in (200, 201):
        msg = f"Handled {method} {path} in {latency_ms}ms (status={status})"
    else:
        msg = f"{method} {path} -> {status} in {latency_ms}ms"

    if with_pii:
        pii = build_pii_payload()
        base["pii_details"] = pii
        # Also embed some PII inline in message for text flavor
        msg += f" | user={pii['name']} email={pii['email']} phone={pii['phone']}"

    base["message"] = msg

    if fmt == "jsonl":
        return json.dumps(base, ensure_ascii=False)
    else:
        # Text format resembling structured server logs
        parts = [
            f"{base['timestamp']}",
            f"{base['level']:<5}",
            f"svc={service}",
            f"req_id={req_id}",
            f"sid={sess_id}",
            f"ip={ip}",
            f"{method} {path}",
            f"status={status}",
            f"latency_ms={latency_ms}",
            f"bytes={size}",
            f'ua="{ua}"',
            f"pii={with_pii}",
            f"msg=\"{msg}\""
        ]
        return " ".join(parts)

def generate_logs(count, pii_rate, fmt, seed=None, now=None):
    if seed is not None:
        random.seed(seed)
    now = now or datetime.utcnow()
    for i in range(count):
        with_pii = random.random() < pii_rate
        yield build_log(with_pii=with_pii, fmt="jsonl" if fmt == "jsonl" else "text", now=now)

def parse_args():
    p = argparse.ArgumentParser(description="Generate synthetic server-style logs with optional PII.")
    p.add_argument("-n", "--count", type=int, default=100, help="Number of log lines to generate.")
    p.add_argument("-r", "--pii-rate", type=float, default=0.1, help="Fraction of logs that include PII (0.0 - 1.0).")
    p.add_argument("-f", "--format", choices=["text", "jsonl"], default="text", help="Output format: text or jsonl (one JSON object per line).")
    p.add_argument("-o", "--outfile", type=str, default="-", help="Output file path or '-' for stdout.")
    p.add_argument("--seed", type=int, default=None, help="Random seed for reproducibility.")
    return p.parse_args()

def main():
    args = parse_args()
    if not (0.0 <= args.pii_rate <= 1.0):
        raise SystemExit("--pii-rate must be between 0.0 and 1.0")

    out = sys.stdout if args.outfile == "-" else open(args.outfile, "w", encoding="utf-8")
    try:
        for line in generate_logs(args.count, args.pii_rate, args.format, seed=args.seed):
            out.write(line + os.linesep)
    finally:
        if out is not sys.stdout:
            out.close()

if __name__ == "__main__":
    main()