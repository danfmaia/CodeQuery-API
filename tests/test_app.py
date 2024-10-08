from unittest.mock import mock_open, patch
from src.app import CodeQueryAPI

PROJECT_PATH = "./"
AGENTIGNORE_FILE_1 = ".agentignore"


class TestCodeQueryAPI:
    """Test suite for the CodeQueryAPI class."""

    # pylint: disable=attribute-defined-outside-init
    def setup_method(self):
        """Setup method to initialize the CodeQueryAPI instance for each test."""
        self.api = CodeQueryAPI()  # Initialize a fresh instance for each test

    def test_ensure_ngrok_tunnel_already_running(self):
        """
        Test that ngrok is not set up again if the tunnel is already running and synchronized.
        """
        # Patch the instance's ngrok_manager attribute
        with patch.object(self.api, 'ngrok_manager') as mock_ngrok_manager:
            mock_ngrok_manager.check_ngrok_status.return_value = True

            # Call ensure_ngrok_tunnel directly on the class instance
            self.api.ensure_ngrok_tunnel()  # Trigger the function manually

            mock_ngrok_manager.check_ngrok_status.assert_called_once()
            mock_ngrok_manager.setup_ngrok.assert_not_called()

    def test_ensure_ngrok_tunnel_not_running(self):
        """
        Test that ngrok is set up if the tunnel is not running or not synchronized.
        """
        # Patch the instance's ngrok_manager attribute
        with patch.object(self.api, 'ngrok_manager') as mock_ngrok_manager:
            mock_ngrok_manager.check_ngrok_status.return_value = False

            # Call ensure_ngrok_tunnel directly on the class instance
            self.api.ensure_ngrok_tunnel()  # Trigger the function manually

            mock_ngrok_manager.check_ngrok_status.assert_called_once()
            mock_ngrok_manager.setup_ngrok.assert_called_once()

    def test_configure_logging(self):
        """Test that logging is correctly configured."""
        assert len(
            self.api.logger.handlers) > 0, "Logger should have handlers configured"

    def test_load_ignore_spec(self):
        """
        Test that the load_ignore_spec function loads patterns correctly from
        multiple ignore files.
        """
        mock_ignore_content_agentignore = """
        # This is a comment
        venv/
        __pycache__/
        """
        mock_ignore_content_gitignore = """
        # Another comment
        .git/
        """

        with patch('builtins.open', mock_open()) as mock_file:
            mock_file.side_effect = [
                mock_open(
                    read_data=mock_ignore_content_agentignore).return_value,
                mock_open(read_data=mock_ignore_content_gitignore).return_value
            ]
            with patch('os.path.exists', return_value=True):
                self.api.load_ignore_spec()

                mock_file.assert_any_call(
                    '.agentignore', 'r', encoding='utf-8')
                mock_file.assert_any_call('.gitignore', 'r', encoding='utf-8')
