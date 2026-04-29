// next ships its own webpack — import via Next's entrypoint, not the bare
// `webpack` package which isn't in our top-level deps.
import webpackLib from "next/dist/compiled/webpack/webpack-lib.js";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";

const __dirname = dirname(fileURLToPath(import.meta.url));

/** @type {import('next').NextConfig} */
const nextConfig = {
  // Full static export for Cloudflare Pages deploy. All dynamic routes
  // already use generateStaticParams() so every page pre-renders at
  // build time. The deploy serves pure static HTML/CSS/JS — no edge
  // runtime, no Worker compute, no fs/path at request time.
  output: "export",
  // next/image optimizer needs a runtime; on static export we disable it
  // and let the browser render <img> tags directly. The site uses very
  // few raster images (mostly diagrams as SVG), so this is a non-cost.
  images: { unoptimized: true },
  // Trailing slashes match Cloudflare Pages' default routing behaviour
  // and avoid double-slash redirects on the edge.
  trailingSlash: true,
  reactStrictMode: true,
  eslint: { ignoreDuringBuilds: true },
  staticPageGenerationTimeout: 300,
  experimental: {
    typedRoutes: false,
    cpus: 1,
    workerThreads: false,
  },
  // Webpack walks up the directory tree resolving modules. The user's
  // ~/node_modules contains `bare-fs` / `bare-tty` / `bare-os` / `bare-stdio`
  // / `bare-url` / `bare-hrtime` / `bare-events` packages (transitives of
  // globally-installed `hyperschema` / `random-access-file`) which expose
  // node-native bindings via `binding.js`. When these end up in the
  // *browser* bundle they crash at runtime with
  // `__webpack_require__(...).addon is not a function`, killing every
  // client-side useEffect — including Observable Plot's chart rendering.
  //
  // Tell webpack to skip every `bare-*` import on the client side.
  webpack: (config, { isServer }) => {
    if (!isServer) {
      // The user's ~/node_modules contains a full Node `process` package
      // (transitive of globally-installed deps) whose `index.js` does
      //   require('bare-abort'); require('bare-events'); …
      // — pulling node-native bindings into the browser bundle. The
      // browser-friendly entry of the same package is `process/browser`,
      // which is a self-contained polyfill that doesn't touch bare-*.
      // Aliasing `process` → `process/browser` for client builds breaks
      // the chain.
      // Absolute path to the LOCAL process/browser.js, otherwise webpack
      // tries to resolve `process/browser` against the user's
      // ~/node_modules/process which has stricter exports.
      config.resolve.alias = {
        ...config.resolve.alias,
        process: join(__dirname, "node_modules", "process", "browser.js"),
      };
      // Restrict webpack to only resolve modules from the project's own
      // node_modules tree. Stops it walking up to ~/node_modules where
      // unrelated globally-installed packages live. Build-only — server
      // resolution still walks normally so SSR + build tooling work.
      config.resolve.modules = [
        join(__dirname, "node_modules"),
        "node_modules",
      ];
      config.resolve.fallback = {
        ...(config.resolve.fallback ?? {}),
        fs: false,
        path: false,
        os: false,
      };
    }
    return config;
  },
};

export default nextConfig;
