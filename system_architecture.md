# System Architecture: Automated EU BAT/RIE Compliance Verification System

## 1. Overview

This document details the system architecture for the Automated EU BAT/RIE Compliance Verification System. The system is designed to run locally on a Macbook and assist users in verifying industrial permit compliance with EU BAT Reference Documents (BREFs) and the Industrial Emissions Directive (RIE).

## 2. Core Components

The system comprises the following core components as outlined in the proposal:

*   **PDF Extraction Engine (Docling):** Responsible for extracting text and metadata from PDF documents (permits, BREFs, RIEs).
*   **Knowledge Base (JSON Files):** Stores structured information extracted from BREF and RIE documents.
*   **Large Language Model (LLM - OpenAI API):** Provides the core intelligence for scope matching and compliance verification.
*   **Backend Application (Python - Flask):** Handles file uploads, orchestrates PDF processing, interacts with the LLM, and serves the user interface.
*   **User Interface (Web-based - HTML, CSS, JavaScript):** Allows users to upload permits and view verification results.

## 3. Architectural Diagram (Conceptual)

```mermaid
graph TD
    User[User via Web Browser] -->|Uploads Permit (PDF)| UI{User Interface}
    UI -->|Permit PDF| Backend[Backend Application (Flask)]
    Backend -->|Process PDF| PDFExt[PDF Extraction Engine (Docling)]
    PDFExt -->|Extracted Text & Metadata| Backend
    Backend -->|Permit Info & KB Scope| LLM_Scope[LLM for Scope Matching (OpenAI API)]
    LLM_Scope -->|Applicable BREF/RIE IDs| Backend
    Backend -->|Load Applicable Documents| KB[(Knowledge Base - JSON Files)]
    KB -->|BREF/RIE Texts & Metadata| Backend
    Backend -->|Permit Text & BREF/RIE Text| LLM_Verify[LLM for Compliance Verification (OpenAI API)]
    LLM_Verify -->|Verification Results| Backend
    Backend -->|Display Results| UI
    User -->|Views Results| UI

    subgraph Initial Setup / Knowledge Base Creation
        Admin[Administrator/Developer] -->|Source BREF/RIE PDFs| PDFExt_KB[PDF Extraction Engine (Docling) for KB]
        PDFExt_KB -->|Extracted BREF/RIE Data| KB_Builder[Knowledge Base Builder Script]
        KB_Builder -->|Structured JSON Data| KB
    end
```

*(Note: This is a conceptual Mermaid diagram. Actual rendering might require a Mermaid-compatible viewer.)*

## 4. Component Specifications

### 4.1. PDF Extraction Engine (Docling)

*   **Library:** Docling (Python)
*   **Functionality:**
    *   Extract full textual content from PDF documents.
    *   Extract metadata: document titles, page numbers, paragraph/section identifiers (where available and feasible with Docling).
*   **Usage:**
    *   **Knowledge Base Population:** One-time processing of source BREF/RIE PDFs to populate the JSON knowledge base.
    *   **Permit Processing:** Real-time processing of user-uploaded permit PDFs.
*   **Output:** Structured text and associated metadata.

### 4.2. Knowledge Base (JSON Files)

*   **Format:** JSON, as detailed in the proposal (Section 3.1).
*   **Content:**
    *   `bref_documents`: Array of BREF document objects.
        *   `bref_id`, `title`, `document_url`, `scope_description`, `publication_date`, `source_metadata` (for scope).
        *   `bat_conclusions`: Array of BAT conclusion objects (`bat_id`, `bat_text_description`, `source_metadata`).
    *   `rie_documents`: Array of RIE document objects.
        *   `rie_id`, `title`, `document_url`, `scope_description`, `source_metadata` (for scope).
        *   `relevant_sections_livestock`: Array of RIE section objects (`section_id`, `section_text`, `source_metadata`).
*   **Location:** `/home/ubuntu/bat_rie_checker/knowledge_base/`
*   **Management:** Initially populated via scripts using Docling. Can be updated by replacing or adding new JSON files.

### 4.3. Large Language Model (LLM - OpenAI API)

*   **Provider:** OpenAI API.
*   **Access:** Via the official OpenAI Python client library.
*   **API Key:** Securely managed as an environment variable (`OPENAI_API_KEY`).
*   **Core Tasks:**
    *   **Scope Matching:** Compare permit activity descriptions with BREF/RIE scope descriptions to identify applicable documents.
    *   **Compliance Verification:** Compare permit conditions against specific BAT conclusions or RIE sections.
*   **Prompting Strategy:** As detailed in the proposal (Sections 4.2 and 4.3), emphasizing expert role-play and detailed, referenced outputs.

### 4.4. Backend Application (Python - Flask)

*   **Framework:** Flask (Python).
*   **Responsibilities:**
    *   Serve the static HTML, CSS, and JavaScript files for the UI.
    *   Handle HTTP requests for permit uploads.
    *   Manage temporary storage of uploaded files (e.g., in `/home/ubuntu/bat_rie_checker/uploads/`).
    *   Orchestrate the workflow: call Docling for PDF extraction, interact with the OpenAI API for analysis, and process results.
    *   Format and send verification results back to the UI.
    *   Implement basic error handling.
*   **Structure (Conceptual):**
    *   `app.py`: Main Flask application file, defining routes and core logic.
    *   `core_logic/`: Directory for Python modules handling specific tasks like PDF processing, LLM interaction, etc.
        *   `pdf_processor.py`: Functions related to Docling.
        *   `llm_handler.py`: Functions for interacting with OpenAI API.
        *   `knowledge_manager.py`: Functions for loading and accessing the JSON knowledge base.

### 4.5. User Interface (Web-based)

*   **Technologies:** HTML, CSS, JavaScript.
*   **Functionality:**
    *   **Permit Upload:** File input for PDF permits, optional metadata fields, "Start Verification" button, processing indicators.
    *   **Results Display:** Summary page (permit ID, overall assessment, applicable documents) and detailed breakdown per BREF/RIE and BAT/section, including cited text snippets and LLM justifications.
    *   **Export:** Option to export results (e.g., as Markdown or PDF - to be implemented in a later phase).
*   **Location:**
    *   HTML: `/home/ubuntu/bat_rie_checker/templates/`
    *   CSS/JS: `/home/ubuntu/bat_rie_checker/static/`
*   **Interaction:** Communicates with the backend via HTTP requests (e.g., AJAX for a smoother experience).

## 5. Data Flow

1.  **User Interaction:** User uploads a permit PDF via the web UI.
2.  **Backend Processing:**
    *   The Flask backend receives the PDF.
    *   Docling is invoked to extract text and metadata from the permit.
3.  **Scope Matching:**
    *   The backend sends the permit's activity description and scope descriptions from the knowledge base to the LLM.
    *   The LLM returns a list of applicable BREF/RIE documents.
4.  **Compliance Verification:**
    *   For each applicable document, the backend retrieves relevant BAT conclusions/RIE sections from the knowledge base.
    *   The backend iteratively sends the permit text and each BAT/RIE section text to the LLM for comparison.
    *   The LLM returns detailed findings (compliance, discrepancies, non-compliance, ambiguity) with references.
5.  **Results Presentation:**
    *   The backend formats the LLM's findings.
    *   The UI displays the structured results to the user.

## 6. Directory Structure (Proposed)

```
/home/ubuntu/bat_rie_checker/
├── app.py                     # Main Flask application
├── requirements.txt           # Python dependencies
├── venv/                      # Python virtual environment
├── core_logic/                # Business logic modules
│   ├── __init__.py
│   ├── pdf_processor.py
│   ├── llm_handler.py
│   └── knowledge_manager.py
├── knowledge_base/            # Stores BREF/RIE JSON data
│   ├── bref_example_1.json
│   └── rie_example_1.json
├── static/                    # CSS, JavaScript, images
│   ├── css/
│   │   └── style.css
│   └── js/
│       └── script.js
├── templates/                 # HTML templates
│   ├── index.html
│   └── results.html
├── uploads/                   # Temporary storage for uploaded permits (ensure .gitignore)
└── README.md                  # Setup and usage instructions
```

This architecture provides a modular and scalable foundation for the Automated EU BAT/RIE Compliance Verification System, aligning with the project proposal and user requirements.

