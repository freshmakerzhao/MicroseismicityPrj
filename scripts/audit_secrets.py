"""Read-only Git credential scan. Reports paths/types, never secret values.

This is a pattern scan, not proof that business data is safe to publish.
"""
import argparse
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PATTERNS = {
    'private key': rb'-----BEGIN (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----',
    'GitHub token': rb'\b(?:gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{40,})\b',
    'AWS access key': rb'\b(?:AKIA|ASIA)[A-Z0-9]{16}\b',
    'API secret token': rb'\bsk-(?:proj-|ant-)?[A-Za-z0-9_-]{32,}\b',
    'Slack token': rb'\bxox[baprs]-[A-Za-z0-9-]{20,}\b',
    'credential URL': rb'https?://[^\s/:"<>]{1,80}:[^\s/@"<>]{4,}@',
}
SENSITIVE_PATH = re.compile(r'(^|/)(\.env(?:\..+)?|users\.json|[^/]+\.(?:db|sqlite3?|pem|p12|pfx|key))$')


def git(*args):
    return subprocess.check_output(['git', *args], cwd=ROOT)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--history', action='store_true')
    args = parser.parse_args()
    if args.history:
        objects = []
        for line in git('rev-list', '--objects', '--all').decode('utf-8').splitlines():
            sha, _, path = line.partition(' ')
            objects.append((sha, path))
    else:
        objects = []
        for entry in git('ls-tree', '-rz', 'HEAD').split(b'\0'):
            if entry:
                meta, path = entry.split(b'\t', 1)
                objects.append((meta.split()[2].decode(), path.decode('utf-8')))
    process = subprocess.Popen(['git', 'cat-file', '--batch'], cwd=ROOT,
                               stdin=subprocess.PIPE, stdout=subprocess.PIPE)
    findings = set()
    count = 0
    for sha, path in objects:
        process.stdin.write((sha + '\n').encode())
        process.stdin.flush()
        header = process.stdout.readline().split()
        size = int(header[2])
        content = process.stdout.read(size)
        process.stdout.read(1)
        if header[1] != b'blob':
            continue
        count += 1
        if SENSITIVE_PATH.search(path) and not path.endswith('.example'):
            findings.add((path, 'credential/store file'))
        if path == 'scripts/audit_secrets.py':
            continue  # Pattern definitions themselves are not credentials.
        for label, pattern in PATTERNS.items():
            if re.search(pattern, content):
                findings.add((path, label))
    process.stdin.close()
    process.wait()
    for path, label in sorted(findings):
        print(f'{label}: {path}')
    print(f'Scanned {count} blobs; {len(findings)} path/type findings.')
    return 1 if findings else 0


if __name__ == '__main__':
    raise SystemExit(main())
