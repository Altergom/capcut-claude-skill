"""Helpers around the official capcut-stdraft-builder for use from Claude.

usage:
  python -B draft_tool.py validate <draft.json>
  python -B draft_tool.py slim <draft.json> <out.json>     # short ids, one segment per line, re-validated
  python -B draft_tool.py summary <draft.json | saved tool-result file>
  python -B draft_tool.py urls <saved push_stdraft_snapshot result file>

A "saved tool-result file" is what the harness writes when an MCP result is too
large to show inline: either the raw JSON object, or a list like [{"type":"text","text":"..."}].
When a result came back inline, save it to a .json file first (or pass "-" to read stdin).
"""
import json
import os
import sys
from collections import Counter

for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding='utf-8')
    except (AttributeError, ValueError):
        pass

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'official', 'capcut-stdraft-builder', 'scripts'))


def _load_any(path):
    """Return (outer_obj, draft_dict) from a draft file or a saved tool result."""
    obj = json.load(sys.stdin if path == '-' else open(path, encoding='utf8'))
    if isinstance(obj, list) and obj and isinstance(obj[0], dict) and 'text' in obj[0]:
        obj = json.loads(obj[0]['text'])
    if isinstance(obj, dict) and 'segments' in obj:
        return obj, obj
    if isinstance(obj, dict) and obj.get('stdraft_json'):
        return obj, json.loads(obj['stdraft_json'])
    if isinstance(obj, dict) and obj.get('stdraft'):
        return obj, json.loads(obj['stdraft'])
    raise SystemExit('no STDraft found in ' + path)


def validate(draft):
    from _draft import load, finish
    model, _, _ = load(draft)
    result = finish(model, draft, [], [], [])
    check = result['check_result']
    errors = {k: v['errors'] for k, v in check['rules'].items() if v.get('errors')}
    warns = Counter(k for k, v in check['rules'].items() for _ in v.get('warnings', []))
    return check['valid'], errors, dict(warns)


def cmd_validate(path):
    _, draft = _load_any(path)
    ok, errors, warns = validate(draft)
    print('valid' if ok else 'INVALID', '| warnings per rule:', warns)
    for rule, errs in errors.items():
        for e in errs[:10]:
            print('  [%s] %s' % (rule, e))
    sys.exit(0 if ok else 1)


def cmd_slim(src, dst):
    _, draft = _load_any(src)
    mapping, counts = {}, Counter()
    for seg in draft['segments']:
        if seg['type'] == 'DRAFT':
            continue
        prefix = seg['type'][0].lower()
        counts[prefix] += 1
        mapping[seg['id']] = prefix + str(counts[prefix])
    for seg in draft['segments']:
        seg['id'] = mapping.get(seg['id'], seg['id'])
        if 'parent_id' in seg:
            seg['parent_id'] = mapping.get(seg['parent_id'], seg['parent_id'])
    order = {'DRAFT': 0, 'VIDEO': 1, 'AUDIO': 2}
    draft['segments'].sort(key=lambda s: (order.get(s['type'], 3), s.get('timeline', {}).get('start.ms', 0)))
    ok, errors, _ = validate(draft)
    if not ok:
        raise SystemExit('slimmed draft failed validation: %s' % errors)
    lines = [json.dumps(s, ensure_ascii=False, separators=(',', ':')) for s in draft['segments']]
    text = '{"version":"%s","segments":[\n%s\n]}' % (draft.get('version', '0.1.0'), ',\n'.join(lines))
    open(dst, 'w', encoding='utf8').write(text)
    print('wrote %s: %d segments, %d chars' % (dst, len(lines), len(text)))
    if len(text) > 60000:
        print('WARNING: over ~60k chars; a single push of this size is unreliable. Drop optional keyframes/styles or split the work.')


def cmd_summary(path):
    outer, draft = _load_any(path)
    segs = draft['segments']
    print('segments:', dict(Counter(s['type'] for s in segs)))
    end = max((s.get('timeline', {}).get('start.ms', 0) + s.get('timeline', {}).get('duration.ms', 0) for s in segs), default=0)
    print('timeline end: %.2fs' % (end / 1000))
    vids = [s for s in segs if s['type'] == 'VIDEO']
    print('video sources:', dict(Counter(s['attributes'].get('source', '').split('://')[0] for s in vids)),
          '| transitions:', sum('transition' in s['attributes'] for s in vids),
          '| clips with keyframes:', sum(any(k.endswith('.keyframes') for k in s.get('layout', {})) for s in vids),
          '| speeds:', dict(Counter(s['attributes'].get('speed', 1) for s in vids)))
    for t in ('AUDIO', 'COLOR_FILTER', 'VIDEO_EFFECT', 'TEXT_TEMPLATE'):
        for s in segs:
            if s['type'] == t:
                print('  %s %s %s' % (t, s['attributes'].get('source', ''), s.get('timeline', {})))
    texts = [s for s in segs if s['type'] == 'TEXT']
    print('texts:', len(texts), '| captions:', sum('caption_timeline' in s['attributes'] for s in texts))
    for s in texts[:5]:
        print('  ', s['attributes'].get('content', '')[:40], s.get('timeline', {}))
    for key in ('server_package_id', 'package_id', 'web_editor_url', 'embed_editor_url'):
        if isinstance(outer, dict) and outer.get(key):
            print(key + ':', outer[key])


def cmd_urls(path):
    outer, _ = _load_any(path)
    for key in ('server_package_id', 'web_editor_text', 'web_editor_url', 'embed_editor_url'):
        print(key + ':', outer.get(key))


if __name__ == '__main__':
    if len(sys.argv) < 3:
        raise SystemExit(__doc__)
    cmd, args = sys.argv[1], sys.argv[2:]
    {'validate': cmd_validate, 'slim': cmd_slim, 'summary': cmd_summary, 'urls': cmd_urls}[cmd](*args)
