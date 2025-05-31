"""Test document conversion functionality."""

import pytest
import tempfile
import os
from pathlib import Path
from services.document_conversion_service import DocumentConversionService


class TestDocumentConversionService:
    """Test cases for document conversion service."""

    @pytest.fixture
    def service(self):
        """Create a document conversion service instance for testing."""
        # Use a temporary directory for testing
        with tempfile.TemporaryDirectory() as temp_dir:
            yield DocumentConversionService(output_dir=temp_dir)

    @pytest.fixture
    def sample_pdf_path(self):
        """Create a simple test PDF file."""
        # For testing, we'll create a simple text file that can be used
        # In a real scenario, you'd want to use an actual PDF
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("This is a test document.\n\nIt has multiple paragraphs.\n\nAnd some content to convert.")
            temp_path = f.name
        
        yield temp_path
        
        # Cleanup
        if os.path.exists(temp_path):
            os.unlink(temp_path)

    def test_service_initialization(self, service):
        """Test service initialization."""
        assert service.output_dir.exists()
        assert (service.output_dir / "markdown").exists()
        assert (service.output_dir / "images").exists()
        assert (service.output_dir / "json").exists()
        assert (service.output_dir / "html").exists()

    def test_supported_formats(self, service):
        """Test supported file formats."""
        supported_formats = service.get_supported_formats()
        
        # Check that common formats are supported
        assert ".pdf" in supported_formats
        assert ".docx" in supported_formats
        assert ".pptx" in supported_formats
        assert ".html" in supported_formats
        
        # Test format checking
        assert service.is_supported_format("test.pdf")
        assert service.is_supported_format("test.docx")
        assert service.is_supported_format("test.PPTX")  # Case insensitive
        assert not service.is_supported_format("test.xyz")

    def test_markdown_to_html_conversion(self, service):
        """Test basic markdown to HTML conversion."""
        markdown_text = "# Header\n\nThis is a paragraph.\n\n## Subheader\n\nAnother paragraph."
        html_result = service._markdown_to_html(markdown_text)
        
        assert "<html>" in html_result
        assert "<body>" in html_result
        assert "<p>" in html_result

    def test_save_images(self, service):
        """Test image saving functionality."""
        # Create mock image data
        mock_images = {
            "image_1": b"fake_image_data_1",
            "image_2": b"fake_image_data_2"
        }
        
        saved_images = service._save_images(mock_images, "test_doc")
        
        assert len(saved_images) == 2
        assert "test_doc_image_1.png" in saved_images
        assert "test_doc_image_2.png" in saved_images
        
        # Check that files were actually created
        for image_name in saved_images:
            image_path = service.output_dir / "images" / image_name
            assert image_path.exists()

    @pytest.mark.skip(reason="Requires marker-pdf installation and actual document")
    def test_document_conversion_markdown(self, service, sample_pdf_path):
        """Test document conversion to markdown format."""
        # This test would require marker-pdf to be installed and working
        result = service.convert_document(
            file_path=sample_pdf_path,
            output_format="markdown",
            extract_images=True,
            use_llm=False
        )
        
        assert result["output_format"] == "markdown"
        assert "markdown_content" in result
        assert "file_path" in result
        assert Path(result["file_path"]).exists()

    @pytest.mark.skip(reason="Requires marker-pdf installation and actual document")
    def test_document_conversion_json(self, service, sample_pdf_path):
        """Test document conversion to JSON format."""
        result = service.convert_document(
            file_path=sample_pdf_path,
            output_format="json",
            extract_images=False,
            use_llm=False
        )
        
        assert result["output_format"] == "json"
        assert "json_content" in result
        assert "file_path" in result
        assert Path(result["file_path"]).exists()

    @pytest.mark.skip(reason="Requires marker-pdf installation and actual document")
    def test_document_conversion_html(self, service, sample_pdf_path):
        """Test document conversion to HTML format."""
        result = service.convert_document(
            file_path=sample_pdf_path,
            output_format="html",
            extract_images=False,
            use_llm=False
        )
        
        assert result["output_format"] == "html"
        assert "html_content" in result
        assert "file_path" in result
        assert Path(result["file_path"]).exists()


@pytest.mark.asyncio
class TestDocumentConversionAPI:
    """Test cases for document conversion API endpoints."""

    @pytest.mark.skip(reason="Requires full API setup and marker-pdf installation")
    async def test_convert_endpoint_with_pdf(self):
        """Test the /v1/convert endpoint with a PDF file."""
        # This would require setting up the full FastAPI test client
        # and having marker-pdf properly installed
        pass

    @pytest.mark.skip(reason="Requires full API setup")
    async def test_convert_endpoint_unsupported_format(self):
        """Test the /v1/convert endpoint with unsupported file format."""
        # This would test error handling for unsupported formats
        pass

    @pytest.mark.skip(reason="Requires full API setup")
    async def test_convert_endpoint_invalid_output_format(self):
        """Test the /v1/convert endpoint with invalid output format."""
        # This would test validation of output format parameter
        pass


if __name__ == "__main__":
    # Simple test runner for basic functionality
    print("Running basic document conversion service tests...")
    
    # Test service initialization
    service = DocumentConversionService("test_output")
    print("✓ Service initialization test passed")
    
    # Test supported formats
    formats = service.get_supported_formats()
    assert len(formats) > 0
    print(f"✓ Supported formats test passed: {len(formats)} formats supported")
    
    # Test format checking
    assert service.is_supported_format("test.pdf")
    assert not service.is_supported_format("test.xyz")
    print("✓ Format checking test passed")
    
    # Test markdown to HTML conversion
    html = service._markdown_to_html("# Test\n\nContent")
    assert "<html>" in html
    print("✓ Markdown to HTML conversion test passed")
    
    print("\nAll basic tests passed! 🎉")
    print("\nNote: Full document conversion tests require marker-pdf installation.")
    print("Install with: pip install marker-pdf[full]")
