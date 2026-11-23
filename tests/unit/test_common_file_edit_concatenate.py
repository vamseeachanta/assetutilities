# ABOUTME: Tests for common/file_edit_concatenate.py — FileConcatenate class.
# ABOUTME: Covers concatenate_one_set and prepare_custom_batch with temp files.

import os
import tempfile

import pytest

from assetutilities.common.file_edit_concatenate import FileConcatenate


# ---------------------------------------------------------------------------
# FileConcatenate.concatenate_one_set
# ---------------------------------------------------------------------------


class TestConcatenateOneSet:
    """FileConcatenate.concatenate_one_set merges files into a single output."""

    def test_concatenates_two_text_files(self):
        # Arrange
        fc = FileConcatenate()
        with tempfile.TemporaryDirectory() as tmpdir:
            file_a = os.path.join(tmpdir, "a.txt")
            file_b = os.path.join(tmpdir, "b.txt")
            output = os.path.join(tmpdir, "merged.txt")

            with open(file_a, "wb") as f:
                f.write(b"content_a\n")
            with open(file_b, "wb") as f:
                f.write(b"content_b\n")

            cfg = {"Analysis": {"analysis_root_folder": tmpdir}}

            # Act
            fc.concatenate_one_set(cfg, [file_a, file_b], output)

            # Assert
            with open(output, "rb") as f:
                result = f.read()
            assert b"content_a" in result
            assert b"content_b" in result

    def test_single_file_copied_to_output(self):
        # Arrange
        fc = FileConcatenate()
        with tempfile.TemporaryDirectory() as tmpdir:
            src = os.path.join(tmpdir, "source.dat")
            dst = os.path.join(tmpdir, "dest.dat")

            with open(src, "wb") as f:
                f.write(b"only content")

            cfg = {"Analysis": {"analysis_root_folder": tmpdir}}

            # Act
            fc.concatenate_one_set(cfg, [src], dst)

            # Assert
            with open(dst, "rb") as f:
                assert f.read() == b"only content"

    def test_order_preserved_in_output(self):
        # Arrange
        fc = FileConcatenate()
        with tempfile.TemporaryDirectory() as tmpdir:
            file_1 = os.path.join(tmpdir, "first.txt")
            file_2 = os.path.join(tmpdir, "second.txt")
            output = os.path.join(tmpdir, "combined.txt")

            with open(file_1, "wb") as f:
                f.write(b"AAA")
            with open(file_2, "wb") as f:
                f.write(b"BBB")

            cfg = {"Analysis": {"analysis_root_folder": tmpdir}}

            # Act
            fc.concatenate_one_set(cfg, [file_1, file_2], output)

            # Assert — first file content comes before second
            with open(output, "rb") as f:
                content = f.read()
            assert content.index(b"AAA") < content.index(b"BBB")

    def test_returns_cfg(self):
        # Arrange
        fc = FileConcatenate()
        with tempfile.TemporaryDirectory() as tmpdir:
            src = os.path.join(tmpdir, "s.txt")
            dst = os.path.join(tmpdir, "d.txt")
            with open(src, "wb") as f:
                f.write(b"data")

            cfg = {"Analysis": {"analysis_root_folder": tmpdir}}

            # Act
            result = fc.concatenate_one_set(cfg, [src], dst)

            # Assert
            assert result is cfg


# ---------------------------------------------------------------------------
# FileConcatenate.prepare_custom_batch
# ---------------------------------------------------------------------------


class TestPrepareCustomBatch:
    """FileConcatenate.prepare_custom_batch creates a .bat file when batch flag is True."""

    def test_batch_flag_false_returns_filename_without_writing(self):
        # Arrange
        fc = FileConcatenate()
        with tempfile.TemporaryDirectory() as tmpdir:
            cfg = {
                "Analysis": {
                    "analysis_root_folder": tmpdir,
                    "file_name": "test_run",
                }
            }
            input_set = {"batch": {"flag": False, "extension": True, "content": "run"}}
            output_files = {"ext": ["/out/file.dat"], "no_ext": ["/out/file"]}

            # Act
            batch_path = fc.prepare_custom_batch(cfg, input_set, 0, output_files)

            # Assert — returns path string but does not write file
            assert isinstance(batch_path, str)
            assert batch_path.endswith(".bat")
            # File should NOT be created since flag=False
            assert not os.path.exists(batch_path)

    def test_batch_flag_true_with_extension_creates_bat_file(self):
        # Arrange
        fc = FileConcatenate()
        with tempfile.TemporaryDirectory() as tmpdir:
            cfg = {
                "Analysis": {
                    "analysis_root_folder": tmpdir,
                    "file_name": "run",
                }
            }
            out_file = os.path.join(tmpdir, "output.dat")
            input_set = {
                "batch": {
                    "flag": True,
                    "extension": True,
                    "content": "myprogram",
                }
            }
            output_files = {"ext": [out_file], "no_ext": [os.path.splitext(out_file)[0]]}

            # Act
            batch_path = fc.prepare_custom_batch(cfg, input_set, 0, output_files)

            # Assert
            assert os.path.exists(batch_path)
            with open(batch_path) as f:
                content = f.read()
            assert "myprogram" in content
            assert out_file in content

    def test_batch_flag_true_without_extension_uses_no_ext_list(self):
        # Arrange
        fc = FileConcatenate()
        with tempfile.TemporaryDirectory() as tmpdir:
            cfg = {
                "Analysis": {
                    "analysis_root_folder": tmpdir,
                    "file_name": "run",
                }
            }
            no_ext_file = os.path.join(tmpdir, "output")
            input_set = {
                "batch": {
                    "flag": True,
                    "extension": False,
                    "content": "program",
                }
            }
            output_files = {"ext": [no_ext_file + ".dat"], "no_ext": [no_ext_file]}

            # Act
            batch_path = fc.prepare_custom_batch(cfg, input_set, 0, output_files)

            # Assert
            assert os.path.exists(batch_path)
            with open(batch_path) as f:
                content = f.read()
            assert no_ext_file in content

    def test_no_batch_key_returns_batch_filename(self):
        # Arrange
        fc = FileConcatenate()
        with tempfile.TemporaryDirectory() as tmpdir:
            cfg = {
                "Analysis": {
                    "analysis_root_folder": tmpdir,
                    "file_name": "myrun",
                }
            }
            input_set = {}  # no 'batch' key
            output_files = {"ext": [], "no_ext": []}

            # Act
            batch_path = fc.prepare_custom_batch(cfg, input_set, 2, output_files)

            # Assert
            assert isinstance(batch_path, str)
            assert "myrun_2.bat" in batch_path
