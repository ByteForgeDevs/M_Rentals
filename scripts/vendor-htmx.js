// Copy htmx into static/ so the app never depends on a CDN at runtime.
const fs = require("node:fs");
const path = require("node:path");

const source = path.join(__dirname, "..", "node_modules", "htmx.org", "dist", "htmx.min.js");
const targetDir = path.join(__dirname, "..", "static", "js");
const target = path.join(targetDir, "htmx.min.js");

if (!fs.existsSync(source)) {
  console.warn("htmx not found in node_modules; skipping vendor step.");
  process.exit(0);
}
fs.mkdirSync(targetDir, { recursive: true });
fs.copyFileSync(source, target);
console.log(`Vendored htmx -> ${path.relative(process.cwd(), target)}`);
