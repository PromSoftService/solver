import fs from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { SpreadsheetFile, Workbook } from "@oai/artifact-tool";


const scriptDir = path.dirname(fileURLToPath(import.meta.url));
const repo = process.env.SOLVER_REPO_ROOT
  ? path.resolve(process.env.SOLVER_REPO_ROOT)
  : path.resolve(scriptDir, "..");
const study = process.argv[2];
if (!study) {
  throw new Error("Usage: build-flop-workbooks.mjs <study-directory-name>");
}
const studyManifest = JSON.parse(
  await fs.readFile(path.join(repo, "studies", study, "study.json"), "utf8"),
);
const studyCode = studyManifest.study_id;
const strategyTitle = studyManifest.strategy_title;
if (!strategyTitle) throw new Error(`${study}: study.json is missing strategy_title`);
const analysisRoot = path.join(repo, "datasets", study, "analysis");

const outputs = [
  {
    key: "strategy-10",
    filename: `${studyCode}_flop_strategy.xlsx`,
    subtitle: "12 категорий рук × 10 итоговых категорий флопов. Чистое действие, строгий микс 50/50 или BDFD.",
    flopHeaders: [
      "ABB (6)", "A[K/Q]x (16)", "A[J-T]x (16)", "A[9-2]x (28)", "BBB (4)",
      "BBx (47)", "K/Qx (56)", "[J-8]x dis (67)", "[J-8]x con (26)", "[7-4]x (20)",
    ],
    csvHeaders: [
      "ABB", "A[K/Q]x", "A[J-T]x", "A[9-2]x", "BBB", "BBx", "K/Qx",
      "[J-8]x dis", "[J-8]x con", "[7-4]x",
    ],
    explanations: [
      "A + 2×B", "A + K/Q + ≤9", "A + J/T", "A + 9…2", "3×B без A",
      "2×B + ≤9", "K/Q high", "J…8 dry", "J…8 connected", "top ≤7",
    ],
    dividerAfter: [2, 4, 6, 7, 8, 9, 10],
    methodFlops: "286 canonical unpaired rainbow flops, 10 итоговых взаимоисключающих категорий",
    methodCategory: "10 итоговых категорий; B13 используется только для однозначного разбиения",
    categoryRows: [
      ["ABB", "ABB", 6, "A + две broadway-карты"],
      ["A[K/Q]x", "A[K/Q]x", 16, "A + K/Q + карта 9 и ниже"],
      ["A[J-T]x", "A[J-T][9-5] + A[J-T][4-2]", 16, "A с J/T"],
      ["A[9-2]x", "A[9-7]x + A[6-2]x", 28, "A со средней картой 9 или ниже"],
      ["BBB", "BBB", 4, "Без A; три broadway-карты"],
      ["BBx", "BBx", 47, "Без A; две broadway + карта 9 и ниже; JT9 исключён"],
      ["K/Qx", "K/Qx dis + K/Qx con", 56, "Старшая K/Q, но не BBx"],
      ["[J-8]x dis", "[J-8]x dis", 67, "Старшая J/T/9/8; две младшие не соседние"],
      ["[J-8]x con", "[J-8]x con", 26, "Старшая J/T/9/8; две младшие соседние; включает JT9"],
      ["[7-4]x", "[7-4]x", 20, "Старшая карта 7 или ниже"],
    ],
  },
];

const branchInfo = studyManifest.branches.map((branch) => ({
  id: branch.id,
  sheet: branch.strategy_sheet,
  title: branch.strategy_title,
  actor: branch.acting_player,
}));
for (const branch of branchInfo) {
  if (!branch.sheet || !branch.title) {
    throw new Error(`${study}/${branch.id}: missing strategy_sheet or strategy_title`);
  }
}

const handOrder = [
  "Two pair+", "Overpair", "Top pair", "Underpair", "Second pair", "Weak pair",
  "Third pair", "Low pocket pair", "OESD", "Gutshot", "2 overcards + BDFD", "Air",
];

const colors = {
  background: "#FFFFFF", text: "#111827", subtle: "#4B5563",
  header: "#1F4E78", section: "#475569", white: "#FFFFFF",
  border: "#94A3B8", borderLight: "#CBD5E1", divider: "#94A3B8",
  x: "#DCEBFA", b: "#DCFCE7", d: "#FFEDD5", f: "#FECACA",
  c: "#DCEBFA", r: "#E9D5FF", mix: "#FEF3C7", dash: "#F3F4F6",
};

function colName(index1) {
  let value = index1;
  let result = "";
  while (value > 0) {
    value -= 1;
    result = String.fromCharCode(65 + (value % 26)) + result;
    value = Math.floor(value / 26);
  }
  return result;
}

function parseCsv(text) {
  const rows = [];
  let row = [];
  let field = "";
  let quoted = false;
  const source = text.replace(/^\uFEFF/, "");
  for (let i = 0; i < source.length; i += 1) {
    const ch = source[i];
    if (quoted) {
      if (ch === '"' && source[i + 1] === '"') {
        field += '"';
        i += 1;
      } else if (ch === '"') {
        quoted = false;
      } else {
        field += ch;
      }
    } else if (ch === '"') {
      quoted = true;
    } else if (ch === ",") {
      row.push(field);
      field = "";
    } else if (ch === "\n") {
      row.push(field.replace(/\r$/, ""));
      rows.push(row);
      row = [];
      field = "";
    } else {
      field += ch;
    }
  }
  if (field || row.length) {
    row.push(field.replace(/\r$/, ""));
    rows.push(row);
  }
  return rows;
}

function frequencyText(values, labels) {
  return Object.entries(values)
    .map(([action, value]) => `${labels[action]} ${(100 * value).toFixed(1)}%`)
    .join("; ");
}

function branchRule(labels) {
  const explanation = Object.entries(labels).map(([action, code]) => {
    const names = { check: "check", donk: "donk", bet: "bet", fold: "fold", call: "call", raise: "raise" };
    return `${code} = ${names[action]}`;
  }).join(", ");
  const bdfd = labels.fold && labels.call ? " BDFD = fold без BDFD, call с BDFD." : "";
  return `${explanation}. Код через / — ровно 50/50.${bdfd} Bet и donk = 50% банка.`;
}

function styleBase(sheet, lastCol, lastRow) {
  sheet.showGridLines = false;
  sheet.getRange(`A1:${lastCol}${lastRow}`).format = {
    fill: colors.background,
    font: { name: "Aptos", size: 11, color: colors.text },
    verticalAlignment: "center",
  };
}

function styleActionCell(cell, value) {
  let fill = colors.dash;
  if (value === "—") fill = colors.dash;
  else if (value.includes("/")) fill = colors.mix;
  else if (value === "X") fill = colors.x;
  else if (value === "B") fill = colors.b;
  else if (value === "D") fill = colors.d;
  else if (value === "F") fill = colors.f;
  else if (value === "C" || value === "BDFD") fill = colors.c;
  else if (value === "R") fill = colors.r;
  cell.format = {
    fill,
    font: { name: "Aptos", size: 11, bold: true, color: colors.text },
    horizontalAlignment: "center",
    verticalAlignment: "center",
    borders: { preset: "all", style: "thin", color: colors.background },
  };
}

async function readModel(model) {
  const root = path.join(analysisRoot, model.key);
  const manifest = JSON.parse(await fs.readFile(path.join(root, "manifest.json"), "utf8"));
  const byBranch = {};
  for (const branch of branchInfo) {
    const rows = parseCsv(await fs.readFile(path.join(root, branch.id, "strategy.csv"), "utf8"));
    const headers = rows[0];
    const records = new Map();
    for (const values of rows.slice(1)) {
      if (!values[0]) continue;
      records.set(values[0], Object.fromEntries(headers.map((header, index) => [header, values[index]])));
    }
    const info = manifest.branches.find((item) => item.branch === branch.id);
    byBranch[branch.id] = { records, info };
  }
  return { manifest, byBranch };
}

function addSummary(workbook, model, loaded) {
  const sheet = workbook.worksheets.add("Summary");
  const lastCol = "J";
  styleBase(sheet, lastCol, 23);
  sheet.mergeCells("A2:J2");
  sheet.mergeCells("A3:J3");
  sheet.getRange("A2").values = [[strategyTitle]];
  sheet.getRange("A3").values = [[model.subtitle]];
  sheet.getRange("A2:J2").format = {
    fill: colors.background,
    font: { name: "Aptos Display", size: 20, bold: true, color: colors.text },
    horizontalAlignment: "left",
    borders: { bottom: { style: "medium", color: colors.header } },
  };
  sheet.getRange("A3:J3").format = {
    fill: colors.background,
    font: { name: "Aptos", size: 11, color: colors.subtle },
  };
  const headers = [
    "Ситуация", "Игрок", "Reach узла", "Solver frequencies", "Стратегия",
    "Loss в узле, bb", "Loss от root, bb", "BDFD ячеек",
    "Комбо reach > 0", "Ячеек",
  ];
  sheet.getRange("A5:J5").values = [headers];
  sheet.getRange("A5:J5").format = {
    fill: colors.header,
    font: { name: "Aptos", size: 10, bold: true, color: colors.white },
    wrapText: true,
    horizontalAlignment: "center",
    borders: { preset: "all", style: "thin", color: colors.white },
  };
  const rows = branchInfo.map((branch) => {
    const info = loaded.byBranch[branch.id].info;
    const s = info.summary;
    return [
      branch.title, branch.actor, s.node_reach_fraction,
      frequencyText(s.solver_reach_weighted_frequencies, info.labels),
      frequencyText(s.simplified_reach_weighted_frequencies, info.labels),
      s.mean_local_loss_bb, s.root_loss_bb, s.bdfd_cells,
      s.active_rows, s.populated_cells,
    ];
  });
  const lastBranchRow = 5 + rows.length;
  sheet.getRange(`A6:J${lastBranchRow}`).values = rows;
  sheet.getRange(`A6:J${lastBranchRow}`).format = {
    fill: colors.background,
    font: { name: "Aptos", size: 10, color: colors.text },
    borders: { preset: "all", style: "thin", color: colors.border },
    wrapText: true,
  };
  sheet.getRange(`C6:C${lastBranchRow}`).format.numberFormat = "0.0%";
  sheet.getRange(`F6:G${lastBranchRow}`).format.numberFormat = "0.000000";
  sheet.getRange(`H6:J${lastBranchRow}`).format.numberFormat = "0";

  sheet.getRange("A13:D13").values = [["Код", "Действие", "Цвет", "Правило"]];
  sheet.getRange("F13:J13").values = [["Категории флопов", null, null, null, null]];
  sheet.getRange("A13:D13").format = {
    fill: colors.section,
    font: { name: "Aptos", size: 10, bold: true, color: colors.white },
    horizontalAlignment: "center",
    borders: { preset: "all", style: "thin", color: colors.borderLight },
  };
  sheet.getRange("F13:J13").format = sheet.getRange("A13:D13").format;
  const legend = [
    ["X", "Check", "синий", null], ["B", "Bet 50%", "зелёный", null],
    ["D", "Donk 50%", "оранжевый", null], ["F", "Fold", "красный", null],
    ["C", "Call", "голубой", null], ["R", "Raise", "фиолетовый", null],
    ["BDFD", "Call только с BDFD", "голубой", "без BDFD — fold"],
    ["X/B, F/C и т. п.", "Два действия", "жёлтый", "строго 50/50"],
    ["—", "Нет категории", "серый", "в диапазоне/классе отсутствует"],
  ];
  sheet.getRange("A14:D22").values = legend;
  sheet.getRange("A14:D22").format = {
    fill: colors.background,
    font: { name: "Aptos", size: 10, color: colors.text },
    borders: { preset: "all", style: "thin", color: colors.borderLight },
  };
  const notes = [
    model.methodCategory,
    "Каждый реальный флоп внутри итоговой категории получает одинаковый вес.",
    "12 категорий рук; OESD и Gutshot имеют приоритет над made hand.",
    "Все значения через / означают только микс 50/50.",
    "EV аудирует потери; только для BDFD служит safety-фильтром.",
  ];
  notes.forEach((note, index) => {
    const row = 14 + index;
    sheet.mergeCells(`F${row}:J${row}`);
    sheet.getRange(`F${row}`).values = [[note]];
  });
  sheet.getRange("F14:J18").format = {
    fill: colors.background,
    font: { name: "Aptos", size: 10, color: colors.text },
    wrapText: true,
  };
  sheet.getRange("A14:D22").format.wrapText = true;
  sheet.getRange("14:22").format.rowHeight = 26;
  sheet.getRange("A1:A23").format.columnWidth = 27;
  sheet.getRange("B1:B23").format.columnWidth = 11;
  sheet.getRange("C1:C23").format.columnWidth = 12;
  sheet.getRange("D1:E23").format.columnWidth = 23;
  sheet.getRange("F1:H23").format.columnWidth = 16;
  sheet.getRange("I1:J23").format.columnWidth = 13;
  sheet.getRange("5:5").format.rowHeight = 36;
  sheet.freezePanes.freezeRows(5);
}

function addStrategySheet(workbook, model, branch, loaded) {
  const info = loaded.byBranch[branch.id].info;
  const sheet = workbook.worksheets.add(branch.sheet);
  const totalCols = 1 + model.flopHeaders.length;
  const lastCol = colName(totalCols);
  const firstDataRow = 7;
  const lastDataRow = firstDataRow + handOrder.length - 1;
  styleBase(sheet, lastCol, lastDataRow);
  sheet.mergeCells(`A2:${lastCol}2`);
  sheet.mergeCells(`A3:${lastCol}3`);
  sheet.getRange("A2").values = [[branch.title]];
  sheet.getRange("A3").values = [[branchRule(info.labels)]];
  sheet.getRange(`A2:${lastCol}2`).format = {
    fill: colors.background,
    font: { name: "Aptos Display", size: 18, bold: true, color: colors.text },
    borders: { bottom: { style: "medium", color: colors.header } },
  };
  sheet.getRange(`A3:${lastCol}3`).format = {
    fill: colors.background,
    font: { name: "Aptos", size: 10, color: colors.subtle },
  };
  sheet.getRange(`A5:${lastCol}5`).values = [["Категория руки", ...model.flopHeaders]];
  sheet.getRange(`A6:${lastCol}6`).values = [[null, ...model.explanations]];
  sheet.getRange(`A5:${lastCol}5`).format = {
    fill: colors.header,
    font: { name: "Aptos", size: 9, bold: true, color: colors.white },
    horizontalAlignment: "center",
    verticalAlignment: "center",
    wrapText: true,
    borders: { preset: "all", style: "thin", color: colors.white },
  };
  sheet.getRange(`A6:${lastCol}6`).format = {
    fill: colors.header,
    font: { name: "Aptos", size: 8, italic: true, color: colors.white },
    horizontalAlignment: "center",
    verticalAlignment: "center",
    wrapText: true,
    borders: { preset: "all", style: "thin", color: colors.header },
  };
  const matrix = handOrder.map((hand) => {
    const record = loaded.byBranch[branch.id].records.get(hand);
    if (!record) throw new Error(`${model.key}/${branch.id}: missing hand row ${hand}`);
    return [hand, ...model.csvHeaders.map((header) => record[header])];
  });
  sheet.getRange(`A${firstDataRow}:${lastCol}${lastDataRow}`).values = matrix;
  sheet.getRange(`A${firstDataRow}:A${lastDataRow}`).format = {
    fill: colors.background,
    font: { name: "Aptos", size: 10, bold: true, color: colors.text },
    borders: { preset: "all", style: "thin", color: colors.border },
  };
  for (let row = firstDataRow; row <= lastDataRow; row += 1) {
    for (let col = 2; col <= totalCols; col += 1) {
      const value = sheet.getRange(`${colName(col)}${row}`).values[0][0];
      styleActionCell(sheet.getRange(`${colName(col)}${row}`), value);
    }
  }
  // Visual separators between made hands, unmade draw-capable hands and air.
  for (const row of [14, 16, 17]) {
    sheet.getRange(`A${row}:${lastCol}${row}`).format.borders = {
      bottom: { style: "medium", color: colors.divider },
    };
  }
  // Visual separators between the agreed final flop families.
  for (const offset of model.dividerAfter) {
    const col = colName(1 + offset);
    sheet.getRange(`${col}5:${col}${lastDataRow}`).format.borders = {
      right: { style: "medium", color: colors.divider },
    };
  }
  sheet.getRange(`A1:A${lastDataRow}`).format.columnWidth = 23;
  for (let col = 2; col <= totalCols; col += 1) {
    sheet.getRange(`${colName(col)}1:${colName(col)}${lastDataRow}`).format.columnWidth = 16;
  }
  sheet.getRange("5:5").format.rowHeight = 34;
  sheet.getRange("6:6").format.rowHeight = 30;
  sheet.getRange(`${firstDataRow}:${lastDataRow}`).format.rowHeight = 24;
  sheet.freezePanes.freezeRows(6);
  sheet.freezePanes.freezeColumns(1);
}

function addMethod(workbook, model) {
  const sheet = workbook.worksheets.add("Method");
  const lastRow = 21 + model.categoryRows.length;
  styleBase(sheet, "D", lastRow);
  sheet.mergeCells("A2:D2");
  sheet.getRange("A2").values = [["Методика"]];
  sheet.getRange("A2:D2").format = {
    fill: colors.background,
    font: { name: "Aptos Display", size: 20, bold: true, color: colors.text },
    borders: { bottom: { style: "medium", color: colors.section } },
  };
  sheet.getRange("A4:B4").values = [["Параметр", "Правило"]];
  sheet.getRange("A4:D4").format = {
    fill: colors.section,
    font: { name: "Aptos", size: 10, bold: true, color: colors.white },
    borders: { preset: "all", style: "thin", color: colors.borderLight },
  };
  const rows = [
    ["Флопы", model.methodFlops],
    ["Диапазоны", studyManifest.strategy_range_note],
    ["Частоты", "Равное среднее по concrete combo на флопе, затем равное среднее по реальным флопам категории"],
    ["Чистое действие", "Наибольшая средняя частота строго >65%"],
    ["Микс", "Иначе два наиболее частых действия, строго 50/50; первым указано более частое действие солвера"],
    ["Вес диапазона", "Combo с reach_probability >0 участвует независимо от величины reach"],
    ["EV-аудит", "Reach-weighted local regret против solved opponent; не adaptive exploitability. Обычное действие выбирают частоты; EV только отклоняет невыгодный BDFD-rule"],
    ["Категории рук", "8 made-категорий, OESD, Gutshot, 2 overcards + BDFD и Air"],
    ["Карманные пары", "Underpair: между top и middle; Weak pair: между middle и low; Low pocket pair: ниже low"],
    ["Приоритет классификации", "OESD > Gutshot > made hand > 2 overcards + BDFD > Air"],
    ["BDFD в ячейке", "Без BDFD fold >65%; с BDFD суммарный continue >65%, который упрощается до call; затем правило проходит EV safety audit"],
    ["Категории флопов", model.methodCategory],
    ["Роль исходной B13", "Только однозначное внутреннее разбиение 286 флопов на 10 итоговых групп"],
    ["JT9", "Исходная B13 = [J-8]x con; итоговая категория = [J-8]x con"],
  ];
  const methodEnd = 4 + rows.length;
  sheet.getRange(`A5:B${methodEnd}`).values = rows;
  sheet.getRange(`A5:B${methodEnd}`).format = {
    fill: colors.background,
    font: { name: "Aptos", size: 10, color: colors.text },
    borders: { preset: "all", style: "thin", color: colors.borderLight },
    wrapText: true,
  };
  const categoryHeaderRow = methodEnd + 3;
  sheet.getRange(`A${categoryHeaderRow}:D${categoryHeaderRow}`).values = [["Категория флопов", "Входящие B13 / определение", "Количество", "Пояснение"]];
  sheet.getRange(`A${categoryHeaderRow}:D${categoryHeaderRow}`).format = {
    fill: colors.section,
    font: { name: "Aptos", size: 10, bold: true, color: colors.white },
    borders: { preset: "all", style: "thin", color: colors.white },
  };
  const categoryEnd = categoryHeaderRow + model.categoryRows.length;
  sheet.getRange(`A${categoryHeaderRow + 1}:D${categoryEnd}`).values = model.categoryRows;
  sheet.getRange(`A${categoryHeaderRow + 1}:D${categoryEnd}`).format = {
    fill: colors.background,
    font: { name: "Aptos", size: 9, color: colors.text },
    borders: { preset: "all", style: "thin", color: colors.borderLight },
    wrapText: true,
  };
  sheet.getRange(`C${categoryHeaderRow + 1}:C${categoryEnd}`).format.numberFormat = "0";
  sheet.getRange(`A1:A${lastRow}`).format.columnWidth = 24;
  sheet.getRange(`B1:B${lastRow}`).format.columnWidth = 52;
  sheet.getRange(`C1:C${lastRow}`).format.columnWidth = 12;
  sheet.getRange(`D1:D${lastRow}`).format.columnWidth = 54;
  sheet.getRange("5:18").format.rowHeight = 42;
  sheet.getRange(`22:${lastRow}`).format.rowHeight = 30;
}

async function build(model) {
  const loaded = await readModel(model);
  const workbook = Workbook.create();
  addSummary(workbook, model, loaded);
  for (const branch of branchInfo) addStrategySheet(workbook, model, branch, loaded);
  addMethod(workbook, model);
  workbook.recalculate();

  const errorScan = await workbook.inspect({
    kind: "match",
    searchTerm: "#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A",
    options: { useRegex: true, maxResults: 100 },
    summary: "final formula error scan",
  });
  const errorMatches = errorScan.ndjson
    .split("\n")
    .filter((line) => line.trim())
    .map((line) => JSON.parse(line))
    .filter((item) => item.kind !== "notice");
  if (errorMatches.length) throw new Error(`Workbook error scan failed:\n${errorScan.ndjson}`);

  const outputPath = path.join(analysisRoot, model.filename);
  const blob = await SpreadsheetFile.exportXlsx(workbook);
  await blob.save(outputPath);
  return { workbook, outputPath };
}

await fs.mkdir(analysisRoot, { recursive: true });
for (const model of outputs) {
  const { workbook, outputPath } = await build(model);
  const previewDir = path.join(analysisRoot, ".preview", model.key);
  await fs.mkdir(previewDir, { recursive: true });
  for (const sheetName of ["Summary", ...branchInfo.map((branch) => branch.sheet), "Method"]) {
    const preview = await workbook.render({ sheetName, autoCrop: "all", scale: 1.2, format: "png" });
    await fs.writeFile(
      path.join(previewDir, `${sheetName.replaceAll(" ", "_").replaceAll("/", "-")}.png`),
      new Uint8Array(await preview.arrayBuffer()),
    );
  }
  console.log(outputPath);
}
