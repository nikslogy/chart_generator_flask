/**
 * File upload module - Handles file upload functionality
 */

export const initFileUpload = (callbacks) => {
    // DOM Elements
    const excelFileInput = document.getElementById('excelFile');
    const fileNameDisplay = document.getElementById('file-name');
    const loadingIndicator = document.getElementById('loading-indicator');
    const dropArea = document.querySelector('.file-upload-label');
    
    // File upload handling
    excelFileInput.addEventListener('change', function(e) {
        if (this.files && this.files[0]) {
            const file = this.files[0];
            fileNameDisplay.textContent = file.name;
            uploadFile(file);
        }
    });
    
    // Drag and drop handling
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        dropArea.addEventListener(eventName, preventDefaults, false);
    });
    
    ['dragenter', 'dragover'].forEach(eventName => {
        dropArea.addEventListener(eventName, highlight, false);
    });
    
    ['dragleave', 'drop'].forEach(eventName => {
        dropArea.addEventListener(eventName, unhighlight, false);
    });
    
    function preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }
    
    function highlight() {
        dropArea.classList.add('highlight');
    }
    
    function unhighlight() {
        dropArea.classList.remove('highlight');
    }
    
    dropArea.addEventListener('drop', function(e) {
        const file = e.dataTransfer.files[0];
        excelFileInput.files = e.dataTransfer.files;
        fileNameDisplay.textContent = file.name;
        uploadFile(file);
    });
    
    // Function to upload the file to the server
    function uploadFile(file) {
        const formData = new FormData();
        formData.append('excelFile', file);
        
        loadingIndicator.classList.remove('hidden');
        
        console.log('Uploading file:', file.name);
        
        fetch('/upload', {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            loadingIndicator.classList.add('hidden');
            console.log('Upload response:', data);
            
            if (data.success) {
                const filename = data.filename;
                const sheets = data.sheets;
                
                console.log('File uploaded successfully:', filename);
                console.log('Available sheets:', sheets);
                
                // Store filename in a more persistent way (for page reloads)
                localStorage.setItem('currentFileName', filename);
                
                if (callbacks && callbacks.onUploadSuccess) {
                    callbacks.onUploadSuccess(filename, sheets);
                }
            } else {
                console.error('Upload error:', data.error);
                alert('Error: ' + data.error);
            }
        })
        .catch(error => {
            loadingIndicator.classList.add('hidden');
            console.error('Error uploading file:', error);
            alert('Error uploading file. Please try again.');
        });
    }
}; 