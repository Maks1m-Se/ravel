"""Protect preview isolation, tamper detection and CLI port forwarding."""

from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from ravel.__main__ import main
from scripts.windows_preview_support import file_manifest, validate_inventory, verify_bundle, write_json


class WindowsPreviewTests(unittest.TestCase):
    def test_ui_keyboard_interrupt_is_a_successful_console_shutdown(self):
        launch=Mock(side_effect=KeyboardInterrupt)
        with patch.dict('sys.modules',{'ravel.ui':SimpleNamespace(launch=launch)}),redirect_stdout(StringIO()) as output:
            try:
                result=main(['ui','--port','8102'])
            except KeyboardInterrupt:
                self.fail('Normal UI shutdown propagated as an unhandled console failure.')
        self.assertEqual(result,0)
        self.assertIn('Ravel stopped',output.getvalue())

    def test_environment_rejects_extra_missing_and_wrong_distributions(self):
        expected={'nicegui':'3.18.0','setuptools':'80.9.0'}
        validate_inventory(expected.copy(),expected)
        for actual in [dict(expected,pip='26.2.1'),{'nicegui':'3.18.0'},dict(expected,setuptools='65.5.0')]:
            with self.subTest(actual=actual),self.assertRaises(ValueError):
                validate_inventory(actual,expected)

    def test_manifest_rejects_changed_missing_and_extra_files(self):
        with tempfile.TemporaryDirectory() as temporary:
            bundle=Path(temporary)
            target=bundle/'Ravel.exe'
            target.write_bytes(b'original-content')
            write_json(bundle/'manifest.json',dict(format='ravel-windows-preview/1',files=file_manifest(bundle)))
            verify_bundle(bundle)
            target.write_bytes(b'changed-content')
            with self.assertRaisesRegex(ValueError,'changed'):
                verify_bundle(bundle)
            target.unlink()
            with self.assertRaisesRegex(ValueError,'missing'):
                verify_bundle(bundle)
            target.write_bytes(b'original-content')
            (bundle/'unexpected').write_bytes(b'extra')
            with self.assertRaisesRegex(ValueError,'unexpected'):
                verify_bundle(bundle)

    def test_ui_port_forwarding_and_invalid_port_before_optional_import(self):
        launch=Mock()
        with patch.dict('sys.modules',{'ravel.ui':SimpleNamespace(launch=launch)}):
            self.assertEqual(main(['ui','--port','8102']),0)
            launch.assert_called_once_with(port=8102)
            with redirect_stderr(StringIO()) as captured:
                self.assertEqual(main(['ui','--port','0']),2)
            self.assertIn('Port must',captured.getvalue())
            launch.assert_called_once()


if __name__=='__main__':
    unittest.main()
