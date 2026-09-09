import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const scriptDirectory = path.dirname(fileURLToPath(import.meta.url));
const repoRoot = path.resolve(scriptDirectory, "..");
const studyDirectory = path.join(
  repoRoot,
  "studies",
  "STU003__RNG002_UTG-vs-BTN__5FLOP_FLOP4",
);
const templatePath = path.join(
  repoRoot,
  "studies",
  "STU002__RNG001_UTG-vs-BB__BRD001_FLOP6",
  "config.json",
);
const rangeDirectory = path.join(repoRoot, "ranges");
const manifestPath = path.join(
  rangeDirectory,
  "RNG002__TSGPU020_6M100_UTG-O2p5_BTN-C__V1.json",
);
const outputPath = path.join(studyDirectory, "config.json");

function readRangeMap(filePath) {
  const map = new Map();
  for (const token of fs.readFileSync(filePath, "utf8").trim().split(",")) {
    const [rawKey, rawValue, ...extra] = token.trim().split(":");
    const key = rawKey?.trim();
    if (!key || rawValue === undefined || extra.length !== 0) {
      throw new Error(`Invalid range token '${token}' in ${filePath}`);
    }
    if (map.has(key)) {
      throw new Error(`Duplicate range key '${key}' in ${filePath}`);
    }
    const value = Number(rawValue.trim());
    if (!Number.isFinite(value) || value < 0 || value > 1) {
      throw new Error(`Invalid weight for '${key}' in ${filePath}`);
    }
    map.set(key, value);
  }
  return map;
}

function startingHandKey(cardA, cardB) {
  const ranks = "23456789TJQKA";
  const rankA = Math.floor(cardA / 4);
  const rankB = Math.floor(cardB / 4);
  if (rankA === rankB) {
    return ranks[rankA] + ranks[rankA];
  }
  const high = Math.max(rankA, rankB);
  const low = Math.min(rankA, rankB);
  const suited = cardA % 4 === cardB % 4 ? "s" : "o";
  return ranks[high] + ranks[low] + suited;
}

function expandRange(filePath) {
  const map = readRangeMap(filePath);
  const values = [];
  for (let cardA = 0; cardA < 51; cardA += 1) {
    for (let cardB = cardA + 1; cardB < 52; cardB += 1) {
      values.push(map.get(startingHandKey(cardA, cardB)) ?? 0);
    }
  }
  if (values.length !== 1326) {
    throw new Error(`Expanded range has ${values.length} combos, expected 1326`);
  }
  return values;
}

function assertWeightedCombos(values, expected, label) {
  const actual = values.reduce((sum, value) => sum + value, 0);
  if (Math.abs(actual - expected) > 1e-9) {
    throw new Error(`${label} weighted combos ${actual}, expected ${expected}`);
  }
}

const template = JSON.parse(fs.readFileSync(templatePath, "utf8"));
const manifest = JSON.parse(fs.readFileSync(manifestPath, "utf8"));
const ipRange = expandRange(path.join(rangeDirectory, manifest.files.BTN));
const oopRange = expandRange(path.join(rangeDirectory, manifest.files.UTG));
assertWeightedCombos(ipRange, manifest.weighted_combos.BTN, "BTN/IP");
assertWeightedCombos(oopRange, manifest.weighted_combos.UTG, "UTG/OOP");

const generated = structuredClone(template);
generated.runner = {
  maxIterations: 1000,
  targetExploitability: 0.5,
  decisionNode: "UTG_OOP_CBET",
  expectedBetAmount: 33,
  expectedRaiseAmount: 112,
};
generated.config.startingPot = 65;
generated.config.effectiveStack = 975;
generated.config.ipRange = ipRange;
generated.config.oopRange = oopRange;

fs.mkdirSync(studyDirectory, { recursive: true });
fs.writeFileSync(outputPath, `${JSON.stringify(generated, null, 2)}\n`, "utf8");
console.log(`Wrote ${path.relative(repoRoot, outputPath)}`);
