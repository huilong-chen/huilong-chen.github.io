from scholarly import scholarly, ProxyGenerator
import json
import sys
import os
from datetime import datetime

SCHOLAR_ID = os.environ['GOOGLE_SCHOLAR_ID']
os.makedirs('results', exist_ok=True)


def write_shieldsio(message):
    data = {"schemaVersion": 1, "label": "citations", "message": str(message)}
    with open('results/gs_data_shieldsio.json', 'w') as f:
        json.dump(data, f, ensure_ascii=False)


def try_fetch():
    pg = ProxyGenerator()
    if pg.FreeProxies():
        scholarly.use_proxy(pg)
    author = scholarly.search_author_id(SCHOLAR_ID)
    scholarly.fill(author, sections=['basics', 'indices', 'counts', 'publications'])
    author['updated'] = str(datetime.now())
    author['publications'] = {v['author_pub_id']: v for v in author['publications']}
    return author


try:
    author = try_fetch()
    print(json.dumps(author, indent=2, default=str))
    with open('results/gs_data.json', 'w') as f:
        json.dump(author, f, ensure_ascii=False, default=str)
    write_shieldsio(author['citedby'])
    print(f"OK: citations = {author['citedby']}")
except Exception as e:
    print(f"WARN: Google Scholar fetch failed: {e}", file=sys.stderr)
    # graceful fallback: keep an "N/A" badge so the workflow doesn't fail outright
    write_shieldsio("N/A")
    sys.exit(0)
