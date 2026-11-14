import {
  AgXToneMapping,
  Box3,
  Color,
  DirectionalLight,
  GridHelper,
  Group,
  type Material,
  Mesh,
  type Object3D,
  OrthographicCamera,
  PerspectiveCamera,
  PlaneGeometry,
  PMREMGenerator,
  Scene,
  ShadowMaterial,
  type Texture,
  Vector3,
  VSMShadowMap,
  WebGLRenderer,
} from "three";
import { OrbitControls } from "three/examples/jsm/controls/OrbitControls.js";
import { GLTFLoader } from "three/examples/jsm/loaders/GLTFLoader.js";

/**
 * The live view of an asset: the published GLB under the review rig of the Blender snapshots
 * (`tools/blender/style.json`): one warm sun, a uniform cool sky, AgX, an orthographic camera at 30 degrees looking
 * at the asset's +x and front (-y) faces. Everything the page lets a visitor change is in `Settings`.
 *
 * Axes: glTF is y up; the asset's x is X, its up is Y and its front (-y) is +Z.
 */
export interface Settings {
  /** Where the sun stands, degrees clockwise from the asset's back (+y) seen from above; 270 is the asset's -x. */
  sunAzimuth: number;
  /** Sun height above the horizon in degrees. */
  sunElevation: number;
  /** Sun strength, as Blender's sun strength. */
  sunStrength: number;
  /** Sky strength, as Blender's world strength. */
  skyStrength: number;
  /** Exposure in stops. */
  exposure: number;
  projection: "orthographic" | "perspective";
  turntable: boolean;
  /** Quarter turns of the model about its up axis. */
  quarterTurns: number;
  shadow: boolean;
  grid: boolean;
}

/** The review rig of `tools/blender/style.json`. */
export const BLENDER: Settings = {
  sunAzimuth: 270,
  sunElevation: 48,
  sunStrength: 6,
  skyStrength: 0.55,
  exposure: -0.15,
  projection: "orthographic",
  turntable: false,
  quarterTurns: 0,
  shadow: true,
  grid: false,
};

const SUN_COLOR = new Color(1.0, 0.87, 0.7);
const SKY_COLOR = new Color(0.5, 0.56, 0.68);
const CAMERA_ELEVATION = 30;
const CAMERA_AZIMUTH = 45;
const SHADOW_OPACITY = 0.6;

const rad = (deg: number): number => (deg * Math.PI) / 180;

/** Unit vector toward a point at `azimuth` (clockwise from -Z, the asset's back, seen from above) and `elevation`. */
export function direction(azimuth: number, elevation: number): Vector3 {
  const a = rad(azimuth);
  const e = rad(elevation);
  return new Vector3(
    Math.sin(a) * Math.cos(e),
    Math.sin(e),
    -Math.cos(a) * Math.cos(e),
  );
}

export class Viewer {
  private readonly renderer: WebGLRenderer;
  private readonly scene = new Scene();
  private readonly ortho = new OrthographicCamera(-1, 1, 1, -1, 0.1, 200);
  private readonly persp = new PerspectiveCamera(28, 1, 0.1, 200);
  private readonly sun = new DirectionalLight(SUN_COLOR, BLENDER.sunStrength);
  private readonly ground: Mesh;
  private readonly model = new Group();
  private readonly controls: OrbitControls;
  private readonly sky: Texture;
  private grid: GridHelper | null = null;
  private settings: Settings = BLENDER;
  private radius = 1;
  private centre = new Vector3();
  private frame = 0;
  private loads = 0;
  private disposed = false;
  private readonly observer: ResizeObserver;

  constructor(private readonly host: HTMLElement) {
    this.renderer = new WebGLRenderer({
      antialias: true,
      alpha: true,
      preserveDrawingBuffer: true,
    });
    this.renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    this.renderer.toneMapping = AgXToneMapping;
    this.renderer.shadowMap.enabled = true;
    this.renderer.shadowMap.type = VSMShadowMap;
    this.renderer.setClearColor(0x000000, 0);
    this.renderer.domElement.setAttribute("aria-hidden", "true");
    host.append(this.renderer.domElement);

    // A uniform sky, as Blender's world colour: it lights the shaded sides and shows in the metals.
    const room = new Scene();
    room.background = SKY_COLOR;
    const pmrem = new PMREMGenerator(this.renderer);
    this.sky = pmrem.fromScene(room).texture;
    pmrem.dispose();
    this.scene.environment = this.sky;

    this.sun.castShadow = true;
    this.sun.shadow.mapSize.set(2048, 2048);
    this.sun.shadow.radius = 5;
    this.sun.shadow.blurSamples = 16;
    this.sun.shadow.bias = -0.0005;
    this.sun.shadow.normalBias = 0.01;
    this.scene.add(this.sun, this.sun.target);

    this.ground = new Mesh(
      new PlaneGeometry(1, 1),
      new ShadowMaterial({ opacity: SHADOW_OPACITY }),
    );
    this.ground.rotation.x = -Math.PI / 2;
    this.ground.receiveShadow = true;
    this.scene.add(this.ground, this.model);

    this.controls = new OrbitControls(this.ortho, this.renderer.domElement);
    this.controls.enableDamping = true;
    this.controls.enablePan = false;
    this.controls.maxPolarAngle = rad(89);
    this.controls.autoRotateSpeed = 4;

    this.observer = new ResizeObserver(() => this.resize());
    this.observer.observe(host);
    this.resize();
    this.apply(BLENDER);
    this.resetView();
    const tick = () => {
      if (this.disposed) return;
      this.frame = requestAnimationFrame(tick);
      if (document.hidden) return;
      this.controls.update();
      this.renderer.render(this.scene, this.camera);
    };
    tick();
  }

  private get camera(): OrthographicCamera | PerspectiveCamera {
    return this.settings.projection === "orthographic"
      ? this.ortho
      : this.persp;
  }

  /** Loads a GLB and frames it; resolves when it is on screen, rejects when the file cannot be read. */
  async load(url: string): Promise<void> {
    const load = ++this.loads;
    const gltf = await new GLTFLoader().loadAsync(url);
    if (this.disposed || load !== this.loads) return;
    this.clearModel();
    gltf.scene.traverse((node: Object3D) => {
      if (node instanceof Mesh) {
        node.castShadow = true;
        node.receiveShadow = true;
      }
    });
    this.model.add(gltf.scene);
    const box = new Box3().setFromObject(this.model);
    const size = box.getSize(new Vector3());
    this.radius = Math.max(size.length() / 2, 0.25);
    this.centre = new Vector3(0, size.y / 2, 0);
    const reach = this.radius * 6;
    this.ground.scale.set(reach * 2, reach * 2, 1);
    const shadow = this.sun.shadow.camera;
    shadow.left = shadow.bottom = -reach;
    shadow.right = shadow.top = reach;
    shadow.near = 0.1;
    shadow.far = this.radius * 40;
    shadow.updateProjectionMatrix();
    this.setGrid(this.settings.grid);
    this.placeSun();
    this.resize();
    this.resetView();
  }

  /** Applies the settings; cheap enough to call on every slider move. */
  apply(settings: Settings): void {
    const before = this.settings;
    this.settings = settings;
    this.sun.intensity = settings.sunStrength;
    this.sun.castShadow = settings.shadow;
    this.ground.visible = settings.shadow;
    this.scene.environmentIntensity = settings.skyStrength;
    this.renderer.toneMapping = AgXToneMapping;
    this.renderer.toneMappingExposure = 2 ** settings.exposure;
    this.model.rotation.y = (-settings.quarterTurns * Math.PI) / 2;
    this.controls.autoRotate = settings.turntable;
    this.placeSun();
    if (settings.grid !== before.grid) this.setGrid(settings.grid);
    if (settings.projection !== before.projection) {
      const from =
        before.projection === "orthographic" ? this.ortho : this.persp;
      const offset = from.position.clone().sub(this.controls.target);
      this.controls.object = this.camera;
      this.camera.position.copy(this.controls.target).add(offset);
      this.resize();
    }
  }

  /** Back to the camera of the Blender snapshot. */
  resetView(): void {
    const distance = this.radius * 6;
    const offset = direction(180 - CAMERA_AZIMUTH, CAMERA_ELEVATION);
    this.controls.target.copy(this.centre);
    for (const camera of [this.ortho, this.persp]) {
      camera.position.copy(this.centre).addScaledVector(offset, distance);
      camera.near = distance / 100;
      camera.far = distance * 10;
      camera.zoom = 1;
      camera.lookAt(this.centre);
      camera.updateProjectionMatrix();
    }
    this.controls.update();
  }

  /** The current picture as a PNG data URL (transparent background). */
  snapshot(): string {
    this.renderer.render(this.scene, this.camera);
    return this.renderer.domElement.toDataURL("image/png");
  }

  dispose(): void {
    this.disposed = true;
    cancelAnimationFrame(this.frame);
    this.observer.disconnect();
    this.controls.dispose();
    this.clearModel();
    this.sky.dispose();
    this.ground.geometry.dispose();
    (this.ground.material as Material).dispose();
    this.grid?.dispose();
    this.renderer.dispose();
    this.renderer.domElement.remove();
  }

  private placeSun(): void {
    const toward = direction(
      this.settings.sunAzimuth,
      this.settings.sunElevation,
    );
    this.sun.target.position.copy(this.centre);
    this.sun.position
      .copy(this.centre)
      .addScaledVector(toward, this.radius * 12);
  }

  private setGrid(on: boolean): void {
    if (this.grid) {
      this.scene.remove(this.grid);
      this.grid.dispose();
      this.grid = null;
    }
    if (!on) return;
    // One metre per cell, so the size reads off the ground.
    const cells = Math.max(4, Math.ceil(this.radius * 3) * 2);
    this.grid = new GridHelper(cells, cells, 0x8a8f98, 0x8a8f98);
    const material = this.grid.material as Material;
    material.transparent = true;
    material.opacity = 0.45;
    this.grid.position.y = 0.002;
    this.scene.add(this.grid);
  }

  private clearModel(): void {
    this.model.traverse((node: Object3D) => {
      if (!(node instanceof Mesh)) return;
      node.geometry.dispose();
      for (const material of [node.material].flat() as Material[]) {
        for (const value of Object.values(material))
          if (value && (value as Texture).isTexture)
            (value as Texture).dispose();
        material.dispose();
      }
    });
    this.model.clear();
  }

  private resize(): void {
    const width = Math.max(1, this.host.clientWidth);
    const height = Math.max(1, this.host.clientHeight);
    this.renderer.setSize(width, height, false);
    const aspect = width / height;
    // The whole model with room for its shadow, whatever the shape of the stage.
    const half = this.radius * 1.12;
    this.ortho.left = -half * Math.max(aspect, 1);
    this.ortho.right = half * Math.max(aspect, 1);
    this.ortho.top = half / Math.min(aspect, 1);
    this.ortho.bottom = -half / Math.min(aspect, 1);
    this.ortho.updateProjectionMatrix();
    this.persp.aspect = aspect;
    this.persp.fov = aspect < 1 ? 28 / aspect : 28;
    this.persp.updateProjectionMatrix();
  }
}
