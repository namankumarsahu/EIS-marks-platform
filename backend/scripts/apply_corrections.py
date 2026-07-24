"""Loops over corrections.json and POSTs each record to
/api/marks/corrections/. Run the Django dev server first.

Usage:
    python scripts/apply_corrections.py [path/to/corrections.json] [api_base_url]

Defaults to data/corrections.json and http://127.0.0.1:8000/api.
"""

import json
import sys
import urllib.error
import urllib.request


def apply_corrections(corrections_path, api_base_url):
    with open(corrections_path, encoding="utf-8") as f:
        corrections = json.load(f)

    results = []
    url = f"{api_base_url.rstrip('/')}/marks/corrections/"

    for record in corrections:
        body = json.dumps(record).encode("utf-8")
        request = urllib.request.Request(
            url, data=body, headers={"Content-Type": "application/json"}, method="POST"
        )
        try:
            with urllib.request.urlopen(request) as response:
                results.append((record, response.status, json.loads(response.read())))
        except urllib.error.HTTPError as exc:
            results.append((record, exc.code, json.loads(exc.read())))
    return results


if __name__ == "__main__":
    corrections_path = sys.argv[1] if len(sys.argv) > 1 else "data/corrections.json"
    api_base_url = sys.argv[2] if len(sys.argv) > 2 else "http://127.0.0.1:8000/api"

    for record, status_code, payload in apply_corrections(corrections_path, api_base_url):
        marker = "OK " if status_code == 200 else "FAIL"
        print(f"[{marker}] {status_code} {record} -> {payload}")
