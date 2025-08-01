"""
Comprehensive unit tests for SyncDBStorageTool.

This module implements task 10 requirements:
- Unit tests for SyncDBStorageTool
- Test database operations with real connections
- Test error handling and edge cases
- Validate storage functionality

Requirements: 5.1, 5.2, 5.3, 5.4
"""
import pytest
import json
import os
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import uuid

# Import the tool to test
import sys
sys.path.append(str(Path(__file__).parent.parent.parent.parent))
from sparkjar_shared.tools.sync_db_storage_tool import SyncDBStorageTool


class TestSyncDBStorageTool:
    """Comprehensive tests for SyncDBStorageTool."""
    
    @pytest.fixture
    def tool(self):
        """Create a SyncDBStorageTool instance."""
        return SyncDBStorageTool()
    
    @pytest.fixture
    def test_db_url(self):
        """Get test database URL from environment or use SQLite."""
        # Use SQLite for testing if no test DB is configured
        return os.getenv('TEST_DATABASE_URL', 'sqlite:///test_book_ingestion.db')
    
    @pytest.fixture
    def test_engine(self, test_db_url):
        """Create test database engine."""
        engine = create_engine(test_db_url)
        
        # Create test table if it doesn't exist
        with engine.connect() as conn:
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS book_ingestions (
                    id TEXT PRIMARY KEY,
                    book_key TEXT NOT NULL,
                    page_number INTEGER NOT NULL,
                    file_name TEXT NOT NULL,
                    language_code TEXT NOT NULL,
                    version TEXT NOT NULL DEFAULT 'original',
                    page_text TEXT NOT NULL,
                    ocr_metadata TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))
            conn.commit()
        
        return engine
    
    @pytest.fixture
    def test_session(self, test_engine):
        """Create test database session."""
        Session = sessionmaker(bind=test_engine)
        session = Session()
        yield session
        # Cleanup
        session.rollback()
        session.close()
    
    @pytest.fixture
    def sample_ocr_metadata(self):
        """Sample OCR metadata for testing."""
        return {
            "file_id": "google-drive-file-123",
            "processing_stats": {
                "total_words": 150,
                "normal_transcription": 120,
                "context_logic_transcription": 25,
                "unable_to_transcribe": 5
            },
            "unclear_sections": ["word1", "phrase2"],
            "ocr_passes": 3,
            "model_used": "gpt-4o"
        }
    
    def test_successful_storage(self, tool, test_session, sample_ocr_metadata):
        """Test successful page storage."""
        with patch('tools.sync_db_storage_tool.create_engine'):
            with patch('tools.sync_db_storage_tool.sessionmaker', return_value=Mock(return_value=test_session)):
                # Run the tool
                result = tool._run(
                    client_user_id='test-client-123',
                    book_key='test_book_folder',
                    page_number=1,
                    file_name='page001.png',
                    language_code='es',
                    page_text='Esta es la primera página del manuscrito.',
                    ocr_metadata=sample_ocr_metadata
                )
                
                # Parse result
                result_data = json.loads(result)
                
                # Assertions
                assert result_data['success'] is True
                assert 'page_id' in result_data
                assert result_data['page_number'] == 1
                assert result_data['file_name'] == 'page001.png'
                
                # Verify data was stored in database
                stored_page = test_session.execute(
                    text("SELECT * FROM book_ingestions WHERE id = :id"),
                    {"id": result_data['page_id']}
                ).fetchone()
                
                assert stored_page is not None
                assert stored_page.book_key == 'test_book_folder'
                assert stored_page.page_number == 1
                assert stored_page.file_name == 'page001.png'
                assert stored_page.language_code == 'es'
                assert stored_page.page_text == 'Esta es la primera página del manuscrito.'
    
    def test_missing_required_fields(self, tool):
        """Test error handling for missing required fields."""
        # Test missing client_user_id
        result = tool._run(
            client_user_id=None,
            book_key='test_book',
            page_number=1,
            file_name='page001.png',
            language_code='es',
            page_text='Test text',
            ocr_metadata={}
        )
        
        result_data = json.loads(result)
        assert result_data['success'] is False
        assert 'client_user_id is required' in result_data['error']
        
        # Test missing book_key
        result = tool._run(
            client_user_id='test-client',
            book_key=None,
            page_number=1,
            file_name='page001.png',
            language_code='es',
            page_text='Test text',
            ocr_metadata={}
        )
        
        result_data = json.loads(result)
        assert result_data['success'] is False
        assert 'book_key is required' in result_data['error']
    
    def test_duplicate_page_handling(self, tool, test_session, sample_ocr_metadata):
        """Test handling of duplicate page numbers."""
        with patch('tools.sync_db_storage_tool.create_engine'):
            with patch('tools.sync_db_storage_tool.sessionmaker', return_value=Mock(return_value=test_session)):
                # Insert first page
                result1 = tool._run(
                    client_user_id='test-client-123',
                    book_key='test_book_folder',
                    page_number=1,
                    file_name='page001.png',
                    language_code='es',
                    page_text='Primera versión del texto.',
                    ocr_metadata=sample_ocr_metadata
                )
                
                # Try to insert same page again
                result2 = tool._run(
                    client_user_id='test-client-123',
                    book_key='test_book_folder',
                    page_number=1,
                    file_name='page001_v2.png',
                    language_code='es',
                    page_text='Segunda versión del texto.',
                    ocr_metadata=sample_ocr_metadata
                )
                
                result1_data = json.loads(result1)
                result2_data = json.loads(result2)
                
                # Both should succeed (no unique constraint on page numbers)
                assert result1_data['success'] is True
                assert result2_data['success'] is True
                
                # Verify both are stored
                pages = test_session.execute(
                    text("SELECT * FROM book_ingestions WHERE book_key = :book_key AND page_number = :page_number"),
                    {"book_key": "test_book_folder", "page_number": 1}
                ).fetchall()
                
                assert len(pages) == 2
    
    def test_ocr_metadata_serialization(self, tool, test_session):
        """Test that OCR metadata is properly serialized."""
        complex_metadata = {
            "file_id": "test-123",
            "processing_stats": {
                "total_words": 200,
                "normal_transcription": 180,
                "context_logic_transcription": 15,
                "unable_to_transcribe": 5
            },
            "unclear_sections": ["section1", "section2", "section3"],
            "ocr_passes": 3,
            "model_used": "gpt-4o",
            "nested": {
                "deep": {
                    "value": "test"
                }
            }
        }
        
        with patch('tools.sync_db_storage_tool.create_engine'):
            with patch('tools.sync_db_storage_tool.sessionmaker', return_value=Mock(return_value=test_session)):
                # Run the tool
                result = tool._run(
                    client_user_id='test-client-123',
                    book_key='test_book_folder',
                    page_number=2,
                    file_name='page002.png',
                    language_code='es',
                    page_text='Texto con metadata compleja.',
                    ocr_metadata=complex_metadata
                )
                
                result_data = json.loads(result)
                assert result_data['success'] is True
                
                # Verify metadata was stored correctly
                stored_page = test_session.execute(
                    text("SELECT ocr_metadata FROM book_ingestions WHERE id = :id"),
                    {"id": result_data['page_id']}
                ).fetchone()
                
                stored_metadata = json.loads(stored_page.ocr_metadata)
                assert stored_metadata['file_id'] == 'test-123'
                assert stored_metadata['processing_stats']['total_words'] == 200
                assert len(stored_metadata['unclear_sections']) == 3
                assert stored_metadata['nested']['deep']['value'] == 'test'
    
    def test_long_text_storage(self, tool, test_session, sample_ocr_metadata):
        """Test storage of long text content."""
        # Create a long text (10KB)
        long_text = "Esta es una línea de texto. " * 500
        
        with patch('tools.sync_db_storage_tool.create_engine'):
            with patch('tools.sync_db_storage_tool.sessionmaker', return_value=Mock(return_value=test_session)):
                # Run the tool
                result = tool._run(
                    client_user_id='test-client-123',
                    book_key='test_book_folder',
                    page_number=3,
                    file_name='page003.png',
                    language_code='es',
                    page_text=long_text,
                    ocr_metadata=sample_ocr_metadata
                )
                
                result_data = json.loads(result)
                assert result_data['success'] is True
                
                # Verify long text was stored
                stored_page = test_session.execute(
                    text("SELECT page_text FROM book_ingestions WHERE id = :id"),
                    {"id": result_data['page_id']}
                ).fetchone()
                
                assert stored_page.page_text == long_text
    
    def test_special_characters_handling(self, tool, test_session, sample_ocr_metadata):
        """Test handling of special characters in text."""
        special_text = "Texto con caracteres especiales: ñ, á, é, í, ó, ú, ¿?, ¡!, €, 'quotes', \"double\""
        
        with patch('tools.sync_db_storage_tool.create_engine'):
            with patch('tools.sync_db_storage_tool.sessionmaker', return_value=Mock(return_value=test_session)):
                # Run the tool
                result = tool._run(
                    client_user_id='test-client-123',
                    book_key='test_book_folder',
                    page_number=4,
                    file_name='page004.png',
                    language_code='es',
                    page_text=special_text,
                    ocr_metadata=sample_ocr_metadata
                )
                
                result_data = json.loads(result)
                assert result_data['success'] is True
                
                # Verify special characters were preserved
                stored_page = test_session.execute(
                    text("SELECT page_text FROM book_ingestions WHERE id = :id"),
                    {"id": result_data['page_id']}
                ).fetchone()
                
                assert stored_page.page_text == special_text
    
    def test_language_code_validation(self, tool, test_session, sample_ocr_metadata):
        """Test various language codes."""
        language_codes = ['es', 'en', 'fr', 'de', 'it', 'pt', 'zh', 'ja', 'ar']
        
        with patch('tools.sync_db_storage_tool.create_engine'):
            with patch('tools.sync_db_storage_tool.sessionmaker', return_value=Mock(return_value=test_session)):
                for idx, lang_code in enumerate(language_codes):
                    result = tool._run(
                        client_user_id='test-client-123',
                        book_key='test_book_folder',
                        page_number=10 + idx,
                        file_name=f'page{10+idx:03d}.png',
                        language_code=lang_code,
                        page_text=f'Text in {lang_code} language.',
                        ocr_metadata=sample_ocr_metadata
                    )
                    
                    result_data = json.loads(result)
                    assert result_data['success'] is True
                    
                    # Verify language code was stored
                    stored_page = test_session.execute(
                        text("SELECT language_code FROM book_ingestions WHERE id = :id"),
                        {"id": result_data['page_id']}
                    ).fetchone()
                    
                    assert stored_page.language_code == lang_code
    
    def test_database_connection_error(self, tool, sample_ocr_metadata):
        """Test handling of database connection errors."""
        with patch('tools.sync_db_storage_tool.create_engine') as mock_create_engine:
            mock_create_engine.side_effect = Exception("Database connection failed")
            
            # Run the tool
            result = tool._run(
                client_user_id='test-client-123',
                book_key='test_book_folder',
                page_number=1,
                file_name='page001.png',
                language_code='es',
                page_text='Test text',
                ocr_metadata=sample_ocr_metadata
            )
            
            result_data = json.loads(result)
            assert result_data['success'] is False
            assert 'Database connection failed' in result_data['error']
    
    def test_transaction_rollback(self, tool, test_session, sample_ocr_metadata):
        """Test that transactions are rolled back on error."""
        with patch('tools.sync_db_storage_tool.create_engine'):
            with patch('tools.sync_db_storage_tool.sessionmaker', return_value=Mock(return_value=test_session)):
                # Mock session.add to raise an error
                original_add = test_session.add
                test_session.add = Mock(side_effect=Exception("Simulated database error"))
                
                # Run the tool
                result = tool._run(
                    client_user_id='test-client-123',
                    book_key='test_book_folder',
                    page_number=99,
                    file_name='page099.png',
                    language_code='es',
                    page_text='This should not be saved.',
                    ocr_metadata=sample_ocr_metadata
                )
                
                # Restore original method
                test_session.add = original_add
                
                result_data = json.loads(result)
                assert result_data['success'] is False
                
                # Verify nothing was saved
                pages = test_session.execute(
                    text("SELECT * FROM book_ingestions WHERE page_number = 99")
                ).fetchall()
                
                assert len(pages) == 0
    
    def test_empty_metadata_handling(self, tool, test_session):
        """Test handling of empty/None OCR metadata."""
        with patch('tools.sync_db_storage_tool.create_engine'):
            with patch('tools.sync_db_storage_tool.sessionmaker', return_value=Mock(return_value=test_session)):
                # Test with None metadata
                result = tool._run(
                    client_user_id='test-client-123',
                    book_key='test_book_folder',
                    page_number=20,
                    file_name='page020.png',
                    language_code='es',
                    page_text='Text without metadata.',
                    ocr_metadata=None
                )
                
                result_data = json.loads(result)
                assert result_data['success'] is True
                
                # Test with empty dict
                result = tool._run(
                    client_user_id='test-client-123',
                    book_key='test_book_folder',
                    page_number=21,
                    file_name='page021.png',
                    language_code='es',
                    page_text='Text with empty metadata.',
                    ocr_metadata={}
                )
                
                result_data = json.loads(result)
                assert result_data['success'] is True


# Run tests if executed directly
if __name__ == "__main__":
    pytest.main([__file__, "-v"])