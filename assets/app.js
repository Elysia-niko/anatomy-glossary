const data = window.ANATOMY_GLOSSARY;

const els = {
  metaLine: document.getElementById("metaLine"),
  searchInput: document.getElementById("searchInput"),
  chapterFilter: document.getElementById("chapterFilter"),
  categoryFilter: document.getElementById("categoryFilter"),
  confidenceFilter: document.getElementById("confidenceFilter"),
  figureOnly: document.getElementById("figureOnly"),
  starOnly: document.getElementById("starOnly"),
  resultCount: document.getElementById("resultCount"),
  clearButton: document.getElementById("clearButton"),
  termList: document.getElementById("termList"),
  emptyState: document.getElementById("emptyState"),
  termDetail: document.getElementById("termDetail"),
  detailChapter: document.getElementById("detailChapter"),
  detailZh: document.getElementById("detailZh"),
  detailEn: document.getElementById("detailEn"),
  detailCategory: document.getElementById("detailCategory"),
  detailPages: document.getElementById("detailPages"),
  detailOccurrences: document.getElementById("detailOccurrences"),
  detailConfidence: document.getElementById("detailConfidence"),
  detailDefinition: document.getElementById("detailDefinition"),
  detailLocation: document.getElementById("detailLocation"),
  detailFunction: document.getElementById("detailFunction"),
  detailStudyNote: document.getElementById("detailStudyNote"),
  figureList: document.getElementById("figureList"),
  pageImages: document.getElementById("pageImages"),
  contextList: document.getElementById("contextList"),
  pdfLink: document.getElementById("pdfLink"),
  starButton: document.getElementById("starButton"),
  randomButton: document.getElementById("randomButton"),
  reviewButton: document.getElementById("reviewButton"),
  reviewPanel: document.getElementById("reviewPanel"),
  reviewScore: document.getElementById("reviewScore"),
  againButton: document.getElementById("againButton"),
  knownButton: document.getElementById("knownButton"),
  revealButton: document.getElementById("revealButton"),
  imageDialog: document.getElementById("imageDialog"),
  dialogImage: document.getElementById("dialogImage"),
  closeDialog: document.getElementById("closeDialog"),
};

const store = {
  stars: readStore("anatomyStars", {}),
  review: readStore("anatomyReview", {}),
};

let state = {
  filtered: [],
  selectedId: "",
  reviewMode: false,
  revealed: true,
};

const figuresByLabel = new Map((data?.figures || []).map((figure) => [figure.label, figure]));

function readStore(key, fallback) {
  try {
    return JSON.parse(localStorage.getItem(key)) || fallback;
  } catch {
    return fallback;
  }
}

function writeStore(key, value) {
  localStorage.setItem(key, JSON.stringify(value));
}

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function normalize(value) {
  return String(value ?? "").trim().toLowerCase();
}

function pageText(pages) {
  if (!pages?.length) return "";
  if (pages.length <= 4) return pages.join(", ");
  return `${pages.slice(0, 4).join(", ")} 等 ${pages.length} 页`;
}

function sourceLink(term) {
  return term.pageImages?.[0] || `assets/pages/pdf-${String(term.firstPdfPage).padStart(3, "0")}.jpg`;
}

function setup() {
  if (!data?.terms?.length) {
    els.metaLine.textContent = "未找到词库数据";
    return;
  }

  els.metaLine.textContent = `${data.meta.totalTerms} 个词条 · ${data.meta.totalFigures} 个图号 · ${data.meta.bodyPages} 页正文`;
  setupFilters();
  bindEvents();
  applyFilters();
  selectTerm(data.terms[0].id);
}

function setupFilters() {
  els.chapterFilter.innerHTML = `<option value="">全部章节</option>${data.chapters
    .map((chapter) => `<option value="${escapeHtml(chapter.name)}">${escapeHtml(chapter.name)}</option>`)
    .join("")}`;

  const categories = [...new Set(data.terms.map((term) => term.category))].sort((a, b) => a.localeCompare(b, "zh-CN"));
  els.categoryFilter.innerHTML = `<option value="">全部分类</option>${categories
    .map((category) => `<option value="${escapeHtml(category)}">${escapeHtml(category)}</option>`)
    .join("")}`;
}

function bindEvents() {
  [
    els.searchInput,
    els.chapterFilter,
    els.categoryFilter,
    els.confidenceFilter,
    els.figureOnly,
    els.starOnly,
  ].forEach((node) => node.addEventListener("input", applyFilters));

  els.clearButton.addEventListener("click", () => {
    els.searchInput.value = "";
    els.chapterFilter.value = "";
    els.categoryFilter.value = "";
    els.confidenceFilter.value = "";
    els.figureOnly.checked = false;
    els.starOnly.checked = false;
    applyFilters();
  });

  els.termList.addEventListener("click", (event) => {
    const button = event.target.closest("[data-term-id]");
    if (button) selectTerm(button.dataset.termId);
  });

  els.randomButton.addEventListener("click", selectRandom);
  els.reviewButton.addEventListener("click", () => {
    state.reviewMode = !state.reviewMode;
    state.revealed = !state.reviewMode;
    els.reviewButton.classList.toggle("active", state.reviewMode);
    selectRandom();
  });

  els.starButton.addEventListener("click", () => {
    if (!state.selectedId) return;
    store.stars[state.selectedId] = !store.stars[state.selectedId];
    if (!store.stars[state.selectedId]) delete store.stars[state.selectedId];
    writeStore("anatomyStars", store.stars);
    renderDetail(currentTerm());
    renderList();
  });

  els.revealButton.addEventListener("click", () => {
    state.revealed = true;
    renderDetail(currentTerm());
  });

  els.againButton.addEventListener("click", () => updateReview(-1));
  els.knownButton.addEventListener("click", () => updateReview(1));
  els.closeDialog.addEventListener("click", () => els.imageDialog.close());
}

function currentTerm() {
  return data.terms.find((term) => term.id === state.selectedId) || state.filtered[0] || data.terms[0];
}

function matchesQuery(term, query) {
  if (!query) return true;
  const haystack = normalize(
    [
      term.zh,
      term.en,
      term.category,
      term.chapters.join(" "),
      term.pages.join(" "),
      term.pdfPages.join(" "),
      term.figures.join(" "),
      term.pageFigures.join(" "),
      term.definition,
      term.location,
      term.function,
    ].join(" ")
  );
  return query
    .split(/\s+/)
    .filter(Boolean)
    .every((part) => haystack.includes(part));
}

function applyFilters() {
  const query = normalize(els.searchInput.value);
  const chapter = els.chapterFilter.value;
  const category = els.categoryFilter.value;
  const confidence = els.confidenceFilter.value;

  state.filtered = data.terms.filter((term) => {
    if (!matchesQuery(term, query)) return false;
    if (chapter && !term.chapters.includes(chapter)) return false;
    if (category && term.category !== category) return false;
    if (confidence && term.confidenceLabel !== confidence) return false;
    if (els.figureOnly.checked && !term.figures.length && !term.pageFigures.length) return false;
    if (els.starOnly.checked && !store.stars[term.id]) return false;
    return true;
  });

  renderList();
  if (!state.filtered.some((term) => term.id === state.selectedId)) {
    selectTerm(state.filtered[0]?.id || "");
  }
}

function renderList() {
  els.resultCount.textContent = `${state.filtered.length} 个词条`;
  const visible = state.filtered.slice(0, 500);
  els.termList.innerHTML = visible
    .map((term) => {
      const active = term.id === state.selectedId ? " active" : "";
      const confidenceClass = term.confidenceLabel === "需复核" ? " warn" : "";
      const star = store.stars[term.id] ? "★ " : "";
      const hasFigure = term.figures.length || term.pageFigures.length;
      return `
        <button class="term-item${active}" type="button" data-term-id="${term.id}">
          <span class="term-main">
            <span class="term-zh">${star}${escapeHtml(term.zh)}</span>
            <span class="term-en">${escapeHtml(term.en)}</span>
          </span>
          <span class="term-side">
            <span class="badge${confidenceClass}">${escapeHtml(term.confidenceLabel)}</span>
            ${hasFigure ? `<span class="badge figure">图</span>` : ""}
          </span>
        </button>
      `;
    })
    .join("");
}

function selectTerm(id) {
  state.selectedId = id;
  state.revealed = !state.reviewMode;
  renderList();
  renderDetail(currentTerm());
  document.querySelector(".detail")?.scrollTo({ top: 0, behavior: "smooth" });
}

function selectRandom() {
  const source = state.filtered.length ? state.filtered : data.terms;
  const weights = source.map((term) => {
    const score = store.review[term.id] || 0;
    return Math.max(1, 5 - score);
  });
  const total = weights.reduce((sum, value) => sum + value, 0);
  let pick = Math.random() * total;
  for (let index = 0; index < source.length; index += 1) {
    pick -= weights[index];
    if (pick <= 0) {
      selectTerm(source[index].id);
      return;
    }
  }
  selectTerm(source[0]?.id || "");
}

function renderDetail(term) {
  if (!term) {
    els.emptyState.classList.remove("hidden");
    els.termDetail.classList.add("hidden");
    return;
  }

  const hiddenAnswer = state.reviewMode && !state.revealed;
  els.emptyState.classList.add("hidden");
  els.termDetail.classList.remove("hidden");
  els.reviewPanel.classList.toggle("hidden", !state.reviewMode);

  els.detailChapter.textContent = term.chapters.join(" / ");
  els.detailZh.textContent = term.zh;
  els.detailEn.textContent = hiddenAnswer ? "••••••" : term.en;
  els.detailCategory.textContent = term.category;
  els.detailPages.textContent = pageText(term.pages);
  els.detailOccurrences.textContent = `${term.occurrences} 次`;
  els.detailConfidence.textContent = `${term.confidenceLabel} (${term.confidence})`;
  els.detailDefinition.textContent = hiddenAnswer ? "••••••" : term.definition || "暂无自动解释";
  els.detailLocation.textContent = hiddenAnswer ? "••••••" : term.location || "未在自动上下文中识别到明确位置";
  els.detailFunction.textContent = hiddenAnswer ? "••••••" : term.function || "未在自动上下文中识别到明确功能";
  els.detailStudyNote.textContent = hiddenAnswer ? "••••••" : term.studyNote;
  els.reviewScore.textContent = store.review[term.id] || 0;
  els.starButton.textContent = store.stars[term.id] ? "★" : "☆";
  els.starButton.classList.toggle("active", Boolean(store.stars[term.id]));
  els.pdfLink.href = sourceLink(term);

  renderFigures(term, hiddenAnswer);
  renderContexts(term, hiddenAnswer);
}

function renderFigures(term, hiddenAnswer) {
  const explicit = term.figures.map((label) => figuresByLabel.get(label)).filter(Boolean);
  const fallback = term.pageFigures.map((label) => figuresByLabel.get(label)).filter(Boolean);
  const figures = explicit.length ? explicit : fallback;

  if (hiddenAnswer) {
    els.figureList.innerHTML = `<span class="figure-pill">••••••</span>`;
    els.pageImages.innerHTML = "";
    return;
  }

  els.figureList.innerHTML = figures.length
    ? figures
        .slice(0, 12)
        .map((figure) => {
          const caption = figure.caption ? ` ${figure.caption}` : "";
          return `<span class="figure-pill">${escapeHtml(figure.label)}${escapeHtml(caption)} · ${figure.bookPage}页</span>`;
        })
        .join("")
    : `<span class="figure-pill">本条目未识别到专属图号</span>`;

  const imageCandidates = [...new Set([...figures.map((figure) => figure.image), ...term.pageImages])].slice(0, 4);
  els.pageImages.innerHTML = imageCandidates
    .map((path, index) => {
      const pdfPage = Number((path.match(/pdf-(\d+)\.jpg/) || [])[1]);
      const bookPage = pdfPage ? pdfPage - data.meta.pageOffset : term.pages[index] || term.firstPage;
      return `
        <div class="page-thumb">
          <img src="${escapeHtml(path)}" alt="书页 ${bookPage}" loading="lazy" data-full-image="${escapeHtml(path)}" />
          <button type="button" data-full-image="${escapeHtml(path)}">书页 ${bookPage}</button>
        </div>
      `;
    })
    .join("");

  els.pageImages.querySelectorAll("[data-full-image]").forEach((node) => {
    node.addEventListener("click", () => openImage(node.dataset.fullImage));
    if (node.tagName === "IMG") {
      node.addEventListener("error", () => node.closest(".page-thumb")?.remove());
    }
  });
}

function renderContexts(term, hiddenAnswer) {
  if (hiddenAnswer) {
    els.contextList.innerHTML = `<div class="context-item">••••••</div>`;
    return;
  }

  els.contextList.innerHTML = term.contexts
    .map(
      (context) => `
      <div class="context-item">
        <span class="context-page">${escapeHtml(context.chapter)} · 书页 ${context.bookPage} · PDF ${context.pdfPage}</span>
        ${escapeHtml(context.text)}
      </div>
    `
    )
    .join("");
}

function openImage(path) {
  if (!path) return;
  els.dialogImage.src = path;
  if (typeof els.imageDialog.showModal === "function") {
    els.imageDialog.showModal();
  } else {
    window.open(path, "_blank");
  }
}

function updateReview(delta) {
  if (!state.selectedId) return;
  const current = store.review[state.selectedId] || 0;
  store.review[state.selectedId] = Math.max(0, Math.min(5, current + delta));
  writeStore("anatomyReview", store.review);
  selectRandom();
}

setup();
