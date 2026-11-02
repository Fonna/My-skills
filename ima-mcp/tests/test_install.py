import importlib.util
from pathlib import Path
import tempfile
import tomllib
import unittest

MODULE = Path(__file__).resolve().parents[1] / 'scripts' / 'install.py'
SPEC = importlib.util.spec_from_file_location('ima_install', MODULE)
installer = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(installer)


class InstallerTests(unittest.TestCase):
    def test_preserves_other_servers_secrets_comments_and_paths_with_spaces(self):
        source = '# keep this comment\nmodel = "example"\n[mcp_servers.other]\ncommand = "other"\nenabled = true\n[mcp_servers.other.env]\nTOKEN = "synthetic-secret"\n'
        result = installer.render_config(source, 'C:/Program Files/nodejs/node.exe', Path('C:/User With Spaces/skills/bridge.mjs'))
        self.assertTrue(result.startswith(source.rstrip()))
        before, after = tomllib.loads(source), tomllib.loads(result)
        self.assertEqual(before['mcp_servers']['other'], after['mcp_servers']['other'])

    def test_collision_requires_explicit_replacement(self):
        with self.assertRaisesRegex(ValueError, '--replace'):
            installer.render_config('[mcp_servers.ima]\nurl="https://old"\n','node',Path('bridge'))

    def test_native_windows_crlf_configuration_is_supported(self):
        source='model="example"\r\n[mcp_servers.ima]\r\nurl="old"\r\n[mcp_servers.other]\r\nenabled=true\r\n'
        result=installer.render_config(source,'node',Path('bridge'),True)
        self.assertIn('[mcp_servers.other]\r\nenabled=true',result)
        self.assertEqual(tomllib.loads(result)['mcp_servers']['ima']['command'],'node')

    def test_replacement_removes_only_ima_and_its_nested_settings(self):
        source = '[mcp_servers.ima]\nurl="old"\n[mcp_servers.ima.env]\nOLD="value"\n[mcp_servers.other]\ncommand="keep"\n'
        result = tomllib.loads(installer.render_config(source,'node',Path('bridge'),True))
        self.assertEqual(result['mcp_servers']['ima'], {'command':'node','args':['bridge']})
        self.assertEqual(result['mcp_servers']['other'], {'command':'keep'})

    def test_table_like_text_inside_multiline_string_cannot_be_silently_rewritten(self):
        source = 'text = """\n[mcp_servers.ima]\nnot a table\n"""\n[mcp_servers.other]\ncommand="keep"\n'
        with self.assertRaises((ValueError, tomllib.TOMLDecodeError)):
            installer.render_config(source,'node',Path('bridge'))

    def test_inline_table_configuration_fails_without_writing(self):
        with self.assertRaisesRegex(ValueError,'Nonstandard'):
            installer.render_config('mcp_servers.ima = {command="old"}\n','node',Path('bridge'),True)

    def test_dry_run_writes_nothing_and_real_install_is_portable(self):
        with tempfile.TemporaryDirectory(prefix='ima-install-') as folder:
            target=Path(folder)/'User With Spaces'/'codex'
            plan=installer.install(target,'node',dry_run=True)
            self.assertTrue(plan['dryRun']);self.assertFalse(target.exists())
            installer.install(target,'node')
            config=tomllib.loads((target/'config.toml').read_text(encoding='utf-8'))
            bridge=Path(config['mcp_servers']['ima']['args'][0])
            self.assertTrue(bridge.is_file());self.assertTrue((bridge.parent/'dpapi.ps1').is_file())
            self.assertTrue((target/'skills/ima-mcp/SKILL.md').is_file())
            original=(target/'config.toml').read_bytes()
            updated=installer.install(target,'node',replace=True)
            self.assertEqual(Path(updated['backup']).read_bytes(),original)
            self.assertEqual((target/'config.toml').read_bytes(),original)


if __name__ == '__main__':
    unittest.main()
