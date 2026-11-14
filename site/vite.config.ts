import preact from "@preact/preset-vite";
import { defineConfig, type Plugin } from "vite";

/**
 * Cloudflare Web Analytics (cookieless, no consent banner) for the published site only. `vite build --mode publish`
 * (`npm run site:publish`) needs the site token `infra/` creates, as `CF_WEB_ANALYTICS_TOKEN`; a missing token fails
 * the build. Every other mode (dev, e2e, a local build) sends nothing.
 */
function webAnalytics(mode: string): Plugin | undefined {
  if (mode !== "publish") return undefined;
  const token = process.env.CF_WEB_ANALYTICS_TOKEN;
  if (!token)
    throw new Error(
      "Missing required environment variable: CF_WEB_ANALYTICS_TOKEN",
    );
  if (!/^\w+$/.test(token))
    throw new Error("CF_WEB_ANALYTICS_TOKEN must be letters and digits only");
  return {
    name: "propsmith-web-analytics",
    transformIndexHtml: () => [
      {
        tag: "script",
        attrs: {
          defer: true,
          src: "https://static.cloudflareinsights.com/beacon.min.js",
          "data-cf-beacon": JSON.stringify({ token }),
        },
        injectTo: "body",
      },
    ],
  };
}

export default defineConfig(({ mode }) => ({
  root: import.meta.dirname,
  base: "./",
  plugins: [preact(), webAnalytics(mode)],
  build: { outDir: "dist", emptyOutDir: true, chunkSizeWarningLimit: 900 },
}));
