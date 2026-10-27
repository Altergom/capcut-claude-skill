"""Download the official CapCut Codex plugin bundle into ../official/.

The official material is CapCut's (license: UNLICENSED), so it is not
redistributed in this repository; this script fetches it from CapCut's CDN.

usage: python fetch_official.py [--force]
"""
import io
import json
import os
import re
import shutil
import sys
import urllib.request
import zipfile

INSTALL_SKILL_URL = 'https://sf16-sg.tiktokcdn.com/obj/eden-sg/962370eh7nupenuhbo/capcut_codex_plugin/SKILL.md'
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
DEST = os.path.join(ROOT, 'official')


def fetch(url):
    req = urllib.request.Request(url, headers={'User-Agent': 'capcut-claude-skill'})
    with urllib.request.urlopen(req, timeout=120) as r:
        return r.read()


def main():
    if os.path.isdir(DEST) and os.listdir(DEST) and '--force' not in sys.argv:
        print('official/ already exists; pass --force to refresh it')
        return
    install_md = fetch(INSTALL_SKILL_URL).decode('utf-8')
    version = re.search(r'plugin-version:\s*"?([\w.\-]+)', install_md)
    zip_url = re.search(r'https://\S+?\.zip', install_md)
    if not zip_url:
        raise SystemExit('could not find the plugin bundle URL in ' + INSTALL_SKILL_URL)
    print('plugin version:', version.group(1) if version else 'unknown')
    print('downloading', zip_url.group(0))
    bundle = zipfile.ZipFile(io.BytesIO(fetch(zip_url.group(0))))

    tmp = DEST + '.tmp'
    shutil.rmtree(tmp, ignore_errors=True)
    os.makedirs(tmp)
    prefix = 'plugins/codex/'
    for name in bundle.namelist():
        if not name.startswith(prefix) or name.endswith('/') or '__MACOSX' in name or name.endswith('.DS_Store'):
            continue
        rel = name[len(prefix):]
        if rel.startswith('skills/'):
            rel = rel[len('skills/'):]
        elif rel == '.mcp.json':
            rel = 'plugin-mcp.json'
        elif rel == '.codex-plugin/plugin.json':
            rel = 'plugin.json'
        else:
            continue
        # Nested SKILL.md files would be loaded by Claude as separate (Codex-only) skills.
        if os.path.basename(rel) == 'SKILL.md':
            rel = os.path.join(os.path.dirname(rel), 'SKILL.official.md')
        out = os.path.join(tmp, rel)
        os.makedirs(os.path.dirname(out), exist_ok=True)
        data = bundle.read(name)
        if out.endswith('.md'):
            data = data.decode('utf-8').replace('SKILL.md', 'SKILL.official.md').encode('utf-8')
        open(out, 'wb').write(data)
    open(os.path.join(tmp, 'INSTALL-codex.md'), 'w', encoding='utf-8').write(install_md.replace('SKILL.md', 'SKILL.official.md'))

    shutil.rmtree(DEST, ignore_errors=True)
    os.replace(tmp, DEST)
    count = sum(len(f) for _, _, f in os.walk(DEST))
    print('installed %d files into %s' % (count, DEST))


if __name__ == '__main__':
    main()
