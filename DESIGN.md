# Design

The site is a tool (see `PRODUCT.md`): the catalogue and the asset page. Tokens and components live in
`site/src/styles.css`; this file records the decisions behind them.

## World

A workshop bench at a desk in the evening: dark by default, a light theme one click away (stored per browser, first
visit follows the system). Neutrals are tinted warm (hue 85) so the grey studio backdrop of the renders sits in them;
one accent, a forge ochre (hue 78), marks the primary action, the selected filter and switched-on controls. Nothing
else is coloured: the props carry the colour.

## Type

The system UI face, one family for everything, 15 px base, a tight scale (0.8 / 0.87 / 0.93 / 1 / 1.15 / 1.5 rem).
Numbers (sizes, counts, bytes, slider values) use tabular figures. Monospace only for code and paths.

## Layout

- A 3 rem top bar; below it two columns: on the catalogue filters (17 rem) and results, on the asset page the 3D
  stage and a 24 rem panel. The stage stays in view while the panel scrolls.
- Under 860 px the columns stack; controls grow to 44 px touch targets.
- Elevation is declared by a 1 px line, not by shadows; radii 6 px (controls), 8 px (thumbnails), pills for filters.

## The stage

- The picture is the published GLB under the rig of the Blender snapshot (`tools/blender/style.json`): the same sun,
  sky, exposure and camera; AgX tone mapping plus a fixed grade on the canvas stands in for Blender's "Medium High
  Contrast" look. `site/src/viewer.ts` holds the numbers; change them only together with the style.
- The backdrop is drawn by CSS behind a transparent canvas, so a saved picture has no background.
- The Blender snapshot shows while the model loads and stays when WebGL is missing; the note under the stage says
  which of the two is on screen.

## Motion

One authored moment: the live view fades in over the snapshot it replaces. Hover and state changes are 150–250 ms;
everything honours `prefers-reduced-motion`.

## Icons

Authored SVG in `site/src/icons.tsx`: 16 px grid, 1.5 px round strokes. No emoji, no glyph stand-ins.
