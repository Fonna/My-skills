#!/usr/bin/env python3
"""Install this skill and register its stdio MCP without rewriting unrelated TOML."""
import argparse
from datetime import datetime
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import tomllib

PACKAGE = Path(__file__).resolve().parent.parent


def render_config(original: str, node: str, bridge: Path, replace: bool = False) -> str:
    before = tomllib.loads(original)
    existing = before.get('mcp_servers', {}).get('ima')
    if existing is not None and not replace:
        raise ValueError('MCP ima already exists; inspect it and use --replace to update it')
    headers = list(re.finditer(r'(?m)^[ \t]*\[(?!\[)[^\r\n]+\][ \t]*(?:#[^\r\n]*)?\r?$', original))
    spans = []
    target = re.compile(r'''^[ \t]*\[mcp_servers\.(?:ima|"ima"|'ima')(?:\.[^\r\n]+)?\][ \t]*(?:#[^\r\n]*)?\r?$''')
    for i, header in enumerate(headers):
        if target.match(header.group()):
            spans.append((header.start(), headers[i+1].start() if i+1 < len(headers) else len(original)))
    if existing is not None and not spans:
        raise ValueError('Nonstandard ima TOML table; configure it manually instead of rewriting it')
    result = original
    for start, end in reversed(spans):
        result = result[:start] + result[end:]
    settings = {'command': node, 'args': [str(bridge)]}
    block = '[mcp_servers.ima]\ncommand = ' + json.dumps(node, ensure_ascii=False)
    block += '\nargs = ' + json.dumps([str(bridge)], ensure_ascii=False) + '\n'
    newline = '\r\n' if '\r\n' in original else '\n'
    result = result.rstrip() + newline*2 + block.replace('\n', newline)
    after = tomllib.loads(result)
    after['mcp_servers'].pop('ima')
    expected = json.loads(json.dumps(before))
    expected.setdefault('mcp_servers', {}).pop('ima', None)
    if expected != after:
        raise ValueError('Refusing to alter unrelated TOML configuration')
    assert tomllib.loads(result)['mcp_servers']['ima'] == settings
    return result


def install(codex_home: Path, node: str, replace=False, dry_run=False):
    codex_home = codex_home.expanduser().resolve()
    destination = codex_home / 'skills' / 'ima-mcp'
    bridge = destination / 'scripts' / 'bridge.mjs'
    config = codex_home / 'config.toml'
    old = config.read_bytes() if config.exists() else b''
    updated = render_config(old.decode('utf-8-sig'), node, bridge, replace)
    if destination.exists() and destination != PACKAGE:
        try:
            marker = json.loads((destination / 'package.json').read_text(encoding='utf-8'))
        except (OSError, ValueError) as error:
            raise ValueError('Existing skill directory is not a recognized ima-mcp package') from error
        if marker.get('name') != 'ima-mcp-workbuddy-bridge':
            raise ValueError('Existing skill directory belongs to another package')
    if dry_run:
        return {'dryRun': True, 'skill': str(destination), 'config': str(config), 'node': node}
    if destination != PACKAGE:
        files = [p for p in PACKAGE.rglob('*') if p.is_file() and '__pycache__' not in p.parts]
        for source in files:
            if source.is_symlink():
                raise ValueError('Skill package must not contain symlinks')
            target = destination / source.relative_to(PACKAGE)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
    codex_home.mkdir(parents=True, exist_ok=True)
    current = config.read_bytes() if config.exists() else b''
    if current != old:
        raise ValueError('Codex configuration changed during installation; retry after reviewing it')
    backup = None
    if old:
        backup = config.with_name('config.toml.ima-backup-' + datetime.now().strftime('%Y%m%d-%H%M%S-%f'))
        backup.write_bytes(old)
    descriptor, temporary = tempfile.mkstemp(prefix='.ima-config-', dir=codex_home)
    try:
        with os.fdopen(descriptor, 'w', encoding='utf-8', newline='\n') as stream:
            stream.write(updated)
        os.replace(temporary, config)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)
    return {'installed': True, 'skill': str(destination), 'config': str(config), 'backup': str(backup) if backup else None}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--codex-home', type=Path, default=Path(os.environ.get('CODEX_HOME', str(Path.home()/'.codex'))))
    parser.add_argument('--node', help='Node.js executable; defaults to PATH discovery')
    parser.add_argument('--replace', action='store_true', help='Replace the existing ima MCP table after reviewing its configuration')
    parser.add_argument('--dry-run', action='store_true', help='Validate and show paths without writing files')
    args = parser.parse_args()
    if sys.platform != 'win32':
        parser.error('This package currently supports Windows only')
    node = shutil.which(args.node or 'node')
    if not node:
        parser.error('Install Node.js 22+ or provide --node with its executable path')
    version = subprocess.run([node, '--version'], capture_output=True, text=True, timeout=10, check=True).stdout.strip()
    if int(version.lstrip('v').split('.')[0]) < 22:
        parser.error('Node.js 22+ is required')
    try:
        print(json.dumps(install(args.codex_home, str(Path(node).resolve()), args.replace, args.dry_run), ensure_ascii=False))
    except (ValueError, OSError) as error:
        parser.exit(1, str(error)+'\n')


if __name__ == '__main__':
    main()
