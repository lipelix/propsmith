import { createHash } from "node:crypto";
import { readFileSync } from "node:fs";
import { expect, type Page, test } from "@playwright/test";
import type { Asset } from "../../site/src/data.ts";
import { EMPTY, filter } from "../../site/src/search.ts";

/** The published catalogue, to count what the filters should leave. */
const ASSETS = (
  JSON.parse(readFileSync("catalog/index.json", "utf8")) as {
    assets: Asset[];
  }
).assets;
/** How many assets a search finds, by the site's own rule, so a new asset with a matching alias does not break the test. */
const found = (text: string) => filter(ASSETS, { ...EMPTY, text }).length;
const caskCount = found("cask");
/** A search no prop answers: an alias like "dragon hoard" made a real word match one. */
const NOTHING = "zzxq";
const ironCount = ASSETS.filter((a) => a.tags.includes("iron")).length;
const ironLightCount = ASSETS.filter(
  (a) => a.tags.includes("iron") && a.category === "light",
).length;

/** A hash of what the 3D stage shows (the canvas and its backdrop), to tell that a control changed the picture. */
async function picture(page: Page): Promise<string> {
  const shown = await page.evaluate(
    "document.querySelector('.stage canvas').toDataURL() + document.querySelector('.stage').dataset.backdrop",
  );
  return createHash("sha256").update(String(shown)).digest("hex");
}

const ready = (page: Page) =>
  expect(page.locator(".stage")).toHaveAttribute("data-load", "ready", {
    timeout: 20_000,
  });

test("the catalogue searches, filters and opens an asset", async ({ page }) => {
  const problems: string[] = [];
  page.on("pageerror", (error) => problems.push(error.message));
  page.on("console", (message) => {
    if (message.type() === "error") problems.push(message.text());
  });
  await page.goto("/");
  const tiles = page.locator(".tile");
  await expect(tiles).toHaveCount(ASSETS.length);

  await page.getByRole("searchbox").fill("cask");
  await expect(tiles).toHaveCount(caskCount);
  await expect(tiles.filter({ hasText: "Wooden barrel" })).toHaveCount(1);
  await expect(page.getByRole("heading", { level: 1 })).toHaveText(
    `${caskCount} ${caskCount === 1 ? "prop" : "props"} of ${ASSETS.length}`,
  );

  expect(found(NOTHING)).toBe(0);
  await page.getByRole("searchbox").fill(NOTHING);
  await expect(page.locator(".empty")).toContainText("Nothing matches");
  await page.getByRole("button", { name: "Clear filters" }).click();
  await expect(tiles).toHaveCount(ASSETS.length);

  await page.getByRole("button", { name: /^iron/ }).click();
  await expect(tiles).toHaveCount(ironCount);
  await page.getByRole("button", { name: /^light\b/ }).click();
  await expect(tiles).toHaveCount(ironLightCount);
  await page.getByRole("searchbox").fill("lamppost");
  await expect(tiles).toHaveCount(1);
  await expect(tiles.first()).toContainText("Street lamp post");
  await tiles.first().click();

  await expect(page).toHaveURL(/#\/asset\/lamp_post$/);
  await expect(page.getByRole("heading", { level: 1 })).toHaveText(
    "Street lamp post",
  );
  await ready(page);
  await expect(page.locator(".facts")).toContainText("light:lantern");
  expect(problems).toEqual([]);
});

test("the asset page renders live and every control changes the picture", async ({
  page,
}) => {
  // A dozen WebGL pictures compared in turn: on the two-core runner's software renderer this nears the 3 min limit.
  test.slow();
  await page.goto("/#/asset/well_stone");
  await ready(page);
  await page.waitForTimeout(500);
  const first = await picture(page);
  const seen = new Set([first]);
  /** Waits until the stage shows a picture not seen before. */
  const changed = async (what: string) => {
    let now = "";
    await expect
      .poll(
        async () => {
          now = await picture(page);
          return seen.has(now);
        },
        { message: `${what} did not change the picture`, timeout: 10_000 },
      )
      .toBe(false);
    await page.waitForTimeout(300);
    seen.add(now);
    seen.add(await picture(page));
  };

  await page.getByLabel("Sun direction").fill("90");
  await changed("sun direction");
  await page.getByLabel("Sun height").fill("80");
  await changed("sun height");
  await page.getByLabel("Sun strength").fill("2");
  await changed("sun strength");
  await page.getByLabel("Sky strength").fill("1.5");
  await changed("sky strength");
  await page.getByLabel("Exposure").fill("1");
  await changed("exposure");

  await page.getByRole("button", { name: "Blender rig" }).click();
  await expect(page.getByLabel("Sun direction")).toHaveValue("270");
  await expect(
    page.getByRole("button", { name: "Blender rig" }),
  ).toBeDisabled();
  expect(
    seen.has(await picture(page)),
    "Blender rig restores the first picture",
  ).toBe(true);

  await page.getByRole("button", { name: /quarter turn right/ }).click();
  await changed("quarter turn");
  await page.getByRole("button", { name: "Perspective" }).click();
  await changed("perspective");
  await page.getByRole("radio", { name: "Grass" }).check({ force: true });
  await changed("background");
  await page
    .getByRole("switch", { name: "Shadow on the ground" })
    .uncheck({ force: true });
  await changed("shadow");
  await page
    .getByRole("switch", { name: "Grid, 1 m squares" })
    .check({ force: true });
  await changed("grid");

  await page.getByRole("switch", { name: "Turntable" }).check({ force: true });
  await changed("the turntable");
  await changed("the turntable, a moment later");
  await page.getByRole("button", { name: "Blender view" }).click();
  await expect(
    page.getByRole("switch", { name: "Turntable" }),
  ).not.toBeChecked();

  const download = page.getByRole("link", { name: /Download GLB/ });
  await expect(download).toHaveAttribute(
    "href",
    "data/well_stone/well_stone.glb",
  );
  const response = await page.request.get("/data/well_stone/well_stone.glb");
  expect(response.ok()).toBe(true);
});

test("an unknown asset says so and leads back", async ({ page }) => {
  await page.goto("/#/asset/dragon_gold");
  await expect(page.getByRole("heading", { level: 1 })).toContainText(
    "No asset",
  );
  await page.getByRole("link", { name: "Back to the catalogue" }).click();
  await expect(page.locator(".tile")).toHaveCount(ASSETS.length);
});

test("a weapon is filtered by its category and shows its grip points", async ({
  page,
}) => {
  const weapons = ASSETS.filter((a) => a.category === "weapon").length;
  await page.goto("/");
  await page.getByRole("button", { name: /^weapon\b/ }).click();
  await expect(page.locator(".tile")).toHaveCount(weapons);

  await page.goto("/#/asset/greatsword");
  await ready(page);
  await expect(page.locator(".facts")).toContainText("two hands");
  const switched = page.getByRole("switch", { name: "Grip points" });
  await expect(switched).toBeChecked();
  await page.waitForTimeout(500);
  const shown = await picture(page);
  await switched.uncheck({ force: true });
  await expect.poll(() => picture(page), { timeout: 10_000 }).not.toBe(shown);

  await page.goto("/#/asset/well_stone");
  await ready(page);
  await expect(page.getByRole("switch", { name: "Grip points" })).toHaveCount(
    0,
  );
});
