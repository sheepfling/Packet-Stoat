import fs from "node:fs";
import path from "node:path";
import milsymbol from "milsymbol";

function readJsonl(filePath) {
  const text = fs.readFileSync(filePath, "utf8");
  return text
    .split("\n")
    .filter((line) => line.trim().length > 0)
    .map((line) => JSON.parse(line));
}

function safeFileName(value) {
  return value.replace(/[^a-zA-Z0-9_.-]/g, "_");
}

function renderDescriptor(descriptor, outDir) {
  const sidc = String(descriptor.sidc ?? "");
  if (sidc.length === 0) {
    throw new Error(`Descriptor ${descriptor.case_id ?? "<unknown>"} does not include a SIDC`);
  }
  const caseId = String(descriptor.case_id ?? sidc);
  const modifiers = descriptor.modifiers ?? {};
  const symbol = new milsymbol.Symbol(sidc, modifiers);
  const svg = symbol.asSVG();
  if (!svg.includes("<svg")) {
    throw new Error(`Renderer did not return SVG for ${caseId}`);
  }
  fs.mkdirSync(outDir, { recursive: true });
  fs.writeFileSync(path.join(outDir, `${safeFileName(caseId)}.svg`), svg, "utf8");
}

const inputPath = process.argv[2];
const outDir = process.argv[3] ?? "extensions/fastdis-symbols-proof/out";
if (inputPath === undefined) {
  throw new Error("Usage: node render_milsymbol.mjs descriptors.jsonl out_dir");
}

const descriptors = readJsonl(inputPath);
for (const descriptor of descriptors) {
  renderDescriptor(descriptor, outDir);
}
console.log(`rendered=${descriptors.length}`);
