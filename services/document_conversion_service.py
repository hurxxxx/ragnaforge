"""Document conversion service using datalab-marker."""

import os
import logging
import tempfile
import shutil
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional

logger = logging.getLogger(__name__)


class DocumentConversionService:
    """Service for converting documents to markdown using datalab-marker."""

    def __init__(self, output_dir: str = "converted_docs"):
        """Initialize the document conversion service.
        
        Args:
            output_dir: Directory to save converted documents and images
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        # Create subdirectories for different types of output
        (self.output_dir / "markdown").mkdir(exist_ok=True)
        (self.output_dir / "images").mkdir(exist_ok=True)
        (self.output_dir / "json").mkdir(exist_ok=True)
        (self.output_dir / "html").mkdir(exist_ok=True)

    def convert_document(
        self,
        file_path: str,
        output_format: str = "markdown",
        extract_images: bool = True,
        use_llm: bool = False
    ) -> Dict[str, Any]:
        """Convert a document to the specified format.
        
        Args:
            file_path: Path to the input document
            output_format: Output format (markdown, json, html)
            extract_images: Whether to extract and save images
            use_llm: Whether to use LLM for improved accuracy
            
        Returns:
            Dictionary containing conversion results
        """
        try:
            # Import marker components
            from marker.converters.pdf import PdfConverter
            from marker.models import create_model_dict
            from marker.output import text_from_rendered
            from marker.config.parser import ConfigParser
            
            logger.info(f"Starting conversion of {file_path} to {output_format}")
            
            # Prepare configuration
            config = {
                "output_format": output_format,
                "disable_image_extraction": not extract_images,
                "use_llm": use_llm
            }
            
            config_parser = ConfigParser(config)
            
            # Create converter
            converter = PdfConverter(
                config=config_parser.generate_config_dict(),
                artifact_dict=create_model_dict(),
                processor_list=config_parser.get_processors(),
                renderer=config_parser.get_renderer()
            )
            
            if use_llm:
                converter.llm_service = config_parser.get_llm_service()
            
            # Convert document
            rendered = converter(file_path)
            
            # Extract content based on format
            result = {
                "output_format": output_format,
                "images": [],
                "metadata": {},
                "file_path": ""
            }
            
            if output_format == "markdown":
                text, metadata, images = text_from_rendered(rendered)
                result["markdown_content"] = text

                # Handle metadata - ensure it's a dictionary
                if isinstance(metadata, dict):
                    result["metadata"] = metadata
                elif metadata is not None:
                    result["metadata"] = {"raw_metadata": str(metadata)}
                else:
                    result["metadata"] = {}

                # Save markdown file
                file_stem = Path(file_path).stem
                markdown_path = self.output_dir / "markdown" / f"{file_stem}.md"
                with open(markdown_path, 'w', encoding='utf-8') as f:
                    f.write(text)
                result["file_path"] = str(markdown_path)

                # Save images if extracted
                if extract_images and images:
                    result["images"] = self._save_images(images, file_stem)
                    
            elif output_format == "json":
                result["json_content"] = rendered.model_dump() if hasattr(rendered, 'model_dump') else rendered
                result["metadata"] = getattr(rendered, 'metadata', {})
                
                # Save JSON file
                import json
                file_stem = Path(file_path).stem
                json_path = self.output_dir / "json" / f"{file_stem}.json"
                with open(json_path, 'w', encoding='utf-8') as f:
                    json.dump(result["json_content"], f, ensure_ascii=False, indent=2)
                result["file_path"] = str(json_path)
                
            elif output_format == "html":
                # For HTML, we need to convert from rendered format
                if hasattr(rendered, 'html'):
                    result["html_content"] = rendered.html
                else:
                    # Fallback: convert markdown to HTML if needed
                    text, metadata, images = text_from_rendered(rendered)
                    result["html_content"] = self._markdown_to_html(text)
                
                result["metadata"] = getattr(rendered, 'metadata', {})
                
                # Save HTML file
                file_stem = Path(file_path).stem
                html_path = self.output_dir / "html" / f"{file_stem}.html"
                with open(html_path, 'w', encoding='utf-8') as f:
                    f.write(result["html_content"])
                result["file_path"] = str(html_path)
            
            logger.info(f"Successfully converted {file_path}")
            return result
            
        except Exception as e:
            logger.error(f"Error converting document {file_path}: {str(e)}")
            raise

    def _save_images(self, images: Dict[str, bytes], file_stem: str) -> List[str]:
        """Save extracted images to the images directory.
        
        Args:
            images: Dictionary of image data (filename -> bytes)
            file_stem: Stem of the original file for naming
            
        Returns:
            List of saved image filenames
        """
        saved_images = []
        
        for i, (image_id, image_data) in enumerate(images.items()):
            try:
                # Generate filename
                image_filename = f"{file_stem}_image_{i+1}.png"
                image_path = self.output_dir / "images" / image_filename
                
                # Save image
                with open(image_path, 'wb') as f:
                    f.write(image_data)
                
                saved_images.append(image_filename)
                logger.debug(f"Saved image: {image_filename}")
                
            except Exception as e:
                logger.warning(f"Failed to save image {image_id}: {str(e)}")
        
        return saved_images

    def _markdown_to_html(self, markdown_text: str) -> str:
        """Simple markdown to HTML conversion fallback.
        
        Args:
            markdown_text: Markdown content
            
        Returns:
            HTML content
        """
        # Very basic markdown to HTML conversion
        # In a production environment, you might want to use a proper markdown library
        html = markdown_text.replace('\n\n', '</p><p>')
        html = f"<html><body><p>{html}</p></body></html>"
        return html

    def get_supported_formats(self) -> List[str]:
        """Get list of supported input file formats.
        
        Returns:
            List of supported file extensions
        """
        return [
            ".pdf", ".png", ".jpg", ".jpeg", ".tiff", ".bmp",
            ".pptx", ".ppt", ".docx", ".doc", ".xlsx", ".xls",
            ".html", ".htm", ".epub"
        ]

    def is_supported_format(self, file_path: str) -> bool:
        """Check if the file format is supported.
        
        Args:
            file_path: Path to the file
            
        Returns:
            True if format is supported, False otherwise
        """
        file_ext = Path(file_path).suffix.lower()
        return file_ext in self.get_supported_formats()


# Global service instance
document_conversion_service = DocumentConversionService()
