## README.md

### Project Overview

This project is a compliance verification system for EU environmental regulations, specifically focusing on Best Available Techniques (BAT) and associated emission limits (AELs) from BREF documents and permits.

### Features

- **PDF Extraction**: Extracts text and data from PDF documents.
- **Document Processing**: Parses and analyzes BREF and permit documents.
- **Compliance Verification**: Compares permit conditions with BAT conclusions.
- **Reporting**: Generates reports on compliance status.

### Setup and Installation

1.  **Prerequisites**:
    -   Python 3.x
    -   pip (Python package installer)
    -   Virtual environment tool (e.g., `venv`)

2.  **Clone the repository**:
    ```bash
    git clone https://github.com/yourusername/bat-rie-compliance-checker.git
    cd bat-rie-compliance-checker
    ```

3.  **Create and activate a virtual environment**:
    ```bash
    python3 -m venv venv
    source venv/bin/activate  # On Windows use `venv\Scripts\activate`
    ```

4.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

### Usage

1.  **Prepare your documents**:
    -   Place your BREF documents in the `data/bref_documents` directory.
    -   Place your permit documents in the `data/permit_documents` directory.

2.  **Run the main script**:
    ```bash
    python main.py
    ```

3.  **View the results**:
    -   The script will output the compliance status and generate a report in the `reports` directory.

### Configuration

-   **API Keys**: If the system uses external APIs (e.g., for OCR or advanced text analysis), you may need to set API keys as environment variables. Refer to the specific API documentation for details.
-   **Database**: If a database is used for storing results or managing documents, ensure it is properly configured. Default settings might be provided, but customization might be necessary depending on your setup.

### Troubleshooting

-   **Missing dependencies**: Ensure all dependencies listed in `requirements.txt` are installed correctly. Try running `pip install -r requirements.txt` again.
-   **File not found errors**: Verify that the paths to BREF and permit documents are correct and that the files exist in the specified locations.
-   **Other issues**: For any other issues, please check the logs or contact the development team.

### Contributing

Contributions are welcome! Please follow these steps:

1.  Fork the repository.
2.  Create a new branch for your feature or bug fix.
3.  Make your changes.
4.  Write tests for your changes.
5.  Ensure all tests pass.
6.  Submit a pull request.

### License

This project is licensed under the MIT License. See the LICENSE file for details.

