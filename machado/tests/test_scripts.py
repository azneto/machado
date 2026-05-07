import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from machado.scripts.startproject import main


class StartProjectScriptTest(unittest.TestCase):
    def test_main(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            test_args = ["machado-startproject", tmpdir, "--verbosity=0"]
            with patch.object(sys, "argv", test_args):
                main()
            
            target = Path(tmpdir)
            self.assertTrue((target / ".env.example").exists())
            self.assertTrue((target / ".env").exists())
            self.assertTrue((target / "manage.py").exists())

    def test_main_overwrite(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            test_args = ["machado-startproject", tmpdir, "--verbosity=0"]
            with patch.object(sys, "argv", test_args):
                main()
            
            # Running again without --overwrite
            with patch.object(sys, "argv", test_args):
                main()
            
            # Running with --overwrite
            test_args_overwrite = [
                "machado-startproject", tmpdir, "--overwrite", "--verbosity=0",
            ]
            with patch.object(sys, "argv", test_args_overwrite):
                main()
            
            target = Path(tmpdir)
            self.assertTrue((target / ".env").exists())
