"""Download original ODRE exports. Existing files are retained unless --refresh is passed."""
import argparse
from pathlib import Path
import urllib.request
import hashlib

URLS = {
    'production_brute.csv': 'https://odre.opendatasoft.com/api/explore/v2.1/catalog/datasets/prod-region-annuelle-filiere/exports/csv?use_labels=true',
    'consommation_brute.csv': 'https://odre.opendatasoft.com/api/explore/v2.1/catalog/datasets/consommation-annuelle-brute-regionale/exports/csv?use_labels=true',
}
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--data-dir', type=Path, default=Path(__file__).resolve().parent.parent / 'data')
parser.add_argument('--refresh', action='store_true', help='Replace the cached snapshot with the current online exports; numbers may change.')
args = parser.parse_args()
args.data_dir.mkdir(parents=True, exist_ok=True)
for name, url in URLS.items():
    target = args.data_dir / name
    if target.exists() and not args.refresh:
        print(f'Cached: {target}')
    else:
        request = urllib.request.Request(url, headers={'User-Agent':'Roy-Tamwo-Student-Data-Project/1.0'})
        with urllib.request.urlopen(request, timeout=60) as response:
            content = response.read()
        if not content.startswith('Année;'.encode('utf-8')):
            raise ValueError(f'The response does not look like the expected ODRE CSV: {name}')
        temp = target.with_suffix('.download')
        temp.write_bytes(content)
        temp.replace(target)
        print(f'Downloaded: {target}')
    print(f'SHA256 {hashlib.sha256(target.read_bytes()).hexdigest()}')
