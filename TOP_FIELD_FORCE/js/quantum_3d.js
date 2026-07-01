/* ==========================================================================
   YEAR 50,000 AD - QUANTUM CORE 3D HOLOGRAPHIC ENGINE
   Powered by Three.js & WebGL
   Simulates Neural Field Force Entanglement & Depot Node Interconnections
   ========================================================================== */

let scene, camera, renderer, particles, globe, lines;
let animationFrameId;

function initQuantum3D() {
    const container = document.getElementById('quantum-3d-canvas');
    if (!container || !window.THREE) return;

    // 1. Scene Setup
    scene = new THREE.Scene();
    scene.fog = new THREE.FogExp2(0x02040a, 0.002);

    // 2. Camera Setup
    camera = new THREE.PerspectiveCamera(60, container.clientWidth / container.clientHeight, 0.1, 1000);
    camera.position.z = 250;

    // 3. Renderer Setup
    renderer = new THREE.WebGLRenderer({ alpha: true, antialias: true });
    renderer.setSize(container.clientWidth, container.clientHeight);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    container.innerHTML = '';
    container.appendChild(renderer.domElement);

    // 4. Create Quantum Core Globe (Inner Sphere)
    const globeGeometry = new THREE.SphereGeometry(70, 32, 32);
    const globeMaterial = new THREE.MeshBasicMaterial({
        color: 0x06b6d4,
        wireframe: true,
        transparent: true,
        opacity: 0.15
    });
    globe = new THREE.Mesh(globeGeometry, globeMaterial);
    scene.add(globe);

    // 5. Create Quantum Particle Cloud (Field Force Nodes)
    const particleCount = 600;
    const geometry = new THREE.BufferGeometry();
    const positions = new Float32Array(particleCount * 3);
    const colors = new Float32Array(particleCount * 3);

    const colorPalette = [
        new THREE.Color(0x6366f1), // Cyber Indigo
        new THREE.Color(0x06b6d4), // Neon Cyan
        new THREE.Color(0xa855f7), // Quantum Purple
        new THREE.Color(0x10b981)  // Bio Emerald
    ];

    for (let i = 0; i < particleCount * 3; i += 3) {
        // Spherical distribution around globe
        const u = Math.random();
        const v = Math.random();
        const theta = u * 2.0 * Math.PI;
        const phi = Math.acos(2.0 * v - 1.0);
        const r = 75 + Math.random() * 80;

        positions[i] = r * Math.sin(phi) * Math.cos(theta);
        positions[i + 1] = r * Math.sin(phi) * Math.sin(theta);
        positions[i + 2] = r * Math.cos(phi);

        const col = colorPalette[Math.floor(Math.random() * colorPalette.length)];
        colors[i] = col.r;
        colors[i + 1] = col.g;
        colors[i + 2] = col.b;
    }

    geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));
    geometry.setAttribute('color', new THREE.BufferAttribute(colors, 3));

    const particleMaterial = new THREE.PointsMaterial({
        size: 3.5,
        vertexColors: true,
        transparent: true,
        opacity: 0.85,
        blending: THREE.AdditiveBlending
    });

    particles = new THREE.Points(geometry, particleMaterial);
    scene.add(particles);

    // 6. Create Quantum Entanglement Beams (Dijkstra Interconnections)
    const lineMaterial = new THREE.LineBasicMaterial({
        color: 0x22d3ee,
        transparent: true,
        opacity: 0.2,
        blending: THREE.AdditiveBlending
    });

    const lineGeometry = new THREE.BufferGeometry();
    const linePositions = [];

    // Connect some nearby nodes to form neural graph
    for (let i = 0; i < particleCount; i += 4) {
        const x1 = positions[i * 3];
        const y1 = positions[i * 3 + 1];
        const z1 = positions[i * 3 + 2];

        // Connect to next particle
        const nextIdx = ((i + 3) % particleCount) * 3;
        const x2 = positions[nextIdx];
        const y2 = positions[nextIdx + 1];
        const z2 = positions[nextIdx + 2];

        linePositions.push(x1, y1, z1);
        linePositions.push(x2, y2, z2);
    }

    lineGeometry.setAttribute('position', new THREE.Float32BufferAttribute(linePositions, 3));
    lines = new THREE.LineSegments(lineGeometry, lineMaterial);
    scene.add(lines);

    // 7. Event Listeners
    window.addEventListener('resize', onWindowResize);
    document.addEventListener('mousemove', onMouseMove);

    animate();
}

let mouseX = 0;
let mouseY = 0;
let targetRotationX = 0;
let targetRotationY = 0;

function onMouseMove(event) {
    mouseX = (event.clientX - window.innerWidth / 2) * 0.001;
    mouseY = (event.clientY - window.innerHeight / 2) * 0.001;
}

function onWindowResize() {
    const container = document.getElementById('quantum-3d-canvas');
    if (!container || !camera || !renderer) return;
    camera.aspect = container.clientWidth / container.clientHeight;
    camera.updateProjectionMatrix();
    renderer.setSize(container.clientWidth, container.clientHeight);
}

function animate() {
    animationFrameId = requestAnimationFrame(animate);

    targetRotationX += (mouseX - targetRotationX) * 0.05;
    targetRotationY += (mouseY - targetRotationY) * 0.05;

    if (globe) {
        globe.rotation.y += 0.003;
        globe.rotation.x += 0.001;
    }

    if (particles) {
        particles.rotation.y -= 0.002;
        particles.rotation.x += targetRotationY * 0.5;
        particles.rotation.y += targetRotationX * 0.5;
    }

    if (lines) {
        lines.rotation.y -= 0.002;
        lines.rotation.x += targetRotationY * 0.5;
        lines.rotation.y += targetRotationX * 0.5;
    }

    if (renderer && scene && camera) {
        renderer.render(scene, camera);
    }
}

document.addEventListener('DOMContentLoaded', () => {
    setTimeout(initQuantum3D, 100);
});
