// Visualizador 3D de G-code usando Three.js
class GCodeViewer {
    constructor(containerId) {
        this.container = document.getElementById(containerId);
        this.scene = null;
        this.camera = null;
        this.renderer = null;
        this.controls = null;
        this.lines = [];
        this.currentLayer = 0;
        this.totalLayers = 0;
        
        this.init();
    }
    
    init() {
        // Cena
        this.scene = new THREE.Scene();
        this.scene.background = new THREE.Color(0x1a1a1a);
        
        // Câmera
        const width = this.container.clientWidth;
        const height = this.container.clientHeight;
        this.camera = new THREE.PerspectiveCamera(45, width / height, 0.1, 1000);
        this.camera.position.set(100, 100, 100);
        this.camera.lookAt(0, 0, 0);
        
        // Renderer
        this.renderer = new THREE.WebGLRenderer({ antialias: true });
        this.renderer.setSize(width, height);
        this.container.appendChild(this.renderer.domElement);
        
        // Controles de órbita
        this.controls = new THREE.OrbitControls(this.camera, this.renderer.domElement);
        this.controls.enableDamping = true;
        this.controls.dampingFactor = 0.05;
        
        // Grade de referência
        const gridHelper = new THREE.GridHelper(200, 20, 0x444444, 0x222222);
        this.scene.add(gridHelper);
        
        // Eixos XYZ
        const axesHelper = new THREE.AxesHelper(100);
        this.scene.add(axesHelper);
        
        // Iluminação
        const ambientLight = new THREE.AmbientLight(0xffffff, 0.6);
        this.scene.add(ambientLight);
        
        const directionalLight = new THREE.DirectionalLight(0xffffff, 0.4);
        directionalLight.position.set(10, 10, 10);
        this.scene.add(directionalLight);
        
        // Mesa de impressão (200x200mm)
        const bedGeometry = new THREE.PlaneGeometry(200, 200);
        const bedMaterial = new THREE.MeshBasicMaterial({ 
            color: 0x333333, 
            side: THREE.DoubleSide,
            transparent: true,
            opacity: 0.5
        });
        const bed = new THREE.Mesh(bedGeometry, bedMaterial);
        bed.rotation.x = -Math.PI / 2;
        this.scene.add(bed);
        
        // Animar
        this.animate();
        
        // Redimensionar
        window.addEventListener('resize', () => this.onWindowResize());
    }
    
    parseGCode(gcodeText) {
        const lines = gcodeText.split('\n');
        const points = [];
        let currentPosition = { x: 0, y: 0, z: 0, e: 0 };
        let isExtruding = false;
        let layerZ = 0;
        const layers = [];
        let currentLayerPoints = [];
        
        for (let line of lines) {
            // Remover comentários
            line = line.split(';')[0].trim();
            if (!line) continue;
            
            // Detectar mudança de camada
            const zMatch = line.match(/Z([\d.]+)/);
            if (zMatch) {
                const newZ = parseFloat(zMatch[1]);
                if (newZ > layerZ) {
                    if (currentLayerPoints.length > 0) {
                        layers.push([...currentLayerPoints]);
                        currentLayerPoints = [];
                    }
                    layerZ = newZ;
                }
            }
            
            // Comandos de movimento
            if (line.startsWith('G0') || line.startsWith('G1')) {
                const x = this.parseCoord(line, 'X', currentPosition.x);
                const y = this.parseCoord(line, 'Y', currentPosition.y);
                const z = this.parseCoord(line, 'Z', currentPosition.z);
                const e = this.parseCoord(line, 'E', currentPosition.e);
                
                // Verificar se está extrudando
                const wasExtruding = isExtruding;
                isExtruding = e > currentPosition.e;
                
                if (isExtruding && wasExtruding) {
                    // Adicionar linha de extrusão
                    currentLayerPoints.push({
                        start: { ...currentPosition },
                        end: { x, y, z }
                    });
                }
                
                currentPosition = { x, y, z, e };
            }
        }
        
        // Adicionar última camada
        if (currentLayerPoints.length > 0) {
            layers.push(currentLayerPoints);
        }
        
        this.totalLayers = layers.length;
        return layers;
    }
    
    parseCoord(line, axis, defaultValue) {
        const match = line.match(new RegExp(axis + '([\\d.-]+)'));
        return match ? parseFloat(match[1]) : defaultValue;
    }
    
    loadGCode(gcodeText) {
        // Limpar linhas anteriores
        this.clearLines();
        
        // Parsear G-code
        const layers = this.parseGCode(gcodeText);
        
        // Renderizar todas as camadas
        this.renderLayers(layers);
        
        // Centralizar câmera
        this.centerCamera();
    }
    
    renderLayers(layers, maxLayer = null) {
        const layersToRender = maxLayer !== null ? layers.slice(0, maxLayer + 1) : layers;
        
        layersToRender.forEach((layer, layerIndex) => {
            // Cor baseada na altura (gradiente do azul ao vermelho)
            const hue = (layerIndex / layers.length) * 0.6; // 0 (vermelho) a 0.6 (azul)
            const color = new THREE.Color().setHSL(0.6 - hue, 1, 0.5);
            
            const material = new THREE.LineBasicMaterial({ 
                color: color,
                linewidth: 2
            });
            
            layer.forEach(segment => {
                const geometry = new THREE.BufferGeometry().setFromPoints([
                    new THREE.Vector3(
                        segment.start.x - 100, 
                        segment.start.z, 
                        segment.start.y - 100
                    ),
                    new THREE.Vector3(
                        segment.end.x - 100, 
                        segment.end.z, 
                        segment.end.y - 100
                    )
                ]);
                
                const line = new THREE.Line(geometry, material);
                this.scene.add(line);
                this.lines.push(line);
            });
        });
    }
    
    clearLines() {
        this.lines.forEach(line => {
            this.scene.remove(line);
            line.geometry.dispose();
            line.material.dispose();
        });
        this.lines = [];
    }
    
    centerCamera() {
        this.camera.position.set(0, 150, 150);
        this.camera.lookAt(0, 50, 0);
        this.controls.target.set(0, 50, 0);
        this.controls.update();
    }
    
    animate() {
        requestAnimationFrame(() => this.animate());
        this.controls.update();
        this.renderer.render(this.scene, this.camera);
    }
    
    onWindowResize() {
        const width = this.container.clientWidth;
        const height = this.container.clientHeight;
        this.camera.aspect = width / height;
        this.camera.updateProjectionMatrix();
        this.renderer.setSize(width, height);
    }
}
