const rawData = window.MED_GLOSSARY || window.ANATOMY_GLOSSARY;
const rawTopics = window.MED_GLOSSARY_TOPICS || [];

const els = {
  metaLine: document.getElementById("metaLine"),
  menuButton: document.getElementById("menuButton"),
  courseSelect: document.getElementById("courseSelect"),
  searchInput: document.getElementById("searchInput"),
  partFilter: document.getElementById("partFilter"),
  chapterFilter: document.getElementById("chapterFilter"),
  categoryFilter: document.getElementById("categoryFilter"),
  figureOnly: document.getElementById("figureOnly"),
  starOnly: document.getElementById("starOnly"),
  topicList: document.getElementById("topicList"),
  clearTopicButton: document.getElementById("clearTopicButton"),
  resultCount: document.getElementById("resultCount"),
  clearButton: document.getElementById("clearButton"),
  drawerBackdrop: document.getElementById("drawerBackdrop"),
  termList: document.getElementById("termList"),
  emptyState: document.getElementById("emptyState"),
  topicDetail: document.getElementById("topicDetail"),
  topicDetailMeta: document.getElementById("topicDetailMeta"),
  topicDetailTitle: document.getElementById("topicDetailTitle"),
  topicDetailSummary: document.getElementById("topicDetailSummary"),
  topicDetailTags: document.getElementById("topicDetailTags"),
  topicTermList: document.getElementById("topicTermList"),
  topicDetailClose: document.getElementById("topicDetailClose"),
  termDetail: document.getElementById("termDetail"),
  detailChapter: document.getElementById("detailChapter"),
  detailZh: document.getElementById("detailZh"),
  detailEn: document.getElementById("detailEn"),
  detailCategory: document.getElementById("detailCategory"),
  detailPages: document.getElementById("detailPages"),
  detailOccurrences: document.getElementById("detailOccurrences"),
  detailDefinition: document.getElementById("detailDefinition"),
  detailLocation: document.getElementById("detailLocation"),
  detailFunction: document.getElementById("detailFunction"),
  detailStudyNote: document.getElementById("detailStudyNote"),
  graySection: document.getElementById("graySection"),
  grayZh: document.getElementById("grayZh"),
  grayEnglish: document.getElementById("grayEnglish"),
  grayEnglishToggle: document.getElementById("grayEnglishToggle"),
  grayCards: document.getElementById("grayCards"),
  grayBookHits: document.getElementById("grayBookHits"),
  relatedList: document.getElementById("relatedList"),
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

const library = normalizeLibrary(rawData);
const topics = normalizeTopics(rawTopics);
const topicsById = new Map(topics.map((topic) => [topic.id, topic]));

const store = {
  stars: readStore("medGlossaryStars", {}),
  review: readStore("medGlossaryReview", {}),
  legacyStars: readStore("anatomyStars", {}),
  legacyReview: readStore("anatomyReview", {}),
};

let data = library.courses[0] || { terms: [], chapters: [], figures: [], parts: [], meta: {} };
let figuresByLabel = new Map();
let termsById = new Map();
let termsByEnglish = new Map();

let state = {
  filtered: [],
  selectedId: "",
  selectedByCourse: {},
  expandedGroups: {},
  courseId: data.id || "",
  activeTopicId: "",
  reviewMode: false,
  revealed: true,
  showGrayEnglish: false,
  showGrayBookPages: false,
};

function normalizeLibrary(payload) {
  if (payload?.courses?.length) return payload;
  if (payload?.terms?.length) {
    const terms = payload.terms.map((term) => ({
      ...term,
      part: term.part || "系统解剖学",
      parts: term.parts || ["系统解剖学"],
      structure: term.structure || term.location || "",
      relatedTerms: term.relatedTerms || [],
    }));
    return {
      schemaVersion: 1,
      meta: {
        totalCourses: 1,
        totalTerms: terms.length,
        totalFigures: payload.figures?.length || 0,
      },
      courses: [
        {
          id: "systematic-anatomy",
          title: "系统解剖学",
          shortTitle: "系统解剖学",
          parts: [{ name: "系统解剖学", start: 1, end: payload.meta?.bodyPages || 0 }],
          chapters: payload.chapters || [],
          figures: payload.figures || [],
          terms,
          meta: payload.meta || {},
        },
      ],
    };
  }
  return { schemaVersion: 2, meta: {}, courses: [] };
}

function normalizeTopics(payload) {
  if (!Array.isArray(payload)) return [];
  return payload
    .filter((topic) => topic?.id && topic?.courseId && Array.isArray(topic.termIds))
    .map((topic) => ({
      ...topic,
      tags: Array.isArray(topic.tags) ? topic.tags : [],
      termIds: [...new Set(topic.termIds.filter(Boolean))],
    }));
}

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

function englishKey(value) {
  return String(value ?? "")
    .toLowerCase()
    .replace(/\([^)]*\)/g, " ")
    .replace(/[^a-z0-9]+/g, "");
}

function pageText(pages) {
  if (!pages?.length) return "";
  if (pages.length <= 4) return pages.join(", ");
  return `${pages.slice(0, 4).join(", ")} 等 ${pages.length} 页`;
}

function sourceLink(term) {
  if (term.pageImages?.[0]) return term.pageImages[0];
  if (term.firstPdfPage) return `assets/pages/pdf-${String(term.firstPdfPage).padStart(3, "0")}.jpg`;
  return "#";
}

function setup() {
  if (!library.courses.length) {
    els.metaLine.textContent = "未找到词库数据";
    return;
  }

  setupCourseSelect();
  bindEvents();
  setCourse(library.courses[0].id);
}

function setupCourseSelect() {
  els.courseSelect.innerHTML = library.courses
    .map((course) => `<option value="${escapeHtml(course.id)}">${escapeHtml(course.shortTitle || course.title)}</option>`)
    .join("");
}

function setCourse(courseId) {
  data = library.courses.find((course) => course.id === courseId) || library.courses[0];
  state.courseId = data.id;
  figuresByLabel = new Map((data.figures || []).map((figure) => [figure.label, figure]));
  termsById = new Map((data.terms || []).map((term) => [term.id, term]));
  termsByEnglish = new Map();
  (data.terms || []).forEach((term) => {
    [term.en, ...(term.aliases || [])].forEach((name) => {
      const key = englishKey(name);
      if (key && !termsByEnglish.has(key)) termsByEnglish.set(key, term);
    });
  });
  els.courseSelect.value = data.id;
  if (currentTopic()?.courseId !== data.id) state.activeTopicId = "";
  renderTopics();
  setupFilters();
  updateMetaLine();
  state.selectedId = state.selectedByCourse[data.id] || data.terms?.[0]?.id || "";
  applyFilters();
}

function updateMetaLine() {
  const totalTerms = data.meta?.totalTerms || data.terms?.length || 0;
  const totalFigures = data.meta?.totalFigures || data.figures?.length || 0;
  const parts = (data.parts || []).map((part) => part.name).join(" / ");
  els.metaLine.textContent = `${totalTerms} 个词条 · ${totalFigures} 个图号${parts ? ` · ${parts}` : ""}`;
}

function courseTopics() {
  return topics.filter((topic) => topic.courseId === data.id && topic.termIds.some((id) => termsById.has(id)));
}

function currentTopic() {
  return topicsById.get(state.activeTopicId) || null;
}

function topicTerms(topic) {
  if (!topic) return [];
  return topic.termIds.map((id) => termsById.get(id)).filter(Boolean);
}

function renderTopics() {
  const items = courseTopics();
  els.topicList.closest(".topic-panel")?.classList.toggle("hidden", !items.length);
  els.clearTopicButton.classList.toggle("hidden", !state.activeTopicId);
  els.topicList.innerHTML = items
    .map((topic) => {
      const active = topic.id === state.activeTopicId ? " active" : "";
      const count = topic.termIds.filter((id) => termsById.has(id)).length;
      const tags = topic.tags.slice(0, 3).map((tag) => `<span>${escapeHtml(tag)}</span>`).join("");
      return `
        <button class="topic-item${active}" type="button" data-topic-id="${escapeHtml(topic.id)}">
          <span class="topic-title">${escapeHtml(topic.title)}</span>
          <span class="topic-summary">${escapeHtml(topic.summary)}</span>
          <span class="topic-foot">
            <span>${count} 个词条</span>
            <span class="topic-mini-tags">${tags}</span>
          </span>
        </button>
      `;
    })
    .join("");
}

function resetFilters() {
  els.searchInput.value = "";
  els.partFilter.value = "";
  els.chapterFilter.value = "";
  els.categoryFilter.value = "";
  els.figureOnly.checked = false;
  els.starOnly.checked = false;
}

function setupFilters() {
  const parts = data.parts?.length
    ? data.parts.map((part) => part.name)
    : [...new Set(data.terms.map((term) => term.part).filter(Boolean))];
  els.partFilter.innerHTML = `<option value="">全部篇章</option>${parts
    .map((part) => `<option value="${escapeHtml(part)}">${escapeHtml(part)}</option>`)
    .join("")}`;
  els.partFilter.classList.toggle("hidden-filter", parts.length <= 1);

  els.chapterFilter.innerHTML = `<option value="">全部章节</option>${(data.chapters || [])
    .map((chapter) => `<option value="${escapeHtml(chapter.name)}">${escapeHtml(chapter.name)}</option>`)
    .join("")}`;

  const categories = [...new Set(data.terms.map((term) => term.category))].sort((a, b) => a.localeCompare(b, "zh-CN"));
  els.categoryFilter.innerHTML = `<option value="">全部分类</option>${categories
    .map((category) => `<option value="${escapeHtml(category)}">${escapeHtml(category)}</option>`)
    .join("")}`;

  resetFilters();
}

function bindEvents() {
  els.courseSelect.addEventListener("change", () => setCourse(els.courseSelect.value));

  els.topicList.addEventListener("click", (event) => {
    const button = event.target.closest("[data-topic-id]");
    if (button) selectTopic(button.dataset.topicId);
  });

  els.clearTopicButton.addEventListener("click", clearTopic);
  els.topicDetailClose.addEventListener("click", clearTopic);
  els.topicTermList.addEventListener("click", (event) => {
    const button = event.target.closest("[data-topic-term-id]");
    if (button) selectTerm(button.dataset.topicTermId);
  });

  [
    els.searchInput,
    els.partFilter,
    els.chapterFilter,
    els.categoryFilter,
    els.figureOnly,
    els.starOnly,
  ].forEach((node) => node.addEventListener("input", applyFilters));

  els.clearButton.addEventListener("click", () => {
    resetFilters();
    state.activeTopicId = "";
    state.selectedId = state.selectedByCourse[data.id] || "";
    renderTopics();
    applyFilters();
  });

  els.termList.addEventListener("click", (event) => {
    const groupButton = event.target.closest("[data-group-key]");
    if (groupButton) {
      toggleGroup(groupButton.dataset.groupKey);
      return;
    }

    const button = event.target.closest("[data-term-id]");
    if (button) {
      selectTerm(button.dataset.termId);
      if (isMobileLayout()) setDrawerOpen(false);
    }
  });

  els.relatedList.addEventListener("click", (event) => {
    const button = event.target.closest("[data-related-id]");
    if (button) selectTerm(button.dataset.relatedId);
  });

  els.grayEnglishToggle.addEventListener("click", () => {
    state.showGrayEnglish = !state.showGrayEnglish;
    renderGray(currentTerm(), state.reviewMode && !state.revealed);
  });

  els.grayCards.addEventListener("click", (event) => {
    const button = event.target.closest("[data-gray-related-id]");
    if (button) selectTerm(button.dataset.grayRelatedId);
  });

  els.grayBookHits.addEventListener("click", (event) => {
    const toggle = event.target.closest("[data-gray-book-toggle]");
    if (toggle) {
      state.showGrayBookPages = !state.showGrayBookPages;
      renderGray(currentTerm(), state.reviewMode && !state.revealed);
      return;
    }

    const imageButton = event.target.closest("[data-full-image]");
    if (imageButton) openImage(imageButton.dataset.fullImage);
  });

  els.menuButton.addEventListener("click", () => setDrawerOpen(!document.body.classList.contains("drawer-open")));
  els.drawerBackdrop.addEventListener("click", () => setDrawerOpen(false));
  window.addEventListener("keydown", (event) => {
    if (event.key === "Escape") setDrawerOpen(false);
  });

  els.randomButton.addEventListener("click", selectRandom);
  els.reviewButton.addEventListener("click", () => {
    state.reviewMode = !state.reviewMode;
    state.revealed = !state.reviewMode;
    els.reviewButton.classList.toggle("active", state.reviewMode);
    selectRandom();
  });

  els.starButton.addEventListener("click", () => {
    const term = currentTerm();
    if (!term) return;
    const key = termKey(term);
    store.stars[key] = !isStarred(term);
    if (!store.stars[key]) delete store.stars[key];
    writeStore("medGlossaryStars", store.stars);
    renderDetail(term);
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

function isMobileLayout() {
  return window.matchMedia("(max-width: 920px)").matches;
}

function setDrawerOpen(open) {
  document.body.classList.toggle("drawer-open", open);
  els.menuButton.setAttribute("aria-expanded", String(open));
}

function termKey(term) {
  return `${data.id}:${term.id}`;
}

function isStarred(term) {
  const key = termKey(term);
  return Boolean(store.stars[key] || (data.id === "systematic-anatomy" && store.legacyStars[term.id]));
}

function reviewScore(term) {
  const key = termKey(term);
  return store.review[key] ?? (data.id === "systematic-anatomy" ? store.legacyReview[term.id] || 0 : 0);
}

function currentTerm() {
  return termsById.get(state.selectedId) || state.filtered[0] || data.terms[0];
}

function termParts(term) {
  return term.parts?.length ? term.parts : term.part ? [term.part] : [];
}

function matchesQuery(term, query) {
  if (!query) return true;
  const haystack = normalize(
    [
      term.zh,
      term.en,
      term.part,
      term.category,
      term.chapters.join(" "),
      term.pages.join(" "),
      term.pdfPages.join(" "),
      term.figures.join(" "),
      term.pageFigures.join(" "),
      term.definition,
      term.structure,
      term.location,
      term.function,
      term.studyNote,
      term.gray?.zh,
      term.gray?.en,
      (term.gray?.cards || [])
        .flatMap((card) => [
          card.title,
          card.source,
          ...(card.matchedLabels || []).flatMap((label) => [label.zh, label.en]),
          ...(card.relatedLabels || []).flatMap((label) => [label.zh, label.en]),
          ...(card.clinicKeywords || []),
        ])
        .join(" "),
      term.gray?.book?.zh,
      term.gray?.book?.en,
      (term.gray?.book?.hits || []).flatMap((hit) => [hit.matched, hit.line, hit.snippet]).join(" "),
    ].join(" ")
  );
  return query
    .split(/\s+/)
    .filter(Boolean)
    .every((part) => haystack.includes(part));
}

function searchRank(term, query) {
  if (!query) return 0;
  const compactQuery = englishKey(query);
  const zh = normalize(term.zh);
  const en = normalize(term.en);
  const enCompact = englishKey(term.en);
  const grayText = normalize(`${term.gray?.zh || ""} ${term.gray?.en || ""}`);

  let score = 0;
  if (zh === query || en === query || (compactQuery && enCompact === compactQuery)) score += 1000;
  if (zh.startsWith(query) || en.startsWith(query)) score += 700;
  if (zh.includes(query) || en.includes(query) || (compactQuery && enCompact.includes(compactQuery))) score += 500;
  if (normalize(term.definition).includes(query)) score += 120;
  if (normalize(term.structure || term.location).includes(query)) score += 90;
  if (normalize(term.function).includes(query)) score += 80;
  if (grayText.includes(query)) score += 60;
  return score;
}

function applyFilters() {
  const query = normalize(els.searchInput.value);
  const part = els.partFilter.value;
  const chapter = els.chapterFilter.value;
  const category = els.categoryFilter.value;
  const topic = currentTopic();
  const topicIds = topic ? new Set(topic.termIds) : null;

  state.filtered = data.terms.filter((term) => {
    if (topicIds && !topicIds.has(term.id)) return false;
    if (!matchesQuery(term, query)) return false;
    if (part && !termParts(term).includes(part)) return false;
    if (chapter && !term.chapters.includes(chapter)) return false;
    if (category && term.category !== category) return false;
    if (els.figureOnly.checked && !term.figures.length && !term.pageFigures.length) return false;
    if (els.starOnly.checked && !isStarred(term)) return false;
    return true;
  });

  if (query) {
    state.filtered.sort((left, right) => searchRank(right, query) - searchRank(left, query));
  }

  const selectedVisible = state.filtered.some((term) => term.id === state.selectedId);
  if (state.selectedId && !selectedVisible) {
    state.selectedId = "";
  }
  if (!state.activeTopicId && !state.selectedId) {
    state.selectedId = state.filtered[0]?.id || "";
  }
  if (state.selectedId) {
    state.selectedByCourse[data.id] = state.selectedId;
  }
  renderList();
  if (state.activeTopicId && !state.selectedId) {
    renderTopicDetail(topic);
  } else {
    renderDetail(currentTerm());
  }
}

function renderList() {
  els.resultCount.textContent = `${state.filtered.length} 个词条`;
  if (state.filtered.length > 500) {
    renderGroupedList();
    return;
  }

  els.termList.innerHTML = state.filtered.map(termItemHtml).join("");
}

function termItemHtml(term) {
  const active = term.id === state.selectedId ? " active" : "";
  const star = isStarred(term) ? "★ " : "";
  const hasFigure = term.figures.length || term.pageFigures.length;
  const hasGray = Boolean(term.gray);
  const badges = [
    hasFigure ? `<span class="badge figure">图</span>` : "",
    hasGray ? `<span class="badge gray">Gray</span>` : "",
  ].join("");
  return `
    <button class="term-item${active}" type="button" data-term-id="${term.id}">
      <span class="term-main">
        <span class="term-zh">${star}${escapeHtml(term.zh)}</span>
        <span class="term-en">${escapeHtml(term.en)}</span>
      </span>
      ${badges ? `<span class="term-side">${badges}</span>` : ""}
    </button>
  `;
}

function renderGroupedList() {
  const groups = groupFilteredTerms();
  const selected = currentTerm();
  const selectedGroupKey = selected ? groupKeyForTerm(selected) : groups[0]?.key;

  els.termList.innerHTML = groups
    .map((group) => {
      const expanded = isGroupExpanded(group.key, group.key === selectedGroupKey);
      return `
        <section class="chapter-group">
          <button class="chapter-toggle" type="button" data-group-key="${escapeHtml(group.key)}" aria-expanded="${expanded}">
            <span class="chapter-title">${escapeHtml(group.label)}</span>
            <span class="chapter-count">${group.terms.length} 条</span>
          </button>
          ${
            expanded
              ? `<div class="chapter-items">${group.terms.map(termItemHtml).join("")}</div>`
              : ""
          }
        </section>
      `;
    })
    .join("");
}

function groupFilteredTerms() {
  const groups = new Map();
  state.filtered.forEach((term) => {
    const key = groupKeyForTerm(term);
    if (!groups.has(key)) {
      groups.set(key, { key, label: groupLabelForTerm(term), terms: [] });
    }
    groups.get(key).terms.push(term);
  });
  return [...groups.values()];
}

function groupKeyForTerm(term) {
  return term.chapters?.[0] || term.part || "未分章";
}

function groupLabelForTerm(term) {
  const chapter = term.chapters?.[0] || "未分章";
  if ((data.parts || []).length > 1 && term.part && !chapter.includes(term.part)) {
    return `${term.part} / ${chapter}`;
  }
  return chapter;
}

function groupStateKey(key) {
  return `${data.id}:${key}`;
}

function isGroupExpanded(key, defaultValue = false) {
  const stored = state.expandedGroups[groupStateKey(key)];
  return stored ?? defaultValue;
}

function toggleGroup(key) {
  const fullKey = groupStateKey(key);
  state.expandedGroups[fullKey] = !isGroupExpanded(key);
  renderList();
}

function selectTopic(id) {
  const topic = topicsById.get(id);
  if (!topic || topic.courseId !== data.id) return;
  state.activeTopicId = id;
  state.selectedId = "";
  resetFilters();
  renderTopics();
  applyFilters();
  if (isMobileLayout()) setDrawerOpen(false);
  document.querySelector(".detail")?.scrollTo({ top: 0, behavior: "smooth" });
}

function clearTopic() {
  state.activeTopicId = "";
  state.selectedId = state.selectedByCourse[data.id] || "";
  renderTopics();
  applyFilters();
}

function selectTerm(id) {
  const topic = currentTopic();
  if (topic && !topic.termIds.includes(id)) {
    state.activeTopicId = "";
  }
  state.selectedId = id;
  state.selectedByCourse[data.id] = id;
  state.revealed = !state.reviewMode;
  renderTopics();
  renderList();
  renderDetail(currentTerm());
  document.querySelector(".detail")?.scrollTo({ top: 0, behavior: "smooth" });
}

function selectRandom() {
  const source = state.filtered.length ? state.filtered : data.terms;
  const weights = source.map((term) => Math.max(1, 5 - reviewScore(term)));
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
    els.topicDetail.classList.add("hidden");
    els.termDetail.classList.add("hidden");
    return;
  }

  const hiddenAnswer = state.reviewMode && !state.revealed;
  els.emptyState.classList.add("hidden");
  els.topicDetail.classList.add("hidden");
  els.termDetail.classList.remove("hidden");
  els.reviewPanel.classList.toggle("hidden", !state.reviewMode);

  const chapterLine = [data.shortTitle || data.title, term.part, ...term.chapters].filter(Boolean);
  els.detailChapter.textContent = [...new Set(chapterLine)].join(" / ");
  els.detailZh.textContent = term.zh;
  els.detailEn.textContent = hiddenAnswer ? "......" : term.en;
  els.detailCategory.textContent = term.category;
  els.detailPages.textContent = pageText(term.pages);
  els.detailOccurrences.textContent = `${term.occurrences} 次`;
  els.detailDefinition.textContent = hiddenAnswer ? "......" : term.definition || "暂无自动解释";
  els.detailLocation.textContent = hiddenAnswer ? "......" : term.structure || term.location || "未在自动上下文中识别到明确结构或分布";
  els.detailFunction.textContent = hiddenAnswer ? "......" : term.function || "未在自动上下文中识别到明确功能或意义";
  els.detailStudyNote.textContent = hiddenAnswer ? "......" : term.studyNote;
  els.reviewScore.textContent = reviewScore(term);
  els.starButton.textContent = isStarred(term) ? "★" : "☆";
  els.starButton.classList.toggle("active", isStarred(term));
  els.pdfLink.href = sourceLink(term);

  renderGray(term, hiddenAnswer);
  renderRelated(term, hiddenAnswer);
  renderFigures(term, hiddenAnswer);
  renderContexts(term, hiddenAnswer);
}

function renderTopicDetail(topic) {
  if (!topic) {
    els.emptyState.classList.remove("hidden");
    els.topicDetail.classList.add("hidden");
    els.termDetail.classList.add("hidden");
    return;
  }

  const filteredIds = new Set(state.filtered.map((term) => term.id));
  const terms = topicTerms(topic).filter((term) => filteredIds.has(term.id));

  els.emptyState.classList.add("hidden");
  els.termDetail.classList.add("hidden");
  els.topicDetail.classList.remove("hidden");
  els.topicDetailMeta.textContent = `${data.shortTitle || data.title} · ${terms.length} / ${topic.termIds.length} 个词条`;
  els.topicDetailTitle.textContent = topic.title;
  els.topicDetailSummary.textContent = topic.summary;
  els.topicDetailTags.innerHTML = topic.tags.map((tag) => `<span>${escapeHtml(tag)}</span>`).join("");
  els.topicTermList.innerHTML = terms.length
    ? terms
        .map(
          (term) => `
            <button class="topic-term-chip" type="button" data-topic-term-id="${escapeHtml(term.id)}">
              <strong>${escapeHtml(term.zh)}</strong>
              <span>${escapeHtml(term.en)}</span>
              <small>${escapeHtml([term.category, term.chapters?.[0]].filter(Boolean).join(" · "))}</small>
            </button>
          `
        )
        .join("")
    : `<div class="topic-empty">当前筛选下没有专题词条。</div>`;
}

function renderGray(term, hiddenAnswer) {
  const gray = term?.gray;
  const bookHits = gray?.book?.hits || [];
  const hasGray = Boolean(gray?.zh || gray?.en || gray?.cards?.length || bookHits.length);
  els.graySection.classList.toggle("hidden", !hasGray);

  if (!hasGray) {
    els.grayZh.textContent = "";
    els.grayEnglish.textContent = "";
    els.grayCards.innerHTML = "";
    els.grayBookHits.innerHTML = "";
    return;
  }

  if (hiddenAnswer) {
    els.grayZh.textContent = "......";
    els.grayEnglish.textContent = "";
    els.grayEnglish.classList.add("hidden");
    els.grayEnglishToggle.classList.add("hidden");
    els.grayCards.innerHTML = `<span class="figure-pill">......</span>`;
    els.grayBookHits.innerHTML = "";
    return;
  }

  els.grayZh.textContent = gray.zh || gray.book?.zh || "暂无中文补充";
  els.grayEnglish.textContent = gray.en || "";
  els.grayEnglish.classList.toggle("hidden", !gray.en || !state.showGrayEnglish);
  els.grayEnglishToggle.classList.toggle("hidden", !(gray.en || bookHits.length));
  els.grayEnglishToggle.textContent = state.showGrayEnglish ? "隐藏英文" : "显示英文";
  els.grayEnglishToggle.setAttribute("aria-expanded", String(state.showGrayEnglish));

  const cards = gray.cards || [];
  els.grayCards.innerHTML = cards.length
    ? cards.slice(0, 3).map((card) => grayCardHtml(card, term)).join("")
    : `<span class="figure-pill">暂无格氏图卡关联</span>`;
  els.grayBookHits.innerHTML = grayBookHtml(gray.book, term);

  els.grayCards.querySelectorAll("[data-full-image]").forEach((node) => {
    node.addEventListener("click", () => openImage(node.dataset.fullImage));
    if (node.tagName === "IMG") {
      node.addEventListener("error", () => node.closest(".gray-image-wrap")?.remove());
    }
  });
  els.grayBookHits.querySelectorAll("img[data-full-image]").forEach((node) => {
    node.addEventListener("error", () => node.closest(".gray-book-image-wrap")?.remove());
  });
}

function grayBookHtml(book, term) {
  const hits = book?.hits || [];
  if (!hits.length) return "";
  const summary = book.zh && term.gray?.zh && book.zh !== term.gray.zh ? `<p class="gray-book-summary">${escapeHtml(book.zh)}</p>` : "";
  const pageToggle = `
    <button class="text-toggle gray-book-toggle" type="button" data-gray-book-toggle aria-expanded="${state.showGrayBookPages}">
      ${state.showGrayBookPages ? "隐藏正书页图" : "显示正书页图"}
    </button>
  `;
  return `
    <div class="gray-book-head">
      <div>
        <strong>格氏正书 OCR 定位</strong>
        <span>${hits.length} 处上下文</span>
      </div>
      ${pageToggle}
    </div>
    ${summary}
    <div class="gray-book-items">
      ${hits.slice(0, 3).map((hit) => grayBookHitHtml(hit)).join("")}
    </div>
  `;
}

function grayBookHitHtml(hit) {
  const page = hit.bookPage ? `正书 ${hit.bookPage} 页` : `PDF ${hit.pdfPage} 页`;
  const source = `${page} · PDF ${hit.pdfPage}`;
  const snippet = state.showGrayEnglish
    ? `<p class="gray-book-snippet">${escapeHtml(hit.snippet || hit.line || "")}</p>`
    : "";
  const imagePath = grayBookPageImage(hit);
  const pageImage = state.showGrayBookPages
    ? `
      <div class="gray-book-image-wrap">
        <img src="${escapeHtml(imagePath)}" alt="${escapeHtml(source)}" loading="lazy" data-full-image="${escapeHtml(imagePath)}" />
        <button type="button" data-full-image="${escapeHtml(imagePath)}">打开正书页图 PDF ${escapeHtml(hit.pdfPage)}</button>
      </div>
    `
    : "";
  return `
    <article class="gray-book-hit">
      <div>
        <strong>${escapeHtml(hit.matched || "Gray OCR")}</strong>
        <span>${escapeHtml(source)}</span>
      </div>
      ${snippet}
      ${pageImage}
    </article>
  `;
}

function grayBookPageImage(hit) {
  const page = String(hit.pdfPage || 0).padStart(4, "0");
  return `assets/pages/gray-book/pdf-${page}.jpg`;
}

function grayCardHtml(card, term) {
  const matched = card.matchedLabels?.length
    ? card.matchedLabels.map((label) => grayLabelHtml(label, { currentId: term.id, mode: "match" })).join("")
    : `<span class="gray-label muted">未定位具体编号</span>`;
  const related = (card.relatedLabels || [])
    .filter((label) => !(card.matchedLabels || []).some((matchedLabel) => matchedLabel.number === label.number))
    .slice(0, 8);
  const relatedHtml = related.length
    ? related.map((label) => grayLabelHtml(label, { currentId: term.id, mode: "related" })).join("")
    : `<span class="gray-label muted">暂无同图关联标签</span>`;
  const clinic = card.clinicKeywords?.length
    ? `<div class="gray-clinic">临床提示：${card.clinicKeywords.map(escapeHtml).join("、")}</div>`
    : "";
  const image = card.image
    ? `
      <div class="gray-image-wrap">
        <img src="${escapeHtml(card.image)}" alt="${escapeHtml(card.title)}" loading="lazy" data-full-image="${escapeHtml(card.image)}" />
        <button type="button" data-full-image="${escapeHtml(card.image)}">打开图卡页 PDF ${escapeHtml(card.imagePdfPage)}</button>
      </div>
    `
    : "";

  return `
    <article class="gray-card">
      <div class="gray-card-head">
        <strong>${escapeHtml(card.title || "Gray's Anatomy")}</strong>
        <span>${escapeHtml(card.source || "Gray's Anatomy for Students Flash Cards")}</span>
      </div>
      ${image}
      <div class="gray-card-block">
        <span class="gray-card-label">标出</span>
        <div class="gray-labels">${matched}</div>
      </div>
      <div class="gray-card-block">
        <span class="gray-card-label">同图关联</span>
        <div class="gray-labels">${relatedHtml}</div>
      </div>
      ${clinic}
    </article>
  `;
}

function grayLabelHtml(label, options = {}) {
  const target = termsByEnglish.get(englishKey(label.en));
  const isCurrent = target?.id && target.id === options.currentId;
  const text = `${label.number ? `${label.number}. ` : ""}${label.zh || label.en}${label.zh && label.en ? ` / ${label.en}` : ""}`;
  const className = `gray-label ${options.mode === "match" ? "match" : ""}`.trim();

  if (target && !isCurrent) {
    return `<button class="${className}" type="button" data-gray-related-id="${escapeHtml(target.id)}">${escapeHtml(text)}</button>`;
  }
  return `<span class="${className}">${escapeHtml(text)}</span>`;
}

function renderRelated(term, hiddenAnswer) {
  if (hiddenAnswer) {
    els.relatedList.innerHTML = `<span class="figure-pill">......</span>`;
    return;
  }
  const related = (term.relatedTerms || []).map((id) => termsById.get(id)).filter(Boolean).slice(0, 10);
  els.relatedList.innerHTML = related.length
    ? related
        .map(
          (item) => `
            <button class="related-chip" type="button" data-related-id="${item.id}">
              <strong>${escapeHtml(item.zh)}</strong>
              <span>${escapeHtml(item.en)}</span>
            </button>
          `
        )
        .join("")
    : `<span class="figure-pill">暂未识别到高相关词条</span>`;
}

function renderFigures(term, hiddenAnswer) {
  const explicit = term.figures.map((label) => figuresByLabel.get(label)).filter(Boolean);
  const fallback = term.pageFigures.map((label) => figuresByLabel.get(label)).filter(Boolean);
  const figures = explicit.length ? explicit : fallback;

  if (hiddenAnswer) {
    els.figureList.innerHTML = `<span class="figure-pill">......</span>`;
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
      const bookPage = pdfPage ? pdfPage - (data.meta?.pageOffset || 0) : term.pages[index] || term.firstPage;
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
    els.contextList.innerHTML = `<div class="context-item">......</div>`;
    return;
  }

  els.contextList.innerHTML = term.contexts
    .map(
      (context) => `
      <div class="context-item">
        <span class="context-page">${escapeHtml(context.part || term.part)} · ${escapeHtml(context.chapter)} · 书页 ${context.bookPage} · PDF ${context.pdfPage}</span>
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
  const term = currentTerm();
  if (!term) return;
  const key = termKey(term);
  const current = reviewScore(term);
  store.review[key] = Math.max(0, Math.min(5, current + delta));
  writeStore("medGlossaryReview", store.review);
  selectRandom();
}

setup();
