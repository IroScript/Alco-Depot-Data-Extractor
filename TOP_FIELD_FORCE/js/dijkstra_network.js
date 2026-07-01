/* ==========================================================================
   YEAR 50,000 AD - DIJKSTRA QUANTUM ROUTE OPTIMIZER
   Simulates shortest path quantum teleportation & supply chain routing
   across regional field force depot nodes.
   ========================================================================== */

const DEPOT_NODES = {
    "DHK": { name: "Dhaka Core (Prime Depot)", x: 250, y: 150, connections: { "CTG": 180, "RAJ": 210, "KHL": 160, "MYM": 110 } },
    "CTG": { name: "Chittagong Nexus", x: 420, y: 280, connections: { "DHK": 180, "SYL": 220, "COM": 90 } },
    "RAJ": { name: "Rajshahi Bio-Hub", x: 100, y: 100, connections: { "DHK": 210, "RNG": 130, "KHL": 170 } },
    "KHL": { name: "Khulna Quantum Grid", x: 150, y: 260, connections: { "DHK": 160, "RAJ": 170, "BAR": 80 } },
    "BAR": { name: "Barishal Coastal Station", x: 220, y: 310, connections: { "KHL": 80, "DHK": 150, "CTG": 170 } },
    "SYL": { name: "Sylhet Highland Vector", x: 380, y: 80, connections: { "DHK": 190, "CTG": 220, "MYM": 130 } },
    "COM": { name: "Comilla Relay", x: 330, y: 220, connections: { "DHK": 100, "CTG": 90, "SYL": 150 } },
    "MYM": { name: "Mymensingh Station", x: 260, y: 70, connections: { "DHK": 110, "SYL": 130, "RNG": 160 } },
    "RNG": { name: "Rangpur Northern Terminal", x: 90, y: 30, connections: { "RAJ": 130, "MYM": 160 } }
};

let activePath = [];

/* Dijkstra's Shortest Path Algorithm Implementation */
function runDijkstra(startNode, endNode) {
    const distances = {};
    const previous = {};
    const unvisited = new Set(Object.keys(DEPOT_NODES));

    unvisited.forEach(node => {
        distances[node] = Infinity;
        previous[node] = null;
    });
    distances[startNode] = 0;

    while (unvisited.size > 0) {
        // Find node with minimum distance in unvisited set
        let current = null;
        let minDist = Infinity;
        unvisited.forEach(node => {
            if (distances[node] < minDist) {
                minDist = distances[node];
                current = node;
            }
        });

        if (current === null || current === endNode) break;
        unvisited.delete(current);

        const neighbors = DEPOT_NODES[current].connections;
        for (const [neighbor, weight] of Object.entries(neighbors)) {
            if (!unvisited.has(neighbor)) continue;
            const altDist = distances[current] + weight;
            if (altDist < distances[neighbor]) {
                distances[neighbor] = altDist;
                previous[neighbor] = current;
            }
        }
    }

    // Reconstruct path
    const path = [];
    let curr = endNode;
    if (previous[curr] !== null || curr === startNode) {
        while (curr !== null) {
            path.unshift(curr);
            curr = previous[curr];
        }
    }
    return { path, distance: distances[endNode] };
}

/* Render Dijkstra Interactive Visualizer */
function initDijkstraVisualizer() {
    const canvas = document.getElementById('dijkstra-canvas');
    if (!canvas) return;
    const ctx = canvas.getContext('2d');

    // Populate dropdowns
    const startSelect = document.getElementById('dijkstra-start');
    const endSelect = document.getElementById('dijkstra-end');
    const btnRun = document.getElementById('btn-run-dijkstra');

    if (startSelect && endSelect) {
        startSelect.innerHTML = '';
        endSelect.innerHTML = '';
        Object.entries(DEPOT_NODES).forEach(([code, data]) => {
            startSelect.innerHTML += `<option value="${code}">${code} - ${data.name}</option>`;
            endSelect.innerHTML += `<option value="${code}" ${code==='CTG'?'selected':''}>${code} - ${data.name}</option>`;
        });
    }

    if (btnRun) {
        btnRun.addEventListener('click', () => {
            const s = startSelect.value;
            const e = endSelect.value;
            if (s === e) {
                alert("Start and End nodes must be different in Quantum Entanglement!");
                return;
            }
            const res = runDijkstra(s, e);
            activePath = res.path;
            const statusEl = document.getElementById('dijkstra-status');
            if (statusEl) {
                statusEl.innerHTML = `
                    <span class="text-cyan-400 font-bold">⚡ QUANTUM TELEPORTATION ROUTE FOUND:</span> 
                    <span class="text-purple-300 font-mono">[ ${res.path.join(" ➔ ")} ]</span> 
                    <span class="text-emerald-400 ml-2">Total Impedance: ${res.distance} Light-ms</span>
                `;
            }
            drawNetwork(ctx, canvas);
            animatePulse(ctx, canvas, res.path);
        });
    }

    // Initial draw
    setTimeout(() => drawNetwork(ctx, canvas), 200);
}

function drawNetwork(ctx, canvas) {
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    // Draw all connection lines
    ctx.lineWidth = 1.5;
    ctx.strokeStyle = "rgba(99, 102, 241, 0.25)";
    Object.entries(DEPOT_NODES).forEach(([code, node]) => {
        Object.entries(node.connections).forEach(([targetCode, weight]) => {
            const target = DEPOT_NODES[targetCode];
            if (target) {
                ctx.beginPath();
                ctx.moveTo(node.x, node.y);
                ctx.lineTo(target.x, target.y);
                ctx.stroke();

                // Draw weight text
                const midX = (node.x + target.x) / 2;
                const midY = (node.y + target.y) / 2;
                ctx.fillStyle = "rgba(148, 163, 184, 0.5)";
                ctx.font = "10px monospace";
                ctx.fillText(`${weight}ms`, midX + 4, midY - 4);
            }
        });
    });

    // Draw highlighted active path
    if (activePath.length > 1) {
        ctx.lineWidth = 4;
        ctx.strokeStyle = "#06b6d4";
        ctx.shadowColor = "#06b6d4";
        ctx.shadowBlur = 15;
        ctx.beginPath();
        for (let i = 0; i < activePath.length - 1; i++) {
            const n1 = DEPOT_NODES[activePath[i]];
            const n2 = DEPOT_NODES[activePath[i+1]];
            ctx.moveTo(n1.x, n1.y);
            ctx.lineTo(n2.x, n2.y);
        }
        ctx.stroke();
        ctx.shadowBlur = 0;
    }

    // Draw depot nodes
    Object.entries(DEPOT_NODES).forEach(([code, node]) => {
        const isPathNode = activePath.includes(code);
        const isStart = activePath[0] === code;
        const isEnd = activePath[activePath.length - 1] === code;

        ctx.beginPath();
        ctx.arc(node.x, node.y, isPathNode ? 10 : 7, 0, Math.PI * 2);
        
        if (isStart) {
            ctx.fillStyle = "#10b981"; // Emerald Start
            ctx.shadowColor = "#10b981";
        } else if (isEnd) {
            ctx.fillStyle = "#f59e0b"; // Amber End
            ctx.shadowColor = "#f59e0b";
        } else if (isPathNode) {
            ctx.fillStyle = "#06b6d4"; // Cyan Relay
            ctx.shadowColor = "#06b6d4";
        } else {
            ctx.fillStyle = "#6366f1"; // Indigo Default
            ctx.shadowColor = "transparent";
        }
        ctx.shadowBlur = isPathNode ? 20 : 0;
        ctx.fill();
        ctx.shadowBlur = 0;

        // Node Code text
        ctx.fillStyle = isPathNode ? "#ffffff" : "#cbd5e1";
        ctx.font = isPathNode ? "bold 12px Orbitron, monospace" : "11px monospace";
        ctx.fillText(code, node.x - 12, node.y - 14);
    });
}

function animatePulse(ctx, canvas, path) {
    if (!path || path.length < 2) return;
    let step = 0;
    const totalSteps = 40;
    
    const interval = setInterval(() => {
        drawNetwork(ctx, canvas);
        
        // Calculate photon position along path
        const segmentFloat = (step / totalSteps) * (path.length - 1);
        const segIdx = Math.floor(segmentFloat);
        const t = segmentFloat - segIdx;
        
        if (segIdx < path.length - 1) {
            const n1 = DEPOT_NODES[path[segIdx]];
            const n2 = DEPOT_NODES[path[segIdx + 1]];
            const px = n1.x + (n2.x - n1.x) * t;
            const py = n1.y + (n2.y - n1.y) * t;
            
            ctx.beginPath();
            ctx.arc(px, py, 6, 0, Math.PI * 2);
            ctx.fillStyle = "#ffffff";
            ctx.shadowColor = "#a855f7";
            ctx.shadowBlur = 25;
            ctx.fill();
            ctx.shadowBlur = 0;
        }
        
        step++;
        if (step > totalSteps) clearInterval(interval);
    }, 25);
}

document.addEventListener('DOMContentLoaded', () => {
    setTimeout(initDijkstraVisualizer, 300);
});
