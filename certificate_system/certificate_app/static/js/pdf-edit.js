let currentPdfId = null;
let textBoxes = [];
let currentZoom = 100;
let isDrawing = false;
let startX, startY, currentBox = null;

document.addEventListener('DOMContentLoaded', function() {
    // Get PDF ID from URL
    const pathParts = window.location.pathname.split('/');
    currentPdfId = parseInt(pathParts[pathParts.length - 2]);
    
    if (currentPdfId) {
        loadPDFData();
        setupEventListeners();
    }
});

async function loadPDFData() {
    try {
        const response = await fetch(`/api/edit/${currentPdfId}/`);
        const data = await response.json();
        
        if (response.ok) {
            document.getElementById('pdfTitle').textContent = data.pdf_name;
            document.getElementById('pdfEmbed').src = data.pdf_data;
            
            textBoxes = data.text_boxes;
            updateBoxesList();
        } else {
            alert('Error loading PDF data');
        }
    } catch (error) {
        console.error('Error:', error);
        alert('Error loading PDF data');
    }
}

function setupEventListeners() {
    // Save boxes button
    document.getElementById('saveBoxes').addEventListener('click', saveBoxes);
    
    // Add box button
    document.getElementById('addBox').addEventListener('click', startDrawing);
    
    // Zoom controls
    document.getElementById('zoomIn').addEventListener('click', () => adjustZoom(10));
    document.getElementById('zoomOut').addEventListener('click', () => adjustZoom(-10));
    
    // Box form
    document.getElementById('boxEditForm').addEventListener('submit', saveBox);
    document.getElementById('cancelEdit').addEventListener('click', cancelEdit);
    document.getElementById('deleteBox').addEventListener('click', deleteCurrentBox);
}

function startDrawing() {
    const overlay = document.getElementById('drawingOverlay');
    const pdfViewer = document.getElementById('pdfViewer');
    
    overlay.style.display = 'block';
    overlay.style.width = pdfViewer.offsetWidth + 'px';
    overlay.style.height = pdfViewer.offsetHeight + 'px';
    
    overlay.onmousedown = function(e) {
        isDrawing = true;
        startX = e.offsetX;
        startY = e.offsetY;
        
        currentBox = document.createElement('div');
        currentBox.style.position = 'absolute';
        currentBox.style.border = '2px dashed #3498db';
        currentBox.style.background = 'rgba(52, 152, 219, 0.1)';
        currentBox.style.left = startX + 'px';
        currentBox.style.top = startY + 'px';
        overlay.appendChild(currentBox);
    };
    
    overlay.onmousemove = function(e) {
        if (!isDrawing) return;
        
        const currentX = e.offsetX;
        const currentY = e.offsetY;
        
        const width = Math.abs(currentX - startX);
        const height = Math.abs(currentY - startY);
        const left = Math.min(currentX, startX);
        const top = Math.min(currentY, startY);
        
        currentBox.style.left = left + 'px';
        currentBox.style.top = top + 'px';
        currentBox.style.width = width + 'px';
        currentBox.style.height = height + 'px';
    };
    
    overlay.onmouseup = function(e) {
        if (!isDrawing) return;
        
        isDrawing = false;
        const width = Math.abs(e.offsetX - startX);
        const height = Math.abs(e.offsetY - startY);
        
        if (width > 10 && height > 10) {
            createNewBox(startX, startY, width, height);
        }
        
        overlay.style.display = 'none';
        overlay.innerHTML = '';
        overlay.onmousedown = null;
        overlay.onmousemove = null;
        overlay.onmouseup = null;
    };
}

function createNewBox(x, y, width, height) {
    const boxNumber = textBoxes.length + 1;
    const newBox = {
        id: 'new-' + Date.now(),
        name: `field_${boxNumber}`,
        x: x,
        y: y,
        width: width,
        height: height,
        page: 1,
        font_size: 12,
        font_family: 'Helvetica'
    };
    
    textBoxes.push(newBox);
    updateBoxesList();
    editBox(newBox);
}

function updateBoxesList() {
    const boxesList = document.getElementById('boxesList');
    boxesList.innerHTML = '';
    
    textBoxes.forEach(box => {
        const boxElement = document.createElement('div');
        boxElement.className = 'box-item';
        boxElement.innerHTML = `
            <strong>${box.name}</strong><br>
            Position: (${Math.round(box.x)}, ${Math.round(box.y)})<br>
            Size: ${Math.round(box.width)} × ${Math.round(box.height)}
        `;
        boxElement.addEventListener('click', () => editBox(box));
        boxesList.appendChild(boxElement);
    });
}

function editBox(box) {
    document.getElementById('boxForm').style.display = 'block';
    document.getElementById('boxId').value = box.id;
    document.getElementById('boxName').value = box.name;
    document.getElementById('boxX').value = box.x;
    document.getElementById('boxY').value = box.y;
    document.getElementById('boxWidth').value = box.width;
    document.getElementById('boxHeight').value = box.height;
    document.getElementById('boxFontSize').value = box.font_size;
    
    // Highlight in list
    document.querySelectorAll('.box-item').forEach(item => {
        item.classList.remove('active');
    });
    event.currentTarget.classList.add('active');
}

function cancelEdit() {
    document.getElementById('boxForm').style.display = 'none';
    document.querySelectorAll('.box-item').forEach(item => {
        item.classList.remove('active');
    });
}

function saveBox(e) {
    e.preventDefault();
    
    const boxId = document.getElementById('boxId').value;
    const boxIndex = textBoxes.findIndex(box => box.id == boxId);
    
    if (boxIndex !== -1) {
        textBoxes[boxIndex] = {
            ...textBoxes[boxIndex],
            name: document.getElementById('boxName').value,
            x: parseFloat(document.getElementById('boxX').value),
            y: parseFloat(document.getElementById('boxY').value),
            width: parseFloat(document.getElementById('boxWidth').value),
            height: parseFloat(document.getElementById('boxHeight').value),
            font_size: parseInt(document.getElementById('boxFontSize').value)
        };
        
        updateBoxesList();
        cancelEdit();
    }
}

function deleteCurrentBox() {
    const boxId = document.getElementById('boxId').value;
    const boxIndex = textBoxes.findIndex(box => box.id == boxId);
    
    if (boxIndex !== -1) {
        textBoxes.splice(boxIndex, 1);
        updateBoxesList();
        cancelEdit();
    }
}

async function saveBoxes() {
    try {
        const response = await fetch(`/api/edit/${currentPdfId}/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                text_boxes: textBoxes
            })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            alert('Text boxes saved successfully!');
            // Reload to get actual IDs from server
            loadPDFData();
        } else {
            alert('Error saving text boxes: ' + data.error);
        }
    } catch (error) {
        console.error('Error:', error);
        alert('Error saving text boxes');
    }
}

function adjustZoom(delta) {
    currentZoom += delta;
    currentZoom = Math.max(50, Math.min(200, currentZoom));
    
    document.getElementById('zoomLevel').textContent = currentZoom + '%';
    document.getElementById('pdfEmbed').style.transform = `scale(${currentZoom / 100})`;
    document.getElementById('pdfEmbed').style.transformOrigin = 'top left';
}