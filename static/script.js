// Global Viewer Instance
let glViewer = null;

// 1. Initialize on Load (Charts only)
document.addEventListener('DOMContentLoaded', function() {
    if (document.getElementById('plotly-chart')) {
        initChart();
    }
});

// 2. THE CRITICAL FIX: Listen for HTMX to finish
// This runs AFTER "Aligning Vectors" finishes and the card is shown.
document.body.addEventListener('htmx:afterSettle', function(evt) {
    
    // Find the hidden data we sent from Python
    const hiddenPdb = document.getElementById('hidden-pdb-data');
    const viewerElement = document.getElementById('molecule-viewer');

    // Only run if we are on the Home page and have data
    if (viewerElement && hiddenPdb && hiddenPdb.value.trim() !== "") {
        console.log("Synapse: Found 3D data. Drawing model...");
        update3DViewer(viewerElement, hiddenPdb.value);
    }
});

// --- 3D Logic ---
function update3DViewer(element, pdbData) {
    let config = { backgroundColor: '#F9FAFB' }; // Light Gray
    
    // Create viewer
    glViewer = $3Dmol.createViewer(element, config);
    
    glViewer.clear();
    glViewer.addModel(pdbData, "pdb");
    
    // Make it look like a cartoon structure with colors
    glViewer.setStyle({}, {cartoon: {color: 'spectrum'}});
    
    // Zoom to fit and start spinning
    glViewer.zoomTo();
    glViewer.render();
    glViewer.spin('y', 0.5); 
}

// --- Chart Logic ---
function initChart() {
    if (!document.getElementById('plotly-chart')) return;

    var trace1 = {
        x: [1, 2, 3, 4, 5], y: [10, 15, 13, 17, 14],
        mode: 'markers', type: 'scatter',
        marker: { size: 10, color: '#2563eb' },
        name: 'Genomic'
    };
    
    var layout = { 
        margin: {t:10, l:30, r:10, b:30},
        paper_bgcolor: 'rgba(0,0,0,0)',
        plot_bgcolor: 'rgba(0,0,0,0)',
        showlegend: false,
        xaxis: {showgrid: false, zeroline: false, showticklabels: false},
        yaxis: {showgrid: true, gridcolor: '#e2e8f0', showticklabels: false}
    };
    
    Plotly.newPlot('plotly-chart', [trace1], layout, {displayModeBar: false});
}