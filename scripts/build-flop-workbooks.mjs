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
    key: "strategy-13",
    filename: `${studyCode}_simplified_flop_strategy.xlsx`,
    subtitle: "11 категорий рук × 13 узких категорий флопов B13. Чистое действие или строгий микс 50/50.",
    flopHeaders: [
      "ABB (6)", "A[K/Q]x (16)", "A[J-T][9-5] (10)", "A[J-T][4-2] (6)",
      "A[9-7]x (18)", "A[6-2]x (10)", "BBB (4)", "BBx (47)",
      "K/Qx dis (42)", "K/Qx con (14)", "[J-8]x dis (67)",
      "[J-8]x con (26)", "[7-4]x (20)",
    ],
    csvHeaders: [
      "ABB", "A[K/Q]x", "A[J-T][9-5]", "A[J-T][4-2]", "A[9-7]x", "A[6-2]x",
      "BBB", "BBx", "K/Qx dis", "K/Qx con", "[J-8]x dis", "[J-8]x con", "[7-4]x",
    ],
    explanations: [
      "A + 2×B", "A + K/Q + ≤9", "A + J/T + 9…5", "A + J/T + 4…2",
      "A + 9/8/7 + x", "A + 6…2 + x", "3×B без A", "2×B + ≤9",
      "K/Q; low gap >1", "K/Q; low gap =1", "J…8; low gap >1",
      "J…8; low gap =1", "top ≤7",
    ],
    dividerAfter: [2, 4, 6, 8, 10, 11, 12, 13],
    methodFlops: "286 canonical unpaired rainbow flops, B13: 13 взаимоисключающих категорий",
    methodCategory: "B13 — итоговые категории этой таблицы",
    categoryRows: [
      ["ABB", "A + две broadway-карты", 6, "B = T/J/Q/K; A отдельно"],
      ["A[K/Q]x", "A + K/Q + карта 9 и ниже", 16, "ABB исключён"],
      ["A[J-T][9-5]", "A + J/T + карта 9…5", 10, ""],
      ["A[J-T][4-2]", "A + J/T + карта 4…2", 6, ""],
      ["A[9-7]x", "A + 9/8/7 + более низкая", 18, ""],
      ["A[6-2]x", "A + 6…3 + более низкая", 10, ""],
      ["BBB", "Без A; три broadway-карты", 4, ""],
      ["BBx", "Без A; две broadway + карта ≤9", 47, "JT9 исключён"],
      ["K/Qx dis", "Старшая K/Q; lower gap >1", 42, "Не BBx"],
      ["K/Qx con", "Старшая K/Q; lower gap =1", 14, "Не BBx"],
      ["[J-8]x dis", "Старшая J/T/9/8; lower gap >1", 67, ""],
      ["[J-8]x con", "Старшая J/T/9/8; lower gap =1", 26, "Включает JT9"],
      ["[7-4]x", "Старшая карта 7 или ниже", 20, ""],
    ],
  },
  {
    key: "strategy-8",
    filename: `${studyCode}_strategy_8_categories.xlsx`,
    subtitle: "11 категорий рук × 8 категорий флопов. Чистое действие или строгий микс 50/50.",
    flopHeaders: [
      "A-high high (22)", "A-high medium (16)", "A-high low (28)", "Broadway (51)",
      "K/Q-high (56)", "Middle dry (67)", "Middle connected (26)", "Low (20)",
    ],
    csvHeaders: [
      "A-high high", "A-high medium", "A-high low", "Broadway", "K/Q-high",
      "Middle dry", "Middle connected", "Low",
    ],
    explanations: [
      "ABB A[K/Q]x", "A[J-T]x", "A[9-2]x", "BBB BBx", "K/Qx",
      "[J-8]x dis", "[J-8]x con", "[7-4]x",
    ],
    dividerAfter: [3, 4, 5, 6, 7, 8],
    methodFlops: "286 canonical unpaired rainbow flops, 8 итоговых категорий",
    methodCategory: "Восемь групп — итоговые категории; B13 только детерминированно задаёт их состав",
    categoryRows: [
      ["A-high high", "ABB (6) + A[K/Q]x (16)", 22, "A с двумя broadway или с K/Q и младшей картой"],
      ["A-high medium", "A[J-T][9-5] (10) + A[J-T][4-2] (6)", 16, "A с J/T"],
      ["A-high low", "A[9-7]x (18) + A[6-2]x (10)", 28, "A со средней картой 9 или ниже"],
      ["Broadway", "BBB (4) + BBx (47)", 51, "Без A; минимум две broadway-карты"],
      ["K/Q-high", "K/Qx dis (42) + K/Qx con (14)", 56, "Старшая K/Q, но не BBx"],
      ["Middle dry", "[J-8]x dis (67)", 67, "Старшая J/T/9/8; две младшие не соседние"],
      ["Middle connected", "[J-8]x con (26)", 26, "Старшая J/T/9/8; две младшие соседние; включает JT9"],
      ["Low", "[7-4]x (20)", 20, "Старшая карта 7 или ниже"],
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
  "Two pair+", "Overpair", "Top pair", "Underpair", "Second pair", "Third pair",
  "Weak pair", "OESD", "Gutshot", "2 overcards + BDFD", "Air",
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
  return `${explanation}. Код через / — ровно 50/50. Bet и donk = 50% банка.`;
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
  else if (value === "C") fill = colors.c;
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
  styleBase(sheet, lastCol, 22);
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
    "Loss в узле, bb", "Loss от root, bb", "Добавка к B13, bb",
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
      s.mean_local_loss_bb, s.root_loss_bb,
      s.incremental_root_loss_vs_B13_bb ?? 0,
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
  sheet.getRange(`F6:H${lastBranchRow}`).format.numberFormat = "0.000000";
  sheet.getRange(`I6:J${lastBranchRow}`).format.numberFormat = "0";

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
    ["X/B, F/C и т. п.", "Два действия", "жёлтый", "строго 50/50"],
    ["—", "Нет категории", "серый", "в диапазоне/классе отсутствует"],
  ];
  sheet.getRange("A14:D21").values = legend;
  sheet.getRange("A14:D21").format = {
    fill: colors.background,
    font: { name: "Aptos", size: 10, color: colors.text },
    borders: { preset: "all", style: "thin", color: colors.borderLight },
  };
  sheet.getRange("F14:J18").values = [
    [model.methodCategory, null, null, null, null],
    ["Каждый реальный флоп внутри итоговой категории получает одинаковый вес.", null, null, null, null],
    ["11 категорий рук: 7 made, OESD, Gutshot, 2 overcards + BDFD и Air.", null, null, null, null],
    ["Все значения через / означают только микс 50/50.", null, null, null, null],
    ["EV используется для аудита потерь, но не выбирает действие.", null, null, null, null],
  ];
  sheet.getRange("F14:J18").format = {
    fill: colors.background,
    font: { name: "Aptos", size: 10, color: colors.text },
    wrapText: true,
  };
  sheet.getRange("A1:A22").format.columnWidth = 27;
  sheet.getRange("B1:B22").format.columnWidth = 11;
  sheet.getRange("C1:C22").format.columnWidth = 12;
  sheet.getRange("D1:E22").format.columnWidth = 23;
  sheet.getRange("F1:H22").format.columnWidth = 16;
  sheet.getRange("I1:J22").format.columnWidth = 13;
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
  for (const row of [13, 15, 16]) {
    sheet.getRange(`A${row}:${lastCol}${row}`).format.borders = {
      bottom: { style: "medium", color: colors.divider },
    };
  }
  // Visual separators between the agreed broader flop families on the B13 sheet.
  for (const offset of model.dividerAfter) {
    const col = colName(1 + offset);
    sheet.getRange(`${col}5:${col}${lastDataRow}`).format.borders = {
      right: { style: "medium", color: colors.divider },
    };
  }
  sheet.getRange(`A1:A${lastDataRow}`).format.columnWidth = 23;
  for (let col = 2; col <= totalCols; col += 1) {
    sheet.getRange(`${colName(col)}1:${colName(col)}${lastDataRow}`).format.columnWidth = model.key === "strategy-13" ? 12 : 16;
  }
  sheet.getRange("5:5").format.rowHeight = 34;
  sheet.getRange("6:6").format.rowHeight = 30;
  sheet.getRange(`${firstDataRow}:${lastDataRow}`).format.rowHeight = 24;
  sheet.freezePanes.freezeRows(6);
  sheet.freezePanes.freezeColumns(1);
}

function addMethod(workbook, model) {
  const sheet = workbook.worksheets.add("Method");
  const lastRow = 20 + model.categoryRows.length;
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
    ["EV-аудит", "Reach-weighted local regret против solved opponent; не adaptive exploitability"],
    ["Категории рук", "7 made-категорий; затем OESD; Gutshot; 2 overcards + BDFD; Air"],
    ["Приоритет неготовых", "OESD > Gutshot > 2 overcards + BDFD > Air; BDFD без двух оверкарт уходит в Air"],
    ["Категории флопов", model.methodCategory],
    ["Роль исходной B13", model.key === "strategy-8" ? "Только детерминированное описание состава новых групп" : "Итоговые столбцы стратегии"],
    ["JT9", "Исходная B13 = [J-8]x con; в 8-групповой таблице = Middle connected"],
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
  sheet.getRange(`5:${lastRow}`).format.rowHeight = 27;
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
