"""Fake ESP32 - lets you demo the whole system without hardware.

    python scripts/simulate_device.py --scenario fault --count 40 --interval 0.5
Scenarios: normal | fault (temperature climbs, voltage sags, oil drops) | off
"""
import argparse
import json
import random
import time
import urllib.error
import urllib.request


def make_reading(scenario: str, step: int, count: int) -> dict:
    progress = step / max(count - 1, 1)
    if scenario == "off":
        return {"temperature": 28, "voltage": 0, "current": 0, "oil": 5}
    temp, volt, cur, oil_pct = 32, 12.2, 1.3, 80
    if scenario == "fault":
        temp += 60 * progress
        volt -= 4 * progress
        cur += 3.2 * progress
        oil_pct -= 70 * progress
    noise = lambda s: random.uniform(-s, s)  # noqa: E731
    tank = 30
    return {
        "temperature": round(temp + noise(0.8), 1),
        "voltage": round(volt + noise(0.1), 2),
        "current": round(cur + noise(0.05), 2),
        "oil": round(tank * (1 - (oil_pct + noise(1)) / 100), 1),  # distance to oil surface, cm
    }


def post(url: str, api_key: str, payload: dict) -> tuple[int, dict]:
    req = urllib.request.Request(
        url, data=json.dumps(payload).encode(), method="POST",
        headers={"Content-Type": "application/json", "X-API-Key": api_key},
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as res:
            return res.status, json.load(res)
    except urllib.error.HTTPError as err:
        return err.code, json.load(err)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--base-url", default="http://127.0.0.1:5000")
    ap.add_argument("--api-key", default="")
    ap.add_argument("--transformer-id", type=int, default=1)
    ap.add_argument("--scenario", choices=["normal", "fault", "off"], default="normal")
    ap.add_argument("--count", type=int, default=30)
    ap.add_argument("--interval", type=float, default=1.0)
    args = ap.parse_args()

    url = f"{args.base_url}/api/v1/transformers/{args.transformer_id}/readings"
    for i in range(args.count):
        status, body = post(url, args.api_key, make_reading(args.scenario, i, args.count))
        r = body.get("reading", {})
        print(f"[{i + 1}/{args.count}] HTTP {status} -> {r.get('status', body)}  {r.get('reasons', '')}")
        time.sleep(args.interval)


if __name__ == "__main__":
    main()
