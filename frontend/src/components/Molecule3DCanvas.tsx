import React, { useEffect, useMemo, useRef, useState } from 'react';
import * as THREE from 'three';
import { TrackballControls } from 'three/examples/jsm/controls/TrackballControls.js';
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js';
import {
  Camera,
  Compass,
  Eye,
  EyeOff,
  GripHorizontal,
  Layers,
  Maximize2,
  Minimize2,
  RotateCw,
  Ruler,
  Tag,
} from 'lucide-react';
import type {
  Atom3D,
  BondLink,
  BondOrderEntry,
  ChargeEntry,
  CriticalPoint,
  DualIsosurfaceResult,
  IsosurfaceMesh,
} from '../types/quantum';
import { Tooltip } from './Tooltip';

interface Molecule3DCanvasProps {
  atoms: Atom3D[];
  bonds: BondLink[];
  charges?: ChargeEntry[];
  bondOrders?: BondOrderEntry[];
  isosurface?: DualIsosurfaceResult | null;
  criticalPoints?: CriticalPoint[];
  isoOpacity?: number;
  onIsoOpacityChange?: (v: number) => void;
  title?: string;
  heightClass?: string;
  defaultHeight?: number;
  resizable?: boolean;
}

type RenderStyle = 'ball-stick' | 'spacefill' | 'wireframe';

function chargeToHexColor(q: number): number {
  // Negative -> warm red/amber, Neutral -> slate-white, Positive -> sky/indigo blue
  const clamped = Math.max(-1.0, Math.min(1.0, q));
  const c = new THREE.Color();
  if (clamped < 0) {
    const t = Math.abs(clamped);
    c.setRGB(0.92, 0.92 - 0.62 * t, 0.94 - 0.68 * t);
  } else {
    const t = clamped;
    c.setRGB(0.92 - 0.68 * t, 0.92 - 0.36 * t, 0.95);
  }
  return c.getHex();
}

function buildMeshGeometry(mesh: IsosurfaceMesh): THREE.BufferGeometry {
  const geom = new THREE.BufferGeometry();
  geom.setAttribute(
    'position',
    new THREE.Float32BufferAttribute(mesh.positions, 3)
  );
  if (mesh.normals.length === mesh.positions.length) {
    geom.setAttribute(
      'normal',
      new THREE.Float32BufferAttribute(mesh.normals, 3)
    );
  }
  // Vertex color binding for mapped isosurfaces (e.g. sign(lambda2)*rho or ESP)
  if (mesh.colors && mesh.colors.length === mesh.positions.length) {
    geom.setAttribute(
      'color',
      new THREE.Float32BufferAttribute(mesh.colors, 3)
    );
  }
  geom.setIndex(mesh.indices);
  if (mesh.normals.length !== mesh.positions.length) {
    geom.computeVertexNormals();
  }
  return geom;
}

export const Molecule3DCanvas: React.FC<Molecule3DCanvasProps> = ({
  atoms,
  bonds,
  charges,
  bondOrders,
  isosurface,
  criticalPoints,
  isoOpacity = 0.62,
  onIsoOpacityChange,
  title = '3D 量子分子视口',
  heightClass = 'h-[500px]',
  defaultHeight,
  resizable = true,
}) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const rendererRef = useRef<THREE.WebGLRenderer | null>(null);
  const cameraRef = useRef<THREE.PerspectiveCamera | null>(null);
  const controlsRef = useRef<any>(null);
  const sceneRef = useRef<THREE.Scene | null>(null);
  const atomMeshesRef = useRef<THREE.Mesh[]>([]);
  const centerOffsetRef = useRef<THREE.Vector3>(new THREE.Vector3());

  // Dynamic Viewport Height & Fullscreen Maximize state
  const initialHeight = useMemo(() => {
    if (defaultHeight) return defaultHeight;
    const match = heightClass.match(/h-\[(\d+)px\]/);
    return match ? parseInt(match[1], 10) : 480;
  }, [defaultHeight, heightClass]);

  const [viewportHeight, setViewportHeight] = useState<number>(initialHeight);
  const [isMaximized, setIsMaximized] = useState(false);
  const [isDraggingHeight, setIsDraggingHeight] = useState(false);
  const dragStartYRef = useRef(0);
  const dragStartHeightRef = useRef(0);

  // Rotation control mode: trackball (unconstrained 360° tumbling with no polar lock) vs orbit
  const [controlMode, setControlMode] = useState<'trackball' | 'orbit'>('trackball');

  const [style, setStyle] = useState<RenderStyle>('ball-stick');
  const [autoRotate, setAutoRotate] = useState(false);
  const [showLabels, setShowLabels] = useState(true);
  const [colorByCharge, setColorByCharge] = useState(false);
  const [showIso, setShowIso] = useState(true);
  const [isoWireframe, setIsoWireframe] = useState(false);
  const [selectedIndices, setSelectedIndices] = useState<number[]>([]);
  const [labelOverlays, setLabelOverlays] = useState<
    { index: number; text: string; x: number; y: number; visible: boolean }[]
  >([]);

  // Keyboard shortcut listener: F to toggle Fullscreen, Escape to exit
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.target instanceof HTMLInputElement || e.target instanceof HTMLTextAreaElement) return;
      if (e.key === 'f' || e.key === 'F') {
        setIsMaximized((v) => !v);
      } else if (e.key === 'Escape' && isMaximized) {
        setIsMaximized(false);
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isMaximized]);

  const startDragHeight = (e: React.MouseEvent) => {
    e.preventDefault();
    setIsDraggingHeight(true);
    dragStartYRef.current = e.clientY;
    dragStartHeightRef.current = viewportHeight;

    const onMouseMove = (ev: MouseEvent) => {
      const delta = ev.clientY - dragStartYRef.current;
      const nextH = Math.max(260, Math.min(1200, dragStartHeightRef.current + delta));
      setViewportHeight(nextH);
    };

    const onMouseUp = () => {
      setIsDraggingHeight(false);
      window.removeEventListener('mousemove', onMouseMove);
      window.removeEventListener('mouseup', onMouseUp);
    };

    window.addEventListener('mousemove', onMouseMove);
    window.addEventListener('mouseup', onMouseUp);
  };

  const setCameraPreset = (view: 'side' | 'top' | 'front' | 'fit') => {
    const cam = cameraRef.current;
    const ctrl = controlsRef.current;
    if (!cam || !ctrl) return;
    const center = centerOffsetRef.current;
    let maxR = 2.0;
    for (const a of atoms) {
      const d = Math.hypot(a.x - center.x, a.y - center.y, a.z - center.z);
      if (d > maxR) maxR = d;
    }
    const dist = maxR * (isosurface ? 2.6 : 2.1);
    ctrl.target.set(0, 0, 0);

    if (view === 'side') {
      // 90° Side View along X-axis: ideal for observing π-π stacking layer separation
      cam.position.set(dist * 1.5, 0, 0);
      cam.up.set(0, 0, 1);
    } else if (view === 'top') {
      // Top View along Y-axis
      cam.position.set(0, dist * 1.5, 0);
      cam.up.set(0, 0, -1);
    } else if (view === 'front') {
      // Front View along Z-axis
      cam.position.set(0, 0, dist * 1.5);
      cam.up.set(0, 1, 0);
    } else {
      // Reset Isometric
      cam.position.set(dist * 1.15, dist * 0.85, dist * 1.35);
      cam.up.set(0, 1, 0);
    }
    cam.lookAt(0, 0, 0);
    ctrl.update();
  };

  const chargeMap = useMemo(() => {
    const m = new Map<number, number>();
    if (charges) {
      for (const c of charges) m.set(c.index, c.charge);
    }
    return m;
  }, [charges]);

  const bondOrderMap = useMemo(() => {
    const m = new Map<string, number>();
    if (bondOrders) {
      for (const b of bondOrders) {
        const key =
          b.atom1_index < b.atom2_index
            ? `${b.atom1_index}-${b.atom2_index}`
            : `${b.atom2_index}-${b.atom1_index}`;
        m.set(key, b.bond_order);
      }
    }
    return m;
  }, [bondOrders]);

  useEffect(() => {
    if (charges && charges.length > 0) {
      setColorByCharge(true);
    }
  }, [charges]);

  useEffect(() => {
    setSelectedIndices((prev) => prev.filter((idx) => atoms.some((a) => a.index === idx)));
  }, [atoms]);

  const measurementText = useMemo(() => {
    if (selectedIndices.length === 0) return '点击原子可测距/测键角';
    const picked = selectedIndices
      .map((id) => atoms.find((a) => a.index === id))
      .filter((x): x is Atom3D => !!x);
    if (picked.length === 1) {
      const a = picked[0];
      const q = chargeMap.get(a.index);
      return `已选 ${a.symbol}${a.index} (${a.x.toFixed(3)}, ${a.y.toFixed(3)}, ${a.z.toFixed(3)} Å)${
        q !== undefined ? ` · q=${q.toFixed(4)}` : ''
      }`;
    }
    if (picked.length === 2) {
      const [a, b] = picked;
      const dist = Math.hypot(a.x - b.x, a.y - b.y, a.z - b.z);
      return `距离 ${a.symbol}${a.index}—${b.symbol}${b.index} = ${dist.toFixed(4)} Å`;
    }
    const [a, b, c] = picked;
    const v1 = new THREE.Vector3(a.x - b.x, a.y - b.y, a.z - b.z);
    const v2 = new THREE.Vector3(c.x - b.x, c.y - b.y, c.z - b.z);
    const angle = THREE.MathUtils.radToDeg(v1.angleTo(v2));
    return `键角 ∠(${a.symbol}${a.index}-${b.symbol}${b.index}-${c.symbol}${c.index}) = ${angle.toFixed(2)}°`;
  }, [selectedIndices, atoms, chargeMap]);

  // Setup Three.js scene once
  useEffect(() => {
    const el = containerRef.current;
    if (!el) return;

    const scene = new THREE.Scene();
    scene.background = new THREE.Color('#070b12');
    sceneRef.current = scene;

    const width = Math.max(el.clientWidth, 320);
    const height = Math.max(el.clientHeight, 260);
    const camera = new THREE.PerspectiveCamera(42, width / height, 0.05, 500);
    camera.position.set(0, 0, 10);
    cameraRef.current = camera;

    let renderer: THREE.WebGLRenderer;
    try {
      renderer = new THREE.WebGLRenderer({
        antialias: true,
        preserveDrawingBuffer: true,
        alpha: false,
      });
    } catch {
      return;
    }
    renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
    renderer.setSize(width, height);
    renderer.toneMapping = THREE.ACESFilmicToneMapping;
    renderer.toneMappingExposure = 1.15;
    el.innerHTML = '';
    el.appendChild(renderer.domElement);
    rendererRef.current = renderer;

    const initControls = (mode: 'trackball' | 'orbit') => {
      if (controlsRef.current) {
        controlsRef.current.dispose();
        controlsRef.current = null;
      }
      if (mode === 'trackball') {
        const tb = new TrackballControls(camera, renderer.domElement);
        tb.rotateSpeed = 2.4;
        tb.zoomSpeed = 1.2;
        tb.panSpeed = 0.8;
        tb.noZoom = false;
        tb.noPan = false;
        tb.staticMoving = false;
        tb.dynamicDampingFactor = 0.16;
        controlsRef.current = tb;
      } else {
        const ob = new OrbitControls(camera, renderer.domElement);
        ob.enableDamping = true;
        ob.dampingFactor = 0.08;
        ob.rotateSpeed = 0.78;
        ob.zoomSpeed = 0.95;
        controlsRef.current = ob;
      }
    };
    initControls(controlMode);

    // Studio three-point lighting
    const ambient = new THREE.AmbientLight(0xdbeafe, 0.75);
    scene.add(ambient);

    const keyLight = new THREE.DirectionalLight(0xffffff, 1.35);
    keyLight.position.set(8, 12, 14);
    scene.add(keyLight);

    const rimLight = new THREE.DirectionalLight(0x38bdf8, 0.65);
    rimLight.position.set(-10, -8, -10);
    scene.add(rimLight);

    const fillLight = new THREE.DirectionalLight(0xa78bfa, 0.35);
    fillLight.position.set(0, -10, 6);
    scene.add(fillLight);

    const ro = new ResizeObserver(() => {
      if (!containerRef.current || !rendererRef.current || !cameraRef.current) return;
      const w = Math.max(containerRef.current.clientWidth, 200);
      const h = Math.max(containerRef.current.clientHeight, 200);
      cameraRef.current.aspect = w / h;
      cameraRef.current.updateProjectionMatrix();
      rendererRef.current.setSize(w, h);
      controlsRef.current?.handleResize?.();
    });
    ro.observe(el);

    let rafId = 0;
    const animate = () => {
      rafId = requestAnimationFrame(animate);
      if (autoRotate && camera) {
        camera.position.applyAxisAngle(new THREE.Vector3(0, 1, 0), 0.012);
        camera.lookAt(0, 0, 0);
      }
      controlsRef.current?.update();
      renderer.render(scene, camera);
    };
    animate();

    return () => {
      cancelAnimationFrame(rafId);
      ro.disconnect();
      controlsRef.current?.dispose();
      renderer.dispose();
      rendererRef.current = null;
      sceneRef.current = null;
      controlsRef.current = null;
    };
  }, []);

  // Switch between Trackball (free unconstrained 3D tumbling) and OrbitControls
  useEffect(() => {
    const cam = cameraRef.current;
    const ren = rendererRef.current;
    if (!cam || !ren) return;
    if (controlsRef.current) {
      controlsRef.current.dispose();
      controlsRef.current = null;
    }
    if (controlMode === 'trackball') {
      const tb = new TrackballControls(cam, ren.domElement);
      tb.rotateSpeed = 2.4;
      tb.zoomSpeed = 1.2;
      tb.panSpeed = 0.8;
      tb.noZoom = false;
      tb.noPan = false;
      tb.staticMoving = false;
      tb.dynamicDampingFactor = 0.16;
      controlsRef.current = tb;
    } else {
      const ob = new OrbitControls(cam, ren.domElement);
      ob.enableDamping = true;
      ob.dampingFactor = 0.08;
      ob.rotateSpeed = 0.78;
      ob.zoomSpeed = 0.95;
      controlsRef.current = ob;
    }
  }, [controlMode]);

  // Populate / update geometry when molecule, style, charges, or isosurface changes
  useEffect(() => {
    const scene = sceneRef.current;
    const camera = cameraRef.current;
    const controls = controlsRef.current;
    if (!scene || !camera || !controls) return;

    // Remove previous dynamic group
    const prevGroup = scene.getObjectByName('wavecraft-mol-group');
    if (prevGroup) {
      prevGroup.traverse((obj) => {
        if ((obj as THREE.Mesh).geometry) (obj as THREE.Mesh).geometry.dispose();
        const mat = (obj as THREE.Mesh).material;
        if (Array.isArray(mat)) mat.forEach((m) => m.dispose());
        else if (mat) mat.dispose();
      });
      scene.remove(prevGroup);
    }

    const group = new THREE.Group();
    group.name = 'wavecraft-mol-group';
    atomMeshesRef.current = [];

    // Compute molecule centroid
    const center = new THREE.Vector3();
    if (atoms.length > 0) {
      for (const a of atoms) {
        center.x += a.x;
        center.y += a.y;
        center.z += a.z;
      }
      center.divideScalar(atoms.length);
    }
    centerOffsetRef.current.copy(center);

    const sphereGeo = new THREE.SphereGeometry(1, 32, 24);
    const cylGeo = new THREE.CylinderGeometry(1, 1, 1, 18);

    // Atoms
    for (const atom of atoms) {
      let radius = Math.max(0.22, atom.covalent_radius * 0.42);
      if (style === 'spacefill') radius = atom.vdw_radius * 0.72;
      if (style === 'wireframe') radius = 0.09;

      const q = chargeMap.get(atom.index);
      const colorHex =
        colorByCharge && q !== undefined
          ? chargeToHexColor(q)
          : new THREE.Color(atom.color || '#94a3b8').getHex();

      const isSelected = selectedIndices.includes(atom.index);
      const mat = new THREE.MeshStandardMaterial({
        color: colorHex,
        roughness: 0.25,
        metalness: 0.15,
        emissive: isSelected ? new THREE.Color('#38bdf8') : new THREE.Color(0x000000),
        emissiveIntensity: isSelected ? 0.55 : 0.0,
      });

      const mesh = new THREE.Mesh(sphereGeo, mat);
      mesh.position.set(atom.x - center.x, atom.y - center.y, atom.z - center.z);
      mesh.scale.setScalar(radius);
      mesh.userData = { atomIndex: atom.index };
      group.add(mesh);
      atomMeshesRef.current.push(mesh);

      if (isSelected) {
        const ringGeo = new THREE.RingGeometry(radius * 1.25, radius * 1.45, 32);
        const ringMat = new THREE.MeshBasicMaterial({
          color: 0x38bdf8,
          side: THREE.DoubleSide,
        });
        const ring = new THREE.Mesh(ringGeo, ringMat);
        ring.position.copy(mesh.position);
        group.add(ring);
      }
    }

    // Bonds
    if (style !== 'spacefill') {
      const atomMap = new Map(atoms.map((a) => [a.index, a]));
      const up = new THREE.Vector3(0, 1, 0);

      for (const bond of bonds) {
        const a1 = atomMap.get(bond.atom1);
        const a2 = atomMap.get(bond.atom2);
        if (!a1 || !a2) continue;

        const p1 = new THREE.Vector3(a1.x - center.x, a1.y - center.y, a1.z - center.z);
        const p2 = new THREE.Vector3(a2.x - center.x, a2.y - center.y, a2.z - center.z);
        const dir = new THREE.Vector3().subVectors(p2, p1);
        const len = dir.length();
        if (len < 1e-4) continue;

        const mid = new THREE.Vector3().addVectors(p1, p2).multiplyScalar(0.5);
        const key =
          bond.atom1 < bond.atom2
            ? `${bond.atom1}-${bond.atom2}`
            : `${bond.atom2}-${bond.atom1}`;
        const realOrder = bondOrderMap.get(key) ?? bond.order;

        const bondRadius =
          style === 'wireframe'
            ? 0.045
            : Math.min(0.16, 0.075 + Math.max(0, realOrder - 0.5) * 0.035);

        const quat = new THREE.Quaternion().setFromUnitVectors(up, dir.clone().normalize());
        const mat = new THREE.MeshStandardMaterial({
          color: realOrder >= 1.4 ? 0x38bdf8 : 0x64748b,
          roughness: 0.35,
          metalness: 0.2,
        });

        const cyl = new THREE.Mesh(cylGeo, mat);
        cyl.position.copy(mid);
        cyl.quaternion.copy(quat);
        cyl.scale.set(bondRadius, len, bondRadius);
        group.add(cyl);
      }
    }

    // Critical Points (AIM Topology)
    if (criticalPoints && criticalPoints.length > 0) {
      const cpGeo = new THREE.SphereGeometry(0.11, 20, 16);
      for (const cp of criticalPoints) {
        const cpColor =
          cp.cp_type_code === 1
            ? 0xc084fc
            : cp.cp_type_code === 2
              ? 0xf97316
              : cp.cp_type_code === 3
                ? 0xfacc15
                : 0x22c55e;
        const cpMat = new THREE.MeshStandardMaterial({
          color: cpColor,
          emissive: cpColor,
          emissiveIntensity: 0.35,
          roughness: 0.2,
        });
        const m = new THREE.Mesh(cpGeo, cpMat);
        m.position.set(cp.x - center.x, cp.y - center.y, cp.z - center.z);
        group.add(m);
      }
    }

    // Dual-phase 3D Marching Cubes Isosurface (supports mapped BGR / BWR vertex colors)
    if (showIso && isosurface) {
      if (isosurface.positive && isosurface.positive.triangle_count > 0) {
        const hasColors = !!(isosurface.positive.colors && isosurface.positive.colors.length > 0);
        const posGeom = buildMeshGeometry(isosurface.positive);
        const posMat = new THREE.MeshPhysicalMaterial({
          color: hasColors ? 0xffffff : (isosurface.has_negative ? 0x0ea5e9 : 0x22d3ee),
          vertexColors: hasColors,
          transparent: true,
          opacity: isoOpacity,
          roughness: 0.28,
          metalness: 0.08,
          side: THREE.DoubleSide,
          wireframe: isoWireframe,
          depthWrite: false,
        });
        const posMesh = new THREE.Mesh(posGeom, posMat);
        posMesh.position.set(-center.x, -center.y, -center.z);
        group.add(posMesh);
      }

      if (isosurface.negative && isosurface.negative.triangle_count > 0) {
        const hasColors = !!(isosurface.negative.colors && isosurface.negative.colors.length > 0);
        const negGeom = buildMeshGeometry(isosurface.negative);
        const negMat = new THREE.MeshPhysicalMaterial({
          color: hasColors ? 0xffffff : 0xf43f5e,
          vertexColors: hasColors,
          transparent: true,
          opacity: isoOpacity,
          roughness: 0.28,
          metalness: 0.08,
          side: THREE.DoubleSide,
          wireframe: isoWireframe,
          depthWrite: false,
        });
        const negMesh = new THREE.Mesh(negGeom, negMat);
        negMesh.position.set(-center.x, -center.y, -center.z);
        group.add(negMesh);
      }
    }

    scene.add(group);

    // Auto-fit camera distance on atom set change
    if (atoms.length > 0) {
      let maxR = 1.8;
      for (const a of atoms) {
        const d = Math.hypot(a.x - center.x, a.y - center.y, a.z - center.z);
        if (d > maxR) maxR = d;
      }
      if (camera.position.length() < 1.0 || prevGroup === undefined) {
        const distMult = isosurface ? 2.55 : 2.15;
        camera.position.set(maxR * distMult, maxR * 1.35, maxR * (distMult + 0.5));
        controls.target.set(0, 0, 0);
        controls.update();
      }
    }
  }, [
    atoms,
    bonds,
    style,
    colorByCharge,
    chargeMap,
    bondOrderMap,
    selectedIndices,
    isosurface,
    showIso,
    isoOpacity,
    isoWireframe,
    criticalPoints,
  ]);

  // Project 2D screen overlays only when camera moves, atoms change, or container resizes
  useEffect(() => {
    if (!showLabels || atoms.length === 0) {
      setLabelOverlays([]);
      return;
    }

    let pendingRaf = 0;
    let lastSignature = '';

    const computeAndSet = () => {
      pendingRaf = 0;
      const el = containerRef.current;
      const cam = cameraRef.current;
      if (!el || !cam) return;
      const w = el.clientWidth;
      const h = el.clientHeight;
      if (w <= 0 || h <= 0) return;

      cam.updateMatrixWorld();
      const center = centerOffsetRef.current;
      const next = atoms
        .filter((a) => atoms.length <= 45 || (a.symbol !== 'H' && atoms.length <= 90))
        .map((a) => {
        const v = new THREE.Vector3(a.x - center.x, a.y - center.y, a.z - center.z);
        v.project(cam);
        const x = Math.round((v.x * 0.5 + 0.5) * w);
        const y = Math.round((-v.y * 0.5 + 0.5) * h);
        const visible = v.z < 1 && x >= 12 && x <= w - 12 && y >= 12 && y <= h - 12;
        const q = chargeMap.get(a.index);
        const text =
          colorByCharge && q !== undefined
            ? `${a.symbol}${a.index} (${q >= 0 ? '+' : ''}${q.toFixed(2)})`
            : `${a.symbol}${a.index}`;
        return { index: a.index, text, x, y, visible };
      });

      const sig = next
        .map((n) => `${n.index}:${n.x},${n.y},${n.visible ? 1 : 0}:${n.text}`)
        .join('|');
      if (sig !== lastSignature) {
        lastSignature = sig;
        setLabelOverlays(next);
      }
    };

    const schedule = () => {
      if (!pendingRaf) {
        pendingRaf = requestAnimationFrame(computeAndSet);
      }
    };

    computeAndSet();
    const controls = controlsRef.current;
    controls?.addEventListener('change', schedule);
    window.addEventListener('resize', schedule);

    return () => {
      if (pendingRaf) cancelAnimationFrame(pendingRaf);
      controls?.removeEventListener('change', schedule);
      window.removeEventListener('resize', schedule);
    };
  }, [showLabels, atoms, colorByCharge, chargeMap, isosurface, style]);

  const handleCanvasClick = (e: React.MouseEvent<HTMLDivElement>) => {
    const el = containerRef.current;
    const cam = cameraRef.current;
    if (!el || !cam || atomMeshesRef.current.length === 0) return;

    const rect = el.getBoundingClientRect();
    const mouse = new THREE.Vector2(
      ((e.clientX - rect.left) / rect.width) * 2 - 1,
      -((e.clientY - rect.top) / rect.height) * 2 + 1
    );
    const raycaster = new THREE.Raycaster();
    raycaster.setFromCamera(mouse, cam);
    const hits = raycaster.intersectObjects(atomMeshesRef.current, false);
    if (hits.length > 0) {
      const atomIdx = hits[0].object.userData.atomIndex as number;
      setSelectedIndices((prev) => {
        if (prev.includes(atomIdx)) return prev.filter((x) => x !== atomIdx);
        const next = [...prev, atomIdx];
        return next.length > 3 ? next.slice(next.length - 3) : next;
      });
    } else if (selectedIndices.length > 0 && e.detail === 2) {
      setSelectedIndices([]);
    }
  };

  const resetView = () => {
    const cam = cameraRef.current;
    const ctrl = controlsRef.current;
    if (!cam || !ctrl) return;
    const center = centerOffsetRef.current;
    let maxR = 2.0;
    for (const a of atoms) {
      const d = Math.hypot(a.x - center.x, a.y - center.y, a.z - center.z);
      if (d > maxR) maxR = d;
    }
    cam.position.set(maxR * 2.0, maxR * 1.15, maxR * 2.5);
    ctrl.target.set(0, 0, 0);
    ctrl.update();
  };

  const exportSnapshot = () => {
    const renderer = rendererRef.current;
    if (!renderer) return;
    const dataUrl = renderer.domElement.toDataURL('image/png');
    const a = document.createElement('a');
    a.href = dataUrl;
    a.download = 'wavecraft_3d_view.png';
    a.click();
  };

  return (
    <div
      className={
        isMaximized
          ? 'fixed inset-0 z-50 bg-[#070b12] p-4 flex flex-col backdrop-blur-xl'
          : 'glass-panel rounded-2xl overflow-hidden flex flex-col'
      }
    >
      {/* Toolbar */}
      <div className="px-3.5 py-2.5 border-b border-slate-800/80 flex items-center justify-between gap-2 flex-wrap bg-slate-950/70">
        <div className="flex items-center gap-2">
          <span className="text-xs font-semibold text-slate-200">{title}</span>
          <span className="text-[11px] font-mono px-2 py-0.5 rounded-md bg-slate-800 text-slate-400">
            {atoms.length} 原子 · {bonds.length} 键
          </span>
          {isosurface && (
            <span className="text-[11px] font-mono px-2 py-0.5 rounded-md bg-sky-500/15 text-sky-300 border border-sky-500/25">
              等值面 {(isosurface.positive.triangle_count + (isosurface.negative?.triangle_count || 0)).toLocaleString()} 三角面
            </span>
          )}
        </div>

        <div className="flex items-center gap-1.5 flex-wrap">
          {/* Quick Camera Angles (Side view is critical for pi-pi dimer stacking) */}
          <div className="flex items-center bg-slate-900 border border-slate-800 rounded-lg p-0.5 text-[11px]">
            <Tooltip content="垂直于二聚体堆积平面，观察层间距与夹心层" title="90° 侧视角">
              <button
                onClick={() => setCameraPreset('side')}
                className="px-2 py-0.5 rounded text-slate-400 hover:text-cyan-300 hover:bg-slate-800 transition cursor-pointer"
              >
                侧视
              </button>
            </Tooltip>
            <Tooltip content="从上方俯瞰分子平面骨架" title="顶视图">
              <button
                onClick={() => setCameraPreset('top')}
                className="px-2 py-0.5 rounded text-slate-400 hover:text-cyan-300 hover:bg-slate-800 transition cursor-pointer"
              >
                顶视
              </button>
            </Tooltip>
            <Tooltip content="自适应重置三维视口居中与轴测投影" title="视口复位">
              <button
                onClick={() => setCameraPreset('fit')}
                className="px-2 py-0.5 rounded text-slate-400 hover:text-cyan-300 hover:bg-slate-800 transition cursor-pointer"
              >
                复位
              </button>
            </Tooltip>
          </div>

          {(['ball-stick', 'spacefill', 'wireframe'] as RenderStyle[]).map((s) => (
            <Tooltip
              key={s}
              content={`切换为${s === 'ball-stick' ? '球棍模型 (Ball-Stick)' : s === 'spacefill' ? '范德华空间填充模型 (CPK)' : '纯线框模型 (Wireframe)'}`}
            >
              <button
                onClick={() => setStyle(s)}
                className={`px-2 py-1 rounded-lg text-[11px] font-medium transition cursor-pointer ${
                  style === s
                    ? 'bg-sky-500/20 text-sky-300 border border-sky-400/40'
                    : 'bg-slate-900 text-slate-400 border border-slate-800 hover:text-slate-200'
                }`}
              >
                {s === 'ball-stick' ? '球棍' : s === 'spacefill' ? '空间填充' : '线框'}
              </button>
            </Tooltip>
          ))}

          {charges && charges.length > 0 && (
            <Tooltip content="按原子电荷量为原子渲染色阶 (负电荷暖红，正电荷冷蓝)" title="原子电荷着色">
              <button
                onClick={() => setColorByCharge((v) => !v)}
                className={`px-2 py-1 rounded-lg text-[11px] font-medium transition cursor-pointer ${
                  colorByCharge
                    ? 'bg-rose-500/20 text-rose-200 border border-rose-400/40'
                    : 'bg-slate-900 text-slate-400 border border-slate-800'
                }`}
              >
                电荷着色
              </button>
            </Tooltip>
          )}

          {isosurface && (
            <>
              <Tooltip content="显示或隐藏 3D 空间等值面网格" title="等值面可见性">
                <button
                  onClick={() => setShowIso((v) => !v)}
                  className={`flex items-center gap-1 px-2 py-1 rounded-lg text-[11px] transition cursor-pointer ${
                    showIso
                      ? 'bg-cyan-500/20 text-cyan-200 border border-cyan-400/40'
                      : 'bg-slate-900 text-slate-400 border border-slate-800'
                  }`}
                >
                  {showIso ? <Eye className="w-3 h-3" /> : <EyeOff className="w-3 h-3" />}
                  <span>等值面</span>
                </button>
              </Tooltip>

              <Tooltip content="以纯三角网格模式透视内部空间结构" title="等值面线框">
                <button
                  onClick={() => setIsoWireframe((v) => !v)}
                  className={`flex items-center gap-1 px-2 py-1 rounded-lg text-[11px] transition cursor-pointer ${
                    isoWireframe
                      ? 'bg-violet-500/20 text-violet-200 border border-violet-400/40'
                      : 'bg-slate-900 text-slate-400 border border-slate-800'
                  }`}
                >
                  <Layers className="w-3 h-3" />
                  <span>网格</span>
                </button>
              </Tooltip>
            </>
          )}

          <Tooltip content="在 3D 画布中显示原子元素与序号标签" title="原子标签">
            <button
              onClick={() => setShowLabels((v) => !v)}
              className={`p-1.5 rounded-lg border transition cursor-pointer ${
                showLabels
                  ? 'bg-sky-500/15 border-sky-400/35 text-sky-300'
                  : 'bg-slate-900 border-slate-800 text-slate-400'
              }`}
            >
              <Tag className="w-3.5 h-3.5" />
            </button>
          </Tooltip>

          <Tooltip content="围绕分子质心轴平滑自动旋转" title="自动旋转">
            <button
              onClick={() => setAutoRotate((v) => !v)}
              className={`p-1.5 rounded-lg border transition cursor-pointer ${
                autoRotate
                  ? 'bg-emerald-500/15 border-emerald-400/35 text-emerald-300'
                  : 'bg-slate-900 border-slate-800 text-slate-400'
              }`}
            >
              <RotateCw className={`w-3.5 h-3.5 ${autoRotate ? 'animate-spin' : ''}`} />
            </button>
          </Tooltip>

          <Tooltip
            content="轨迹球模式支持 360° 无死角任意角度立体自由翻转（彻底解除两极触墙死角）；环绕轨道为传统水平锁定旋转"
            title="空间旋转模式"
          >
            <button
              onClick={() => setControlMode((m) => (m === 'trackball' ? 'orbit' : 'trackball'))}
              className={`flex items-center gap-1 px-2 py-1 rounded-lg text-[11px] font-medium transition cursor-pointer ${
                controlMode === 'trackball'
                  ? 'bg-cyan-500/20 text-cyan-200 border border-cyan-400/40 shadow-sm'
                  : 'bg-slate-900 text-slate-400 border border-slate-800 hover:text-slate-200'
              }`}
            >
              <Compass className="w-3.5 h-3.5" />
              <span>{controlMode === 'trackball' ? '轨迹球翻转' : '环绕轨道'}</span>
            </button>
          </Tooltip>

          {/* Quick height presets */}
          {!isMaximized && resizable && (
            <div className="hidden sm:flex items-center bg-slate-900 border border-slate-800 rounded-lg p-0.5 text-[10px] font-mono">
              <Tooltip content="视口高度 380px，紧凑型展示" title="紧凑尺寸">
                <button
                  onClick={() => setViewportHeight(380)}
                  className={`px-1.5 py-0.5 rounded transition cursor-pointer ${
                    viewportHeight <= 400 ? 'bg-sky-500/20 text-sky-300 font-bold' : 'text-slate-400 hover:text-slate-200'
                  }`}
                >
                  紧凑
                </button>
              </Tooltip>
              <Tooltip content="视口高度 540px，兼顾结构与参数" title="标准尺寸">
                <button
                  onClick={() => setViewportHeight(540)}
                  className={`px-1.5 py-0.5 rounded transition cursor-pointer ${
                    viewportHeight > 400 && viewportHeight <= 600 ? 'bg-sky-500/20 text-sky-300 font-bold' : 'text-slate-400 hover:text-slate-200'
                  }`}
                >
                  标准
                </button>
              </Tooltip>
              <Tooltip content="视口高度 760px，超大视界精细剖析" title="大屏巨幕">
                <button
                  onClick={() => setViewportHeight(760)}
                  className={`px-1.5 py-0.5 rounded transition cursor-pointer ${
                    viewportHeight > 600 ? 'bg-sky-500/20 text-sky-300 font-bold' : 'text-slate-400 hover:text-slate-200'
                  }`}
                >
                  巨幕
                </button>
              </Tooltip>
            </div>
          )}

          {/* Fullscreen / Maximize */}
          <Tooltip
            content={isMaximized ? "退出全屏视口模式" : "铺满全屏沉浸式观察分子 3D 几何构型与等值面"}
            title={isMaximized ? "退出全屏" : "全屏放大"}
            shortcut="F / Esc"
          >
            <button
              onClick={() => setIsMaximized((v) => !v)}
              className={`p-1.5 rounded-lg border transition cursor-pointer ${
                isMaximized
                  ? 'bg-amber-500/20 border-amber-400/40 text-amber-200'
                  : 'bg-slate-900 border-slate-800 text-slate-400 hover:text-sky-300'
              }`}
            >
              {isMaximized ? <Minimize2 className="w-3.5 h-3.5" /> : <Maximize2 className="w-3.5 h-3.5" />}
            </button>
          </Tooltip>

          <Tooltip content="导出当前 3D 分子高保真透明 PNG 图像" title="高清截图">
            <button
              onClick={exportSnapshot}
              className="p-1.5 rounded-lg bg-slate-900 border border-slate-800 text-slate-400 hover:text-sky-300 transition cursor-pointer"
            >
              <Camera className="w-3.5 h-3.5" />
            </button>
          </Tooltip>
        </div>
      </div>

      {/* Viewport Canvas Container */}
      <div
        className="relative w-full bg-[#070b12] overflow-hidden select-none"
        style={{
          height: isMaximized ? 'calc(100vh - 80px)' : `${viewportHeight}px`,
        }}
      >
        <div
          ref={containerRef}
          onClick={handleCanvasClick}
          className="w-full h-full cursor-grab active:cursor-grabbing"
        />

        {/* Floating Scientific BGR Colorbar (for mapped NCI / IGMH) */}
        {isosurface?.color_scale === 'bgr' && (
          <div className="absolute top-3 right-3 pointer-events-auto bg-slate-950/85 backdrop-blur-md border border-slate-700/60 rounded-xl p-2.5 shadow-xl flex flex-col gap-1.5 w-44">
            <div className="flex items-center justify-between text-[10px] font-semibold text-slate-200">
              <span>sign(λ₂)ρ 映射色阶</span>
              <span className="font-mono text-cyan-400 text-[9px]">a.u.</span>
            </div>
            <div
              className="h-3 rounded-full w-full border border-slate-700/50 shadow-inner"
              style={{
                background:
                  'linear-gradient(to right, #2563eb 0%, #06b6d4 30%, #22c55e 50%, #eab308 75%, #ef4444 100%)',
              }}
            />
            <div className="flex justify-between text-[9px] font-mono text-slate-400">
              <span className="text-blue-400">&le; -0.04</span>
              <span className="text-emerald-400">0.00</span>
              <span className="text-rose-400">&ge; +0.02</span>
            </div>
            <div className="flex justify-between text-[8.5px] text-slate-400 leading-tight pt-0.5 border-t border-slate-800/80">
              <span className="text-blue-300">强吸引</span>
              <span className="text-emerald-300">范德华/π-π</span>
              <span className="text-rose-300">位阻排斥</span>
            </div>
          </div>
        )}

        {/* Floating Scientific BWR Colorbar (for ESP) */}
        {isosurface?.color_scale === 'bwr' && (
          <div className="absolute top-3 right-3 pointer-events-auto bg-slate-950/85 backdrop-blur-md border border-slate-700/60 rounded-xl p-2.5 shadow-xl flex flex-col gap-1.5 w-40">
            <div className="flex items-center justify-between text-[10px] font-semibold text-slate-200">
              <span>ESP 静电势色阶</span>
              <span className="font-mono text-cyan-400 text-[9px]">a.u.</span>
            </div>
            <div
              className="h-3 rounded-full w-full border border-slate-700/50 shadow-inner"
              style={{
                background:
                  'linear-gradient(to right, #2563eb 0%, #ffffff 50%, #ef4444 100%)',
              }}
            />
            <div className="flex justify-between text-[9px] font-mono text-slate-400">
              <span className="text-blue-400">-0.05</span>
              <span className="text-slate-300">0.00</span>
              <span className="text-rose-400">+0.05</span>
            </div>
          </div>
        )}

        {/* Projected Atom Labels */}
        {showLabels &&
          labelOverlays.map(
            (lbl) =>
              lbl.visible && (
                <div
                  key={lbl.index}
                  className="pointer-events-none absolute -translate-x-1/2 -translate-y-1/2 px-1.5 py-0.5 rounded bg-slate-950/75 border border-slate-700/60 text-[10px] font-mono text-slate-200 shadow"
                  style={{ left: lbl.x, top: lbl.y - 16 }}
                >
                  {lbl.text}
                </div>
              )
          )}

        {/* Empty State */}
        {atoms.length === 0 && (
          <div className="absolute inset-0 flex flex-col items-center justify-center text-slate-500 pointer-events-none">
            <p className="text-sm font-medium">暂无三维分子结构</p>
            <p className="text-xs mt-1">请在顶部加载波函数或分子坐标文件</p>
          </div>
        )}

        {/* Bottom HUD */}
        <div className="absolute bottom-2.5 left-3 right-3 flex items-center justify-between gap-2 pointer-events-none">
          <div className="pointer-events-auto flex items-center gap-2 px-3 py-1.5 rounded-xl bg-slate-950/85 border border-slate-800/90 text-[11px] text-slate-300 backdrop-blur">
            <Ruler className="w-3.5 h-3.5 text-sky-400" />
            <span className="font-mono">{measurementText}</span>
            {selectedIndices.length > 0 && (
              <button
                onClick={() => setSelectedIndices([])}
                className="text-slate-400 hover:text-white ml-1 underline cursor-pointer"
              >
                清除
              </button>
            )}
          </div>

          {isosurface && onIsoOpacityChange && (
            <div className="pointer-events-auto flex items-center gap-2 px-3 py-1.5 rounded-xl bg-slate-950/85 border border-slate-800/90 text-[11px] text-slate-300 backdrop-blur">
              <span>透明度</span>
              <input
                type="range"
                min={0.15}
                max={0.95}
                step={0.05}
                value={isoOpacity}
                onChange={(e) => onIsoOpacityChange(parseFloat(e.target.value))}
                className="w-20 accent-sky-400 cursor-pointer"
              />
              <span className="font-mono w-7 text-right">{Math.round(isoOpacity * 100)}%</span>
            </div>
          )}
        </div>
      </div>

      {/* Draggable Height Resize Handle */}
      {resizable && !isMaximized && (
        <div
          onMouseDown={startDragHeight}
          className={`w-full h-3 bg-slate-900/90 hover:bg-sky-500/30 border-t border-slate-800 flex items-center justify-center cursor-row-resize transition select-none group ${
            isDraggingHeight ? 'bg-sky-500/40' : ''
          }`}
          title="上下拖拽动态调整视口高度"
        >
          <div className="flex items-center gap-1.5 text-slate-500 group-hover:text-sky-300 transition-colors">
            <GripHorizontal className="w-3.5 h-3.5" />
            <span className="text-[10px] font-mono opacity-0 group-hover:opacity-100 transition-opacity">
              {viewportHeight}px (拖拽自由伸缩)
            </span>
          </div>
        </div>
      )}
    </div>
  );
};
