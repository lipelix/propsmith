import { defineConfig, devices } from "@playwright/test";

/**
 * End-to-end tests of the site (`npm run test:e2e`). They need the baked catalogue in `site/public/data`
 * (`npm run bake && npm run site:data`, which needs Blender), so they run locally, not in CI.
 */
const PORT = 5394;

export default defineConfig({
  testDir: "tests/e2e",
  testMatch: /.*\.e2e\.ts/,
  outputDir: ".cache/e2e",
  // Headless Chromium draws WebGL in software: one page at a time keeps the timing honest.
  workers: 1,
  use: { baseURL: `http://localhost:${PORT}`, trace: "off" },
  webServer: {
    command: `npm run site:dev -- --port ${PORT} --strictPort`,
    url: `http://localhost:${PORT}`,
    reuseExistingServer: false,
  },
  projects: [
    {
      name: "desktop",
      use: {
        ...devices["Desktop Chrome"],
        viewport: { width: 1440, height: 900 },
      },
    },
    { name: "phone", use: { ...devices["Pixel 7"] } },
  ],
});
