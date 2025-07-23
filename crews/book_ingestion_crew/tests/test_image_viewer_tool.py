"""
Comprehensive unit tests for ImageViewerTool.

This module implements task 10 requirements:
- Unit tests for ImageViewerTool
- Test 3-pass OCR processing
- Test error handling and edge cases
- Validate OCR functionality

Requirements: 2.1, 2.2, 2.3, 2.4
"""
import pytest
import json
import os
import base64
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import tempfile

# Import the tool to test
import sys
sys.path.append(str(Path(__file__).parent.parent.parent.parent))
from tools.image_viewer_tool import ImageViewerTool


class TestImageViewerTool:
    """Comprehensive tests for ImageViewerTool."""
    
    @pytest.fixture
    def tool(self):
        """Create an ImageViewerTool instance."""
        return ImageViewerTool()
    
    @pytest.fixture
    def test_image_path(self):
        """Create a test image file."""
        # Create a simple 1x1 white pixel PNG
        png_data = base64.b64decode(
            'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg=='
        )
        
        with tempfile.NamedTemporaryFile(mode='wb', suffix='.png', delete=False) as f:
            f.write(png_data)
            temp_path = f.name
        
        yield temp_path
        
        # Cleanup
        if os.path.exists(temp_path):
            os.remove(temp_path)
    
    @pytest.fixture
    def mock_openai_response(self):
        """Create mock OpenAI responses for 3-pass OCR."""
        pass1_response = Mock()
        pass1_response.choices = [Mock(message=Mock(content=json.dumps({
            "transcription": "Esta es la primera línea del manuscrito.\nAquí está la segunda línea con texto.",
            "pass_type": "contextual",
            "uncertain_words": ["manuscrito[CONTEXT?]"],
            "illegible_sections": [],
            "total_words_found": 12,
            "confidence_level": "medium"
        })))]
        
        pass2_response = Mock()
        pass2_response.choices = [Mock(message=Mock(content=json.dumps({
            "transcription": "Esta es la primera línea del manuscrito.\nAquí está la segunda línea con texto.",
            "pass_type": "word_level",
            "improvements_made": ["manuscrito clarified"],
            "remaining_uncertain": [],
            "remaining_illegible": [],
            "total_words_found": 12,
            "confidence_level": "high"
        })))]
        
        pass3_response = Mock()
        pass3_response.choices = [Mock(message=Mock(content=json.dumps({
            "transcription": "Esta es la primera línea del manuscrito.\nAquí está la segunda línea con texto.",
            "pass_type": "letter_level",
            "final_improvements": [],
            "logic_guesses": [],
            "final_illegible": [],
            "processing_stats": {
                "total_words": 12,
                "normal_transcription": 11,
                "context_logic_transcription": 1,
                "unable_to_transcribe": 0
            },
            "unclear_sections": [],
            "confidence_level": "high"
        })))]
        
        return [pass1_response, pass2_response, pass3_response]
    
    def test_successful_ocr_processing(self, tool, test_image_path, mock_openai_response):
        """Test successful 3-pass OCR processing."""
        with patch('tools.image_viewer_tool.openai.OpenAI') as mock_openai_class:
            mock_client = Mock()
            mock_openai_class.return_value = mock_client
            mock_client.chat.completions.create.side_effect = mock_openai_response
            
            # Run the tool
            result = tool._run(image_path=test_image_path)
            
            # Parse result
            result_data = json.loads(result)
            
            # Assertions
            assert 'transcription' in result_data
            assert result_data['transcription'] == "Esta es la primera línea del manuscrito.\nAquí está la segunda línea con texto."
            assert result_data['ocr_passes'] == 3
            assert result_data['model_used'] == 'gpt-4o'
            assert 'processing_stats' in result_data
            assert result_data['processing_stats']['total_words'] == 12
            assert result_data['processing_stats']['normal_transcription'] == 11
            assert result_data['processing_stats']['context_logic_transcription'] == 1
            
            # Verify 3 API calls were made
            assert mock_client.chat.completions.create.call_count == 3
    
    def test_missing_image_file(self, tool):
        """Test error when image file doesn't exist."""
        result = tool._run(image_path='/non/existent/file.png')
        
        result_data = json.loads(result)
        assert 'error' in result_data
        assert 'not found' in result_data['error']
    
    def test_pass_details_tracking(self, tool, test_image_path, mock_openai_response):
        """Test that all 3 passes are tracked with details."""
        with patch('tools.image_viewer_tool.openai.OpenAI') as mock_openai_class:
            mock_client = Mock()
            mock_openai_class.return_value = mock_client
            mock_client.chat.completions.create.side_effect = mock_openai_response
            
            # Run the tool
            result = tool._run(image_path=test_image_path)
            
            # Parse result
            result_data = json.loads(result)
            
            # Check pass details
            assert 'pass_details' in result_data
            assert 'pass1_contextual' in result_data['pass_details']
            assert 'pass2_word_level' in result_data['pass_details']
            assert 'pass3_letter_level' in result_data['pass_details']
            
            # Verify pass 1 details
            pass1 = result_data['pass_details']['pass1_contextual']
            assert pass1['confidence'] == 'medium'
            assert pass1['uncertain_words'] == 1
            assert pass1['illegible_sections'] == 0
            
            # Verify pass 2 details
            pass2 = result_data['pass_details']['pass2_word_level']
            assert pass2['confidence'] == 'high'
            assert pass2['improvements_made'] == 1
            assert pass2['remaining_uncertain'] == 0
            
            # Verify pass 3 details
            pass3 = result_data['pass_details']['pass3_letter_level']
            assert pass3['confidence'] == 'high'
            assert pass3['final_improvements'] == 0
            assert 'logic_guesses' in pass3
    
    def test_ocr_with_unclear_sections(self, tool, test_image_path):
        """Test OCR with unclear sections."""
        pass3_response = Mock()
        pass3_response.choices = [Mock(message=Mock(content=json.dumps({
            "transcription": "Esta es la [ILLEGIBLE] línea del manuscrito.",
            "pass_type": "letter_level",
            "final_improvements": [],
            "logic_guesses": ["palabra unclear guessed as 'primera'"],
            "final_illegible": ["word at position 3"],
            "processing_stats": {
                "total_words": 7,
                "normal_transcription": 5,
                "context_logic_transcription": 1,
                "unable_to_transcribe": 1
            },
            "unclear_sections": ["word at position 3"],
            "confidence_level": "medium"
        })))]
        
        with patch('tools.image_viewer_tool.openai.OpenAI') as mock_openai_class:
            mock_client = Mock()
            mock_openai_class.return_value = mock_client
            # Return same response for all 3 passes for simplicity
            mock_client.chat.completions.create.return_value = pass3_response
            
            # Run the tool
            result = tool._run(image_path=test_image_path)
            
            # Parse result
            result_data = json.loads(result)
            
            # Assertions
            assert '[ILLEGIBLE]' in result_data['transcription']
            assert len(result_data['unclear_sections']) == 1
            assert result_data['processing_stats']['unable_to_transcribe'] == 1
    
    def test_api_error_handling(self, tool, test_image_path):
        """Test handling of OpenAI API errors."""
        with patch('tools.image_viewer_tool.openai.OpenAI') as mock_openai_class:
            mock_client = Mock()
            mock_openai_class.return_value = mock_client
            mock_client.chat.completions.create.side_effect = Exception("OpenAI API Error: Rate limit exceeded")
            
            # Run the tool
            result = tool._run(image_path=test_image_path)
            
            # Parse result
            result_data = json.loads(result)
            
            # Assertions
            assert 'error' in result_data
            assert 'OpenAI API Error' in result_data['error']
            assert result_data['ocr_passes'] == 0
    
    def test_invalid_json_response_fallback(self, tool, test_image_path):
        """Test fallback when API returns invalid JSON."""
        invalid_response = Mock()
        invalid_response.choices = [Mock(message=Mock(content="This is plain text, not JSON"))]
        
        with patch('tools.image_viewer_tool.openai.OpenAI') as mock_openai_class:
            mock_client = Mock()
            mock_openai_class.return_value = mock_client
            mock_client.chat.completions.create.return_value = invalid_response
            
            # Run the tool
            result = tool._run(image_path=test_image_path)
            
            # Parse result
            result_data = json.loads(result)
            
            # Should still return a valid response with fallback handling
            assert 'transcription' in result_data
            assert result_data['transcription'] == "This is plain text, not JSON"
            assert result_data['ocr_passes'] == 3
    
    def test_sequential_thinking_session_id(self, tool, test_image_path, mock_openai_response):
        """Test that sequential thinking session ID is accepted."""
        with patch('tools.image_viewer_tool.openai.OpenAI') as mock_openai_class:
            mock_client = Mock()
            mock_openai_class.return_value = mock_client
            mock_client.chat.completions.create.side_effect = mock_openai_response
            
            # Run the tool with session ID
            result = tool._run(
                image_path=test_image_path,
                sequential_thinking_session_id='test-session-123'
            )
            
            # Parse result
            result_data = json.loads(result)
            
            # Should complete successfully
            assert 'transcription' in result_data
            assert result_data['ocr_passes'] == 3
    
    def test_temperature_setting(self, tool, test_image_path, mock_openai_response):
        """Test that temperature is set to 0.1 for consistency."""
        with patch('tools.image_viewer_tool.openai.OpenAI') as mock_openai_class:
            mock_client = Mock()
            mock_openai_class.return_value = mock_client
            mock_client.chat.completions.create.side_effect = mock_openai_response
            
            # Run the tool
            result = tool._run(image_path=test_image_path)
            
            # Verify temperature setting in all 3 calls
            for call in mock_client.chat.completions.create.call_args_list:
                assert call[1]['temperature'] == 0.1
    
    def test_max_tokens_setting(self, tool, test_image_path, mock_openai_response):
        """Test that max_tokens is set appropriately."""
        with patch('tools.image_viewer_tool.openai.OpenAI') as mock_openai_class:
            mock_client = Mock()
            mock_openai_class.return_value = mock_client
            mock_client.chat.completions.create.side_effect = mock_openai_response
            
            # Run the tool
            result = tool._run(image_path=test_image_path)
            
            # Verify max_tokens setting in all 3 calls
            for call in mock_client.chat.completions.create.call_args_list:
                assert call[1]['max_tokens'] == 2500
    
    def test_image_encoding(self, tool, test_image_path):
        """Test that image is properly encoded as base64."""
        captured_messages = []
        
        def capture_messages(*args, **kwargs):
            captured_messages.append(kwargs['messages'])
            # Return a mock response
            response = Mock()
            response.choices = [Mock(message=Mock(content=json.dumps({
                "transcription": "test",
                "pass_type": "test",
                "confidence_level": "high"
            })))]
            return response
        
        with patch('tools.image_viewer_tool.openai.OpenAI') as mock_openai_class:
            mock_client = Mock()
            mock_openai_class.return_value = mock_client
            mock_client.chat.completions.create.side_effect = capture_messages
            
            # Run the tool
            result = tool._run(image_path=test_image_path)
            
            # Verify image was encoded in all 3 passes
            assert len(captured_messages) == 3
            for messages in captured_messages:
                user_message = messages[0]
                assert user_message['role'] == 'user'
                assert len(user_message['content']) == 2
                assert user_message['content'][0]['type'] == 'text'
                assert user_message['content'][1]['type'] == 'image_url'
                assert user_message['content'][1]['image_url']['url'].startswith('data:image/jpeg;base64,')
    
    def test_prompt_includes_top_lines_emphasis(self, tool, test_image_path):
        """Test that prompts emphasize capturing top 4-5 lines."""
        captured_messages = []
        
        def capture_messages(*args, **kwargs):
            captured_messages.append(kwargs['messages'])
            # Return a mock response
            response = Mock()
            response.choices = [Mock(message=Mock(content=json.dumps({
                "transcription": "test",
                "pass_type": "test",
                "confidence_level": "high"
            })))]
            return response
        
        with patch('tools.image_viewer_tool.openai.OpenAI') as mock_openai_class:
            mock_client = Mock()
            mock_openai_class.return_value = mock_client
            mock_client.chat.completions.create.side_effect = capture_messages
            
            # Run the tool
            result = tool._run(image_path=test_image_path)
            
            # Check that all prompts mention top lines
            assert len(captured_messages) == 3
            for messages in captured_messages:
                prompt_text = messages[0]['content'][0]['text']
                assert 'top' in prompt_text.lower() or 'first 4-5 lines' in prompt_text.lower()


# Run tests if executed directly
if __name__ == "__main__":
    pytest.main([__file__, "-v"])