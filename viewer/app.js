const ACTIONS = {
  fold: { label: "Фолд", color: "var(--fold)" }, call: { label: "Колл", color: "var(--call)" },
  raise: { label: "Рейз", color: "var(--raise)" }, check: { label: "Чек", color: "var(--check)" },
  bet: { label: "Бет", color: "var(--bet)" }, donk: { label: "Донк", color: "var(--donk)" },
};
const RANKS = "AKQJT98765432".split("");
const SUITS = ["s", "h", "d", "c"];
const SUIT_SYMBOL = { s: "♠", h: "♥", d: "♦", c: "♣" };
const MADE_ORDER = ["Two pair+", "Overpair", "Top pair", "Underpair", "Second pair", "Weak pair", "Third pair", "Low pocket pair", "2 overcards", "A-high", "Air"];
const MADE_RU = {
  "Two pair+": "Две пары+", Overpair: "Оверпара", "Top pair": "Топ-пара",
  Underpair: "Карманка между 1-й и 2-й", "Second pair": "Вторая пара",
  "Weak pair": "Карманка между 2-й и 3-й", "Third pair": "Третья пара",
  "Low pocket pair": "Низкая карманка", "2 overcards": "Две оверкарты",
  "A-high": "Туз-хай", Air: "Воздух",
};
const DRAW_RU = { OESD: "OESD", Gutshot: "Гатшот", BDFD: "Бэкдор-флеш-дро", "No draw": "Без дро" };

const state = {
  catalog: null, study: null, node: null, view: "range",
  actionFilters: new Set(), madeFilters: new Set(), drawFilters: new Set(),
  selectedCell: null, selectedCombo: null,
};
const $ = (id) => document.getElementById(id);
const fmtPct = (value, digits = 1) => `${(value * 100).toFixed(digits)}%`;

async function getJSON(url) {
  const response = await fetch(url);
  const payload = await response.json();
  if (!response.ok) throw new Error(payload.error || `HTTP ${response.status}`);
  return payload;
}
function setLoading(active) { $("loading").classList.toggle("hidden", !active); }
function showError(message) {
  $("toast").textContent = message; $("toast").classList.remove("hidden");
  window.setTimeout(() => $("toast").classList.add("hidden"), 5000);
}
function option(value, label) {
  const element = document.createElement("option"); element.value = value; element.textContent = label; return element;
}
function currentStudy() { return state.catalog.studies.find((study) => study.slug === $("studySelect").value); }

function populateStudies() {
  const select = $("studySelect"); select.replaceChildren();
  state.catalog.studies.forEach((study) => select.append(option(study.slug, `${study.id} · ${study.name.replace(/^RNG\d+\s*/i, "")}`)));
  const preferred = state.catalog.studies.find((study) => study.id === "STU005") || state.catalog.studies[0];
  select.value = preferred.slug; populateStudyControls();
}
function populateStudyControls() {
  state.study = currentStudy();
  const branchSelect = $("branchSelect"); branchSelect.replaceChildren();
  state.study.branches.forEach((branch) => {
    branchSelect.append(option(branch.id, `${branch.history}  →  ${branch.actor}: ${branch.actionsText}`));
  });
  const boardList = $("boardList"); boardList.replaceChildren();
  state.study.boards.forEach((board) => boardList.append(option(board, board)));
  const preferredBranch = state.study.branches.find((branch) => branch.id.includes("AFTER_CBET")) || state.study.branches[0];
  branchSelect.value = preferredBranch.id;
  $("boardInput").value = state.study.boards.find((board) => /Q.\s+7.\s+2./i.test(board)) || state.study.boards[0];
  loadNode();
}
async function loadNode() {
  setLoading(true);
  try {
    const query = new URLSearchParams({ study: $("studySelect").value, branch: $("branchSelect").value, board: $("boardInput").value.trim() });
    state.node = await getJSON(`/api/node?${query}`); $("boardInput").value = state.node.board;
    state.actionFilters.clear(); state.madeFilters.clear(); state.drawFilters.clear();
    state.selectedCell = null; state.selectedCombo = null; renderAll();
  } catch (error) { showError(error.message); } finally { setLoading(false); }
}

function comboDraws(combo) {
  const values = []; if (combo.draw !== "none") values.push(combo.draw); if (combo.bdfd) values.push("BDFD");
  if (!values.length) values.push("No draw"); return values;
}
function categoryMatches(combo) {
  if (state.madeFilters.size && !state.madeFilters.has(combo.base)) return false;
  if (state.drawFilters.size && !comboDraws(combo).some((draw) => state.drawFilters.has(draw))) return false;
  return true;
}
function actionMass(combo) {
  if (!state.actionFilters.size) return 1;
  return [...state.actionFilters].reduce((sum, action) => sum + (combo.frequencies[action] || 0), 0);
}
function filteredWeight(combo) { return categoryMatches(combo) ? combo.reach * actionMass(combo) : 0; }
function renderAll() { renderHeader(); renderFilters(); renderRange(); renderSuits(); renderLegend(); renderDetail(); }

function renderHeader() {
  const node = state.node;
  $("nodeSummary").textContent = `${node.branch.actor} принимает решение · ${node.combos.length} конкретных комбинаций · экспорт ${state.study.run}`;
  $("lineLabel").textContent = `${node.branch.history} · ${node.branch.actionsText} · reach относительно ${node.baselineBranch}`;
  $("boardCards").replaceChildren(...node.board.split(/\s+/).map(cardElement));
}
function cardElement(card) {
  const span = document.createElement("span"); span.className = `card ${["h", "d"].includes(card[1].toLowerCase()) ? "red" : ""}`;
  span.textContent = `${card[0].toUpperCase()}${SUIT_SYMBOL[card[1].toLowerCase()]}`; return span;
}
function weightedStats(combos) {
  const totalReach = combos.reduce((sum, combo) => sum + combo.reach, 0);
  const actionTotals = Object.fromEntries(state.node.actions.map((action) => [action, 0]));
  combos.forEach((combo) => state.node.actions.forEach((action) => { actionTotals[action] += combo.reach * combo.frequencies[action]; }));
  return { totalReach, actionTotals };
}

function renderFilters() {
  const { totalReach, actionTotals } = weightedStats(state.node.combos);
  const actionHolder = $("actionFilters"); actionHolder.replaceChildren();
  state.node.actions.forEach((action) => actionHolder.append(filterButton(
    action, ACTIONS[action].label, actionTotals[action] / totalReach, state.actionFilters, ACTIONS[action].color, renderAll,
  )));
  const madeHolder = $("madeFilters"); madeHolder.replaceChildren();
  MADE_ORDER.filter((name) => state.node.combos.some((combo) => combo.base === name)).forEach((name) => {
    const weight = state.node.combos.filter((combo) => combo.base === name).reduce((sum, combo) => sum + combo.reach * actionMass(combo), 0);
    madeHolder.append(filterButton(name, MADE_RU[name], weight / totalReach, state.madeFilters, null, renderAll));
  });
  const drawHolder = $("drawFilters"); drawHolder.replaceChildren();
  ["OESD", "Gutshot", "BDFD", "No draw"].forEach((name) => {
    const weight = state.node.combos.filter((combo) => comboDraws(combo).includes(name)).reduce((sum, combo) => sum + combo.reach * actionMass(combo), 0);
    drawHolder.append(filterButton(name, DRAW_RU[name], weight / totalReach, state.drawFilters, null, renderAll));
  });
}
function filterButton(key, label, value, selectedSet, color, onChange) {
  const button = document.createElement("button"); button.type = "button";
  button.className = `filter-button ${selectedSet.has(key) ? "active" : ""}`;
  button.innerHTML = `<i class="filter-dot"></i><span class="filter-name"></span><span class="filter-value"></span>`;
  button.querySelector(".filter-dot").style.background = color || "#718096";
  button.querySelector(".filter-name").textContent = label; button.querySelector(".filter-value").textContent = fmtPct(value);
  button.addEventListener("click", () => {
    selectedSet.has(key) ? selectedSet.delete(key) : selectedSet.add(key);
    state.selectedCell = null; state.selectedCombo = null; onChange();
  });
  return button;
}

function rangeGroups() {
  const groups = new Map(); state.node.combos.forEach((combo) => {
    if (!groups.has(combo.label)) groups.set(combo.label, []); groups.get(combo.label).push(combo);
  }); return groups;
}
function aggregateCell(combos) {
  const allBaseline = combos.reduce((sum, combo) => sum + combo.baselineReach, 0);
  const matching = combos.filter(categoryMatches);
  const reach = matching.reduce((sum, combo) => sum + combo.reach * actionMass(combo), 0);
  const actionTotals = Object.fromEntries(state.node.actions.map((action) => [action, 0]));
  matching.forEach((combo) => state.node.actions.forEach((action) => {
    if (!state.actionFilters.size || state.actionFilters.has(action)) actionTotals[action] += combo.reach * combo.frequencies[action];
  }));
  return { reach, height: allBaseline ? Math.min(1, reach / allBaseline) : 0, actionTotals };
}
function addSlices(fill, totals, total) {
  state.node.actions.forEach((action) => {
    const amount = totals[action] || 0; if (amount <= 0 || total <= 0) return;
    const slice = document.createElement("i"); slice.className = "action-slice";
    slice.style.width = `${(amount / total) * 100}%`; slice.style.background = ACTIONS[action].color; fill.append(slice);
  });
}
function renderRange() {
  const holder = $("rangeView"); holder.replaceChildren(); const groups = rangeGroups();
  for (let row = 0; row < 13; row += 1) for (let col = 0; col < 13; col += 1) {
    const label = row === col ? RANKS[row] + RANKS[col] : row < col ? RANKS[row] + RANKS[col] + "s" : RANKS[col] + RANKS[row] + "o";
    const combos = groups.get(label) || []; const agg = aggregateCell(combos); const cell = document.createElement("button");
    cell.type = "button"; cell.className = `range-cell ${combos.length ? "" : "empty"} ${state.selectedCell === label ? "selected" : ""}`;
    cell.innerHTML = `<span class="cell-fill"></span><span class="cell-label"></span><small class="cell-sub"></small>`;
    cell.querySelector(".cell-label").textContent = label;
    cell.querySelector(".cell-sub").textContent = combos.length && agg.height > 0 ? fmtPct(agg.height, 0) : "";
    const fill = cell.querySelector(".cell-fill"); fill.style.height = `${agg.height * 100}%`; addSlices(fill, agg.actionTotals, agg.reach);
    if (combos.length) {
      cell.title = `${label}: дошло ${fmtPct(agg.height)} · ${combos.length} комбинаций в экспорте`;
      cell.addEventListener("click", () => {
        state.selectedCell = state.selectedCell === label ? null : label; state.selectedCombo = null;
        renderRange(); renderSuits(); renderDetail();
      });
    }
    holder.append(cell);
  }
  holder.classList.toggle("hidden", state.view !== "range");
}

function cardDeck() { return RANKS.flatMap((rank) => SUITS.map((suit) => `${rank}${suit}`)); }
function renderSuits() {
  const holder = $("suitsGrid"); holder.replaceChildren(); const deck = cardDeck(); holder.append(document.createElement("span"));
  deck.forEach((card) => holder.append(axisCard(card, false)));
  const combos = new Map(state.node.combos.map((combo) => [[...combo.cards].sort().join(""), combo]));
  deck.forEach((rowCard, row) => {
    holder.append(axisCard(rowCard, true));
    deck.forEach((colCard, col) => {
      const cell = document.createElement("span");
      if (col >= row) { cell.className = "suit-cell blocked"; holder.append(cell); return; }
      const combo = combos.get([rowCard, colCard].sort().join(""));
      cell.className = `suit-cell ${combo ? "" : "blocked"} ${state.selectedCombo === combo?.combo ? "selected" : ""}`;
      if (combo) {
        const mass = categoryMatches(combo) ? actionMass(combo) : 0;
        const reachHeight = combo.baselineReach ? Math.min(1, combo.reach * mass / combo.baselineReach) : 0;
        const fill = document.createElement("span"); fill.className = "cell-fill"; fill.style.height = `${reachHeight * 100}%`;
        const totals = Object.fromEntries(state.node.actions.map((action) => [action, (!state.actionFilters.size || state.actionFilters.has(action)) ? combo.frequencies[action] : 0]));
        addSlices(fill, totals, Object.values(totals).reduce((a, b) => a + b, 0)); cell.append(fill);
        cell.title = `${prettyCombo(combo.combo)} · ${combo.category} · дошло ${fmtPct(combo.reachFraction)}`;
        cell.addEventListener("click", () => {
          state.selectedCombo = state.selectedCombo === combo.combo ? null : combo.combo; state.selectedCell = combo.label;
          renderRange(); renderSuits(); renderDetail();
        });
      }
      holder.append(cell);
    });
  });
  $("suitsView").classList.toggle("hidden", state.view !== "suits");
}
function axisCard(card, left) {
  const span = document.createElement("span"); span.className = `axis-card ${left ? "left" : ""} ${["h", "d"].includes(card[1]) ? "red" : ""}`;
  span.textContent = `${card[0]}${SUIT_SYMBOL[card[1]]}`; return span;
}
function renderLegend() {
  const holder = $("actionLegend"); holder.replaceChildren(); const combos = state.node.combos.filter(categoryMatches);
  const denominator = combos.reduce((sum, combo) => sum + combo.reach * actionMass(combo), 0);
  state.node.actions.forEach((action) => {
    if (state.actionFilters.size && !state.actionFilters.has(action)) return;
    const amount = combos.reduce((sum, combo) => sum + combo.reach * combo.frequencies[action], 0);
    const item = document.createElement("div"); item.className = "legend-action"; item.style.background = ACTIONS[action].color;
    item.style.flex = Math.max(amount, denominator * 0.08);
    item.innerHTML = `<strong>${ACTIONS[action].label}</strong><span>${fmtPct(denominator ? amount / denominator : 0)} · weight ${amount.toFixed(1)}</span>`;
    holder.append(item);
  });
}
function prettyCombo(combo) {
  return combo.match(/.{2}/g).map((card) => `${card[0].toUpperCase()}${SUIT_SYMBOL[card[1].toLowerCase()]}`).join("");
}
function renderDetail() {
  const panel = $("detailPanel"); let combos = []; let title = "Выбранная рука";
  if (state.selectedCombo) { combos = state.node.combos.filter((combo) => combo.combo === state.selectedCombo); title = prettyCombo(state.selectedCombo); }
  else if (state.selectedCell) { combos = state.node.combos.filter((combo) => combo.label === state.selectedCell && categoryMatches(combo) && actionMass(combo) > 0); title = state.selectedCell; }
  if (!combos.length) { panel.innerHTML = `<h2>Выбранная рука</h2><p class="muted">Нажми на ячейку матрицы.</p>`; return; }
  combos.sort((a, b) => filteredWeight(b) - filteredWeight(a)); const agg = aggregateCell(combos); panel.replaceChildren();
  const heading = document.createElement("div"); heading.className = "detail-title"; heading.innerHTML = `<strong></strong><span></span>`;
  heading.querySelector("strong").textContent = title; heading.querySelector("span").textContent = `${combos.length} комб. · reach ${fmtPct(agg.height)}`; panel.append(heading);
  const list = document.createElement("div"); list.className = "combo-list";
  combos.forEach((combo) => {
    const row = document.createElement("div"); row.className = "combo-row"; const label = document.createElement("span");
    label.textContent = prettyCombo(combo.combo); label.title = combo.category;
    const bar = document.createElement("span"); bar.className = "mini-bar";
    const totals = Object.fromEntries(state.node.actions.map((action) => [action, (!state.actionFilters.size || state.actionFilters.has(action)) ? combo.frequencies[action] : 0]));
    addSlices(bar, totals, Object.values(totals).reduce((a, b) => a + b, 0));
    const reach = document.createElement("span"); reach.className = "combo-reach"; reach.textContent = fmtPct(combo.reachFraction, 0);
    row.append(label, bar, reach); list.append(row);
  });
  panel.append(list);
}

function bindEvents() {
  $("studySelect").addEventListener("change", populateStudyControls); $("branchSelect").addEventListener("change", loadNode);
  $("loadBoard").addEventListener("click", loadNode); $("boardInput").addEventListener("keydown", (event) => { if (event.key === "Enter") loadNode(); });
  $("clearFilters").addEventListener("click", () => {
    state.actionFilters.clear(); state.madeFilters.clear(); state.drawFilters.clear(); state.selectedCell = null; state.selectedCombo = null; renderAll();
  });
  document.querySelectorAll("[data-view]").forEach((button) => button.addEventListener("click", () => {
    state.view = button.dataset.view;
    document.querySelectorAll("[data-view]").forEach((item) => item.classList.toggle("active", item === button));
    $("rangeView").classList.toggle("hidden", state.view !== "range"); $("suitsView").classList.toggle("hidden", state.view !== "suits");
  }));
}
async function init() {
  bindEvents(); setLoading(true);
  try {
    state.catalog = await getJSON("/api/catalog"); if (!state.catalog.studies.length) throw new Error("Не найдено ни одного combos.csv"); populateStudies();
  } catch (error) { showError(error.message); } finally { setLoading(false); }
}
init();
