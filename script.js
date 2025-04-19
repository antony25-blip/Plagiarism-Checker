document.addEventListener('DOMContentLoaded', function() {
    // DOM Elements
    const doc1Input = document.getElementById('doc1');
    const folderInput = document.getElementById('folder');
    const mainDocBox = document.getElementById('mainDocBox');
    const folderBox = document.getElementById('folderBox');
    const mainDocDetails = document.getElementById('mainDocDetails');
    const folderDetails = document.getElementById('folderDetails');
    const checkBtn = document.getElementById('checkPlagiarism');
    const loading = document.getElementById('loading');
    const errorMessage = document.getElementById('errorMessage');
    const resultsSection = document.getElementById('resultsSection');
    const plagiarismResults = document.getElementById('plagiarism-results');
    const progressBar = document.getElementById('progressBar');
    const summary = document.getElementById('summary');

    if (!checkBtn) {
        console.error('Error: Check button with ID "checkPlagiarism" not found in HTML.');
        alert('Error: Check button not found. Please check your HTML.');
        return;
    }
    console.log('Script loaded and DOM ready');

    // Make upload boxes trigger file input clicks
    mainDocBox.addEventListener('click', () => {
        if (doc1Input) doc1Input.click();
        else console.error('doc1 input not found');
    });
    folderBox.addEventListener('click', () => {
        if (folderInput) folderInput.click();
        else console.error('folder input not found');
    });

    // File upload handling
    doc1Input.addEventListener('change', function(e) {
        if (e.target.files.length > 0) {
            const file = e.target.files[0];
            mainDocBox.classList.add('active');
            mainDocDetails.innerHTML = getFileDetailsHTML(file);
            updateCheckButton();
        }
    });

    folderInput.addEventListener('change', function(e) {
        if (e.target.files.length > 0) {
            folderBox.classList.add('active');
            folderDetails.innerHTML = `
                <p><strong>${e.target.files.length} files selected</strong></p>
                ${Array.from(e.target.files).map(file => getFileDetailsHTML(file)).join('')}
            `;
            updateCheckButton();
        }
    });

    // Drag and drop functionality
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        mainDocBox.addEventListener(eventName, preventDefaults, false);
        folderBox.addEventListener(eventName, preventDefaults, false);
    });

    ['dragenter', 'dragover'].forEach(eventName => {
        mainDocBox.addEventListener(eventName, highlight, false);
        folderBox.addEventListener(eventName, highlight, false);
    });

    ['dragleave', 'drop'].forEach(eventName => {
        mainDocBox.addEventListener(eventName, unhighlight, false);
        folderBox.addEventListener(eventName, unhighlight, false);
    });

    mainDocBox.addEventListener('drop', handleDropMainDoc, false);
    folderBox.addEventListener('drop', handleDropFolder, false);

    function preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }

    function highlight(e) {
        e.currentTarget.classList.add('highlight');
    }

    function unhighlight(e) {
        e.currentTarget.classList.remove('highlight');
    }

    function handleDropMainDoc(e) {
        const dt = e.dataTransfer;
        const files = dt.files;
        if (files.length > 0) {
            doc1Input.files = files;
            const event = new Event('change');
            doc1Input.dispatchEvent(event);
        }
    }

    function handleDropFolder(e) {
        const dt = e.dataTransfer;
        const files = dt.files;
        if (files.length > 0) {
            folderInput.files = files;
            const event = new Event('change');
            folderInput.dispatchEvent(event);
        }
    }

    // Update check button state
    function updateCheckButton() {
        checkBtn.disabled = !(doc1Input.files.length > 0 && folderInput.files.length > 0);
        console.log('Check button state updated:', checkBtn.disabled);
    }

    // Check plagiarism button click
    checkBtn.addEventListener('click', async function() {
        console.log('Check button clicked');
        errorMessage.style.display = 'none';
        loading.style.display = 'block';
        resultsSection.style.display = 'none';
        checkBtn.disabled = true;

        const formData = new FormData();
        if (!doc1Input.files[0]) {
            console.error('No main document selected');
            errorMessage.textContent = 'Please select a main document.';
            errorMessage.style.display = 'block';
            loading.style.display = 'none';
            checkBtn.disabled = false;
            return;
        }
        formData.append('doc1', doc1Input.files[0]);
        for (let i = 0; i < folderInput.files.length; i++) {
            formData.append('folder', folderInput.files[i]);
        }

        try {
            let progress = 0;
            const progressInterval = setInterval(() => {
                progress += 10;
                progressBar.style.width = `${progress}%`;
                if (progress >= 100) clearInterval(progressInterval);
            }, 200);

            const response = await fetch('/check-plagiarism-folder', {
                method: 'POST',
                body: formData
            });

            console.log('Fetch response status:', response.status);
            if (!response.ok) {
                throw new Error(`Server returned ${response.status} - ${response.statusText}`);
            }

            const data = await response.json();
            console.log('Received data:', data);

            displayResults(data.files);
        } catch (error) {
            console.error('Error during fetch:', error);
            errorMessage.textContent = `Error: ${error.message}`;
            errorMessage.style.display = 'block';
            alert(`Fetch failed: ${error.message}`);
        } finally {
            loading.style.display = 'none';
            checkBtn.disabled = false;
            progressBar.style.width = '0%';
        }
    });

    // Display results
    function displayResults(files) {
        console.log('Displaying results for:', files);
        plagiarismResults.innerHTML = '';
        resultsSection.style.display = 'block';

        if (!files || files.length === 0) {
            plagiarismResults.innerHTML = '<p>No results found.</p>';
            console.log('No files to display');
            return;
        }

        const total = files.reduce((sum, file) => sum + (file.plagiarism_percentage || 0), 0);
        const average = total / files.length || 0;
        summary.innerHTML = `
            <span class="percentage ${getPercentageClass(average)}">
                Average: ${average.toFixed(1)}%
            </span>
        `;

        files.sort((a, b) => (b.plagiarism_percentage || 0) - (a.plagiarism_percentage || 0));

        files.forEach(file => {
            const resultItem = document.createElement('div');
            resultItem.className = 'result-item';
            const percentageClass = getPercentageClass(file.plagiarism_percentage || 0);
            const fileTypeIndicator = file.error ? ' (OCR/Processing Error)' : 
                /\.(jpg|png|pdf)$/.test(file.file_name) ? ' (Image/PDF - OCR Processed)' : '';

            resultItem.innerHTML = `
                <div class="result-header">
                    <span class="filename">${file.file_name}${fileTypeIndicator}</span>
                    <span class="percentage ${percentageClass}">
                        ${file.plagiarism_percentage !== undefined ? file.plagiarism_percentage.toFixed(1) : 'N/A'}%
                    </span>
                </div>
                ${file.error ? `
                    <div class="error-message">
                        <p><strong>Error:</strong> ${file.error}</p>
                    </div>
                ` : ''}
                ${file.matches && file.matches.length > 0 ? `
                    <div class="matches">
                        <p><strong>Matching Content:</strong></p>
                        ${file.matches.slice(0, 3).map(match => `
                            <div class="match">${truncate(match, 150)}</div>
                        `).join('')}
                        ${file.matches.length > 3 ? `<p>+ ${file.matches.length - 3} more matches...</p>` : ''}
                    </div>
                ` : ''}
                ${file.suggestions && file.suggestions.length > 0 ? `
                    <div class="suggestions">
                        <p><strong>Suggestions:</strong></p>
                        ${file.suggestions.slice(0, 2).map(suggestion => `
                            <div class="suggestion">${suggestion}</div>
                        `).join('')}
                    </div>
                ` : ''}
            `;

            plagiarismResults.appendChild(resultItem);
        });
    }

    // Helper functions
    function getPercentageClass(percentage) {
        if (percentage > 50) return 'high';
        if (percentage > 20) return 'medium';
        return 'low';
    }

    function truncate(text, length) {
        return text.length > length ? text.substring(0, length) + '...' : text;
    }

    function getFileDetailsHTML(file) {
        const fileType = /\.(jpg|png|pdf)$/.test(file.name) ? ' (Image/PDF)' : '';
        return `
            <p><strong>${file.name}${fileType}</strong></p>
            <p>${(file.size / 1024).toFixed(2)} KB</p>
        `;
    }
});