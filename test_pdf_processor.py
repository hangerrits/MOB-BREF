# /home/ubuntu/bat_rie_checker_app/src/tests/test_pdf_processor.py
import unittest
import os
import sys
from unittest.mock import patch, MagicMock, PropertyMock

# Add the src directory to the Python path
SRC_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

# --- Create Mocks for docling --- 
# This section prepares mocks that will be injected into sys.modules
# to simulate the presence of the docling library and its components.

# Create a mock for the top-level 'docling' module
mock_docling_module = MagicMock()

# Create a mock for the 'docling.document_converter' module
mock_docling_document_converter_module = MagicMock()

# Create a mock for the DocumentConverter class itself
# This is what `from docling.document_converter import DocumentConverter` would import.
MockDocumentConverterClass = MagicMock(name="MockDocumentConverterClass")

# Configure the instance that MockDocumentConverterClass() will return
mock_converter_instance = MagicMock(name="mock_converter_instance")
MockDocumentConverterClass.return_value = mock_converter_instance

# Configure the document object that mock_converter_instance.convert() will return
mock_docling_doc_instance = MagicMock(name="mock_docling_doc_instance")
mock_converter_instance.convert.return_value = mock_docling_doc_instance

# Setup the methods and properties of the mock document object
mock_docling_doc_instance.get_title = MagicMock(return_value="Mocked PDF Title from Method")
mock_docling_doc_instance.get_full_text = MagicMock(return_value="This is page 1 for unit testing. This is page 2 for unit testing.")

# Simulate page structure for get_pages() and individual page text
mock_page1 = MagicMock(name="mock_page1")
mock_page1.get_text.return_value = "This is page 1 for unit testing."
mock_page2 = MagicMock(name="mock_page2")
mock_page2.get_text.return_value = "This is page 2 for unit testing."
mock_docling_doc_instance.get_pages.return_value = [mock_page1, mock_page2]

# Assign our mocked DocumentConverter class to the mocked docling.document_converter module
mock_docling_document_converter_module.DocumentConverter = MockDocumentConverterClass

# Use patch.dict to temporarily insert these mocks into sys.modules
# This must be active *before* core_logic.pdf_processor is imported by this test file.
# The context manager approach is cleaner for this initial import.
with patch.dict(sys.modules, {
    "docling": mock_docling_module,
    "docling.document_converter": mock_docling_document_converter_module
}):
    from core_logic.pdf_processor import extract_text_and_metadata

# --- End Mocks for docling ---

from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter

TEST_FILES_DIR = os.path.join(os.path.dirname(__file__), "test_generated_files")
if not os.path.exists(TEST_FILES_DIR):
    os.makedirs(TEST_FILES_DIR)

class TestPdfProcessor(unittest.TestCase):

    def setUp(self):
        """Set up for test methods."""
        self.sample_pdf_path = os.path.join(TEST_FILES_DIR, "unittest_sample.pdf")
        self.create_dummy_pdf(self.sample_pdf_path, "Unit Test PDF Title", "This is page 1 for unit testing.", "This is page 2 for unit testing.")
        
        # Reset mocks before each test to ensure test isolation for call counts etc.
        MockDocumentConverterClass.reset_mock()
        mock_converter_instance.reset_mock()
        mock_docling_doc_instance.reset_mock()
        mock_page1.reset_mock()
        mock_page2.reset_mock()

        # Re-apply default mock configurations as reset_mock clears them
        MockDocumentConverterClass.return_value = mock_converter_instance
        mock_converter_instance.convert.return_value = mock_docling_doc_instance
        mock_docling_doc_instance.get_title.return_value = "Mocked PDF Title from Method"
        mock_docling_doc_instance.get_full_text.return_value = "This is page 1 for unit testing. This is page 2 for unit testing."
        mock_page1.get_text.return_value = "This is page 1 for unit testing."
        mock_page2.get_text.return_value = "This is page 2 for unit testing."
        mock_docling_doc_instance.get_pages.return_value = [mock_page1, mock_page2]


    def create_dummy_pdf(self, path, title, page1_text, page2_text):
        c = canvas.Canvas(path, pagesize=letter)
        c.setTitle(title)
        c.drawString(100, 750, page1_text)
        c.showPage()
        c.drawString(100, 750, page2_text)
        c.save()
        # print(f"Test dummy PDF created at {path}") # Reduced print verbosity

    # The @patch decorator targets the name 'DocumentConverter' as it is used *within* the core_logic.pdf_processor module.
    # Thanks to the sys.modules patching above, this name should already be our MockDocumentConverterClass.
    # This decorator provides a fresh mock instance for the test or can re-patch if needed.
    @patch("core_logic.pdf_processor.DocumentConverter", new=MockDocumentConverterClass)
    def test_extract_text_and_metadata_success_with_mock(self, _mock_dc_in_test_method_arg):
        """Test successful extraction using a mocked DocumentConverter."""
        print(f"Testing PDF extraction with mock for: {self.sample_pdf_path}")
        result = extract_text_and_metadata(self.sample_pdf_path)
        
        self.assertIsNotNone(result, "Extraction result should not be None.")
        self.assertNotIn("error", result, f"Extraction should not produce an error. Got: {result.get('error')}")
        self.assertEqual(result.get("title"), "Mocked PDF Title from Method", "PDF title mismatch from mock.")
        self.assertEqual(result.get("full_text"), "This is page 1 for unit testing. This is page 2 for unit testing.", "Full text mismatch from mock.")
        
        self.assertIsInstance(result.get("pages_data"), list, "Pages data should be a list.")
        if result.get("pages_data"):
             self.assertEqual(len(result.get("pages_data")), 2, "Should have 2 pages of data from mock.")
             self.assertEqual(result.get("pages_data")[0]["text"], "This is page 1 for unit testing.")

        MockDocumentConverterClass.assert_called_once_with(self.sample_pdf_path)
        mock_converter_instance.convert.assert_called_once()

    @patch("core_logic.pdf_processor.DocumentConverter", new=MockDocumentConverterClass)
    def test_extract_text_docling_conversion_failure_with_mock(self, _mock_dc_in_test_method_arg):
        """Test extraction when Docling (mocked) convert method returns None."""
        mock_converter_instance.convert.return_value = None # Simulate Docling failing to convert

        print(f"Testing PDF extraction with mock (conversion failure) for: {self.sample_pdf_path}")
        result = extract_text_and_metadata(self.sample_pdf_path)

        self.assertIsNotNone(result, "Result should not be None even for errors.")
        self.assertIn("error", result, "Result should contain an error key for Docling conversion failure.")
        self.assertIn("Docling conversion failed", result.get("error", ""), "Error message mismatch.")
        MockDocumentConverterClass.assert_called_once_with(self.sample_pdf_path)
        mock_converter_instance.convert.assert_called_once()

    def test_extract_text_from_nonexistent_pdf(self):
        """Test extraction from a non-existent PDF file (does not involve Docling mock)."""
        non_existent_pdf = os.path.join(TEST_FILES_DIR, "non_existent_invalid.pdf") # Ensure unique name
        print(f"Testing PDF extraction for non-existent file: {non_existent_pdf}")
        result = extract_text_and_metadata(non_existent_pdf)
        self.assertIsNotNone(result, "Result should not be None even for errors.")
        self.assertIn("error", result, "Result should contain an error key for non-existent file.")
        self.assertIn("not found" , result.get("error", "").lower(), "Error message should indicate file not found.")

    def tearDown(self):
        """Clean up after tests."""
        if os.path.exists(self.sample_pdf_path):
            os.remove(self.sample_pdf_path)
        # print(f"Test dummy PDF removed: {self.sample_pdf_path}") # Reduced verbosity

if __name__ == "__main__":
    unittest.main()

