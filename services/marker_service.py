"""Marker PDF conversion service."""

import logging
import time
import os
from pathlib import Path
from typing import Dict, Any, Optional
import torch

logger = logging.getLogger(__name__)


class MarkerService:
    """Service for converting PDFs to markdown using marker-pdf."""
    
    def __init__(self):
        self._converter = None
        self._model_dict = None
        self._is_initialized = False
        
    def _initialize(self):
        """Initialize marker converter and models."""
        if self._is_initialized:
            return
            
        try:
            from marker.converters.pdf import PdfConverter
            from marker.models import create_model_dict
            
            logger.info("Initializing Marker service...")
            
            # Set CUDA device if available
            if torch.cuda.is_available():
                os.environ['TORCH_DEVICE'] = 'cuda'
                logger.info(f"Using CUDA device: {torch.cuda.get_device_name()}")
            else:
                logger.warning("CUDA not available, using CPU")
            
            # Create model dictionary (downloads models if needed)
            self._model_dict = create_model_dict()
            
            # Create converter
            self._converter = PdfConverter(
                artifact_dict=self._model_dict,
            )
            
            self._is_initialized = True
            logger.info("Marker service initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Marker service: {str(e)}")
            raise
    
    def convert_pdf_to_markdown(
        self, 
        pdf_path: str, 
        output_dir: Optional[str] = None,
        extract_images: bool = True
    ) -> Dict[str, Any]:
        """
        Convert PDF to markdown using marker.
        
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
            logger.info(f"Converting PDF with Marker: {pdf_path}")
            rendered = self._converter(pdf_path)
            
            # Extract text and metadata
            from marker.output import text_from_rendered
            markdown_text, metadata, images = text_from_rendered(rendered)
            
            conversion_time = time.time() - start_time
            
            # Save files if output directory is specified
            saved_files = []
            if output_dir:
                output_path = Path(output_dir)
                output_path.mkdir(parents=True, exist_ok=True)
                
                # Save markdown
                pdf_name = Path(pdf_path).stem
                markdown_file = output_path / f"{pdf_name}_marker.md"
                with open(markdown_file, 'w', encoding='utf-8') as f:
                    f.write(markdown_text)
                saved_files.append(str(markdown_file))
                
                # Save images if any
                if images and extract_images:
                    images_dir = output_path / f"{pdf_name}_marker_images"
                    images_dir.mkdir(exist_ok=True)
                    
                    for img_name, img_data in images.items():
                        img_path = images_dir / img_name
                        with open(img_path, 'wb') as f:
                            f.write(img_data)
                        saved_files.append(str(img_path))
            
            # Get GPU memory usage if available
            gpu_memory_used = None
            if torch.cuda.is_available():
                gpu_memory_used = torch.cuda.max_memory_allocated() / 1024**3  # GB
                torch.cuda.reset_peak_memory_stats()
            
            result = {
                'success': True,
                'markdown': markdown_text,
                'metadata': metadata,
                'images_count': len(images) if images else 0,
                'conversion_time': conversion_time,
                'gpu_memory_used_gb': gpu_memory_used,
                'saved_files': saved_files,
                'library': 'marker-pdf',
                'file_size_mb': os.path.getsize(pdf_path) / 1024**2,
                'markdown_length': len(markdown_text)
            }
            
            logger.info(f"Marker conversion completed in {conversion_time:.2f}s")
            return result
            
        except Exception as e:
            conversion_time = time.time() - start_time
            logger.error(f"Marker conversion failed: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'conversion_time': conversion_time,
                'library': 'marker-pdf'
            }
    
    def get_info(self) -> Dict[str, Any]:
        """Get service information."""
        return {
            'service': 'marker-pdf',
            'initialized': self._is_initialized,
            'cuda_available': torch.cuda.is_available(),
            'cuda_device': torch.cuda.get_device_name() if torch.cuda.is_available() else None
        }


# Global marker service instance
marker_service = MarkerService()
