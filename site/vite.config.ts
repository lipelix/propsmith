import preact from "@preact/preset-vite";
import { defineConfig, type Plugin } from "vite";

/**
 * Cloudflare Web Analytics (cookieless page metrics): the beacon is added to the page only when the build is given
 * the site's token in `CF_BEACON_TOKEN`. The deploy job requires it; a local or pull-request build has none and
 * reports nothing.
 */
function webAnalytics(token: string | undefined): Plugin {
  return {
    name: "propsmith-web-analytics",
    transformIndexHtml() {
      if (token === undefined || token === "") return [];
      if (!/^[0-9a-f]{32}$/.test(token))
        throw new Error(
          "CF_BEACON_TOKEN must be the 32 hex characters of a Web Analytics site token",
        );
      return [
        {
          tag: "script",
          attrs: {
            defer: true,
            src: "https://static.cloudflareinsights.com/beacon.min.js",
            "data-cf-beacon": JSON.stringify({ token }),
          },
          injectTo: "body",
        },
      ];
    },
  };
}

export default defineConfig({
  root: import.meta.dirname,
  base: "./",
  plugins: [preact(), webAnalytics(process.env.CF_BEACON_TOKEN)],
  build: { outDir: "dist", emptyOutDir: true, chunkSizeWarningLimit: 900 },
});
