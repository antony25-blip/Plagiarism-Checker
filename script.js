document.getElementById('checkPlagiarism').addEventListener('click', async function() {
    const doc1 = document.getElementById('doc1').files[0];
    const folder = document.getElementById('folder').files;

    // Check if both the document and folder are uploaded
    if (!doc1 || folder.length === 0) {
        alert("Please upload the document and folder of files.");
        return;
    }

    const formData = new FormData();
    formData.append("doc1", doc1);
    for (let i = 0; i < folder.length; i++) {
        formData.append("folder", folder[i]);
    }

    try {
        // Make a POST request to the Flask server
        const response = await fetch('http://127.0.0.1:5000/check-plagiarism-folder', {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            throw new Error("Failed to fetch plagiarism results. Status: " + response.status);
        }

        const result = await response.json();
        displayResults(result);

    } catch (error) {
        console.error('Error checking plagiarism:', error);
        document.getElementById('error').textContent = 'Error: ' + error.message;
    }
});

function displayResults(result) {
    const plagiarismResults = document.getElementById('plagiarism-results');
    plagiarismResults.innerHTML = ''; // Clear previous results

    result.files.forEach((fileResult, index) => {
        const resultDiv = document.createElement('div');
        resultDiv.innerHTML = `<h3>File: ${fileResult.file_name}</h3>
                               <p>Plagiarism Percentage: ${fileResult.plagiarism_percentage}%</p>
                               <p>Matched Content:</p>
                               <ul>${fileResult.matches.map(match => `<li>${match}</li>`).join('')}</ul>
                               <p>Suggestions for Changes:</p>
                               <ul>${fileResult.suggestions.map(suggestion => `<li>${suggestion}</li>`).join('')}</ul>`;
        plagiarismResults.appendChild(resultDiv);
    });
}
