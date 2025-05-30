#!/usr/bin/env python3
"""
Manageable BAT/BBT Texts Generator
Creates separate, manageable PDFs for verification
"""

import json
import os
from datetime import datetime
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_LEFT, TA_CENTER

class ManageableTextsGenerator:
    """Creates manageable PDFs for BAT/BBT verification"""
    
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self.custom_styles = self._create_styles()
        
    def _create_styles(self):
        """Create custom styles"""
        custom_styles = {}
        
        custom_styles['Title'] = ParagraphStyle(
            'Title', parent=self.styles['Title'],
            fontSize=18, spaceAfter=20, alignment=TA_CENTER, textColor=colors.darkblue
        )
        
        custom_styles['DocHeader'] = ParagraphStyle(
            'DocHeader', parent=self.styles['Heading1'],
            fontSize=14, spaceAfter=10, textColor=colors.darkgreen,
            backColor=colors.lightgreen, leftIndent=5, rightIndent=5,
            topPadding=5, bottomPadding=5
        )
        
        custom_styles['EntryHeader'] = ParagraphStyle(
            'EntryHeader', parent=self.styles['Heading2'],
            fontSize=11, spaceAfter=5, textColor=colors.darkblue
        )
        
        custom_styles['Metadata'] = ParagraphStyle(
            'Metadata', parent=self.styles['Normal'],
            fontSize=8, spaceAfter=3, textColor=colors.grey
        )
        
        custom_styles['Content'] = ParagraphStyle(
            'Content', parent=self.styles['Normal'],
            fontSize=9, spaceAfter=8, leftIndent=10, rightIndent=5
        )
        
        return custom_styles
    
    def generate_manageable_pdfs(self):
        """Generate separate manageable PDFs"""
        
        print("📄 === GENERATING MANAGEABLE VERIFICATION PDFs ===\n")
        
        # Load data
        dutch_data = self._load_dutch_data()
        english_data = self._load_english_data()
        
        generated_files = []
        
        # Create summary PDF
        summary_file = self._create_summary_pdf(dutch_data, english_data)
        if summary_file:
            generated_files.append(summary_file)
        
        # Create sample documents PDF (top documents)
        sample_file = self._create_sample_documents_pdf(dutch_data, english_data)
        if sample_file:
            generated_files.append(sample_file)
        
        # Create English BATs PDF (smaller dataset)
        english_file = self._create_english_bats_pdf(english_data)
        if english_file:
            generated_files.append(english_file)
        
        # Create top Dutch documents PDFs
        dutch_files = self._create_top_dutch_pdfs(dutch_data)
        generated_files.extend(dutch_files)
        
        print(f"\n🎉 Generated {len(generated_files)} verification PDFs:")
        for file in generated_files:
            print(f"   📁 {file}")
        
        return generated_files
    
    def _load_dutch_data(self):
        """Load Dutch BBT data"""
        if os.path.exists("batc_extractions/dutch_only_bbts.json"):
            with open("batc_extractions/dutch_only_bbts.json", 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
    
    def _load_english_data(self):
        """Load English BAT data"""
        if os.path.exists("bref_extractions/all_bref_final_complete.json"):
            with open("bref_extractions/all_bref_final_complete.json", 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
    
    def _create_summary_pdf(self, dutch_data, english_data):
        """Create summary PDF with key statistics and samples"""
        
        filename = "BAT_BBT_Summary_Verification.pdf"
        doc = SimpleDocTemplate(filename, pagesize=A4, rightMargin=50, leftMargin=50, topMargin=50, bottomMargin=50)
        
        story = []
        
        # Title
        story.append(Paragraph("BAT/BBT Extraction Summary & Samples", self.custom_styles['Title']))
        story.append(Spacer(1, 0.3*inch))
        
        # Statistics
        dutch_count = sum(len(bbts) for bbts in dutch_data.values())
        english_count = sum(len(bats) for bats in english_data.values())
        
        stats_text = f"""
        <b>Extraction Summary:</b><br/>
        • Total Documents: {len(dutch_data) + len(english_data)}<br/>
        • Total Techniques: {dutch_count + english_count}<br/>
        • Dutch BBTs: {dutch_count} from {len(dutch_data)} documents<br/>
        • English BATs: {english_count} from {len(english_data)} documents<br/>
        """
        story.append(Paragraph(stats_text, self.custom_styles['Content']))
        story.append(Spacer(1, 0.2*inch))
        
        # Document breakdown
        story.append(Paragraph("Document Breakdown", self.custom_styles['DocHeader']))
        
        # Dutch documents
        story.append(Paragraph("Dutch BATC Documents:", self.custom_styles['EntryHeader']))
        for doc_code, bbts in sorted(dutch_data.items(), key=lambda x: len(x[1]), reverse=True):
            doc_text = f"{doc_code}: {len(bbts)} BBTs"
            story.append(Paragraph(doc_text, self.custom_styles['Content']))
        
        story.append(Spacer(1, 0.1*inch))
        
        # English documents
        story.append(Paragraph("English BREF Documents:", self.custom_styles['EntryHeader']))
        for doc_code, bats in sorted(english_data.items(), key=lambda x: len(x[1]), reverse=True):
            doc_text = f"{doc_code}: {len(bats)} BATs"
            story.append(Paragraph(doc_text, self.custom_styles['Content']))
        
        story.append(PageBreak())
        
        # Sample entries
        story.append(Paragraph("Sample Extracted Content", self.custom_styles['DocHeader']))
        
        # Sample Dutch BBT
        if dutch_data:
            sample_doc = 'CWW' if 'CWW' in dutch_data else list(dutch_data.keys())[0]
            if dutch_data[sample_doc]:
                sample_bbt = dutch_data[sample_doc][0]
                story.append(Paragraph(f"Sample Dutch BBT from {sample_doc}:", self.custom_styles['EntryHeader']))
                story.append(Paragraph(f"ID: {sample_bbt.get('bbt_id', 'Unknown')}", self.custom_styles['Metadata']))
                story.append(Paragraph(f"Title: {sample_bbt.get('title', 'No title')}", self.custom_styles['Metadata']))
                sample_text = sample_bbt.get('full_text', '')[:1000] + "..."
                story.append(Paragraph(self._clean_text(sample_text), self.custom_styles['Content']))
                story.append(Spacer(1, 0.2*inch))
        
        # Sample English BAT
        if english_data:
            sample_doc = 'ENE' if 'ENE' in english_data else list(english_data.keys())[0]
            if english_data[sample_doc]:
                sample_bat = english_data[sample_doc][0]
                story.append(Paragraph(f"Sample English BAT from {sample_doc}:", self.custom_styles['EntryHeader']))
                story.append(Paragraph(f"ID: {sample_bat.get('bat_id', 'Unknown')}", self.custom_styles['Metadata']))
                story.append(Paragraph(f"Title: {sample_bat.get('title', 'No title')}", self.custom_styles['Metadata']))
                sample_text = sample_bat.get('full_text', '')[:1000] + "..."
                story.append(Paragraph(self._clean_text(sample_text), self.custom_styles['Content']))
        
        doc.build(story)
        print(f"✅ Generated summary: {filename}")
        return filename
    
    def _create_sample_documents_pdf(self, dutch_data, english_data):
        """Create PDF with complete texts from sample documents"""
        
        filename = "BAT_BBT_Sample_Documents.pdf"
        doc = SimpleDocTemplate(filename, pagesize=A4, rightMargin=50, leftMargin=50, topMargin=50, bottomMargin=50)
        
        story = []
        
        story.append(Paragraph("Sample Documents - Complete Texts", self.custom_styles['Title']))
        story.append(Spacer(1, 0.3*inch))
        
        # Sample Dutch document (CWW - known to be good)
        if 'CWW' in dutch_data:
            story.append(Paragraph("Sample Dutch Document: CWW", self.custom_styles['DocHeader']))
            story.append(Paragraph("Common Waste Water Treatment - Complete BBT Texts", self.custom_styles['Content']))
            
            for bbt in sorted(dutch_data['CWW'][:10], key=lambda x: x.get('bbt_number', 0)):  # First 10 BBTs
                story.extend(self._create_entry_content(bbt, is_dutch=True))
            
            story.append(PageBreak())
        
        # Sample English document (ENE - known to be good)
        if 'ENE' in english_data:
            story.append(Paragraph("Sample English Document: ENE", self.custom_styles['DocHeader']))
            story.append(Paragraph("Energy Efficiency - Complete BAT Texts", self.custom_styles['Content']))
            
            for bat in sorted(english_data['ENE'][:10], key=lambda x: x.get('bat_number', 0)):  # First 10 BATs
                story.extend(self._create_entry_content(bat, is_dutch=False))
        
        doc.build(story)
        print(f"✅ Generated sample documents: {filename}")
        return filename
    
    def _create_english_bats_pdf(self, english_data):
        """Create PDF with all English BATs (smaller dataset)"""
        
        filename = "All_English_BATs_Complete.pdf"
        doc = SimpleDocTemplate(filename, pagesize=A4, rightMargin=50, leftMargin=50, topMargin=50, bottomMargin=50)
        
        story = []
        
        story.append(Paragraph("All English BATs - Complete Texts", self.custom_styles['Title']))
        story.append(Spacer(1, 0.3*inch))
        
        for doc_code in sorted(english_data.keys()):
            bats = english_data[doc_code]
            if not bats:
                continue
                
            story.append(Paragraph(f"Document: {doc_code} ({len(bats)} BATs)", self.custom_styles['DocHeader']))
            
            for bat in sorted(bats, key=lambda x: x.get('bat_number', 0)):
                story.extend(self._create_entry_content(bat, is_dutch=False))
            
            story.append(PageBreak())
        
        doc.build(story)
        print(f"✅ Generated all English BATs: {filename}")
        return filename
    
    def _create_top_dutch_pdfs(self, dutch_data):
        """Create PDFs for top Dutch documents"""
        
        generated_files = []
        
        # Get top 3 documents by BBT count
        top_docs = sorted(dutch_data.items(), key=lambda x: len(x[1]), reverse=True)[:3]
        
        for doc_code, bbts in top_docs:
            filename = f"Dutch_{doc_code}_Complete_BBTs.pdf"
            doc = SimpleDocTemplate(filename, pagesize=A4, rightMargin=50, leftMargin=50, topMargin=50, bottomMargin=50)
            
            story = []
            
            story.append(Paragraph(f"Dutch Document {doc_code} - Complete BBTs", self.custom_styles['Title']))
            story.append(Paragraph(f"{len(bbts)} BBT entries extracted", self.custom_styles['Content']))
            story.append(Spacer(1, 0.3*inch))
            
            for bbt in sorted(bbts, key=lambda x: x.get('bbt_number', 0)):
                story.extend(self._create_entry_content(bbt, is_dutch=True))
            
            doc.build(story)
            print(f"✅ Generated {doc_code}: {filename}")
            generated_files.append(filename)
        
        return generated_files
    
    def _create_entry_content(self, entry, is_dutch=True):
        """Create content for a single BAT/BBT entry"""
        
        story = []
        
        # Header
        entry_id = entry.get('bbt_id' if is_dutch else 'bat_id', 'Unknown')
        title = entry.get('title', 'No title')
        
        story.append(Paragraph(f"{entry_id}: {title}", self.custom_styles['EntryHeader']))
        
        # Metadata
        metadata = f"Page: {entry.get('page', 'Unknown')} | Length: {entry.get('text_length', 0):,} chars"
        story.append(Paragraph(metadata, self.custom_styles['Metadata']))
        
        # Full text
        full_text = entry.get('full_text', 'No text available')
        story.append(Paragraph(self._clean_text(full_text), self.custom_styles['Content']))
        story.append(Spacer(1, 0.2*inch))
        
        return story
    
    def _clean_text(self, text):
        """Clean text for PDF"""
        if not text:
            return "No text available"
        
        text = str(text)
        text = text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
        text = text.replace('\n', '<br/>')
        
        # Limit very long texts
        if len(text) > 10000:
            text = text[:10000] + "...<br/><i>[Text truncated for PDF readability]</i>"
        
        return text

def main():
    """Generate manageable verification PDFs"""
    
    generator = ManageableTextsGenerator()
    files = generator.generate_manageable_pdfs()
    
    print(f"\n📖 VERIFICATION PDFs READY:")
    print(f"🔍 Start with 'BAT_BBT_Summary_Verification.pdf' for overview")
    print(f"📄 Review 'BAT_BBT_Sample_Documents.pdf' for sample complete texts")
    print(f"🇬🇧 Check 'All_English_BATs_Complete.pdf' for all English BATs")
    print(f"🇳🇱 Review top Dutch documents for detailed verification")

if __name__ == "__main__":
    main()