// Constantes
const CM_TO_PIXELS = 3.7795275591; // 1 cm = ~3.78 pixels (96 DPI)

// Variables globales
let canvas, ctx;
let canvasWidthCm = 100;
let canvasHeightCm = 100;
let isDrawing = false;
let currentMode = 'draw'; // 'draw' o 'ruler'
let trajectoryPoints = [];
let rulerStart = null;
let rulerEnd = null;

// Inicialización
document.addEventListener('DOMContentLoaded', function() {
    canvas = document.getElementById('drawingCanvas');
    ctx = canvas.getContext('2d');
    
    // Inicializar canvas
    updateCanvasSize();
    
    // Event listeners para controles
    document.getElementById('applyCanvasSize').addEventListener('click', applyCanvasSize);
    document.getElementById('drawMode').addEventListener('click', setDrawMode);
    document.getElementById('rulerMode').addEventListener('click', setRulerMode);
    document.getElementById('clearCanvas').addEventListener('click', clearCanvas);
    document.getElementById('saveCoordinates').addEventListener('click', saveCoordinates);
    document.getElementById('loadJSON').addEventListener('click', () => {
        document.getElementById('jsonFileInput').click();
    });
    document.getElementById('jsonFileInput').addEventListener('change', loadJSONFile);
    
    // Event listeners del canvas
    canvas.addEventListener('mousedown', handleMouseDown);
    canvas.addEventListener('mousemove', handleMouseMove);
    canvas.addEventListener('mouseup', handleMouseUp);
    canvas.addEventListener('mouseleave', handleMouseLeave);
    
    // Actualizar información inicial
    updatePointCount();
});

// Funciones de configuración del canvas
function updateCanvasSize() {
    const widthPx = Math.round(canvasWidthCm * CM_TO_PIXELS);
    const heightPx = Math.round(canvasHeightCm * CM_TO_PIXELS);
    
    canvas.width = widthPx;
    canvas.height = heightPx;
    
    redrawCanvas();
}

function applyCanvasSize() {
    const newWidth = parseFloat(document.getElementById('canvasWidth').value);
    const newHeight = parseFloat(document.getElementById('canvasHeight').value);
    
    if (newWidth >= 10 && newWidth <= 500 && newHeight >= 10 && newHeight <= 500) {
        canvasWidthCm = newWidth;
        canvasHeightCm = newHeight;
        updateCanvasSize();
    } else {
        alert('Por favor, ingrese valores válidos entre 10 y 500 cm.');
    }
}

// Funciones de modo
function setDrawMode() {
    currentMode = 'draw';
    document.getElementById('drawMode').classList.add('active');
    document.getElementById('rulerMode').classList.remove('active');
    canvas.style.cursor = 'crosshair';
    rulerStart = null;
    rulerEnd = null;
    redrawCanvas();
}

function setRulerMode() {
    currentMode = 'ruler';
    document.getElementById('rulerMode').classList.add('active');
    document.getElementById('drawMode').classList.remove('active');
    canvas.style.cursor = 'crosshair';
    rulerStart = null;
    rulerEnd = null;
    document.getElementById('rulerDistance').textContent = '0.00 cm';
}

// Funciones de dibujo
function handleMouseDown(e) {
    const rect = canvas.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;
    
    if (currentMode === 'draw') {
        isDrawing = true;
        trajectoryPoints.push({ x, y });
        drawPoint(x, y);
        updatePointCount();
    } else if (currentMode === 'ruler') {
        rulerStart = { x, y };
        rulerEnd = null;
    }
}

function handleMouseMove(e) {
    const rect = canvas.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;
    
    if (currentMode === 'draw' && isDrawing) {
        trajectoryPoints.push({ x, y });
        drawLine(trajectoryPoints[trajectoryPoints.length - 2], { x, y });
        updatePointCount();
    } else if (currentMode === 'ruler' && rulerStart) {
        rulerEnd = { x, y };
        redrawCanvas();
        drawRuler();
        calculateDistance();
    }
}

function handleMouseUp(e) {
    if (currentMode === 'draw') {
        isDrawing = false;
    } else if (currentMode === 'ruler' && rulerStart) {
        const rect = canvas.getBoundingClientRect();
        const x = e.clientX - rect.left;
        const y = e.clientY - rect.top;
        rulerEnd = { x, y };
        redrawCanvas();
        drawRuler();
        calculateDistance();
    }
}

function handleMouseLeave(e) {
    if (currentMode === 'draw') {
        isDrawing = false;
    }
}

function drawPoint(x, y) {
    ctx.fillStyle = '#e74c3c';
    ctx.beginPath();
    ctx.arc(x, y, 3, 0, 2 * Math.PI);
    ctx.fill();
}

function drawLine(start, end) {
    ctx.strokeStyle = '#3498db';
    ctx.lineWidth = 2;
    ctx.lineCap = 'round';
    ctx.lineJoin = 'round';
    ctx.beginPath();
    ctx.moveTo(start.x, start.y);
    ctx.lineTo(end.x, end.y);
    ctx.stroke();
}

function drawRuler() {
    if (!rulerStart || !rulerEnd) return;
    
    // Dibujar línea de la regla
    ctx.strokeStyle = '#e74c3c';
    ctx.lineWidth = 2;
    ctx.setLineDash([5, 5]);
    ctx.beginPath();
    ctx.moveTo(rulerStart.x, rulerStart.y);
    ctx.lineTo(rulerEnd.x, rulerEnd.y);
    ctx.stroke();
    ctx.setLineDash([]);
    
    // Dibujar puntos de inicio y fin
    ctx.fillStyle = '#e74c3c';
    ctx.beginPath();
    ctx.arc(rulerStart.x, rulerStart.y, 5, 0, 2 * Math.PI);
    ctx.fill();
    ctx.beginPath();
    ctx.arc(rulerEnd.x, rulerEnd.y, 5, 0, 2 * Math.PI);
    ctx.fill();
}

function calculateDistance() {
    if (!rulerStart || !rulerEnd) return;
    
    const dx = rulerEnd.x - rulerStart.x;
    const dy = rulerEnd.y - rulerStart.y;
    const distancePx = Math.sqrt(dx * dx + dy * dy);
    const distanceCm = distancePx / CM_TO_PIXELS;
    
    document.getElementById('rulerDistance').textContent = distanceCm.toFixed(2) + ' cm';
}

function redrawCanvas() {
    // Limpiar canvas
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    
    // Redibujar trayectoria
    if (trajectoryPoints.length > 0) {
        drawPoint(trajectoryPoints[0].x, trajectoryPoints[0].y);
        
        for (let i = 1; i < trajectoryPoints.length; i++) {
            drawLine(trajectoryPoints[i - 1], trajectoryPoints[i]);
            drawPoint(trajectoryPoints[i].x, trajectoryPoints[i].y);
        }
    }
}

function clearCanvas() {
    if (confirm('¿Está seguro de que desea limpiar el canvas?')) {
        trajectoryPoints = [];
        rulerStart = null;
        rulerEnd = null;
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        updatePointCount();
        document.getElementById('rulerDistance').textContent = '0.00 cm';
    }
}

function updatePointCount() {
    document.getElementById('pointCount').textContent = trajectoryPoints.length;
}

// Funciones de guardado y carga
function saveCoordinates() {
    if (trajectoryPoints.length === 0) {
        alert('No hay coordenadas para guardar.');
        return;
    }
    
    // Convertir puntos de pixels a centímetros
    const coordinatesCm = trajectoryPoints.map(point => ({
        x: (point.x / CM_TO_PIXELS).toFixed(2),
        y: (point.y / CM_TO_PIXELS).toFixed(2)
    }));
    
    const data = {
        canvasSize: {
            width: canvasWidthCm,
            height: canvasHeightCm
        },
        trajectory: coordinatesCm,
        metadata: {
            pointCount: trajectoryPoints.length,
            createdAt: new Date().toISOString()
        }
    };
    
    const jsonString = JSON.stringify(data, null, 2);
    const blob = new Blob([jsonString], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `trajectory_${Date.now()}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    
    alert(`Coordenadas guardadas: ${trajectoryPoints.length} puntos`);
}

function loadJSONFile(event) {
    const file = event.target.files[0];
    if (!file) return;
    
    const reader = new FileReader();
    reader.onload = function(e) {
        try {
            const data = JSON.parse(e.target.result);
            loadTrajectory(data);
        } catch (error) {
            alert('Error al cargar el archivo JSON: ' + error.message);
        }
    };
    reader.readAsText(file);
}

function loadTrajectory(data) {
    // Validar estructura del JSON
    if (!data.trajectory || !Array.isArray(data.trajectory)) {
        alert('El archivo JSON no contiene una estructura de trayectoria válida.');
        return;
    }
    
    // Limpiar trayectoria actual
    trajectoryPoints = [];
    
    // Aplicar tamaño de canvas si está definido
    if (data.canvasSize) {
        if (data.canvasSize.width) {
            canvasWidthCm = parseFloat(data.canvasSize.width);
            document.getElementById('canvasWidth').value = canvasWidthCm;
        }
        if (data.canvasSize.height) {
            canvasHeightCm = parseFloat(data.canvasSize.height);
            document.getElementById('canvasHeight').value = canvasHeightCm;
        }
        updateCanvasSize();
    }
    
    // Convertir coordenadas de cm a pixels y añadir a trayectoria
    data.trajectory.forEach(point => {
        const xPx = parseFloat(point.x) * CM_TO_PIXELS;
        const yPx = parseFloat(point.y) * CM_TO_PIXELS;
        trajectoryPoints.push({ x: xPx, y: yPx });
    });
    
    // Redibujar canvas
    redrawCanvas();
    updatePointCount();
    
    alert(`Trayectoria cargada: ${trajectoryPoints.length} puntos`);
}
