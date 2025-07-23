"""
Comprehensive unit tests for GoogleDriveDownloadTool.

This module implements task 10 requirements:
- Unit tests for GoogleDriveDownloadTool
- Test with actual test data 
- Test error handling paths and edge cases
- Validate all tool functionality

Requirements: 1.1, 1.2, 1.3
"""
import pytest
import json
import os
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import io

# Import the tool to test
import sys
sys.path.append(str(Path(__file__).parent.parent.parent.parent))
from tools.google_drive_download_tool import GoogleDriveDownloadTool


class TestGoogleDriveDownloadTool:
    """Comprehensive tests for GoogleDriveDownloadTool."""
    
    @pytest.fixture
    def tool(self):
        """Create a GoogleDriveDownloadTool instance."""
        return GoogleDriveDownloadTool()
    
    @pytest.fixture
    def mock_db_session(self):
        """Create a mock database session."""
        mock_session = Mock()
        mock_client_user = Mock()
        mock_client_user.google_drive_credentials = json.dumps({
            "type": "service_account",
            "project_id": "test-project",
            "private_key_id": "test-key-id",
            "private_key": "-----BEGIN PRIVATE KEY-----\ntest-key\n-----END PRIVATE KEY-----",
            "client_email": "test@test.iam.gserviceaccount.com",
            "client_id": "123456789",
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
            "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/test%40test.iam.gserviceaccount.com"
        })
        mock_session.query.return_value.filter.return_value.first.return_value = mock_client_user
        return mock_session
    
    @pytest.fixture
    def mock_drive_service(self):
        """Create a mock Google Drive service."""
        mock_service = Mock()
        
        # Mock file get response
        mock_file_get = Mock()
        mock_file_get.execute.return_value = {
            'id': 'test-file-id',
            'name': 'test_image.png',
            'mimeType': 'image/png',
            'size': '1024'
        }
        
        # Mock media download
        mock_media = Mock()
        mock_media.execute.return_value = b'fake image content'
        
        # Wire up the mocks
        mock_service.files.return_value.get.return_value = mock_file_get
        mock_service.files.return_value.get_media.return_value = mock_media
        
        return mock_service
    
    def test_successful_download(self, tool, mock_db_session, mock_drive_service):
        """Test successful file download."""
        with patch('tools.google_drive_download_tool.create_engine'):
            with patch('tools.google_drive_download_tool.sessionmaker', return_value=Mock(return_value=mock_db_session)):
                with patch('tools.google_drive_download_tool.service_account.Credentials.from_service_account_info'):
                    with patch('tools.google_drive_download_tool.build', return_value=mock_drive_service):
                        # Mock MediaIoBaseDownload
                        with patch('tools.google_drive_download_tool.MediaIoBaseDownload') as mock_download_class:
                            # Configure download progress
                            mock_downloader = Mock()
                            mock_downloader.next_chunk.side_effect = [
                                (Mock(progress=Mock(return_value=0.5)), False),
                                (Mock(progress=Mock(return_value=1.0)), True)
                            ]
                            mock_download_class.return_value = mock_downloader
                            
                            # Run the tool
                            result = tool._run(
                                file_id='test-file-id',
                                file_name='test_image.png',
                                client_user_id='test-client-id'
                            )
                            
                            # Parse result
                            result_data = json.loads(result)
                            
                            # Assertions
                            assert result_data['status'] == 'success'
                            assert 'local_path' in result_data
                            assert result_data['file_name'] == 'test_image.png'
                            assert result_data['file_id'] == 'test-file-id'
                            
                            # Verify file was created
                            local_path = result_data['local_path']
                            assert os.path.exists(local_path)
                            
                            # Clean up
                            if os.path.exists(local_path):
                                os.remove(local_path)
    
    def test_supported_image_formats(self, tool, mock_db_session, mock_drive_service):
        """Test all supported image formats."""
        supported_formats = [
            ('image.png', 'image/png'),
            ('image.jpg', 'image/jpeg'),
            ('image.jpeg', 'image/jpeg'),
            ('image.webp', 'image/webp'),
            ('image.gif', 'image/gif'),
            ('image.bmp', 'image/bmp'),
            ('image.tiff', 'image/tiff')
        ]
        
        with patch('tools.google_drive_download_tool.create_engine'):
            with patch('tools.google_drive_download_tool.sessionmaker', return_value=Mock(return_value=mock_db_session)):
                with patch('tools.google_drive_download_tool.service_account.Credentials.from_service_account_info'):
                    with patch('tools.google_drive_download_tool.build', return_value=mock_drive_service):
                        with patch('tools.google_drive_download_tool.MediaIoBaseDownload') as mock_download_class:
                            mock_downloader = Mock()
                            mock_downloader.next_chunk.return_value = (Mock(progress=Mock(return_value=1.0)), True)
                            mock_download_class.return_value = mock_downloader
                            
                            for file_name, mime_type in supported_formats:
                                # Update mock response
                                mock_drive_service.files.return_value.get.return_value.execute.return_value = {
                                    'id': 'test-file-id',
                                    'name': file_name,
                                    'mimeType': mime_type,
                                    'size': '1024'
                                }
                                
                                # Run the tool
                                result = tool._run(
                                    file_id='test-file-id',
                                    file_name=file_name,
                                    client_user_id='test-client-id'
                                )
                                
                                # Parse result
                                result_data = json.loads(result)
                                
                                # Assertions
                                assert result_data['status'] == 'success', f"Failed for {file_name}"
                                assert result_data['file_name'] == file_name
                                
                                # Clean up
                                if 'local_path' in result_data and os.path.exists(result_data['local_path']):
                                    os.remove(result_data['local_path'])
    
    def test_missing_client_user_id(self, tool):
        """Test error when client_user_id is missing."""
        result = tool._run(
            file_id='test-file-id',
            file_name='test.png',
            client_user_id=None
        )
        
        result_data = json.loads(result)
        assert result_data['status'] == 'error'
        assert 'client_user_id is required' in result_data['error']
    
    def test_missing_file_id(self, tool):
        """Test error when file_id is missing."""
        result = tool._run(
            file_id=None,
            file_name='test.png',
            client_user_id='test-client-id'
        )
        
        result_data = json.loads(result)
        assert result_data['status'] == 'error'
        assert 'file_id is required' in result_data['error']
    
    def test_client_not_found(self, tool):
        """Test error when client is not found in database."""
        mock_session = Mock()
        mock_session.query.return_value.filter.return_value.first.return_value = None
        
        with patch('tools.google_drive_download_tool.create_engine'):
            with patch('tools.google_drive_download_tool.sessionmaker', return_value=Mock(return_value=mock_session)):
                result = tool._run(
                    file_id='test-file-id',
                    file_name='test.png',
                    client_user_id='non-existent-client'
                )
                
                result_data = json.loads(result)
                assert result_data['status'] == 'error'
                assert 'Client user not found' in result_data['error']
    
    def test_no_credentials(self, tool):
        """Test error when client has no Google Drive credentials."""
        mock_session = Mock()
        mock_client_user = Mock()
        mock_client_user.google_drive_credentials = None
        mock_session.query.return_value.filter.return_value.first.return_value = mock_client_user
        
        with patch('tools.google_drive_download_tool.create_engine'):
            with patch('tools.google_drive_download_tool.sessionmaker', return_value=Mock(return_value=mock_session)):
                result = tool._run(
                    file_id='test-file-id',
                    file_name='test.png',
                    client_user_id='test-client-id'
                )
                
                result_data = json.loads(result)
                assert result_data['status'] == 'error'
                assert 'No Google Drive credentials' in result_data['error']
    
    def test_invalid_credentials_json(self, tool):
        """Test error when credentials JSON is invalid."""
        mock_session = Mock()
        mock_client_user = Mock()
        mock_client_user.google_drive_credentials = 'invalid json'
        mock_session.query.return_value.filter.return_value.first.return_value = mock_client_user
        
        with patch('tools.google_drive_download_tool.create_engine'):
            with patch('tools.google_drive_download_tool.sessionmaker', return_value=Mock(return_value=mock_session)):
                result = tool._run(
                    file_id='test-file-id',
                    file_name='test.png',
                    client_user_id='test-client-id'
                )
                
                result_data = json.loads(result)
                assert result_data['status'] == 'error'
                assert 'credentials' in result_data['error'].lower()
    
    def test_google_drive_api_error(self, tool, mock_db_session):
        """Test handling of Google Drive API errors."""
        with patch('tools.google_drive_download_tool.create_engine'):
            with patch('tools.google_drive_download_tool.sessionmaker', return_value=Mock(return_value=mock_db_session)):
                with patch('tools.google_drive_download_tool.service_account.Credentials.from_service_account_info'):
                    mock_service = Mock()
                    mock_service.files.return_value.get.side_effect = Exception("API Error: File not found")
                    
                    with patch('tools.google_drive_download_tool.build', return_value=mock_service):
                        result = tool._run(
                            file_id='non-existent-file',
                            file_name='test.png',
                            client_user_id='test-client-id'
                        )
                        
                        result_data = json.loads(result)
                        assert result_data['status'] == 'error'
                        assert 'API Error' in result_data['error']
    
    def test_download_progress(self, tool, mock_db_session, mock_drive_service):
        """Test download progress reporting."""
        with patch('tools.google_drive_download_tool.create_engine'):
            with patch('tools.google_drive_download_tool.sessionmaker', return_value=Mock(return_value=mock_db_session)):
                with patch('tools.google_drive_download_tool.service_account.Credentials.from_service_account_info'):
                    with patch('tools.google_drive_download_tool.build', return_value=mock_drive_service):
                        # Mock MediaIoBaseDownload with multiple progress updates
                        with patch('tools.google_drive_download_tool.MediaIoBaseDownload') as mock_download_class:
                            mock_downloader = Mock()
                            progress_values = []
                            
                            def capture_progress(progress):
                                progress_values.append(progress)
                                return progress
                            
                            mock_downloader.next_chunk.side_effect = [
                                (Mock(progress=lambda: capture_progress(0.25)), False),
                                (Mock(progress=lambda: capture_progress(0.50)), False),
                                (Mock(progress=lambda: capture_progress(0.75)), False),
                                (Mock(progress=lambda: capture_progress(1.00)), True)
                            ]
                            mock_download_class.return_value = mock_downloader
                            
                            # Run the tool
                            result = tool._run(
                                file_id='test-file-id',
                                file_name='large_image.png',
                                client_user_id='test-client-id'
                            )
                            
                            # Verify progress was tracked
                            assert len(progress_values) == 4
                            assert progress_values == [0.25, 0.50, 0.75, 1.00]
    
    def test_temp_directory_creation(self, tool, mock_db_session, mock_drive_service):
        """Test that temp directory is created if it doesn't exist."""
        with patch('tools.google_drive_download_tool.create_engine'):
            with patch('tools.google_drive_download_tool.sessionmaker', return_value=Mock(return_value=mock_db_session)):
                with patch('tools.google_drive_download_tool.service_account.Credentials.from_service_account_info'):
                    with patch('tools.google_drive_download_tool.build', return_value=mock_drive_service):
                        with patch('tools.google_drive_download_tool.MediaIoBaseDownload') as mock_download_class:
                            mock_downloader = Mock()
                            mock_downloader.next_chunk.return_value = (Mock(progress=Mock(return_value=1.0)), True)
                            mock_download_class.return_value = mock_downloader
                            
                            # Use a custom temp dir that doesn't exist
                            custom_temp_dir = '/tmp/test_google_drive_downloads_' + str(os.getpid())
                            if os.path.exists(custom_temp_dir):
                                os.rmdir(custom_temp_dir)
                            
                            with patch.object(tool, 'temp_dir', custom_temp_dir):
                                result = tool._run(
                                    file_id='test-file-id',
                                    file_name='test.png',
                                    client_user_id='test-client-id'
                                )
                                
                                # Verify temp directory was created
                                assert os.path.exists(custom_temp_dir)
                                
                                # Clean up
                                result_data = json.loads(result)
                                if 'local_path' in result_data and os.path.exists(result_data['local_path']):
                                    os.remove(result_data['local_path'])
                                if os.path.exists(custom_temp_dir):
                                    os.rmdir(custom_temp_dir)
    
    def test_file_size_in_response(self, tool, mock_db_session, mock_drive_service):
        """Test that file size is included in the response."""
        mock_drive_service.files.return_value.get.return_value.execute.return_value = {
            'id': 'test-file-id',
            'name': 'test_image.png',
            'mimeType': 'image/png',
            'size': '2048576'  # 2MB
        }
        
        with patch('tools.google_drive_download_tool.create_engine'):
            with patch('tools.google_drive_download_tool.sessionmaker', return_value=Mock(return_value=mock_db_session)):
                with patch('tools.google_drive_download_tool.service_account.Credentials.from_service_account_info'):
                    with patch('tools.google_drive_download_tool.build', return_value=mock_drive_service):
                        with patch('tools.google_drive_download_tool.MediaIoBaseDownload') as mock_download_class:
                            mock_downloader = Mock()
                            mock_downloader.next_chunk.return_value = (Mock(progress=Mock(return_value=1.0)), True)
                            mock_download_class.return_value = mock_downloader
                            
                            result = tool._run(
                                file_id='test-file-id',
                                file_name='test_image.png',
                                client_user_id='test-client-id'
                            )
                            
                            result_data = json.loads(result)
                            assert result_data['status'] == 'success'
                            assert result_data['file_size'] == '2048576'


# Run tests if executed directly
if __name__ == "__main__":
    pytest.main([__file__, "-v"])