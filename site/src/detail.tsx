import { useEffect, useRef, useState } from "preact/hooks";

import { type Asset, count, DATA, hangs, kilobytes, metres } from "./data.ts";
import {
  BackIcon,
  CopyIcon,
  DownloadIcon,
  ResetIcon,
  TurnLeftIcon,
  TurnRightIcon,
} from "./icons.tsx";
import { BLENDER, type Settings, Viewer } from "./viewer.ts";

const REPO = "https://github.com/lipelix/propsmith";

const BACKDROPS = [
  { id: "studio", name: "Studio" },
  { id: "dark", name: "Dark" },
  { id: "light", name: "Light" },
  { id: "grass", name: "Grass" },
  { id: "checker", name: "Transparent" },
] as const;
type Backdrop = (typeof BACKDROPS)[number]["id"];

type Load = "loading" | "ready" | "failed";

function Slider(props: {
  label: string;
  value: number;
  min: number;
  max: number;
  step: number;
  unit: string;
  onChange: (value: number) => void;
}) {
  const shown = Number.isInteger(props.step)
    ? String(props.value)
    : props.value.toFixed(2);
  const id = `slider-${props.label.toLowerCase().replaceAll(" ", "-")}`;
  return (
    <div class="slider">
      <label class="slider-label" for={id}>
        {props.label}
      </label>
      <output class="num" for={id}>
        {shown}
        {props.unit}
      </output>
      <input
        id={id}
        type="range"
        min={props.min}
        max={props.max}
        step={props.step}
        value={props.value}
        onInput={(event) => props.onChange(Number(event.currentTarget.value))}
      />
    </div>
  );
}

function Switch(props: {
  label: string;
  checked: boolean;
  onChange: (checked: boolean) => void;
}) {
  return (
    <label class="switch">
      <input
        type="checkbox"
        // Native switch where supported (Safari); role keeps it a switch elsewhere.
        {...({ switch: true } as Record<string, boolean>)}
        role="switch"
        checked={props.checked}
        onChange={(event) => props.onChange(event.currentTarget.checked)}
      />
      <span class="switch-track" aria-hidden="true" />
      {props.label}
    </label>
  );
}

export function Detail({
  asset,
  variant: wanted,
}: {
  asset: Asset;
  variant: string | null;
}) {
  const variant =
    asset.variants.find((v) => v.id === wanted) ?? asset.variants[0];
  const stage = useRef<HTMLDivElement>(null);
  const viewer = useRef<Viewer | null>(null);
  const [settings, setSettings] = useState<Settings>(BLENDER);
  const [backdrop, setBackdrop] = useState<Backdrop>("studio");
  const [load, setLoad] = useState<Load>("loading");
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    if (!stage.current) return;
    let made: Viewer;
    try {
      made = new Viewer(stage.current);
    } catch {
      // No WebGL: the snapshot stays, and the page says so.
      setLoad("failed");
      return;
    }
    viewer.current = made;
    return () => {
      made.dispose();
      viewer.current = null;
    };
  }, []);

  useEffect(() => {
    if (!viewer.current || !variant) return;
    setLoad("loading");
    viewer.current.load(`${DATA}/${variant.glb}`).then(
      () => setLoad("ready"),
      () => setLoad("failed"),
    );
  }, [variant?.id]);

  useEffect(() => {
    viewer.current?.apply(settings);
  }, [settings]);

  if (!variant) return null;
  const hanging = hangs(asset, variant);
  const set = (patch: Partial<Settings>) =>
    setSettings((current) => ({ ...current, ...patch }));
  const lightChanged = (
    [
      "sunAzimuth",
      "sunElevation",
      "sunStrength",
      "skyStrength",
      "exposure",
    ] as const
  ).some((key) => settings[key] !== BLENDER[key]);
  const source = `catalog/${asset.id}/asset.py`;

  const savePicture = () => {
    const url = viewer.current?.snapshot();
    if (!url) return;
    const link = document.createElement("a");
    link.href = url;
    link.download = `${variant.id}.png`;
    link.click();
  };
  const copySource = async () => {
    await navigator.clipboard.writeText(source);
    setCopied(true);
    setTimeout(() => setCopied(false), 1600);
  };

  return (
    <main class="detail">
      <section class="stage-wrap" aria-label="3D view">
        <div
          ref={stage}
          class="stage"
          data-backdrop={backdrop}
          data-load={load}
          role="img"
          aria-label={`${asset.name}, live 3D view. Drag to turn it, scroll to zoom.`}
        >
          <img class="stage-still" src={`${DATA}/${variant.png}`} alt="" />
        </div>
        <p class="stage-note" role="status">
          {load === "loading" && "Loading the model…"}
          {load === "ready" &&
            "The published GLB, lit in your browser with the rig of the Blender snapshot. Drag to turn, scroll to zoom."}
          {load === "failed" &&
            "The 3D view did not start (no WebGL, or the model did not load). This is the Blender snapshot."}
        </p>
      </section>

      <div class="panel">
        <a class="back" href="#/">
          <BackIcon /> Catalogue
        </a>
        <h1>{asset.name}</h1>
        <p class="description">{asset.description}</p>

        {asset.variants.length > 1 && (
          <div class="segmented" role="group" aria-label="Variant">
            {asset.variants.map((v) => (
              <a
                key={v.id}
                href={`#/asset/${asset.id}/${v.id}`}
                aria-current={v.id === variant.id ? "true" : undefined}
              >
                {v.id === asset.id
                  ? "default"
                  : v.id.slice(asset.id.length + 1)}
              </a>
            ))}
          </div>
        )}

        <div class="actions">
          <a
            class="button primary"
            href={`${DATA}/${variant.glb}`}
            download={`${variant.id}.glb`}
          >
            <DownloadIcon /> Download GLB
            <span class="num"> · {kilobytes(variant.glbBytes)}</span>
          </a>
          <button
            type="button"
            class="button"
            onClick={savePicture}
            disabled={load !== "ready"}
          >
            Save picture
          </button>
        </div>

        <section class="group" aria-labelledby="light-h">
          <div class="group-head">
            <h2 id="light-h">Light</h2>
            <button
              type="button"
              class="quiet"
              disabled={!lightChanged}
              onClick={() =>
                set({
                  sunAzimuth: BLENDER.sunAzimuth,
                  sunElevation: BLENDER.sunElevation,
                  sunStrength: BLENDER.sunStrength,
                  skyStrength: BLENDER.skyStrength,
                  exposure: BLENDER.exposure,
                })
              }
            >
              <ResetIcon /> Blender rig
            </button>
          </div>
          <Slider
            label="Sun direction"
            value={settings.sunAzimuth}
            min={0}
            max={360}
            step={5}
            unit="°"
            onChange={(sunAzimuth) => set({ sunAzimuth })}
          />
          <Slider
            label="Sun height"
            value={settings.sunElevation}
            min={5}
            max={90}
            step={1}
            unit="°"
            onChange={(sunElevation) => set({ sunElevation })}
          />
          <Slider
            label="Sun strength"
            value={settings.sunStrength}
            min={0}
            max={12}
            step={0.25}
            unit=""
            onChange={(sunStrength) => set({ sunStrength })}
          />
          <Slider
            label="Sky strength"
            value={settings.skyStrength}
            min={0}
            max={2}
            step={0.05}
            unit=""
            onChange={(skyStrength) => set({ skyStrength })}
          />
          <Slider
            label="Exposure"
            value={settings.exposure}
            min={-2}
            max={2}
            step={0.05}
            unit=" EV"
            onChange={(exposure) => set({ exposure })}
          />
        </section>

        <section class="group" aria-labelledby="view-h">
          <div class="group-head">
            <h2 id="view-h">View</h2>
            <button
              type="button"
              class="quiet"
              onClick={() => {
                set({ quarterTurns: 0, turntable: false });
                viewer.current?.resetView();
              }}
            >
              <ResetIcon /> Blender view
            </button>
          </div>
          <div class="row">
            <span class="row-label">Turn the model</span>
            <div class="pair">
              <button
                type="button"
                class="button icon-only"
                aria-label="Turn the model a quarter turn left"
                onClick={() => set({ quarterTurns: settings.quarterTurns - 1 })}
              >
                <TurnLeftIcon />
              </button>
              <button
                type="button"
                class="button icon-only"
                aria-label="Turn the model a quarter turn right"
                onClick={() => set({ quarterTurns: settings.quarterTurns + 1 })}
              >
                <TurnRightIcon />
              </button>
            </div>
          </div>
          <Switch
            label="Turntable"
            checked={settings.turntable}
            onChange={(turntable) => set({ turntable })}
          />
          <div class="row">
            <span class="row-label" id="projection-l">
              Camera
            </span>
            <div class="segmented" role="group" aria-labelledby="projection-l">
              {(["orthographic", "perspective"] as const).map((projection) => (
                <button
                  type="button"
                  key={projection}
                  aria-pressed={settings.projection === projection}
                  onClick={() => set({ projection })}
                >
                  {projection === "orthographic" ? "Ortho" : "Perspective"}
                </button>
              ))}
            </div>
          </div>
        </section>

        <section class="group" aria-labelledby="stage-h">
          <div class="group-head">
            <h2 id="stage-h">Background and ground</h2>
          </div>
          <div class="swatches" role="radiogroup" aria-label="Background">
            {BACKDROPS.map((b) => (
              <label key={b.id} class="swatch" data-backdrop={b.id}>
                <input
                  type="radio"
                  name="backdrop"
                  checked={backdrop === b.id}
                  onChange={() => setBackdrop(b.id)}
                />
                <span class="swatch-chip" aria-hidden="true" />
                {b.name}
              </label>
            ))}
          </div>
          <Switch
            label="Shadow on the ground"
            checked={settings.shadow}
            onChange={(shadow) => set({ shadow })}
          />
          <Switch
            label="Grid, 1 m squares"
            checked={settings.grid}
            onChange={(grid) => set({ grid })}
          />
        </section>

        <section class="group" aria-labelledby="facts-h">
          <div class="group-head">
            <h2 id="facts-h">Facts</h2>
          </div>
          <dl class="facts">
            <dt>Size</dt>
            <dd class="num">{metres(variant.measured)}</dd>
            <dt>Fits in</dt>
            <dd class="num">{metres(asset.size)}</dd>
            <dt>Triangles</dt>
            <dd class="num">
              {count(variant.tris)} ({variant.tris.toLocaleString("en")})
            </dd>
            <dt>Category</dt>
            <dd>
              {asset.category}, {asset.family}
            </dd>
            <dt>Tags</dt>
            <dd>{asset.tags.join(", ")}</dd>
            {asset.aliases.length > 0 && (
              <>
                <dt>Also called</dt>
                <dd>{asset.aliases.join(", ")}</dd>
              </>
            )}
            {asset.anchors.length > 0 && (
              <>
                <dt>Anchors</dt>
                <dd class="num">{asset.anchors.join(", ")}</dd>
              </>
            )}
            {hanging !== null && (
              <>
                <dt>Hangs</dt>
                <dd>{hanging}</dd>
              </>
            )}
            <dt>Mesh</dt>
            <dd>
              {asset.closed ? "closed (can be fractured or printed)" : "open"}
            </dd>
            <dt>Made</dt>
            <dd>
              {asset.source === "generated"
                ? "by a coding agent, from a description"
                : asset.source === "handwritten"
                  ? "by hand"
                  : "from an asset pack"}
            </dd>
            <dt>Licence</dt>
            <dd>{asset.licence} (public domain)</dd>
          </dl>
        </section>

        <section class="group" aria-labelledby="source-h">
          <div class="group-head">
            <h2 id="source-h">Source</h2>
          </div>
          <p class="source">
            The model is a Blender script. A Blender pipeline can build it from
            source instead of using the GLB.
          </p>
          <div class="code">
            <code>{source}</code>
            <button
              type="button"
              class="quiet"
              onClick={copySource}
              aria-label="Copy the path of the source"
            >
              <CopyIcon /> {copied ? "Copied" : "Copy"}
            </button>
          </div>
          <a href={`${REPO}/blob/main/${source}`}>Read the source on GitHub</a>
        </section>
      </div>
    </main>
  );
}
