#!/usr/bin/env python3
"""
Complete BAT/BBT Texts PDF Generator
Creates comprehensive PDF with all extracted BAT/BBT full texts for verification
"""

import json
import os
from datetime import datetime
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, KeepTogether
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY

class CompleteBATTextsPDFGenerator:
    """Generates PDF with complete BAT/BBT texts for verification"""
    
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self.custom_styles = self._create_custom_styles()
        
    def _create_custom_styles(self):
        """Create custom paragraph styles for full text display"""
        
        custom_styles = {}
        
        # Title style
        custom_styles['MainTitle'] = ParagraphStyle(
            'MainTitle',
            parent=self.styles['Title'],
            fontSize=20,
            spaceAfter=30,
            alignment=TA_CENTER,
            textColor=colors.darkblue
        )
        
        # Document section heading
        custom_styles['DocumentHeading'] = ParagraphStyle(
            'DocumentHeading',
            parent=self.styles['Heading1'],
            fontSize=16,
            spaceAfter=15,
            spaceBefore=25,
            textColor=colors.darkblue,
            backColor=colors.lightblue,
            borderWidth=1,
            borderColor=colors.darkblue,
            leftIndent=10,
            rightIndent=10,
            topPadding=8,
            bottomPadding=8
        )
        
        # BAT/BBT heading
        custom_styles['BATHeading'] = ParagraphStyle(
            'BATHeading',
            parent=self.styles['Heading2'],
            fontSize=12,
            spaceAfter=8,
            spaceBefore=15,
            textColor=colors.darkgreen,
            backColor=colors.lightgreen,
            borderWidth=1,
            borderColor=colors.darkgreen,
            leftIndent=5,
            rightIndent=5,
            topPadding=5,
            bottomPadding=5
        )
        
        # BAT/BBT metadata
        custom_styles['Metadata'] = ParagraphStyle(
            'Metadata',
            parent=self.styles['Normal'],
            fontSize=9,
            spaceAfter=6,
            textColor=colors.grey,
            leftIndent=20
        )
        
        # Full text content
        custom_styles['FullText'] = ParagraphStyle(
            'FullText',
            parent=self.styles['Normal'],
            fontSize=9,
            spaceAfter=12,
            spaceBefore=6,
            alignment=TA_JUSTIFY,
            leftIndent=20,
            rightIndent=10,
            borderWidth=0.5,
            borderColor=colors.grey,
            leftPadding=10,
            rightPadding=10,
            topPadding=8,
            bottomPadding=8
        )
        
        # Summary style
        custom_styles['Summary'] = ParagraphStyle(
            'Summary',
            parent=self.styles['Normal'],
            fontSize=10,
            spaceAfter=8,
            alignment=TA_LEFT
        )
        
        return custom_styles
    
    def generate_complete_texts_pdf(self, output_filename: str = "Complete_BAT_BBT_Texts.pdf"):
        """Generate PDF with all complete BAT/BBT texts"""
        
        print("📄 === GENERATING COMPLETE TEXTS PDF ===\n")
        
        # Load all data
        data = self._load_all_data()
        
        if not data:
            print("❌ No data found to generate complete texts PDF")
            return None
        
        # Create PDF document with more margin for readability
        doc = SimpleDocTemplate(
            output_filename,
            pagesize=A4,
            rightMargin=50,
            leftMargin=50,
            topMargin=50,
            bottomMargin=50
        )
        
        # Build content
        story = []
        
        # Title page
        story.extend(self._create_title_page(data))
        story.append(PageBreak())
        
        # Table of contents
        story.extend(self._create_table_of_contents(data))
        story.append(PageBreak())
        
        # Dutch BBTs with complete texts
        if 'dutch_bbts' in data:
            story.extend(self._create_dutch_complete_texts(data['dutch_bbts']))
        
        # English BATs with complete texts
        if 'english_bats' in data:
            story.extend(self._create_english_complete_texts(data['english_bats']))
        
        # Build PDF
        print("🔨 Building PDF with complete texts...")
        doc.build(story)
        
        print(f"✅ Complete texts PDF generated: {output_filename}")
        print(f"📊 This PDF contains all {self._count_total_entries(data)} extracted BAT/BBT full texts")
        
        return output_filename
    
    def _load_all_data(self):
        """Load all extraction data"""
        
        data = {}
        
        # Load Dutch BBTs
        if os.path.exists("batc_extractions/dutch_only_bbts.json"):
            with open("batc_extractions/dutch_only_bbts.json", 'r', encoding='utf-8') as f:
                data['dutch_bbts'] = json.load(f)
                print(f"✅ Loaded Dutch BBTs: {sum(len(bbts) for bbts in data['dutch_bbts'].values())} entries")
        
        # Load English BATs
        if os.path.exists("bref_extractions/all_bref_final_complete.json"):
            with open("bref_extractions/all_bref_final_complete.json", 'r', encoding='utf-8') as f:
                data['english_bats'] = json.load(f)
                print(f"✅ Loaded English BATs: {sum(len(bats) for bats in data['english_bats'].values())} entries")
        
        return data if data else None
    
    def _count_total_entries(self, data):
        """Count total BAT/BBT entries"""
        
        total = 0
        if 'dutch_bbts' in data:
            total += sum(len(bbts) for bbts in data['dutch_bbts'].values())
        if 'english_bats' in data:
            total += sum(len(bats) for bats in data['english_bats'].values())
        return total
    
    def _create_title_page(self, data):
        """Create title page"""
        
        story = []
        
        # Main title
        title = Paragraph(
            "Complete BAT/BBT Extracted Texts<br/>Verification Document",
            self.custom_styles['MainTitle']
        )
        story.append(title)
        story.append(Spacer(1, 0.5*inch))
        
        # Summary
        total_entries = self._count_total_entries(data)
        dutch_count = sum(len(bbts) for bbts in data.get('dutch_bbts', {}).values())
        english_count = sum(len(bats) for bats in data.get('english_bats', {}).values())
        
        summary_text = f"""
        This document contains the complete extracted texts of all {total_entries} BAT/BBT entries 
        for verification and review purposes.
        
        Contents:
        • {dutch_count} Dutch BBTs (Legally Binding) from BATC documents
        • {english_count} English BATs (Technical Reference) from BREF documents
        
        Each entry includes:
        • Complete full text as extracted
        • Source document and page information
        • Extraction metadata
        • Title and identification
        
        Generated: {datetime.now().strftime('%B %d, %Y at %H:%M')}
        """
        
        story.append(Paragraph(summary_text, self.custom_styles['Summary']))
        
        return story
    
    def _create_table_of_contents(self, data):
        """Create table of contents"""
        
        story = []
        
        story.append(Paragraph("Table of Contents", self.custom_styles['DocumentHeading']))
        
        # Dutch BBTs section
        if 'dutch_bbts' in data:
            story.append(Paragraph("Dutch BBTs (BATC Documents)", self.custom_styles['BATHeading']))
            
            for doc_code, bbts in sorted(data['dutch_bbts'].items()):
                doc_line = f"{doc_code}: {len(bbts)} BBT entries"
                story.append(Paragraph(doc_line, self.custom_styles['Summary']))
        
        story.append(Spacer(1, 0.2*inch))
        
        # English BATs section
        if 'english_bats' in data:
            story.append(Paragraph("English BATs (BREF Documents)", self.custom_styles['BATHeading']))
            
            for doc_code, bats in sorted(data['english_bats'].items()):
                doc_line = f"{doc_code}: {len(bats)} BAT entries"
                story.append(Paragraph(doc_line, self.custom_styles['Summary']))
        
        return story
    
    def _create_dutch_complete_texts(self, dutch_data):
        """Create complete Dutch BBT texts section"""
        
        story = []
        
        story.append(Paragraph("Dutch BBT Complete Texts (BATC Documents)", self.custom_styles['DocumentHeading']))
        story.append(Paragraph("Legally Binding Best Available Techniques", self.custom_styles['Summary']))
        story.append(Spacer(1, 0.2*inch))
        
        # Process each document
        for doc_code in sorted(dutch_data.keys()):
            bbts = dutch_data[doc_code]
            
            if not bbts:
                continue
            
            # Document header
            doc_header = f"Document: {doc_code} ({len(bbts)} BBT entries)"
            story.append(Paragraph(doc_header, self.custom_styles['BATHeading']))
            
            # Process each BBT
            for i, bbt in enumerate(sorted(bbts, key=lambda x: x.get('bbt_number', 0))):
                story.extend(self._create_bbt_entry(bbt, doc_code, i+1, len(bbts)))
            
            story.append(PageBreak())
        
        return story
    
    def _create_english_complete_texts(self, english_data):
        """Create complete English BAT texts section"""
        
        story = []
        
        story.append(Paragraph("English BAT Complete Texts (BREF Documents)", self.custom_styles['DocumentHeading']))
        story.append(Paragraph("Technical Reference Best Available Techniques", self.custom_styles['Summary']))
        story.append(Spacer(1, 0.2*inch))
        
        # Process each document
        for doc_code in sorted(english_data.keys()):
            bats = english_data[doc_code]
            
            if not bats:
                continue
            
            # Document header
            doc_header = f"Document: {doc_code} ({len(bats)} BAT entries)"
            story.append(Paragraph(doc_header, self.custom_styles['BATHeading']))
            
            # Process each BAT
            for i, bat in enumerate(sorted(bats, key=lambda x: x.get('bat_number', 0))):
                story.extend(self._create_bat_entry(bat, doc_code, i+1, len(bats)))
            
            story.append(PageBreak())
        
        return story
    
    def _create_bbt_entry(self, bbt, doc_code, entry_num, total_entries):
        """Create individual BBT entry with complete text"""
        
        story = []
        
        # BBT header
        bbt_id = bbt.get('bbt_id', f'BBT {bbt.get("bbt_number", "Unknown")}')
        title = bbt.get('title', 'No title available')
        
        header_text = f"{bbt_id}: {title}"
        story.append(Paragraph(header_text, self.custom_styles['BATHeading']))
        
        # Metadata
        metadata_items = [
            f"Document: {doc_code}",
            f"Entry: {entry_num}/{total_entries}",
            f"Page: {bbt.get('page', 'Unknown')}",
            f"Length: {bbt.get('text_length', 0):,} characters",
            f"Language: {bbt.get('language', 'Dutch')}",
            f"Extraction Method: {bbt.get('extraction_method', 'Unknown')}",
            f"Has Tables: {'Yes' if bbt.get('has_tables', False) else 'No'}"
        ]
        
        metadata_text = " | ".join(metadata_items)
        story.append(Paragraph(metadata_text, self.custom_styles['Metadata']))
        
        # Full text content
        full_text = bbt.get('full_text', 'No text available')
        
        # Clean and format text for PDF
        formatted_text = self._format_text_for_pdf(full_text)
        
        # Use KeepTogether to avoid awkward page breaks in middle of short entries
        if len(formatted_text) < 1000:
            text_paragraph = KeepTogether([
                Paragraph("Complete Text:", self.custom_styles['Metadata']),
                Paragraph(formatted_text, self.custom_styles['FullText'])
            ])
            story.append(text_paragraph)
        else:
            story.append(Paragraph("Complete Text:", self.custom_styles['Metadata']))
            story.append(Paragraph(formatted_text, self.custom_styles['FullText']))
        
        story.append(Spacer(1, 0.3*inch))
        
        return story
    
    def _create_bat_entry(self, bat, doc_code, entry_num, total_entries):
        """Create individual BAT entry with complete text"""
        
        story = []
        
        # BAT header
        bat_id = bat.get('bat_id', f'BAT {bat.get("bat_number", "Unknown")}')
        title = bat.get('title', 'No title available')
        
        header_text = f"{bat_id}: {title}"
        story.append(Paragraph(header_text, self.custom_styles['BATHeading']))
        
        # Metadata
        metadata_items = [
            f"Document: {doc_code}",
            f"Entry: {entry_num}/{total_entries}",
            f"Page: {bat.get('page', 'Unknown')}",
            f"Length: {bat.get('text_length', 0):,} characters",
            f"Language: {bat.get('language', 'English')}",
            f"Extraction Method: {bat.get('extraction_method', 'Unknown')}"
        ]
        
        metadata_text = " | ".join(metadata_items)
        story.append(Paragraph(metadata_text, self.custom_styles['Metadata']))
        
        # Full text content
        full_text = bat.get('full_text', 'No text available')
        
        # Clean and format text for PDF
        formatted_text = self._format_text_for_pdf(full_text)
        
        # Use KeepTogether for shorter entries
        if len(formatted_text) < 1000:
            text_paragraph = KeepTogether([
                Paragraph("Complete Text:", self.custom_styles['Metadata']),
                Paragraph(formatted_text, self.custom_styles['FullText'])
            ])
            story.append(text_paragraph)
        else:
            story.append(Paragraph("Complete Text:", self.custom_styles['Metadata']))
            story.append(Paragraph(formatted_text, self.custom_styles['FullText']))
        
        story.append(Spacer(1, 0.3*inch))
        
        return story
    
    def _format_text_for_pdf(self, text):
        """Format text for PDF display"""
        
        if not text:
            return "No text available"
        
        # Clean up text
        text = str(text)
        
        # Replace problematic characters for PDF
        text = text.replace('&', '&amp;')
        text = text.replace('<', '&lt;')
        text = text.replace('>', '&gt;')
        
        # Normalize line breaks
        text = text.replace('\r\n', '\n')
        text = text.replace('\r', '\n')
        
        # Convert line breaks to HTML breaks for Paragraph
        text = text.replace('\n', '<br/>')
        
        # Remove excessive breaks
        while '<br/><br/><br/>' in text:
            text = text.replace('<br/><br/><br/>', '<br/><br/>')
        
        return text
    
def main():
    """Generate complete texts PDF"""
    
    generator = CompleteBATTextsPDFGenerator()
    pdf_file = generator.generate_complete_texts_pdf()
    
    if pdf_file:
        print(f"\n🎉 Complete texts PDF successfully generated!")
        print(f"📁 File: {pdf_file}")
        print(f"📖 This PDF contains all extracted BAT/BBT full texts for verification")
        print(f"💡 You can now review every single extracted entry in detail")
    else:
        print("\n❌ Failed to generate complete texts PDF")

if __name__ == "__main__":
    main()