"""Docling PDF conversion service."""

import logging
import time
import os
from pathlib import Path
from typing import Dict, Any, Optional, List
import torch

logger = logging.getLogger(__name__)


class DoclingService:
    """Service for converting PDFs to markdown using docling."""
    
    def __init__(self):
        self._converter = None
        self._is_initialized = False
        
    def _initialize(self):
        """Initialize docling converter."""
        if self._is_initialized:
            return

        try:
            # Check if docling is installed
            try:
                import docling
            except ImportError:
                raise ImportError("docling package is not installed. Please install with: pip install docling")

            from docling.document_converter import DocumentConverter
            from docling.datamodel.base_models import InputFormat
            from docling.datamodel.pipeline_options import PdfPipelineOptions
            from docling.document_converter import PdfFormatOption

            logger.info("Initializing Docling service...")

            # Configure pipeline options for GPU if available
            pipeline_options = PdfPipelineOptions()

            if torch.cuda.is_available():
                logger.info(f"Using CUDA device: {torch.cuda.get_device_name()}")
                # Enable GPU acceleration for docling
                try:
                    from docling.datamodel.pipeline_options import AcceleratorDevice
                    pipeline_options.accelerator_options.device = AcceleratorDevice.CUDA
                    pipeline_options.accelerator_options.cuda_use_flash_attention2 = True
                    logger.info("GPU acceleration enabled for Docling")
                except (ImportError, AttributeError) as e:
                    logger.warning(f"GPU acceleration options not available in this docling version: {e}")
            else:
                logger.warning("CUDA not available, using CPU")

            # Create converter with multi-format support
            logger.info("Creating Docling converter with multi-format support...")
            format_options = {
                InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
                # DOCX, PPTX, XLSX use default options (no special configuration needed)
            }

            self._converter = DocumentConverter(format_options=format_options)

            # Log supported formats
            supported_formats = [fmt.value for fmt in InputFormat]
            logger.info(f"Docling converter supports: {', '.join(supported_formats)}")

            self._is_initialized = True
            logger.info("Docling service initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize Docling service: {str(e)}")
            raise
    
    def convert_pdf_to_markdown(
        self, 
        pdf_path: str, 
        output_dir: Optional[str] = None,
        extract_images: bool = True
    ) -> Dict[str, Any]:
        """
        Convert PDF to markdown using docling.
        
        Args:
            pdf_path: Path to the PDF file
            output_dir: Directory to save output files (optional)
            extract_images: Whether to extract images
            
        Returns:
            Dictionary containing conversion results and metadata
        """
        self._initialize()
        
        start_time = time.time()
        
        try:
            # Convert PDF
            logger.info(f"Converting PDF with Docling: {pdf_path}")
            result = self._converter.convert(pdf_path)
            
            # Extract markdown
            markdown_text = result.document.export_to_markdown()
            
            conversion_time = time.time() - start_time
            
            # Save files if output directory is specified
            saved_files = []
            if output_dir:
                output_path = Path(output_dir)
                output_path.mkdir(parents=True, exist_ok=True)
                
                # Save markdown
                pdf_name = Path(pdf_path).stem
                markdown_file = output_path / f"{pdf_name}_docling.md"
                with open(markdown_file, 'w', encoding='utf-8') as f:
                    f.write(markdown_text)
                saved_files.append(str(markdown_file))
                
                # Save as HTML and JSON as well
                html_file = output_path / f"{pdf_name}_docling.html"
                result.document.save_as_html(html_file)
                saved_files.append(str(html_file))
                
                json_file = output_path / f"{pdf_name}_docling.json"
                result.document.save_as_json(json_file)
                saved_files.append(str(json_file))
            
            # Get GPU memory usage if available
            gpu_memory_used = None
            if torch.cuda.is_available():
                gpu_memory_used = torch.cuda.max_memory_allocated() / 1024**3  # GB
                torch.cuda.reset_peak_memory_stats()
            
            # Extract metadata
            metadata = {
                'num_pages': result.document.num_pages(),
                'title': getattr(result.document, 'title', None),
                'creation_date': getattr(result.document, 'creation_date', None),
                'modification_date': getattr(result.document, 'modification_date', None)
            }
            
            # Count images in the document
            images_count = 0
            try:
                for page in result.document.pages:
                    for item in page.items:
                        if hasattr(item, 'label') and 'picture' in str(item.label).lower():
                            images_count += 1
            except:
                images_count = 0
            
            conversion_result = {
                'success': True,
                'markdown': markdown_text,
                'metadata': metadata,
                'images_count': images_count,
                'conversion_time': conversion_time,
                'gpu_memory_used_gb': gpu_memory_used,
                'saved_files': saved_files,
                'library': 'docling',
                'file_size_mb': os.path.getsize(pdf_path) / 1024**2,
                'markdown_length': len(markdown_text)
            }
            
            logger.info(f"Docling conversion completed in {conversion_time:.2f}s")
            return conversion_result
            
        except Exception as e:
            conversion_time = time.time() - start_time
            logger.error(f"Docling conversion failed: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'conversion_time': conversion_time,
                'library': 'docling',
                'file_size_mb': os.path.getsize(pdf_path) / 1024**2 if os.path.exists(pdf_path) else 0.0,
                'markdown_length': 0,
                'images_count': 0,
                'gpu_memory_used_gb': None,
                'saved_files': [],
                'metadata': None
            }
    
    def convert_office_to_markdown(
        self,
        file_path: str,
        output_dir: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Convert Office documents (DOCX, PPTX, XLSX) to markdown using docling.

        Args:
            file_path: Path to the Office file
            output_dir: Directory to save output files (optional)

        Returns:
            Dictionary containing conversion results and metadata
        """
        self._initialize()

        start_time = time.time()
        file_path = Path(file_path)

        # Validate file type
        supported_extensions = {'.docx', '.pptx', '.xlsx'}
        if file_path.suffix.lower() not in supported_extensions:
            raise ValueError(f"Unsupported file type: {file_path.suffix}. Supported: {supported_extensions}")

        try:
            # Convert Office document
            logger.info(f"Converting Office document with Docling: {file_path}")
            result = self._converter.convert(str(file_path))

            # Extract markdown
            markdown_text = result.document.export_to_markdown()

            conversion_time = time.time() - start_time

            # Extract metadata
            metadata = {
                'title': getattr(result.document, 'title', ''),
                'page_count': len(result.document.pages) if hasattr(result.document, 'pages') else 1,
                'file_type': file_path.suffix.lower(),
                'file_name': file_path.name
            }

            # Save files if output directory is specified
            saved_files = []
            if output_dir:
                output_path = Path(output_dir)
                output_path.mkdir(parents=True, exist_ok=True)

                # Save markdown
                file_stem = file_path.stem
                markdown_file = output_path / f"{file_stem}_docling.md"
                with open(markdown_file, 'w', encoding='utf-8') as f:
                    f.write(markdown_text)
                saved_files.append(str(markdown_file))

                # Save as HTML and JSON as well
                html_file = output_path / f"{file_stem}_docling.html"
                result.document.save_as_html(html_file)
                saved_files.append(str(html_file))

                json_file = output_path / f"{file_stem}_docling.json"
                result.document.save_as_json(json_file)
                saved_files.append(str(json_file))

                logger.info(f"Saved conversion results to {len(saved_files)} files")

            # Get GPU memory usage if available
            gpu_memory_used = None
            if torch.cuda.is_available():
                gpu_memory_used = torch.cuda.max_memory_allocated() / 1024**3  # GB
                torch.cuda.reset_peak_memory_stats()

            conversion_result = {
                'success': True,
                'markdown': markdown_text,
                'metadata': metadata,
                'conversion_time': conversion_time,
                'gpu_memory_used_gb': gpu_memory_used,
                'saved_files': saved_files,
                'library': 'docling',
                'file_size_mb': file_path.stat().st_size / 1024**2,
                'markdown_length': len(markdown_text),
                'file_type': file_path.suffix.lower()
            }

            logger.info(f"Docling Office conversion completed in {conversion_time:.2f}s")
            return conversion_result

        except Exception as e:
            conversion_time = time.time() - start_time
            logger.error(f"Docling Office conversion failed: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'conversion_time': conversion_time,
                'library': 'docling',
                'file_size_mb': file_path.stat().st_size / 1024**2 if file_path.exists() else 0.0,
                'markdown_length': 0,
                'gpu_memory_used_gb': None,
                'saved_files': [],
                'metadata': None,
                'file_type': file_path.suffix.lower()
            }

    def convert_document(
        self,
        file_path: str,
        output_dir: Optional[str] = None,
        extract_images: bool = True
    ) -> Dict[str, Any]:
        """
        Universal document converter that handles both PDF and Office documents.

        Args:
            file_path: Path to the document file
            output_dir: Directory to save output files (optional)
            extract_images: Whether to extract images (for PDF only)

        Returns:
            Dictionary containing conversion results and metadata
        """
        file_path = Path(file_path)
        file_extension = file_path.suffix.lower()

        if file_extension == '.pdf':
            return self.convert_pdf_to_markdown(str(file_path), output_dir, extract_images)
        elif file_extension in {'.docx', '.pptx', '.xlsx'}:
            return self.convert_office_to_markdown(str(file_path), output_dir)
        else:
            raise ValueError(f"Unsupported file type: {file_extension}. Supported: .pdf, .docx, .pptx, .xlsx")

    def get_supported_formats(self) -> List[str]:
        """Get list of supported file formats."""
        return ['.pdf', '.docx', '.pptx', '.xlsx']

    def get_info(self) -> Dict[str, Any]:
        """Get service information."""
        return {
            'service': 'docling',
            'initialized': self._is_initialized,
            'cuda_available': torch.cuda.is_available(),
            'cuda_device': torch.cuda.get_device_name() if torch.cuda.is_available() else None,
            'supported_formats': self.get_supported_formats()
        }


# Global docling service instance
docling_service = DoclingService()
