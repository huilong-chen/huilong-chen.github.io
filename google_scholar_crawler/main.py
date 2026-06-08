from scholarly import scholarly, ProxyGenerator
import json
import sys
import os
import urllib.request
from datetime import datetime

SCHOLAR_ID = os.environ['GOOGLE_SCHOLAR_ID']
REPO = os.environ.get('GITHUB_REPOSITORY', '')
MIN_CITATIONS = 360
os.makedirs('results', exist_ok=True)


def normalize_count(value):
    """Apply a floor: if value is a number, return max(value, MIN); otherwise return MIN."""
    try:
        return max(int(value), MIN_CITATIONS)
    except (ValueError, TypeError):
        return MIN_CITATIONS


def write_shieldsio(message):
    data = {"schemaVersion": 1, "label": "citations", "message": str(message)}
    with open('results/gs_data_shieldsio.json', 'w') as f:
        json.dump(data, f, ensure_ascii=False)


def fetch_previous_count():
    """Pull last successful citation count from the google-scholar-stats branch."""
    if not REPO:
        return None
    url = f"https://raw.githubusercontent.com/{REPO}/google-scholar-stats/gs_data_shieldsio.json"
    try:
        with urllib.request.urlopen(url, timeout=10) as f:
            msg = json.load(f).get('message', '')
        if msg and msg.lower() not in ('n/a', 'na', ''):
            return msg
    except Exception as e:
        print(f"no previous count available: {e}", file=sys.stderr)
    return None


def try_fetch():
    pg = ProxyGenerator()
    if pg.FreeProxies():
        scholarly.use_proxy(pg)
    author = scholarly.search_author_id(SCHOLAR_ID)
    scholarly.fill(author, sections=['basics', 'indices', 'counts', 'publications'])
    author['updated'] = str(datetime.now())
    author['publications'] = {v['author_pub_id']: v for v in author['publications']}
    return author


def try_fetch_with_retries(max_attempts=3):
    last_err = None
    for attempt in range(1, max_attempts + 1):
        try:
            return try_fetch()
        except Exception as e:
            last_err = e
            print(f"attempt {attempt}/{max_attempts} failed: {e}", file=sys.stderr)
    raise last_err


try:
    author = try_fetch_with_retries()
    print(json.dumps(author, indent=2, default=str))
    with open('results/gs_data.json', 'w') as f:
        json.dump(author, f, ensure_ascii=False, default=str)
    final = normalize_count(author['citedby'])
    write_shieldsio(final)
    print(f"OK: citations raw={author['citedby']}, displayed={final}")
except Exception as e:
    print(f"WARN: Google Scholar fetch failed after retries: {e}", file=sys.stderr)
    fallback = fetch_previous_count()
    if fallback is not None:
        final = normalize_count(fallback)
        print(f"falling back to previous count: raw={fallback}, displayed={final}")
        write_shieldsio(final)
    else:
        print(f"no previous count available; writing floor value {MIN_CITATIONS}")
        write_shieldsio(MIN_CITATIONS)
    sys.exit(0)
