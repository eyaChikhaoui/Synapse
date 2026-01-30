// File: src/Backend/static/script.js

// Global Instances
let glViewers = {}; // Store multiple viewer instances by mode
let chapterCount = 0; // Tracks report chapters

// 1. Initialize on Load
document.addEventListener('DOMContentLoaded', function() {
    console.log("🚀 Synapse Frontend Initialized");
    initRealTimeSimulator();
    // Default state if not set
    if (!window.currentMode) window.currentMode = 'dna'; 
});

// 2. THE MAIN EVENT LISTENER (Handles Rendering & Report Accumulation)
document.body.addEventListener('htmx:afterSettle', async function(evt) {
    
    // Determine which workspace is active (dna, protein, batch, variant)
    const mode = window.currentMode || 'dna'; 
    
    // --- A. RENDER INTERACTIVE VIEW (Targeted by Mode) ---
    
    // 1. 3D Structure Logic
    const hiddenPdb = document.getElementById('hidden-pdb-data');
    // Select the specific viewer for the current mode
    const viewerElement = document.getElementById(`workspace-${mode}-3d`);
    let has3D = false;

    if (viewerElement && hiddenPdb && hiddenPdb.value.trim() !== "") {
         console.log(`🧬 Synapse: Rendering 3D Structure for [${mode}]...`);
         update3DViewer(viewerElement, hiddenPdb.value, mode);
         has3D = true;
    }

    // 2. 2D Chart Logic
    const hiddenViz = document.getElementById('hidden-viz-data');
    // Select the specific chart container for the current mode
    const chartElement = document.getElementById(`workspace-${mode}-2d`);
    let has2D = false;

    if (chartElement && hiddenViz && hiddenViz.value.trim() !== "") {
        try {
            const vizData = JSON.parse(hiddenViz.value);
            console.log(`📊 Synapse: Rendering 2D Chart for [${mode}]...`);
            renderPlotlyChart(chartElement, vizData);
            has2D = true;
        } catch (e) {
            console.error("Plotly JSON Error:", e);
        }
    }

    // --- B. ACCUMULATE TO REPORT (The "Historian") ---
    // Wait 800ms for canvases to fully render before taking snapshots
    setTimeout(async () => {
        // Scrape the ACTIVE workspace content
        const resultsWrapper = document.getElementById(`workspace-${mode}-content`);
        
        // Validation: Check if we have valid results (Result Card or Table)
        // We look for specific classes that appear in your result_card.html or batch table
        const hasResultCard = resultsWrapper && resultsWrapper.querySelector('.text-2xl'); // Score
        const hasBatchTable = resultsWrapper && resultsWrapper.querySelector('table');     // Batch
        
        if (hasResultCard || hasBatchTable) {
            await appendToReport(resultsWrapper, has3D, has2D, mode);
        }
    }, 800);
});

// --- REPORT ACCUMULATION LOGIC ---
async function appendToReport(sourceNode, capture3D, capture2D, mode) {
    chapterCount++;
    
    // 1. SCIENTIFIC NAMING ENGINE
    let chapterTitle = "Analysis Report";
    let chapterSubtitle = "General Output";
    let modeCode = "GEN-001"; 

    if (mode === 'variant') {
        chapterTitle = "In Silico Mutagenesis Assessment";
        modeCode = "VAR-SEQ";
        const score = sourceNode.querySelector('.text-2xl')?.innerText || "0%";
        const impact = sourceNode.querySelector('.text-xs.font-semibold')?.innerText || "Unknown";
        chapterSubtitle = `Wild Type vs Mutant | Similarity: ${score} (${impact})`;
    
    } else if (mode === 'batch') {
        chapterTitle = "High-Throughput Cohort Screening";
        modeCode = "BTC-HTS";
        const rowCount = sourceNode.querySelectorAll('tbody tr').length;
        chapterSubtitle = `Batch Size: ${rowCount} Sequences | Modality: Multi-Vector Inference`;
    
    } else if (mode === 'dna') {
        chapterTitle = "Nucleotide-to-Protein Translation";
        modeCode = "NUC-PROT";
        const targetName = sourceNode.querySelector('h3')?.innerText || "Target Unknown";
        chapterSubtitle = `Query: DNA Sequence > Predicted Phenotype: ${targetName}`;
        
    } else if (mode === 'protein') {
        chapterTitle = "Proteomic Reverse-Translation";
        modeCode = "PROT-GEN";
        const targetName = sourceNode.querySelector('h3')?.innerText || "Target Unknown";
        chapterSubtitle = `Query: Amino Acid Sequence > Predicted Gene: ${targetName}`;
    }

    console.log(`📝 Archiving Chapter ${chapterCount}: ${chapterTitle}`);

    // 2. CAPTURE SNAPSHOTS (High-Res)
    let img3D = "";
    if (capture3D && glViewers[mode]) {
        img3D = glViewers[mode].pngURI();
    }
    
    let img2D = "";
    if (capture2D) {
        const chartEl = document.getElementById(`workspace-${mode}-2d`);
        try {
            img2D = await Plotly.toImage(chartEl, {format: 'png', width: 1000, height: 500});
        } catch(e) { console.warn("Snapshot failed", e); }
    }

    // 3. CLONE CONTENT USING TEMPLATE
    const template = document.getElementById('chapter-template');
    const clone = template.content.cloneNode(true);

    // Fill Text
    clone.querySelector('.t-chapter-num').innerText = chapterCount.toString().padStart(2, '0');
    clone.querySelector('.t-title').innerText = chapterTitle;
    clone.querySelector('.t-subtitle').innerText = chapterSubtitle;
    clone.querySelector('.t-content').innerHTML = sourceNode.innerHTML; // <--- COPIES TABLE/CARD EXACTLY

    // Fill Images
    if (img3D) {
        const box = clone.querySelector('.t-viz-3d-box');
        box.classList.remove('hidden');
        box.querySelector('.t-chapter-num-a').innerText = chapterCount;
        box.querySelector('.t-img-3d').src = img3D;
    }
    if (img2D) {
        const box = clone.querySelector('.t-viz-2d-box');
        box.classList.remove('hidden');
        box.querySelector('.t-chapter-num-b').innerText = chapterCount;
        box.querySelector('.t-img-2d').src = img2D;
    }

    // 4. APPEND TO REPORT BUFFER
    document.getElementById('report-chapters').appendChild(clone);

    // 5. UPDATE TOC
    const tocContainer = document.getElementById('report-toc');
    if (chapterCount === 1 && tocContainer.innerText.includes("Analysis Log is empty")) {
        tocContainer.innerHTML = "";
    }
    const tocEntry = `
        <div class="toc-entry">
            <span class="toc-chapter-name">Chapter ${chapterCount}: ${chapterTitle}</span>
            <div class="toc-dots"></div>
            <span class="toc-page-ref">${modeCode}</span>
        </div>
    `;
    tocContainer.insertAdjacentHTML('beforeend', tocEntry);

    // 6. USER FEEDBACK
    const btn = document.querySelector('button[onclick="generatePDF()"]');
    if (btn) {
        const originalText = btn.innerHTML;
        btn.innerHTML = `<i class="fa-solid fa-check"></i> SAVED TO REPORT`;
        btn.classList.add("bg-green-600", "text-white");
        btn.classList.remove("bg-slate-800");
        
        setTimeout(() => { 
            btn.innerHTML = originalText; 
            btn.classList.add("bg-slate-800");
            btn.classList.remove("bg-green-600");
        }, 2500);
    }
}

// --- STANDARD VIEWER LOGIC (Updated for Multi-Instance) ---
function update3DViewer(element, pdbData, mode) {
    let config = { backgroundColor: '#F9FAFB', antialias: true };
    element.innerHTML = "";
    // Store viewer instance in global object keyed by mode
    glViewers[mode] = $3Dmol.createViewer(element, config);
    
    const v = glViewers[mode];
    v.clear();
    v.addModel(pdbData, "pdb");
    v.setStyle({}, {cartoon: {color: 'spectrum'}});
    v.zoomTo();
    v.render();
    v.spin('y', 0.5);
}

function renderPlotlyChart(element, points) {
    const trace = {
        x: points.map(p => p.x),
        y: points.map(p => p.y),
        text: points.map(p => p.label),
        mode: 'markers+text',
        type: 'scatter',
        textposition: 'top center',
        marker: {
            size: points.map(p => p.size),
            color: points.map(p => p.color),
            opacity: 0.8,
            line: { width: 1, color: 'white' }
        },
        hoverinfo: 'text'
    };
    const layout = {
        title: { text: 'Shared Latent Space Projection', font: { size: 12, color: '#64748b' } },
        margin: { t: 30, b: 30, l: 30, r: 30 },
        paper_bgcolor: 'rgba(0,0,0,0)',
        plot_bgcolor: 'rgba(0,0,0,0)',
        xaxis: { showgrid: true, zeroline: true, showticklabels: false, gridcolor: '#e2e8f0' },
        yaxis: { showgrid: true, zeroline: true, showticklabels: false, gridcolor: '#e2e8f0' },
        showlegend: false,
        dragmode: false
    };
    const config = { responsive: true, displayModeBar: false };
    Plotly.newPlot(element, [trace], layout, config);
}

// --- REAL-TIME SIMULATOR ---
function initRealTimeSimulator() {
    const wildInput = document.querySelector('input[name="wild_type"]');
    const mutantInput = document.querySelector('input[name="mutant"]');
    // Ensure we select the form inside the variant container
    const compareForm = document.querySelector('#variant-analysis-container form');

    if (wildInput && mutantInput && compareForm) {
        console.log("⚡ Real-Time Mutation Simulator: Active");
        const triggerAnalysis = debounce(() => {
            const w = wildInput.value.trim();
            const m = mutantInput.value.trim();
            if (w.length > 3 && m.length > 3) {
                 console.log("⚡ Triggering Zero-Shot Scoring...");
                htmx.trigger(compareForm, 'submit');
            }
        }, 800);
        wildInput.addEventListener('input', triggerAnalysis);
        mutantInput.addEventListener('input', triggerAnalysis);
    }
}

// --- UTILITIES ---
function debounce(func, wait) {
    let timeout;
    return function(...args) {
        clearTimeout(timeout);
        timeout = setTimeout(() => func.apply(this, args), wait);
    };
}

// --- UX LOCKING ---
document.body.addEventListener('htmx:beforeRequest', function(evt) {
    // Generic locker for any submit button in the active form
    const btn = evt.target.querySelector('button[type="submit"]');
    if(btn) {
        const icon = btn.querySelector('i');
        // Save original icon class to restore later
        if(icon) {
            btn.dataset.originalIcon = icon.className;
            icon.className = "fa-solid fa-spinner fa-spin";
        }
    }
});

document.body.addEventListener('htmx:afterRequest', function(evt) {
    const btn = evt.target.querySelector('button[type="submit"]');
    if(btn) {
        const icon = btn.querySelector('i');
        if(icon && btn.dataset.originalIcon) {
            icon.className = btn.dataset.originalIcon; // Restore original icon
        }
    }
});