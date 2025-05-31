"""Docling PDF conversion service."""

import logging
import time
import os
from pathlib import Path
from typing import Dict, Any, Optional
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
                except ImportError:
                    logger.warning("GPU acceleration options not available in this docling version")
            else:
                logger.warning("CUDA not available, using CPU")
            
            # Create converter with optimized settings
            self._converter = DocumentConverter(
                format_options={
                    InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
                }
            )
            
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
                'library': 'docling'
            }
    
    def get_info(self) -> Dict[str, Any]:
        """Get service information."""
        return {
            'service': 'docling',
            'initialized': self._is_initialized,
            'cuda_available': torch.cuda.is_available(),
            'cuda_device': torch.cuda.get_device_name() if torch.cuda.is_available() else None
        }


# Global docling service instance
docling_service = DoclingService()
