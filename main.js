// /home/ubuntu/bat_rie_checker_app/src/static/js/main.js

document.addEventListener("DOMContentLoaded", () => {
    const uploadForm = document.getElementById("upload-form");
    const statusMessages = document.getElementById("status-messages");
    const reportLinks = document.getElementById("report-links");
    const jsonResults = document.getElementById("json-results");

    if (uploadForm) {
        uploadForm.addEventListener("submit", async (event) => {
            event.preventDefault();
            statusMessages.innerHTML = ""; // Clear previous messages
            reportLinks.innerHTML = "";
            jsonResults.textContent = "";

            const formData = new FormData(uploadForm);
            const permitFile = formData.get("permit_file");
            const brefFiles = formData.getAll("bref_files"); // Get all BREF files

            if (!permitFile || permitFile.size === 0) {
                displayMessage("Please select a permit document.", "error");
                return;
            }

            displayMessage("Processing... Please wait. This may take a few minutes depending on the document size and complexity.", "info");

            try {
                const response = await fetch("/verify", {
                    method: "POST",
                    body: formData,
                });

                if (response.ok) {
                    const result = await response.json();
                    displayMessage("Verification complete!", "success");
                    
                    if (result.report_paths) {
                        if (result.report_paths.markdown) {
                            const mdLink = document.createElement("a");
                            mdLink.href = result.report_paths.markdown;
                            mdLink.textContent = "Download Markdown Report";
                            mdLink.target = "_blank"; // Open in new tab
                            mdLink.download = result.report_paths.markdown.split("/").pop(); // Suggest filename
                            reportLinks.appendChild(mdLink);
                        }
                        if (result.report_paths.pdf) {
                            const pdfLink = document.createElement("a");
                            pdfLink.href = result.report_paths.pdf;
                            pdfLink.textContent = "Download PDF Report";
                            pdfLink.target = "_blank";
                            pdfLink.download = result.report_paths.pdf.split("/").pop();
                            reportLinks.appendChild(pdfLink);
                        }
                    }
                    // Displaying the full JSON for now, can be refined
                    jsonResults.textContent = JSON.stringify(result.full_analysis || result, null, 2);

                } else {
                    const errorResult = await response.json();
                    displayMessage(`Error: ${errorResult.error || response.statusText}`, "error");
                    jsonResults.textContent = JSON.stringify(errorResult, null, 2);
                }
            } catch (error) {
                console.error("Error during form submission:", error);
                displayMessage(`An unexpected error occurred: ${error.message}`, "error");
            }
        });
    }

    function displayMessage(message, type) {
        statusMessages.innerHTML = ""; // Clear previous messages
        const messageDiv = document.createElement("div");
        messageDiv.className = type; // e.g., "success", "error", "info"
        messageDiv.textContent = message;
        statusMessages.appendChild(messageDiv);
    }
});

