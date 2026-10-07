const ACTIONS = {
  fold: { label: "Фолд", color: "var(--fold)" }, call: { label: "Колл", color: "var(--call)" },
  raise: { label: "Рейз", color: "var(--raise)" }, check: { label: "Чек", color: "var(--check)" },
  bet: { label: "Бет", color: "var(--bet)" }, donk: { label: "Донк", color: "var(--donk)" },
};
const RANKS = "AKQJT98765432".split("");
const SUITS = ["c", "s", "h", "d"];
const POSITION_ORDER = ["UTG", "HJ", "CO", "BTN", "SB", "BB"];
const SUIT_SYMBOL = { s: "♠", h: "♥", d: "♦", c: "♣" };
const MADE_ORDER = ["Two pair+", "Overpair", "Top pair", "Underpair", "Second pair", "Weak pair", "Third pair", "Low pocket pair", "2 overcards", "A-high", "Air"];
const MADE_RU = {
  "Two pair+": "Две пары+", Overpair: "Оверпара", "Top pair": "Топ-пара",
  Underpair: "Андерпара", "Second pair": "Вторая пара",
  "Weak pair": "Weak pair", "Third pair": "Третья пара",
  "Low pocket pair": "Low pocket", "2 overcards": "Две оверкарты",
  "A-high": "Туз-хай", Air: "Воздух",
};
const DRAW_RU = { OESD: "OESD", Gutshot: "Гатшот", BDFD: "БДФД", "No draw": "Без дро" };

const state = {
  catalog: null, study: null, node: null, view: "range", actor: "BB", branchesByActor: {},
  actionFilters: new Set(), madeFilters: new Set(), drawFilters: new Set(),
  madePreview: null, drawPreview: null,
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
  const boardList = $("boardList"); boardList.replaceChildren();
  state.study.boards.forEach((board) => boardList.append(option(board, board)));
  const actors = [...new Set(state.study.branches.map((branch) => branch.actor))].sort((left, right) => {
    const leftIndex = POSITION_ORDER.indexOf(left); const rightIndex = POSITION_ORDER.indexOf(right);
    return (leftIndex < 0 ? POSITION_ORDER.length : leftIndex) - (rightIndex < 0 ? POSITION_ORDER.length : rightIndex) || left.localeCompare(right);
  });
  if (!actors.includes(state.actor)) state.actor = actors[0];
  renderActorTabs(actors);
  populateActorBranches();
  $("boardInput").value = state.study.boards.find((board) => /Q.\s+7.\s+2./i.test(board)) || state.study.boards[0];
  loadNode();
}
function renderActorTabs(actors) {
  const holder = $("actorTabs"); holder.replaceChildren();
  actors.forEach((actor) => {
    const button = document.createElement("button"); button.type = "button"; button.role = "tab";
    button.textContent = actor; button.className = actor === state.actor ? "active" : "";
    button.setAttribute("aria-selected", String(actor === state.actor));
    button.addEventListener("click", () => {
      if (state.actor === actor) return;
      state.actor = actor; renderActorTabs(actors); populateActorBranches(); loadNode();
    });
    holder.append(button);
  });
}
function preferredBranchForActor(branches) {
  const saved = state.branchesByActor[state.actor];
  if (saved && branches.some((branch) => branch.id === saved)) return saved;
  const preferred = state.actor === "BB"
    ? branches.find((branch) => branch.id.includes("AFTER_CBET")) || branches.find((branch) => branch.id.includes("FIRST"))
    : branches.find((branch) => /AFTER_CHECK$/.test(branch.id)) || branches.find((branch) => branch.id.includes("AFTER_DONK"));
  return (preferred || branches[0]).id;
}
function populateActorBranches() {
  const branches = state.study.branches.filter((branch) => branch.actor === state.actor);
  const select = $("branchSelect"); select.replaceChildren();
  branches.forEach((branch) => select.append(option(branch.id, `${branch.history}  →  ${branch.actionsText}`)));
  select.value = preferredBranchForActor(branches); state.branchesByActor[state.actor] = select.value;
}
async function loadNode() {
  setLoading(true);
  try {
    const query = new URLSearchParams({ study: $("studySelect").value, branch: $("branchSelect").value, board: $("boardInput").value.trim() });
    state.node = await getJSON(`/api/node?${query}`); $("boardInput").value = state.node.board;
    state.actionFilters.clear(); state.madeFilters.clear(); state.drawFilters.clear();
    state.madePreview = null; state.drawPreview = null;
    state.selectedCell = null; state.selectedCombo = null; renderAll();
  } catch (error) { showError(error.message); } finally { setLoading(false); }
}

function comboDraws(combo) {
  const values = []; if (combo.draw !== "none") values.push(combo.draw); if (combo.bdfd) values.push("BDFD");
  if (!values.length) values.push("No draw"); return values;
}
function categoryMatches(combo) {
  if (!state.madePreview && state.madeFilters.size && !state.madeFilters.has(combo.base)) return false;
  if (!state.drawPreview && state.drawFilters.size && !comboDraws(combo).some((draw) => state.drawFilters.has(draw))) return false;
  return true;
}
function previewActive() { return Boolean(state.madePreview || state.drawPreview); }
function previewMatches(combo) {
  if (state.madePreview && combo.base !== state.madePreview) return false;
  if (state.drawPreview && !comboDraws(combo).includes(state.drawPreview)) return false;
  return true;
}
function previewRatio(combos) {
  if (!previewActive()) return 1;
  const eligible = combos.filter(categoryMatches);
  const total = eligible.reduce((sum, combo) => sum + combo.reach * actionMass(combo), 0);
  const highlighted = eligible.filter(previewMatches).reduce((sum, combo) => sum + combo.reach * actionMass(combo), 0);
  return total ? highlighted / total : 0;
}
function actionMass(combo) {
  if (!state.actionFilters.size) return 1;
  return [...state.actionFilters].reduce((sum, action) => sum + (combo.frequencies[action] || 0), 0);
}
function filteredWeight(combo) { return categoryMatches(combo) ? combo.reach * actionMass(combo) : 0; }
function renderAll() { renderHeader(); renderFilters(); renderRange(); renderSuits(); renderLegend(); renderDetail(); }

function previewCategory(group, name, active) {
  const stateKey = group === "made" ? "madePreview" : "drawPreview";
  const holder = $(group === "made" ? "madeFilters" : "drawFilters");
  const selected = group === "made" ? state.madeFilters : state.drawFilters;
  state[stateKey] = active ? name : null;
  holder.querySelectorAll(".filter-button").forEach((button) => {
    const isPreview = active && button.dataset.filterKey === name;
    button.classList.toggle("preview", isPreview);
    button.classList.toggle("active", active ? isPreview : selected.has(button.dataset.filterKey));
    button.classList.toggle("dim", active && !isPreview);
  });
  renderRange(); renderSuits(); renderDetail();
}

function bindCategoryPreview(button, group, name) {
  button.dataset.filterKey = name;
  button.addEventListener("pointerenter", () => previewCategory(group, name, true));
  button.addEventListener("pointerleave", () => {
    const stateKey = group === "made" ? "madePreview" : "drawPreview";
    if (state[stateKey] === name) previewCategory(group, name, false);
  });
}

function renderHeader() {
  const node = state.node;
  const ownPath = node.actorPath.map((step) => step.label).join(" → ");
  const heightText = ownPath
    ? `префлоп-вес × действия ${node.branch.actor}: ${ownPath}`
    : `префлоп-вес ${node.branch.actor}`;
  $("nodeSummary").textContent = `Диапазон ${node.branch.actor} · ${node.combos.length} конкретных комбинаций · экспорт ${state.study.run}`;
  $("rangeOwner").textContent = `ДИАПАЗОН ${node.branch.actor}`;
  $("lineLabel").textContent = `${node.branch.history} · ${node.branch.actionsText} · высота: ${heightText}`;
  $("reachLegend").lastChild.textContent = ` Высота — ${heightText}`;
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
  state.node.actions.forEach((action) => {
    const button = filterButton(action, ACTIONS[action].label, actionTotals[action] / totalReach, state.actionFilters, ACTIONS[action].color, renderAll);
    const shown = !state.actionFilters.size || state.actionFilters.has(action);
    button.classList.toggle("active", shown); button.classList.toggle("dim", !shown);
    actionHolder.append(button);
  });
  const madeHolder = $("madeFilters"); madeHolder.replaceChildren();
  MADE_ORDER.filter((name) => state.node.combos.some((combo) => combo.base === name)).forEach((name) => {
    const weight = state.node.combos.filter((combo) => combo.base === name).reduce((sum, combo) => sum + combo.reach * actionMass(combo), 0);
    const button = filterButton(name, MADE_RU[name], weight / totalReach, state.madeFilters, null, () => {
      state.madePreview = null; renderAll();
    });
    bindCategoryPreview(button, "made", name); madeHolder.append(button);
  });
  const drawHolder = $("drawFilters"); drawHolder.replaceChildren();
  ["OESD", "Gutshot", "BDFD", "No draw"].forEach((name) => {
    const weight = state.node.combos.filter((combo) => comboDraws(combo).includes(name)).reduce((sum, combo) => sum + combo.reach * actionMass(combo), 0);
    const button = filterButton(name, DRAW_RU[name], weight / totalReach, state.drawFilters, null, () => {
      state.drawPreview = null; renderAll();
    });
    bindCategoryPreview(button, "draw", name); drawHolder.append(button);
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
  const matching = combos.filter(categoryMatches);
  const reach = matching.reduce((sum, combo) => sum + combo.reach * actionMass(combo), 0);
  const actionTotals = Object.fromEntries(state.node.actions.map((action) => [action, 0]));
  matching.forEach((combo) => state.node.actions.forEach((action) => {
    if (!state.actionFilters.size || state.actionFilters.has(action)) actionTotals[action] += combo.reach * combo.frequencies[action];
  }));
  return { reach, height: combos.length ? Math.min(1, reach / combos.length) : 0, actionTotals };
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
  const boardRanks = new Set(state.node.board.split(/\s+/).map((card) => card[0].toUpperCase()));
  for (let row = 0; row < 13; row += 1) for (let col = 0; col < 13; col += 1) {
    const label = row === col ? RANKS[row] + RANKS[col] : row < col ? RANKS[row] + RANKS[col] + "s" : RANKS[col] + RANKS[row] + "o";
    const combos = groups.get(label) || []; const agg = aggregateCell(combos); const cell = document.createElement("button");
    const boardBlocked = [...boardRanks].some((rank) => label.includes(rank));
    const emphasis = previewRatio(combos); const previewDim = previewActive() && emphasis < 0.999;
    cell.type = "button"; cell.className = `range-cell ${previewDim ? "preview-dim" : ""} ${boardBlocked ? "board-blocked" : ""} ${combos.length ? "" : "empty"} ${state.selectedCell === label ? "selected" : ""}`;
    if (previewDim) cell.style.setProperty("--preview-opacity", String(0.28 + 0.72 * emphasis));
    cell.innerHTML = `<span class="cell-fill"></span><span class="cell-label"></span>`;
    cell.querySelector(".cell-label").textContent = label;
    const fill = cell.querySelector(".cell-fill"); fill.style.height = `${agg.height * 100}%`; addSlices(fill, agg.actionTotals, agg.reach);
    if (combos.length) {
      cell.title = `${label}: осталось ${fmtPct(agg.height)} · ${combos.length} комбинаций в экспорте`;
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
function suitGridClasses(row, col) {
  const classes = [];
  if (row % 4 === 0) classes.push("rank-top");
  if (row % 4 === 3) classes.push("rank-bottom");
  if (col % 4 === 0) classes.push("rank-left");
  if (col % 4 === 3) classes.push("rank-right");
  return classes.join(" ");
}
function isPokerMatrixSlot(row, col) {
  const rowRank = Math.floor(row / 4); const colRank = Math.floor(col / 4);
  const rowSuit = row % 4; const colSuit = col % 4;
  if (rowRank === colRank) return rowSuit < colSuit;
  if (rowRank < colRank) return rowSuit === colSuit;
  return rowSuit !== colSuit;
}
function renderSuits() {
  const holder = $("suitsGrid"); holder.replaceChildren(); const deck = cardDeck(); holder.append(document.createElement("span"));
  const boardCards = new Set(state.node.board.split(/\s+/).map((card) => `${card[0].toUpperCase()}${card[1].toLowerCase()}`));
  deck.forEach((card, index) => holder.append(axisCard(card, index, false)));
  const combos = new Map(state.node.combos.map((combo) => [[...combo.cards].sort().join(""), combo]));
  deck.forEach((rowCard, row) => {
    holder.append(axisCard(rowCard, row, true));
    deck.forEach((colCard, col) => {
      const cell = document.createElement("span");
      const validSlot = isPokerMatrixSlot(row, col);
      const flopCardBlocked = boardCards.has(rowCard) || boardCards.has(colCard);
      const combo = validSlot ? combos.get([rowCard, colCard].sort().join("")) : null;
      const previewDim = combo && previewActive() && !previewMatches(combo);
      cell.className = `suit-cell ${previewDim ? "preview-dim" : ""} ${suitGridClasses(row, col)} ${flopCardBlocked ? "flop-card-blocked" : ""} ${validSlot ? "" : "invalid"} ${combo ? "" : "blocked"} ${state.selectedCombo === combo?.combo ? "selected" : ""}`;
      if (combo) {
        const mass = categoryMatches(combo) ? actionMass(combo) : 0;
        const reachHeight = Math.min(1, combo.reach * mass);
        const fill = document.createElement("span"); fill.className = "cell-fill"; fill.style.height = `${reachHeight * 100}%`;
        const totals = Object.fromEntries(state.node.actions.map((action) => [action, (!state.actionFilters.size || state.actionFilters.has(action)) ? combo.frequencies[action] : 0]));
        addSlices(fill, totals, Object.values(totals).reduce((a, b) => a + b, 0)); cell.append(fill);
        cell.title = `${prettyCombo(combo.combo)} · ${combo.category} · осталось ${fmtPct(combo.reachFraction)}`;
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
function axisCard(card, index, left) {
  const startsRank = index % 4 === 0;
  const span = document.createElement("span");
  span.className = `axis-card ${left ? "left" : ""} ${startsRank ? "rank-start" : ""} ${["h", "d"].includes(card[1]) ? "red" : ""}`;
  span.textContent = `${startsRank ? card[0] : ""}${SUIT_SYMBOL[card[1]]}`; return span;
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
  return combo.match(/.{2}/g)
    .sort((first, second) => RANKS.indexOf(first[0].toUpperCase()) - RANKS.indexOf(second[0].toUpperCase()) || SUITS.indexOf(first[1].toLowerCase()) - SUITS.indexOf(second[1].toLowerCase()))
    .map((card) => `${card[0].toUpperCase()}${SUIT_SYMBOL[card[1].toLowerCase()]}`)
    .join("");
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
  $("studySelect").addEventListener("change", populateStudyControls);
  $("branchSelect").addEventListener("change", () => {
    state.branchesByActor[state.actor] = $("branchSelect").value; loadNode();
  });
  $("loadBoard").addEventListener("click", loadNode); $("boardInput").addEventListener("keydown", (event) => { if (event.key === "Enter") loadNode(); });
  $("clearFilters").addEventListener("click", () => {
    state.actionFilters.clear(); state.madeFilters.clear(); state.drawFilters.clear(); state.madePreview = null; state.drawPreview = null;
    state.selectedCell = null; state.selectedCombo = null; renderAll();
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
