#!/usr/bin/env python3
# /Users/han/Code/MOB-BREF/enhanced_pdf_processor.py

"""
Enhanced PDF Processor voor Vergunningen
Extraheert tekst, schema's, foto's, tabellen en bijlagen
"""

from docling.document_converter import DocumentConverter
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions
from docling.backend.pypdfium2_backend import PyPdfiumDocumentBackend
import json
import fitz  # PyMuPDF voor afbeeldingen
import pandas as pd
import os
from typing import Dict, List, Any, Optional
from pathlib import Path
import base64
from PIL import Image
import io

class EnhancedPDFProcessor:
    """Enhanced PDF processor die alle content types extraheert"""
    
    def __init__(self):
        # Configure Docling for comprehensive extraction
        self.pipeline_options = PdfPipelineOptions()
        self.pipeline_options.do_ocr = True  # OCR voor gescande documenten
        self.pipeline_options.do_table_structure = True  # Tabel extractie
        self.pipeline_options.table_structure_options.do_cell_matching = True
        
        self.converter = DocumentConverter(
            format_options={
                InputFormat.PDF: self.pipeline_options,
            }
        )
    
    def extract_comprehensive_content(self, pdf_path: str, output_dir: Optional[str] = None) -> Dict[str, Any]:
        """Comprehensieve extractie van alle PDF content"""
        
        print(f"🔍 === ENHANCED PDF EXTRACTION: {os.path.basename(pdf_path)} ===")
        
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)
        
        result = {
            "file_info": self._get_file_info(pdf_path),
            "text_content": {},
            "images": [],
            "tables": [],
            "metadata": {},
            "structure": {},
            "extraction_stats": {}
        }
        
        try:
            # 1. Docling extraction voor tekst en structuur
            print("📝 Extracting text and structure with Docling...")
            docling_result = self._extract_with_docling(pdf_path)
            result["text_content"] = docling_result["text_content"]
            result["tables"].extend(docling_result.get("tables", []))
            result["structure"] = docling_result.get("structure", {})
            result["metadata"].update(docling_result.get("metadata", {}))
            
            # 2. PyMuPDF extraction voor afbeeldingen en schema's
            print("🖼️ Extracting images and diagrams with PyMuPDF...")
            images_result = self._extract_images_pymupdf(pdf_path, output_dir)
            result["images"] = images_result["images"]
            result["extraction_stats"]["images_found"] = len(images_result["images"])
            
            # 3. Detailed metadata extraction
            print("📊 Extracting detailed metadata...")
            detailed_metadata = self._extract_detailed_metadata(pdf_path)
            result["metadata"].update(detailed_metadata)
            
            # 4. Document structure analysis
            print("🏗️ Analyzing document structure...")
            structure_analysis = self._analyze_document_structure(result["text_content"])
            result["structure"].update(structure_analysis)
            
            # 5. Statistics
            result["extraction_stats"].update({
                "total_pages": result["file_info"]["page_count"],
                "total_text_length": len(result["text_content"].get("full_text", "")),
                "tables_found": len(result["tables"]),
                "sections_identified": len(result["structure"].get("sections", [])),
                "processing_success": True
            })
            
            print(f"✅ Extraction complete!")
            print(f"  📄 Pages: {result['extraction_stats']['total_pages']}")
            print(f"  📝 Text length: {result['extraction_stats']['total_text_length']:,} chars")
            print(f"  🖼️ Images: {result['extraction_stats']['images_found']}")
            print(f"  📊 Tables: {result['extraction_stats']['tables_found']}")
            
            return result
            
        except Exception as e:
            print(f"❌ Error in comprehensive extraction: {e}")
            result["extraction_stats"]["processing_success"] = False
            result["extraction_stats"]["error"] = str(e)
            return result
    
    def _get_file_info(self, pdf_path: str) -> Dict[str, Any]:
        """Get basic file information"""
        file_path = Path(pdf_path)
        return {
            "filename": file_path.name,
            "file_size": file_path.stat().st_size,
            "page_count": self._get_page_count(pdf_path)
        }
    
    def _get_page_count(self, pdf_path: str) -> int:
        """Get page count using PyMuPDF"""
        try:
            doc = fitz.open(pdf_path)
            count = len(doc)
            doc.close()
            return count
        except:
            return 0
    
    def _extract_with_docling(self, pdf_path: str) -> Dict[str, Any]:
        """Extract text and structure using Docling"""
        try:
            result = self.converter.convert(source=pdf_path)
            doc = result.document
            
            docling_data = {
                "text_content": {
                    "full_text": "",
                    "pages": []
                },
                "tables": [],
                "metadata": {},
                "structure": {}
            }
            
            # Extract main text
            if hasattr(doc, 'export_to_markdown'):
                docling_data["text_content"]["full_text"] = doc.export_to_markdown()
            
            # Extract page-by-page content
            if hasattr(doc, 'pages') and isinstance(doc.pages, dict):
                for page_key, page_obj in doc.pages.items():
                    page_data = {
                        "page_number": page_key,
                        "text": "",
                        "elements": []
                    }
                    
                    if hasattr(page_obj, 'export_to_markdown'):
                        page_data["text"] = page_obj.export_to_markdown()
                    
                    # Extract structured elements if available
                    if hasattr(page_obj, 'elements'):
                        for element in page_obj.elements:
                            element_data = {
                                "type": getattr(element, 'type', 'unknown'),
                                "content": getattr(element, 'text', ''),
                                "bbox": getattr(element, 'bbox', None)
                            }
                            page_data["elements"].append(element_data)
                    
                    docling_data["text_content"]["pages"].append(page_data)
            
            # Extract tables
            if hasattr(doc, 'tables'):
                for table in doc.tables:
                    table_data = {
                        "page": getattr(table, 'page', None),
                        "bbox": getattr(table, 'bbox', None),
                        "data": getattr(table, 'data', []),
                        "caption": getattr(table, 'caption', '')
                    }
                    docling_data["tables"].append(table_data)
            
            # Extract metadata
            if hasattr(doc, 'metadata'):
                docling_data["metadata"] = doc.metadata or {}
            
            return docling_data
            
        except Exception as e:
            print(f"❌ Docling extraction error: {e}")
            return {"text_content": {"full_text": "", "pages": []}, "tables": [], "metadata": {}}
    
    def _extract_images_pymupdf(self, pdf_path: str, output_dir: Optional[str] = None) -> Dict[str, Any]:
        """Extract images, diagrams, and figures using PyMuPDF"""
        images_data = {"images": []}
        
        try:
            doc = fitz.open(pdf_path)
            
            for page_num in range(len(doc)):
                page = doc[page_num]
                image_list = page.get_images()
                
                for img_index, img in enumerate(image_list):
                    try:
                        xref = img[0]
                        pix = fitz.Pixmap(doc, xref)
                        
                        if pix.n - pix.alpha < 4:  # GRAY or RGB
                            image_data = {
                                "page": page_num + 1,
                                "index": img_index,
                                "xref": xref,
                                "width": pix.width,
                                "height": pix.height,
                                "colorspace": pix.colorspace.name if pix.colorspace else "unknown",
                                "size_estimate": len(pix.tobytes()),
                                "type": "image"
                            }
                            
                            # Save image if output directory provided
                            if output_dir:
                                img_filename = f"page_{page_num+1}_img_{img_index}.png"
                                img_path = os.path.join(output_dir, img_filename)
                                pix.save(img_path)
                                image_data["saved_path"] = img_path
                            else:
                                # Store as base64 for later use
                                img_bytes = pix.tobytes("png")
                                image_data["base64_data"] = base64.b64encode(img_bytes).decode()
                            
                            images_data["images"].append(image_data)
                        
                        pix = None  # Free memory
                        
                    except Exception as img_e:
                        print(f"⚠️ Error extracting image {img_index} from page {page_num + 1}: {img_e}")
                
                # Also extract drawings/vector graphics
                drawings = page.get_drawings()
                for draw_index, drawing in enumerate(drawings):
                    drawing_data = {
                        "page": page_num + 1,
                        "index": draw_index,
                        "type": "drawing/diagram",
                        "bbox": drawing.get("rect", []),
                        "items_count": len(drawing.get("items", []))
                    }
                    images_data["images"].append(drawing_data)
            
            doc.close()
            
        except Exception as e:
            print(f"❌ PyMuPDF image extraction error: {e}")
        
        return images_data
    
    def _extract_detailed_metadata(self, pdf_path: str) -> Dict[str, Any]:
        """Extract detailed PDF metadata"""
        metadata = {}
        
        try:
            doc = fitz.open(pdf_path)
            
            # Basic metadata
            pdf_metadata = doc.metadata
            if pdf_metadata:
                metadata.update(pdf_metadata)
            
            # Document outline/bookmarks
            toc = doc.get_toc()
            if toc:
                metadata["table_of_contents"] = toc
            
            # Form fields (if any)
            metadata["has_forms"] = False
            for page_num in range(len(doc)):
                page = doc[page_num]
                if page.get_widgets():
                    metadata["has_forms"] = True
                    break
            
            doc.close()
            
        except Exception as e:
            print(f"⚠️ Metadata extraction error: {e}")
        
        return metadata
    
    def _analyze_document_structure(self, text_content: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze document structure and identify sections"""
        structure = {"sections": [], "document_type": "unknown"}
        
        full_text = text_content.get("full_text", "")
        
        # Identify document type based on keywords
        if any(word in full_text.lower() for word in ["vergunning", "beschikking", "besluit"]):
            structure["document_type"] = "vergunning"
        elif any(word in full_text.lower() for word in ["rapport", "onderzoek", "analyse"]):
            structure["document_type"] = "rapport"
        elif any(word in full_text.lower() for word in ["aanvraag", "application"]):
            structure["document_type"] = "aanvraag"
        
        # Identify sections (simple pattern matching)
        import re
        section_patterns = [
            r"^#{1,3}\s+(.+)$",  # Markdown headers
            r"^\d+\.?\s+([A-Z][^.]+)$",  # Numbered sections
            r"^([A-Z][A-Z\s]{3,}):?\s*$",  # All caps headings
            r"^(Artikel\s+\d+|Art\.\s*\d+)",  # Legal articles
        ]
        
        lines = full_text.split('\n')
        for line_num, line in enumerate(lines):
            line = line.strip()
            for pattern in section_patterns:
                match = re.match(pattern, line, re.MULTILINE)
                if match:
                    section = {
                        "title": match.group(1) if match.lastindex else line,
                        "line_number": line_num,
                        "type": "heading"
                    }
                    structure["sections"].append(section)
                    break
        
        return structure

def test_enhanced_processor():
    """Test the enhanced processor"""
    processor = EnhancedPDFProcessor()
    
    # Test with Zoeterwoude permit
    test_file = "/Users/han/Code/MOB-BREF/permit_sample.pdf"
    if os.path.exists(test_file):
        print(f"🧪 Testing enhanced processor with: {test_file}")
        result = processor.extract_comprehensive_content(test_file, output_dir="test_extraction")
        
        print(f"\n📊 === TEST RESULTS ===")
        print(json.dumps(result["extraction_stats"], indent=2))
        
        if result["images"]:
            print(f"\n🖼️ Found {len(result['images'])} visual elements:")
            for i, img in enumerate(result["images"][:5]):  # Show first 5
                print(f"  {i+1}. Page {img['page']}: {img['type']} ({img.get('width', '?')}x{img.get('height', '?')})")
        
        return result
    else:
        print(f"❌ Test file not found: {test_file}")
        return None

if __name__ == "__main__":
    test_enhanced_processor()