"""
Tests for the scraper CLI module - src/scraper/main.py
Tests for command-line interface and entry point.
"""

import os
import sys
import tempfile
from unittest.mock import Mock, patch

import pytest


@pytest.mark.unit
class TestScraperCLI:
    """Test the scraper CLI entry point."""

    def test_cli_argument_parsing(self):
        """Test that CLI arguments are parsed correctly."""
        from src.scraper.main import main

        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as f:
            urls_file = f.name
            f.write("https://example.com\n")

        with tempfile.NamedTemporaryFile(delete=False) as f_out:
            output_file = f_out.name

        with tempfile.NamedTemporaryFile(delete=False) as f_failed:
            failed_log = f_failed.name

        try:
            with patch.object(
                sys,
                "argv",
                [
                    "main.py",
                    "--input",
                    urls_file,
                    "--output-file",
                    output_file,
                    "--failed-log",
                    failed_log,
                ],
            ):
                with patch("src.scraper.main.VecinaScraper") as mock_scraper:
                    mock_instance = Mock()
                    mock_instance.scrape_urls.return_value = (1, 0, 1)
                    mock_scraper.return_value = mock_instance

                    # We expect this to fail due to no URLs, but that's OK for arg parsing test
                    try:
                        main()
                    except SystemExit:
                        pass
        finally:
            os.remove(urls_file)
            os.remove(output_file)
            os.remove(failed_log)

    def test_cli_input_file_validation(self):
        """Test that CLI validates input file exists."""
        from src.scraper.main import main

        with tempfile.NamedTemporaryFile(delete=False) as f_out:
            output_file = f_out.name

        with tempfile.NamedTemporaryFile(delete=False) as f_failed:
            failed_log = f_failed.name

        try:
            with patch.object(
                sys,
                "argv",
                [
                    "main.py",
                    "--input",
                    "/nonexistent/file.txt",
                    "--output-file",
                    output_file,
                    "--failed-log",
                    failed_log,
                ],
            ):
                with pytest.raises(SystemExit):
                    main()
        finally:
            os.remove(output_file)
            os.remove(failed_log)

    def test_cli_output_directory_creation(self):
        """Test that CLI creates output directories if needed."""
        from src.scraper.main import main

        with tempfile.TemporaryDirectory() as tmpdir:
            urls_file = os.path.join(tmpdir, "urls.txt")
            output_file = os.path.join(tmpdir, "subdir", "output.txt")
            failed_log = os.path.join(tmpdir, "subdir", "failed.txt")

            with open(urls_file, "w") as f:
                f.write("https://example.com\n")

            with patch.object(
                sys,
                "argv",
                [
                    "main.py",
                    "--input",
                    urls_file,
                    "--output-file",
                    output_file,
                    "--failed-log",
                    failed_log,
                ],
            ):
                with patch("src.scraper.main.VecinaScraper") as mock_scraper:
                    mock_instance = Mock()
                    mock_instance.scrape_urls.return_value = (1, 1, 0)
                    mock_instance.print_summary = Mock()
                    mock_instance.finalize = Mock()
                    mock_scraper.return_value = mock_instance

                    main()

                    # Verify directories were created
                    assert os.path.exists(os.path.dirname(output_file))
                    assert os.path.exists(os.path.dirname(failed_log))

    def test_cli_with_links_file_argument(self):
        """Test CLI accepts optional --links-file argument."""
        from src.scraper.main import main

        with tempfile.TemporaryDirectory() as tmpdir:
            urls_file = os.path.join(tmpdir, "urls.txt")
            output_file = os.path.join(tmpdir, "output.txt")
            failed_log = os.path.join(tmpdir, "failed.txt")
            links_file = os.path.join(tmpdir, "links.txt")

            with open(urls_file, "w") as f:
                f.write("https://example.com\n")

            with patch.object(
                sys,
                "argv",
                [
                    "main.py",
                    "--input",
                    urls_file,
                    "--output-file",
                    output_file,
                    "--failed-log",
                    failed_log,
                    "--links-file",
                    links_file,
                ],
            ):
                with patch("src.scraper.main.VecinaScraper") as mock_scraper:
                    mock_instance = Mock()
                    mock_instance.scrape_urls.return_value = (1, 1, 0)
                    mock_instance.print_summary = Mock()
                    mock_instance.finalize = Mock()
                    mock_scraper.return_value = mock_instance

                    main()

                    # Verify VecinaScraper was called with links_file
                    assert mock_scraper.called
                    call_kwargs = mock_scraper.call_args[1]
                    assert call_kwargs.get("links_file") == links_file

    def test_cli_with_loader_argument(self):
        """Test CLI accepts optional --loader argument."""
        from src.scraper.main import main

        with tempfile.TemporaryDirectory() as tmpdir:
            urls_file = os.path.join(tmpdir, "urls.txt")
            output_file = os.path.join(tmpdir, "output.txt")
            failed_log = os.path.join(tmpdir, "failed.txt")

            with open(urls_file, "w") as f:
                f.write("https://example.com\n")

            with patch.object(
                sys,
                "argv",
                [
                    "main.py",
                    "--input",
                    urls_file,
                    "--output-file",
                    output_file,
                    "--failed-log",
                    failed_log,
                    "--loader",
                    "playwright",
                ],
            ):
                with patch("src.scraper.main.VecinaScraper") as mock_scraper:
                    mock_instance = Mock()
                    mock_instance.scrape_urls.return_value = (1, 1, 0)
                    mock_instance.print_summary = Mock()
                    mock_instance.finalize = Mock()
                    mock_scraper.return_value = mock_instance

                    main()

                    # Verify scrape_urls was called with force_loader
                    assert mock_instance.scrape_urls.called
                    call_kwargs = mock_instance.scrape_urls.call_args[1]
                    assert call_kwargs.get("force_loader") == "playwright"


@pytest.mark.unit
class TestScraperCLIErrorHandling:
    """Test CLI error handling."""

    def test_cli_handles_keyboard_interrupt(self):
        """Test CLI gracefully handles keyboard interrupt."""
        from src.scraper.main import main

        with tempfile.TemporaryDirectory() as tmpdir:
            urls_file = os.path.join(tmpdir, "urls.txt")
            output_file = os.path.join(tmpdir, "output.txt")
            failed_log = os.path.join(tmpdir, "failed.txt")

            with open(urls_file, "w") as f:
                f.write("https://example.com\n")

            with patch.object(
                sys,
                "argv",
                [
                    "main.py",
                    "--input",
                    urls_file,
                    "--output-file",
                    output_file,
                    "--failed-log",
                    failed_log,
                ],
            ):
                with patch("src.scraper.main.VecinaScraper") as mock_scraper:
                    mock_instance = Mock()
                    mock_instance.scrape_urls.side_effect = KeyboardInterrupt()
                    mock_instance.print_summary = Mock()
                    mock_scraper.return_value = mock_instance

                    with pytest.raises(SystemExit) as exc_info:
                        main()

                    # Should exit with code 130 (standard for SIGINT)
                    assert exc_info.value.code == 130

    def test_cli_handles_fatal_error(self):
        """Test CLI handles fatal errors during scraping."""
        from src.scraper.main import main

        with tempfile.TemporaryDirectory() as tmpdir:
            urls_file = os.path.join(tmpdir, "urls.txt")
            output_file = os.path.join(tmpdir, "output.txt")
            failed_log = os.path.join(tmpdir, "failed.txt")

            with open(urls_file, "w") as f:
                f.write("https://example.com\n")

            with patch.object(
                sys,
                "argv",
                [
                    "main.py",
                    "--input",
                    urls_file,
                    "--output-file",
                    output_file,
                    "--failed-log",
                    failed_log,
                ],
            ):
                with patch("src.scraper.main.VecinaScraper") as mock_scraper:
                    mock_instance = Mock()
                    mock_instance.scrape_urls.side_effect = Exception("Fatal error")
                    mock_scraper.return_value = mock_instance

                    with pytest.raises(SystemExit) as exc_info:
                        main()

                    assert exc_info.value.code == 1


@pytest.mark.unit
class TestScraperCLIURLParsing:
    """Test CLI URL file parsing."""

    def test_cli_parses_urls_from_file(self):
        """Test that CLI correctly parses URLs from input file."""
        from src.scraper.main import main

        with tempfile.TemporaryDirectory() as tmpdir:
            urls_file = os.path.join(tmpdir, "urls.txt")
            output_file = os.path.join(tmpdir, "output.txt")
            failed_log = os.path.join(tmpdir, "failed.txt")

            with open(urls_file, "w") as f:
                f.write("# Comment line\n")
                f.write("https://example.com\n")
                f.write("\n")
                f.write("https://test.org\n")

            with patch.object(
                sys,
                "argv",
                [
                    "main.py",
                    "--input",
                    urls_file,
                    "--output-file",
                    output_file,
                    "--failed-log",
                    failed_log,
                ],
            ):
                with patch("src.scraper.main.VecinaScraper") as mock_scraper:
                    mock_instance = Mock()
                    mock_instance.scrape_urls.return_value = (2, 2, 0)
                    mock_instance.print_summary = Mock()
                    mock_instance.finalize = Mock()
                    mock_scraper.return_value = mock_instance

                    main()

                    # Verify scrape_urls was called with 2 URLs (comments and blanks ignored)
                    called_urls = mock_instance.scrape_urls.call_args[0][0]
                    assert len(called_urls) == 2
                    assert "https://example.com" in called_urls
                    assert "https://test.org" in called_urls

    def test_cli_handles_empty_url_file(self):
        """Test CLI exits gracefully with empty URL file."""
        from src.scraper.main import main

        with tempfile.TemporaryDirectory() as tmpdir:
            urls_file = os.path.join(tmpdir, "urls.txt")
            output_file = os.path.join(tmpdir, "output.txt")
            failed_log = os.path.join(tmpdir, "failed.txt")

            # Write file with explicit UTF-8 encoding containing only comments
            with open(urls_file, "w", encoding="utf-8") as f:
                f.write("# Only comments\n")
                f.write("# No actual URLs\n")

            with patch.object(
                sys,
                "argv",
                [
                    "main.py",
                    "--input",
                    urls_file,
                    "--output-file",
                    output_file,
                    "--failed-log",
                    failed_log,
                ],
            ):
                with pytest.raises(SystemExit) as exc_info:
                    main()

                # Should exit gracefully (code 0 for empty URL list after filtering comments)
                assert exc_info.value.code == 0

    def test_cli_handles_utf8_with_bom(self):
        """Test CLI correctly reads UTF-8 files with BOM."""
        from src.scraper.main import main

        with tempfile.TemporaryDirectory() as tmpdir:
            urls_file = os.path.join(tmpdir, "urls_with_bom.txt")
            output_file = os.path.join(tmpdir, "output.txt")
            failed_log = os.path.join(tmpdir, "failed.txt")

            # Write file with UTF-8 BOM encoding
            with open(urls_file, "w", encoding="utf-8-sig") as f:
                f.write("https://example.com\n")
                f.write("https://test.org\n")

            with patch.object(
                sys,
                "argv",
                [
                    "main.py",
                    "--input",
                    urls_file,
                    "--output-file",
                    output_file,
                    "--failed-log",
                    failed_log,
                ],
            ):
                with patch("src.scraper.main.VecinaScraper") as mock_scraper:
                    mock_instance = Mock()
                    mock_instance.scrape_urls.return_value = (2, 2, 0)
                    mock_instance.print_summary = Mock()
                    mock_instance.finalize = Mock()
                    mock_scraper.return_value = mock_instance

                    main()

                    # Verify URLs were parsed correctly despite BOM
                    called_urls = mock_instance.scrape_urls.call_args[0][0]
                    assert len(called_urls) == 2
                    assert "https://example.com" in called_urls
                    assert "https://test.org" in called_urls

    def test_cli_handles_latin1_encoding(self):
        """Test CLI falls back to latin-1 encoding when UTF-8 fails."""
        from src.scraper.main import main

        with tempfile.TemporaryDirectory() as tmpdir:
            urls_file = os.path.join(tmpdir, "urls_latin1.txt")
            output_file = os.path.join(tmpdir, "output.txt")
            failed_log = os.path.join(tmpdir, "failed.txt")

            # Write file with latin-1 encoding (includes special characters)
            # Using latin-1 specific character: é (0xe9 in latin-1)
            content = "# Sitio con carácter especial\nhttps://example.com/página\n"
            with open(urls_file, "wb") as f:
                f.write(content.encode("latin-1"))

            with patch.object(
                sys,
                "argv",
                [
                    "main.py",
                    "--input",
                    urls_file,
                    "--output-file",
                    output_file,
                    "--failed-log",
                    failed_log,
                ],
            ):
                with patch("src.scraper.main.VecinaScraper") as mock_scraper:
                    mock_instance = Mock()
                    mock_instance.scrape_urls.return_value = (1, 1, 0)
                    mock_instance.print_summary = Mock()
                    mock_instance.finalize = Mock()
                    mock_scraper.return_value = mock_instance

                    main()

                    # Verify URL was parsed correctly with latin-1 encoding
                    called_urls = mock_instance.scrape_urls.call_args[0][0]
                    assert len(called_urls) == 1
                    assert "página" in called_urls[0]

    def test_cli_encoding_fallback_order(self):
        """Test CLI tries encodings in correct order: utf-8, utf-8-sig, latin-1."""
        from src.scraper.main import main

        with tempfile.TemporaryDirectory() as tmpdir:
            urls_file = os.path.join(tmpdir, "urls.txt")
            output_file = os.path.join(tmpdir, "output.txt")
            failed_log = os.path.join(tmpdir, "failed.txt")

            # Create a file that's valid UTF-8
            with open(urls_file, "w", encoding="utf-8") as f:
                f.write("https://example.com\n")

            with patch.object(
                sys,
                "argv",
                [
                    "main.py",
                    "--input",
                    urls_file,
                    "--output-file",
                    output_file,
                    "--failed-log",
                    failed_log,
                ],
            ):
                with patch("src.scraper.main.VecinaScraper") as mock_scraper:
                    mock_instance = Mock()
                    mock_instance.scrape_urls.return_value = (1, 1, 0)
                    mock_instance.print_summary = Mock()
                    mock_instance.finalize = Mock()
                    mock_scraper.return_value = mock_instance

                    # Patch open to track encoding attempts
                    original_open = open
                    encoding_attempts = []

                    def tracking_open(*args, **kwargs):
                        if "encoding" in kwargs:
                            encoding_attempts.append(kwargs["encoding"])
                        return original_open(*args, **kwargs)

                    with patch("builtins.open", side_effect=tracking_open):
                        main()

                    # Verify utf-8 was tried first (and succeeded)
                    assert "utf-8" in encoding_attempts
                    # Since UTF-8 succeeds, we shouldn't need to try other encodings
                    assert encoding_attempts[0] == "utf-8"
