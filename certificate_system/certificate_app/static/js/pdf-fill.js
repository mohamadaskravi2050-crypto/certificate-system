let currentPdfId = null;
let textBoxes = [];

document.addEventListener('DOMContentLoaded', function() {
    // Get PDF ID from URL
    const pathParts = window.location.pathname.split('/');
    currentPdfId = parseInt(pathParts[pathParts.length - 2]);
    
    if (currentPdfId) {
        loadPDFForm();
        setupEventListeners();
    }
});

async function loadPDFForm() {
    try {
        const response = await fetch(`/api/fill/${currentPdfId}/`);
        const data = await response.json();
        
        if (response.ok) {
            document.getElementById('formTitle').textContent = `Fill: ${data.pdf_name}`;
            document.getElementById('pdfPreview').src = data.pdf_preview;
            
            textBoxes = data.text_boxes;
            generateFormFields();
        } else {
            alert('Error loading PDF form');
        }
    } catch (error) {
        console.error('Error:', error);
        alert('Error loading PDF form');
    }
}

function setupEventListeners() {
    document.getElementById('downloadPdf').addEventListener('click', downloadFilledPDF);
}

function generateFormFields() {
    const formFields = document.getElementById('formFields');
    formFields.innerHTML = '';
    
    textBoxes.forEach(box => {
        const fieldDiv = document.createElement('div');
        fieldDiv.className = 'form-group';
        
        fieldDiv.innerHTML = `
            <label for="field_${box.id}">${box.label}:</label>
            <input type="text" 
                   id="field_${box.id}" 
                   name="${box.name}" 
                   class="text-input" 
                   placeholder="Enter ${box.label}">
        `;
        
        formFields.appendChild(fieldDiv);
    });
}

async function downloadFilledPDF() {
    const formData = new FormData(document.getElementById('fillForm'));
    const values = {};
    
    textBoxes.forEach(box => {
        const input = document.getElementById(`field_${box.id}`);
        values[box.name] = input.value;
    });
    
    try {
        const response = await fetch(`/api/fill/${currentPdfId}/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                values: values
            })
        });
        
        if (response.ok) {
            // Create download link
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `filled_document_${currentPdfId}.pdf`;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);
        } else {
            const errorData = await response.json();
            alert('Error generating PDF: ' + errorData.error);
        }
    } catch (error) {
        console.error('Error:', error);
        alert('Error generating PDF');
    }
}