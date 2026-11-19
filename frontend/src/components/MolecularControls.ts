import * as THREE from 'three';

export interface MolecularControlsOptions {
  rotateSpeed?: number;
  panSpeed?: number;
  zoomSpeed?: number;
  dampingFactor?: number;
  enableDamping?: boolean;
  rotationMode?: 'free' | 'horizon';
}

/**
 * MolecularControls: Professional Screen-Space Camera Controller for Molecular Graphics
 * 
 * Specifically engineered to eliminate:
 * 1. Polar angle singularity (OrbitControls polar lock / upside-down flipping bug)
 * 2. Inverted drag direction when viewed upside down (TrackballControls bug)
 * 3. Gimbal lock and orientation stutter
 * 
 * Guarantees:
 * - Full unconstrained 360° continuous vertical tumbling ("上下翻转") and horizontal rotation.
 * - Drag directions always align with user screen space (dragging up always tilts up, dragging right always rotates right).
 * - Smooth inertia damping and 1:1 screen-to-world panning.
 */
export class MolecularControls {
  camera: THREE.PerspectiveCamera | THREE.OrthographicCamera;
  domElement: HTMLElement;
  target: THREE.Vector3 = new THREE.Vector3(0, 0, 0);

  enabled: boolean = true;
  rotateSpeed: number = 1.0;
  panSpeed: number = 1.0;
  zoomSpeed: number = 1.0;
  dampingFactor: number = 0.08;
  enableDamping: boolean = true;

  // 'free' = 360° unconstrained trackball tumbling ("上下翻转"); 'horizon' = locked world-Y up
  rotationMode: 'free' | 'horizon' = 'free';
  dragAction: 'rotate' | 'pan' = 'rotate';

  private isPointerDown: boolean = false;
  private activePointerId: number | null = null;
  private prevPointer: THREE.Vector2 = new THREE.Vector2();
  private activeAction: 'rotate' | 'pan' | null = null;

  rotVelocity: THREE.Vector2 = new THREE.Vector2();
  panVelocity: THREE.Vector2 = new THREE.Vector2();

  // Bound event handlers
  private onPointerDownBound: (e: PointerEvent) => void;
  private onPointerMoveBound: (e: PointerEvent) => void;
  private onPointerUpBound: (e: PointerEvent) => void;
  private onWheelBound: (e: WheelEvent) => void;
  private onContextMenuBound: (e: MouseEvent) => void;

  constructor(
    camera: THREE.PerspectiveCamera | THREE.OrthographicCamera,
    domElement: HTMLElement,
    options?: MolecularControlsOptions
  ) {
    this.camera = camera;
    this.domElement = domElement;

    if (options?.rotateSpeed !== undefined) this.rotateSpeed = options.rotateSpeed;
    if (options?.panSpeed !== undefined) this.panSpeed = options.panSpeed;
    if (options?.zoomSpeed !== undefined) this.zoomSpeed = options.zoomSpeed;
    if (options?.dampingFactor !== undefined) this.dampingFactor = options.dampingFactor;
    if (options?.enableDamping !== undefined) this.enableDamping = options.enableDamping;
    if (options?.rotationMode !== undefined) this.rotationMode = options.rotationMode;

    this.onPointerDownBound = this.onPointerDown.bind(this);
    this.onPointerMoveBound = this.onPointerMove.bind(this);
    this.onPointerUpBound = this.onPointerUp.bind(this);
    this.onWheelBound = this.onWheel.bind(this);
    this.onContextMenuBound = (e) => e.preventDefault();

    this.connect();
  }

  connect() {
    const el = this.domElement;
    el.addEventListener('pointerdown', this.onPointerDownBound);
    el.addEventListener('wheel', this.onWheelBound, { passive: false });
    el.addEventListener('contextmenu', this.onContextMenuBound);
  }

  dispose() {
    const el = this.domElement;
    el.removeEventListener('pointerdown', this.onPointerDownBound);
    el.removeEventListener('wheel', this.onWheelBound);
    el.removeEventListener('contextmenu', this.onContextMenuBound);
    window.removeEventListener('pointermove', this.onPointerMoveBound);
    window.removeEventListener('pointerup', this.onPointerUpBound);
    window.removeEventListener('pointercancel', this.onPointerUpBound);
  }

  private onPointerDown(e: PointerEvent) {
    if (!this.enabled) return;
    if (this.isPointerDown) return;

    // Determine action from button and dragAction state
    // Button 0 = Left, 1 = Middle, 2 = Right
    if (e.button === 0) {
      this.activeAction = this.dragAction === 'pan' ? 'pan' : 'rotate';
    } else if (e.button === 1 || e.button === 2) {
      this.activeAction = 'pan';
    } else {
      return;
    }

    this.isPointerDown = true;
    this.activePointerId = e.pointerId;
    this.prevPointer.set(e.clientX, e.clientY);
    this.rotVelocity.set(0, 0);
    this.panVelocity.set(0, 0);

    window.addEventListener('pointermove', this.onPointerMoveBound);
    window.addEventListener('pointerup', this.onPointerUpBound);
    window.addEventListener('pointercancel', this.onPointerUpBound);
  }

  private onPointerMove(e: PointerEvent) {
    if (!this.enabled || !this.isPointerDown) return;
    if (e.pointerId !== this.activePointerId) return;

    const dx = e.clientX - this.prevPointer.x;
    const dy = e.clientY - this.prevPointer.y;
    this.prevPointer.set(e.clientX, e.clientY);

    if (this.activeAction === 'rotate') {
      this.rotate(dx, dy);
      this.rotVelocity.set(dx, dy);
    } else if (this.activeAction === 'pan') {
      this.pan(dx, dy);
      this.panVelocity.set(dx, dy);
    }
  }

  private onPointerUp(e: PointerEvent) {
    if (e.pointerId !== this.activePointerId) return;
    this.isPointerDown = false;
    this.activePointerId = null;
    this.activeAction = null;

    window.removeEventListener('pointermove', this.onPointerMoveBound);
    window.removeEventListener('pointerup', this.onPointerUpBound);
    window.removeEventListener('pointercancel', this.onPointerUpBound);
  }

  private onWheel(e: WheelEvent) {
    if (!this.enabled) return;
    e.preventDefault();
    this.zoom(e.deltaY);
  }

  /**
   * Screen-Space 360° Trackball Rotation
   * 
   * Mathematical Guarantee:
   * Rotates around the instantaneous camera screen-right and screen-up axes.
   * Completely immune to gimbal lock, polar clipping, and inverted drag directions.
   */
  rotate(deltaX: number, deltaY: number) {
    const el = this.domElement;
    const w = el.clientWidth || window.innerWidth || 800;
    const h = el.clientHeight || window.innerHeight || 600;

    const angleX = (-deltaX / w) * Math.PI * 1.85 * this.rotateSpeed;
    const angleY = (-deltaY / h) * Math.PI * 1.85 * this.rotateSpeed;

    const cam = this.camera;
    const target = this.target;

    const eye = new THREE.Vector3().subVectors(cam.position, target);
    const dist = eye.length();
    if (dist < 1e-5) return;

    if (this.rotationMode === 'horizon') {
      // Horizon locked: rotate around world Y axis for horizontal yaw,
      // and camera right axis for vertical pitch (with safe polar clamping)
      const forward = eye.clone().negate().normalize();
      const worldUp = new THREE.Vector3(0, 1, 0);
      const right = new THREE.Vector3().crossVectors(forward, worldUp).normalize();
      if (right.lengthSq() < 1e-5) right.set(1, 0, 0);

      // Horizontal yaw around world Y
      const qYaw = new THREE.Quaternion().setFromAxisAngle(worldUp, angleX);
      eye.applyQuaternion(qYaw);
      right.applyQuaternion(qYaw);

      // Vertical pitch around right axis with polar angle safety clamp
      const newEye = eye.clone();
      const qPitch = new THREE.Quaternion().setFromAxisAngle(right, angleY);
      newEye.applyQuaternion(qPitch);

      // Check angle with worldUp
      const polar = Math.acos(Math.max(-1, Math.min(1, newEye.clone().normalize().dot(worldUp))));
      if (polar > 0.04 && polar < Math.PI - 0.04) {
        eye.copy(newEye);
      }

      cam.position.copy(target).add(eye);
      cam.up.set(0, 1, 0);
      cam.lookAt(target);
      return;
    }

    // Default 'free' mode: True 360° unrestricted molecular arcball tumbling
    const forward = eye.clone().negate().normalize();
    const right = new THREE.Vector3().crossVectors(forward, cam.up).normalize();
    if (right.lengthSq() < 1e-5) {
      right.set(1, 0, 0);
    }
    const up = new THREE.Vector3().crossVectors(right, forward).normalize();

    // 1. Horizontal rotation around screen vertical axis (up)
    const qX = new THREE.Quaternion().setFromAxisAngle(up, angleX);
    eye.applyQuaternion(qX);
    right.applyQuaternion(qX);

    // 2. Vertical rotation around screen horizontal axis (right) - unrestricted 360° tumbling
    const qY = new THREE.Quaternion().setFromAxisAngle(right, angleY);
    eye.applyQuaternion(qY);
    up.applyQuaternion(qY);

    cam.position.copy(target).add(eye);
    cam.up.copy(up);
    cam.lookAt(target);
  }

  /**
   * Screen-Space 1:1 Planar Pan
   */
  pan(deltaX: number, deltaY: number) {
    const el = this.domElement;
    const h = el.clientHeight || window.innerHeight || 600;

    const cam = this.camera;
    const target = this.target;

    const eye = new THREE.Vector3().subVectors(cam.position, target);
    const dist = eye.length();

    let factor = 1.0;
    if (cam instanceof THREE.PerspectiveCamera) {
      factor = (2.0 * Math.tan(THREE.MathUtils.degToRad(cam.fov * 0.5)) * dist) / h;
    }

    const forward = eye.clone().negate().normalize();
    const right = new THREE.Vector3().crossVectors(forward, cam.up).normalize();
    const up = new THREE.Vector3().crossVectors(right, forward).normalize();

    const panOffset = new THREE.Vector3()
      .addScaledVector(right, -deltaX * factor * this.panSpeed)
      .addScaledVector(up, deltaY * factor * this.panSpeed);

    cam.position.add(panOffset);
    target.add(panOffset);
  }

  /**
   * Exponential Smooth Zoom
   */
  zoom(deltaY: number) {
    const cam = this.camera;
    const target = this.target;
    const eye = new THREE.Vector3().subVectors(cam.position, target);
    const dist = eye.length();

    const scale = deltaY > 0 ? 1.08 : 0.92;
    const newDist = Math.max(0.15, Math.min(dist * scale, 1500));
    eye.setLength(newDist);
    cam.position.copy(target).add(eye);
  }

  zoomIn() {
    this.zoom(-100);
  }

  zoomOut() {
    this.zoom(100);
  }

  recenter() {
    this.rotVelocity.set(0, 0);
    this.panVelocity.set(0, 0);
    this.target.set(0, 0, 0);
    this.camera.lookAt(this.target);
  }

  setView(preset: 'front' | 'top' | 'side' | 'fit', radius: number = 4.0) {
    this.rotVelocity.set(0, 0);
    this.panVelocity.set(0, 0);
    this.target.set(0, 0, 0);
    const cam = this.camera;
    const dist = Math.max(radius * 2.2, 3.5);

    if (preset === 'top') {
      cam.position.set(0, dist, 0.001);
      cam.up.set(0, 0, -1);
    } else if (preset === 'side') {
      cam.position.set(dist, 0, 0);
      cam.up.set(0, 1, 0);
    } else if (preset === 'front') {
      cam.position.set(0, 0, dist);
      cam.up.set(0, 1, 0);
    } else {
      cam.position.set(dist * 0.72, dist * 0.52, dist * 0.88);
      cam.up.set(0, 1, 0);
    }
    cam.lookAt(this.target);
  }

  handleResize() {
    // No-op for compatibility
  }

  /**
   * Frame tick for smooth momentum inertia
   */
  update() {
    if (!this.enabled) return;

    if (this.enableDamping && !this.isPointerDown) {
      if (this.rotVelocity.lengthSq() > 1e-5) {
        this.rotate(this.rotVelocity.x, this.rotVelocity.y);
        this.rotVelocity.multiplyScalar(1 - this.dampingFactor);
      }
      if (this.panVelocity.lengthSq() > 1e-5) {
        this.pan(this.panVelocity.x, this.panVelocity.y);
        this.panVelocity.multiplyScalar(1 - this.dampingFactor);
      }
    }
  }
}
