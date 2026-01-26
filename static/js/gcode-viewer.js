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
        this.parsedLayers = []; // Armazenar camadas parseadas
        
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
        const ambientLight = new THREE.AmbientLight(0xffffff, 0.8);
        this.scene.add(ambientLight);
        
        const directionalLight = new THREE.DirectionalLight(0xffffff, 0.8);
        directionalLight.position.set(10, 10, 10);
        this.scene.add(directionalLight);
        
        const directionalLight2 = new THREE.DirectionalLight(0xffffff, 0.4);
        directionalLight2.position.set(-10, -10, -10);
        this.scene.add(directionalLight2);
        
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
        let currentPosition = { x: 0, y: 0, z: 0, e: 0 };
        let currentZ = -1;
        const layers = [];
        let currentLayerPoints = [];
        
        console.log('🔍 Iniciando parse do G-code...');
        
        for (let line of lines) {
            // Remover comentários
            line = line.split(';')[0].trim();
            if (!line) continue;
            
            // Comandos de movimento
            if (line.startsWith('G0') || line.startsWith('G1')) {
                const x = this.parseCoord(line, 'X', currentPosition.x);
                const y = this.parseCoord(line, 'Y', currentPosition.y);
                const z = this.parseCoord(line, 'Z', currentPosition.z);
                const e = this.parseCoord(line, 'E', currentPosition.e);
                
                // Detectar mudança de camada (mudança em Z)
                if (z !== currentPosition.z && z > currentZ) {
                    if (currentLayerPoints.length > 0) {
                        layers.push([...currentLayerPoints]);
                        console.log(`  Camada ${layers.length}: Z=${currentZ.toFixed(2)}mm, ${currentLayerPoints.length} segmentos`);
                        currentLayerPoints = [];
                    }
                    currentZ = z;
                }
                
                // Adicionar QUALQUER movimento com extrusão (e > posição anterior)
                if (e > currentPosition.e) {
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
            console.log(`  Camada ${layers.length}: Z=${currentZ.toFixed(2)}mm, ${currentLayerPoints.length} segmentos`);
        }
        
        this.totalLayers = layers.length;
        console.log(`✅ Total: ${layers.length} camadas detectadas`);
        return layers;
    }
    
    parseCoord(line, axis, defaultValue) {
        const match = line.match(new RegExp(axis + '([\\d.-]+)'));
        return match ? parseFloat(match[1]) : defaultValue;
    }
    
    loadGCode(gcodeText) {
        console.log('📥 Carregando G-code... tamanho:', gcodeText.length, 'caracteres');
        
        // Limpar linhas anteriores
        this.clearLines();
        
        // Parsear G-code
        const layers = this.parseGCode(gcodeText);
        this.parsedLayers = layers; // Salvar para controle de camadas
        
        console.log('📊 Camadas encontradas:', layers.length);
        console.log('📐 Total de segmentos:', layers.reduce((sum, layer) => sum + layer.length, 0));
        
        if (layers.length === 0) {
            console.error('❌ Nenhuma camada encontrada no G-code!');
            alert('Erro: Nenhuma camada encontrada no G-code');
            return;
        }
        
        // Renderizar todas as camadas
        this.renderLayers(layers);
        
        console.log('✅ G-code renderizado com', this.lines.length, 'linhas');
        
        // Centralizar câmera
        this.centerCamera();
    }
    
    renderLayers(layers, maxLayer = null) {
        const layersToRender = maxLayer !== null ? layers.slice(0, maxLayer + 1) : layers;
        const lineWidth = 0.8; // Aumentar espessura para 0.8mm
        
        layersToRender.forEach((layer, layerIndex) => {
            // Cor baseada na altura (gradiente) - cores sólidas e vibrantes
            const hue = (layerIndex / layers.length) * 0.7;
            const color = new THREE.Color().setHSL(0.15 + hue, 1.0, 0.5);
            
            // Material com iluminação para parecer sólido - SEM CULLING
            const material = new THREE.MeshPhongMaterial({ 
                color: color,
                shininess: 30,
                specular: 0x333333,
                transparent: false,
                opacity: 1.0,
                flatShading: false,
                side: THREE.DoubleSide  // Renderizar ambos os lados
            });
            
            layer.forEach(segment => {
                const start = new THREE.Vector3(
                    segment.start.x - 100, 
                    segment.start.z, 
                    segment.start.y - 100
                );
                const end = new THREE.Vector3(
                    segment.end.x - 100, 
                    segment.end.z, 
                    segment.end.y - 100
                );
                
                // Criar tubo cilíndrico representando a linha de extrusão
                const direction = new THREE.Vector3().subVectors(end, start);
                const length = direction.length();
                
                if (length > 0.01) { // Evitar linhas muito pequenas
                    const geometry = new THREE.CylinderGeometry(
                        lineWidth / 2,  // raio topo
                        lineWidth / 2,  // raio base
                        length,         // altura
                        8,              // segmentos radiais (otimizado para performance)
                        1,              // segmentos de altura
                        false           // sem tampa
                    );
                    
                    const cylinder = new THREE.Mesh(geometry, material);
                    
                    // Posicionar e orientar o cilindro
                    cylinder.position.copy(start).add(direction.multiplyScalar(0.5));
                    cylinder.quaternion.setFromUnitVectors(
                        new THREE.Vector3(0, 1, 0),
                        direction.normalize()
                    );
                    
                    this.scene.add(cylinder);
                    this.lines.push(cylinder);
                }
            });
        });
    }
    
    clearLines() {
        this.lines.forEach(line => {
            this.scene.remove(line);
            if (line.geometry) line.geometry.dispose();
            if (line.material) line.material.dispose();
        });
        this.lines = [];
    }
    
    centerCamera() {
        // Posição otimizada para ver o objeto inteiro
        this.camera.position.set(80, 120, 80);
        this.camera.lookAt(0, 30, 0);
        this.controls.target.set(0, 30, 0);
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
