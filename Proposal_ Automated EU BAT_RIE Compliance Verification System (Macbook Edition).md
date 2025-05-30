# Proposal: Automated EU BAT/RIE Compliance Verification System (Macbook Edition)

## 1. Introduction & Objectives

This document outlines the proposal for an automated system designed to assist in verifying whether industrial permits comply with the conditions set forth in EU Best Available Technologies (BAT) Reference Documents (BREFs) and the Industrial Emissions Directive (RIE), particularly for veehouderijen (livestock farming).

**Primary Objectives:**

*   **Automated Verification:** To provide an automated tool that compares the textual content of an industrial permit (in PDF format) against relevant BREF documents and RIE provisions.
*   **Identification of Discrepancies:** To help users identify potential areas of non-compliance, partial compliance, discrepancies, or ambiguities between the permit conditions and the BAT conclusions or RIE requirements.
*   **Support for Supervisors:** To serve as an intelligent assistant for toezichthouders (supervisors), streamlining the initial review process and highlighting areas requiring expert attention.
*   **Local Deployment:** The system is designed to run locally on the user's Macbook, ensuring data control and ease of use for individual analysis.

This system aims to enhance the efficiency and consistency of permit verification processes by leveraging Natural Language Processing (NLP) capabilities through a Large Language Model (LLM).

## 2. System Architecture

The proposed system will be a local web application with the following core components:

*   **PDF Extraction Engine (Docling):** Utilizes the Docling library to extract full textual content and crucial metadata (document titles, page numbers, paragraph/section identifiers) from uploaded permit PDFs and the source BREF/RIE PDF documents during the initial knowledge base creation.
*   **Knowledge Base (JSON Files):** A collection of structured JSON files storing the processed information from BREF and RIE documents. Each BAT conclusion and relevant RIE section will be a distinct entry, including its full text and associated metadata for precise referencing.
*   **Large Language Model (LLM - OpenAI API):** The core intelligence of the system, responsible for:
    *   **Scope Matching:** Determining which BREF/RIE documents are applicable to the activities described in an uploaded permit.
    *   **Compliance Verification:** Comparing the conditions in the permit against the specific requirements of each applicable BAT conclusion or RIE section.
*   **Backend Application (Python - Flask/FastAPI):** A Python-based backend using Flask or FastAPI to handle:
    *   File uploads.
    *   Orchestration of Docling for PDF processing.
    *   Interaction with the LLM API.
    *   Serving the user interface.
*   **User Interface (Web-based - HTML, CSS, JavaScript):** A simple, browser-based interface allowing users to upload permits and view the verification results.

**High-Level Workflow:**

1.  **User Uploads Permit:** The supervisor uploads a permit PDF via the web UI.
2.  **Text & Metadata Extraction:** The backend uses Docling to extract the full text and metadata (page/paragraph numbers) from the permit.
3.  **Scope Matching:** The extracted permit information is sent to the LLM, along with the scope descriptions from the BREF/RIE JSON knowledge base. The LLM identifies applicable documents.
4.  **BAT/RIE Compliance Verification:** For each applicable BREF/RIE document, the system iteratively sends the permit text and individual BAT conclusion texts (or RIE section texts) from the JSON knowledge base to the LLM. The LLM analyzes for compliance, discrepancies, etc., referencing specific text and metadata from both permit and source documents.
5.  **Results Display:** The structured findings from the LLM are presented to the user in the web UI, highlighting key areas and providing detailed justifications with precise references.

## 3. Data Management

**3.1. Knowledge Base Format (JSON)**

The BREF and RIE information will be stored locally in structured JSON files. A high-level representation:

```json
{
  "bref_documents": [
    {
      "bref_id": "UNIQUE_BREF_ID",
      "title": "BREF Document Title",
      "document_url": "URL_to_PDF_Source",
      "scope_description": "Full text of the BREF scope...",
      "publication_date": "YYYY-MM-DD",
      "source_metadata": {"page_number": "X", "paragraph_id": "Y"}, // For the scope itself
      "bat_conclusions": [
        {
          "bat_id": "UNIQUE_BAT_ID_within_BREF",
          "bat_text_description": "Full text description of the BAT conclusion...",
          "source_metadata": {"page_number": "A", "paragraph_id": "B"} // For this specific BAT
        }
      ]
    }
  ],
  "rie_documents": [
    {
      "rie_id": "UNIQUE_RIE_ID",
      "title": "RIE Document Title",
      "document_url": "URL_to_PDF_Source",
      "scope_description": "Full text of the RIE scope...",
      "source_metadata": {"page_number": "M", "paragraph_id": "N"}, // For the scope itself
      "relevant_sections_livestock": [
        {
          "section_id": "Article_X_Paragraph_Y",
          "section_text": "Full text of the relevant RIE section...",
          "source_metadata": {"page_number": "P", "paragraph_id": "Q"} // For this specific section
        }
      ]
    }
  ]
}
```

**3.2. PDF Extraction (Docling)**

Docling will be used for:

*   **Initial Knowledge Base Population:** Processing source BREF/RIE PDFs to extract scope descriptions, BAT conclusions, relevant RIE sections, and their associated metadata (document title, page numbers, paragraph/section identifiers where possible) to create the JSON files.
*   **Real-time Permit Processing:** When a user uploads a permit PDF, Docling will extract its full textual content and corresponding metadata (page/paragraph numbers for each segment of text). This metadata is crucial for providing precise references in the verification results.

**3.3. Permit Data Handling (Local)**

*   Uploaded permit PDFs will be processed locally on the user's Macbook.
*   Temporary storage will be used during a session, with clear mechanisms for data cleanup or user-initiated deletion to manage local storage and privacy.

## 4. Verification Algorithms (LLM-Powered)

The core analytical tasks will be performed by an LLM (e.g., via OpenAI API), orchestrated by Python scripts.

**4.1. Programming Language:** Python

**4.2. Scope Matching Algorithm**

*   **Input:** Extracted text from the uploaded permit (focusing on activity descriptions) and the `scope_description` fields from all BREF/RIE documents in the JSON knowledge base.
*   **LLM Prompting:** The LLM will be prompted to act as an expert in EU environmental regulations. It will be asked to compare the permit's activities against each BREF/RIE scope description and classify applicability as 'Likely Applicable', 'Potentially Applicable', or 'Not Applicable', providing a brief justification for each, referencing specific parts of the permit and the scope description.
*   **Output:** A list of `bref_id`s and `rie_id`s identified as applicable, along with justifications.

**4.3. BAT/RIE Compliance Verification Algorithm**

*   **Input:** Full extracted text of the permit (with its granular page/paragraph metadata) and the `bat_text_description` (with its source metadata) for each BAT from the applicable BREF documents, or `section_text` (with source metadata) for applicable RIE sections.
*   **Process:** The system will iterate through each applicable BAT conclusion (or RIE section) individually.
*   **LLM Prompting (per BAT/RIE section):** The LLM will be instructed to meticulously compare the permit conditions against the specific requirements of the BAT/RIE section. The prompt will ask the LLM to identify and report on:
    1.  **Compliance:** Citing specific permit text (with page/paragraph) and the relevant BAT/RIE text (with page/paragraph).
    2.  **Partial Compliance/Discrepancies:** Detailing each, citing relevant permit text (with page/paragraph) and the specific part of the BAT/RIE it relates to.
    3.  **Non-Compliance/Missing Elements:** Listing these, referencing the specific BAT/RIE requirement.
    4.  **Ambiguity/Insufficient Information:** Specifying parts of the BAT/RIE that cannot be verified and what information is missing from the permit.
*   **Output:** A structured report for each BAT/RIE section, detailing the findings with precise references to both the permit and the source BREF/RIE document.

## 5. User Interface (UI) Design

The system will feature a simple, local web-based UI.

**5.1. Permit Upload Interface**

*   Clean interface with a prominent "Upload Permit PDF" button/drag-and-drop area (PDFs only).
*   Optional fields for user to input Permit ID or facility name.
*   "Start Verification" button.
*   Clear processing indicator (e.g., spinner, progress message) managing user expectations for processing time.
*   Basic error handling for incorrect file types or upload failures.

**5.2. Verification Results Interface**

*   **Summary Page:** Displays permit identification, a high-level overall assessment (e.g., "Potential Issues Found"), and a list of BREF/RIE documents identified as applicable with justifications.
*   **Detailed Breakdown:** Organized by applicable BREF/RIE document, then by BAT conclusion/RIE section.
    *   For each BAT/RIE section: Displays its text, the LLM's compliance finding (Compliant, Partial, Non-Compliant, Ambiguity), and detailed evidence/justification.
    *   **Crucially, justifications will include:**
        *   Relevant permit text snippet with its page/paragraph number.
        *   Relevant BREF/BAT or RIE section text snippet with its source page/paragraph number.
        *   The LLM's explanation for its finding.
*   **Features:**
    *   Search/filter results.
    *   Expand/collapse details for readability.
    *   Export results to a structured format (e.g., PDF or Markdown report).
    *   Clear disclaimer about AI assistance and the need for expert review.

## 6. Implementation Approach (for Macbook)

**6.1. Technology Stack**

*   **Backend:** Python 3.9+ with Flask (or FastAPI).
*   **PDF Extraction:** Docling (Python library).
*   **LLM:** OpenAI API (via Python client library).
*   **Data Storage:** Local JSON files.
*   **Frontend:** HTML, CSS, JavaScript.

**6.2. Local Macbook Environment Setup**

*   Requires Python 3 and pip.
*   Project-specific Python virtual environment (`venv`).
*   Installation of dependencies (Docling, Flask, OpenAI library) via `pip` from a `requirements.txt` file.
*   Secure configuration of OpenAI API key as an environment variable.

**6.3. Application Structure (Conceptual)**

*   `app.py`: Main Flask/FastAPI application logic.
*   `templates/`: HTML files.
*   `static/`: CSS, JS files.
*   `knowledge_base/`: Stores BREF/RIE JSON data.
*   `uploads/`: Temporary storage for uploaded permits.
*   `core_logic/`: Python modules for scope matching and compliance verification algorithms.

**6.4. Phased Implementation**

1.  **Phase 1: Knowledge Base & Core Logic (Command-Line):**
    *   Develop scripts for Docling to create the BREF/RIE JSON knowledge base with metadata.
    *   Develop and test Python functions for scope matching and BAT compliance using the LLM with sample data.
2.  **Phase 2: Web Application Development:**
    *   Set up Flask/FastAPI server.
    *   Implement UI for permit upload and results display.
    *   Integrate Docling and LLM logic into the backend.
3.  **Phase 3: Refinement & Usability:**
    *   Enhance error handling, user feedback.
    *   Create a `README.md` with setup and usage instructions.

## 7. Deployment Strategy (for Macbook)

A `README.md` file will provide detailed instructions:

1.  **Prerequisites:** Check/install Python 3, pip.
2.  **Code:** Download/clone project code.
3.  **Virtual Environment:** Create and activate (`python3 -m venv venv`, `source venv/bin/activate`).
4.  **Dependencies:** Install (`pip install -r requirements.txt`).
5.  **API Key:** Set `OPENAI_API_KEY` environment variable.
6.  **Knowledge Base:** Place provided JSON files in `knowledge_base/`.
7.  **Run:** Execute `python3 app.py`.
8.  **Access:** Open `http://127.0.0.1:5000/` (or similar) in a browser.
9.  **Stop:** `Control+C` in Terminal; `deactivate` virtual environment.

## 8. Data Privacy and Security (Local Macbook)

*   Given the data is publicly available (BREF/RIE) and permits are processed locally, the primary security relies on the user's Macbook security (FileVault for disk encryption, strong passwords, OS updates).
*   Permit data sent to the OpenAI API will be transmitted over HTTPS.
*   The application will not send permit data to other external services.
*   Temporary files from uploaded permits will be handled with options for cleanup.

## 9. Future Considerations (Deferred)

*   Integration with existing external systems used by supervisors will be considered as a future enhancement after the core functionality is proven and validated.

This proposal outlines a comprehensive plan to develop a valuable tool for assisting in the complex task of BAT/RIE compliance verification. We look forward to your feedback.

