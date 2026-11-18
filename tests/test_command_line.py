"""Command-line file opening tests (file manager 'Open With')."""

from astrostudio.app import paths_from_command_line


class FakeFile:
    def __init__(self, path):
        self.path = path

    def get_path(self):
        return self.path


class FakeCommandLine:
    def __init__(self, files, arguments):
        self.files = files
        self.arguments = arguments

    def get_files(self):
        return self.files

    def get_arguments(self):
        return self.arguments


def test_paths_are_extracted_and_deduplicated(tmp_path):
    image = tmp_path / "light.png"
    image.write_bytes(b"png")
    missing = tmp_path / "missing.fits"

    command_line = FakeCommandLine(
        [FakeFile(str(image))],
        ["astro-studio", str(image), "--debug", str(missing)],
    )

    assert paths_from_command_line(command_line) == [str(image)]


def test_raw_arguments_work_when_gfiles_are_empty(tmp_path):
    image = tmp_path / "light.fits"
    image.write_bytes(b"fits")
    command_line = FakeCommandLine([], ["astro-studio", str(image)])
    assert paths_from_command_line(command_line) == [str(image)]
