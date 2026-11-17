"use strict";

const state = {
  files: [],
  inventory: null,
  goDatabase: null,
  sessionId: null,
  overview: null,
  cleanup: null,
  libraryCleanup: null,
  upgrades: null,
};

const $ = (selector) => document.querySelector(selector);
const $$ = (selector) => [...document.querySelectorAll(selector)];
const escapeHtml = (value) => String(value ?? "")
  .replaceAll("&", "&amp;")
  .replaceAll("<", "&lt;")
  .replaceAll(">", "&gt;")
  .replaceAll('"', "&quot;")
  .replaceAll("'", "&#039;");

const formatNumber = new Intl.NumberFormat();
const percent = (value, digits = 1) => `${(Number(value || 0) * 100).toFixed(digits)}%`;
const warningIcon = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 4 3 20h18L12 4Zm0 6v4m0 3h.01"/></svg>';

function toast(message) {
  const element = $("#toast");
  element.textContent = message;
  element.classList.add("show");
  window.setTimeout(() => element.classList.remove("show"), 2400);
}

function showError(message) {
  const element = $("#importError");
  element.textContent = message;
  element.classList.remove("hidden");
}

function showPasteError(message) {
  const element = $("#pasteError");
  element.textContent = message;
  element.classList.remove("hidden");
}

function notices(target, warnings) {
  target.innerHTML = (warnings || []).map((warning) =>
    `<div class="notice">${warningIcon}<span>${escapeHtml(warning)}</span></div>`
  ).join("");
}

async function readFiles(fileList) {
  $("#importError").classList.add("hidden");
  const parsed = [];
  for (const file of fileList) {
    if (!file.name.toLowerCase().endsWith(".json")) {
      showError(`${file.name} is not a JSON export.`);
      continue;
    }
    try {
      const data = JSON.parse(await file.text());
      parsed.push({ name: file.name, size: file.size, data });
    } catch {
      showError(`${file.name} could not be read as JSON.`);
    }
  }
  state.files = parsed;
  classifyFiles();
  renderFileQueue();
}

function isGood(item) {
  return item?.data?.format === "GOOD" && Number(item?.data?.version) === 3 && Array.isArray(item?.data?.artifacts);
}

function isGoDatabase(item) {
  return isGood(item) && item.data.source === "Genshin Optimizer" && Array.isArray(item.data.teams);
}

function classifyFiles() {
  state.goDatabase = state.files.find(isGoDatabase) || null;
  state.inventory = state.files.find((item) => isGood(item) && !isGoDatabase(item)) || state.goDatabase;
}

function usePastedDatabase(text) {
  $("#pasteError").classList.add("hidden");
  let data;
  try {
    data = JSON.parse(text.trim());
  } catch {
    showPasteError("The clipboard does not contain valid JSON. Copy the full database from GO and try again.");
    return false;
  }
  const item = {
    name: "Pasted GO database",
    size: new Blob([text]).size,
    data,
  };
  if (!isGoDatabase(item)) {
    showPasteError("This does not look like a full Genshin Optimizer database backup.");
    return false;
  }
  state.files = state.files.filter((existing) => !isGoDatabase(existing));
  state.files.push(item);
  classifyFiles();
  renderFileQueue();
  $("#pasteInput").value = "";
  $("#pastePanel").classList.add("hidden");
  toast("GO database added from clipboard");
  return true;
}

async function pasteGoDatabase() {
  $("#pasteError").classList.add("hidden");
  if (navigator.clipboard?.readText) {
    try {
      const text = await navigator.clipboard.readText();
      if (text.trim() && usePastedDatabase(text)) return;
    } catch {
      // Browser settings can deny clipboard access. Manual paste still works.
    }
  }
  $("#pastePanel").classList.remove("hidden");
  $("#pasteInput").focus();
}

function fileRole(item) {
  if (item === state.goDatabase && item === state.inventory) return "Inventory + team targets";
  if (item === state.goDatabase) return "GO team targets";
  if (item === state.inventory) return "Artifact inventory";
  return "Not used";
}

function renderFileQueue() {
  const queue = $("#fileQueue");
  const button = $("#importButton");
  queue.classList.toggle("hidden", state.files.length === 0);
  button.classList.toggle("hidden", !state.inventory);
  queue.innerHTML = state.files.map((item, index) => `
    <div class="file-row">
      <span class="file-badge">JSON</span>
      <p><strong>${escapeHtml(item.name)}</strong><small>${escapeHtml(fileRole(item))} · ${(item.size / 1024).toFixed(0)} KB</small></p>
      <button data-remove-file="${index}" aria-label="Remove ${escapeHtml(item.name)}">×</button>
    </div>`).join("");
  if (state.files.length && !state.inventory) {
    showError("No GOOD v3 inventory was found in the selected files.");
  }
}

async function importInventory() {
  if (!state.inventory) return;
  const button = $("#importButton");
  button.disabled = true;
  button.textContent = "Opening inventory…";
  try {
    const payload = {
      inventory: { name: state.inventory.name, data: state.inventory.data },
      goDatabase: state.goDatabase
        ? { name: state.goDatabase.name, data: state.goDatabase.data }
        : null,
    };
    const response = await fetch("/api/import", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || "Inventory could not be opened");
    state.sessionId = data.sessionId;
    state.overview = data;
    state.cleanup = null;
    state.libraryCleanup = null;
    state.upgrades = null;
    $("#cleanupSetup").classList.remove("hidden");
    $("#cleanupResults").classList.add("hidden");
    $("#libraryCleanupResults").classList.add("hidden");
    $("#upgradeEmpty").classList.remove("hidden");
    $("#upgradeResults").classList.add("hidden");
    $("#cleanupSearch").value = "";
    $("#upgradeSearch").value = "";
    renderOverview(data);
    $$(".nav-item").forEach((item) => item.disabled = false);
    $("#accountStatus").classList.remove("hidden");
    $("#accountSource").textContent = data.inventory.source;
    $("#accountFile").textContent = data.inventory.name;
    switchView("inventory");
  } catch (error) {
    showError(error.message);
  } finally {
    button.disabled = false;
    button.textContent = "Open my inventory";
  }
}

function switchView(name) {
  if (!state.sessionId && name !== "inventory") return;
  $$(".view").forEach((view) => view.classList.remove("active"));
  $$(".nav-item").forEach((item) => item.classList.toggle("active", item.dataset.view === name));
  const target = state.sessionId ? $(`#${name}View`) : $("#importView");
  target.classList.add("active");
  window.scrollTo({ top: 0, behavior: "smooth" });
}

function resetImport() {
  state.sessionId = null;
  state.overview = null;
  state.cleanup = null;
  state.libraryCleanup = null;
  state.upgrades = null;
  state.files = [];
  state.inventory = null;
  state.goDatabase = null;
  $("#fileInput").value = "";
  $("#pasteInput").value = "";
  $("#pastePanel").classList.add("hidden");
  $("#fileQueue").classList.add("hidden");
  $("#importButton").classList.add("hidden");
  $("#accountStatus").classList.add("hidden");
  $$(".nav-item").forEach((item, index) => {
    item.disabled = index > 0;
    item.classList.toggle("active", index === 0);
  });
  $$(".view").forEach((view) => view.classList.remove("active"));
  $("#importView").classList.add("active");
}

function renderOverview(data) {
  const inventory = data.inventory;
  $("#metricTotal").textContent = formatNumber.format(inventory.total);
  $("#metricMaxed").textContent = formatNumber.format(inventory.maxed);
  $("#metricUnfinished").textContent = formatNumber.format(inventory.unfinished);
  $("#metricProtected").textContent = formatNumber.format(inventory.protected);
  $("#metricSource").textContent = `${inventory.fiveStar.toLocaleString()} five-star pieces`;
  $("#setCount").textContent = `${inventory.sets} sets`;
  notices($("#noticeArea"), data.warnings);

  const maxSlot = Math.max(...inventory.slots.map((slot) => slot.count), 1);
  $("#slotChart").innerHTML = inventory.slots.map((slot) => `
    <div class="slot-bar">
      <b>${formatNumber.format(slot.count)}</b>
      <i style="height:${Math.max(5, slot.count / maxSlot * 100)}%"></i>
      <span>${escapeHtml(slot.label)}</span>
    </div>`).join("");
  $("#setList").innerHTML = inventory.topSets.map((set) => `
    <div class="set-item"><span class="set-gem">${escapeHtml(set.name.slice(0, 1))}</span><p><strong>${escapeHtml(set.name)}</strong><small>${set.count} artifacts</small></p></div>`
  ).join("");

  const maximum = Math.max(1, inventory.availableToClean);
  const suggested = Math.min(100, maximum);
  $("#freeCount").max = maximum;
  $("#freeCount").value = suggested;
  $("#freeSlider").max = maximum;
  $("#freeSlider").value = suggested;
  $("#availableLabel").textContent = `${formatNumber.format(maximum)} available`;
}

function setFreeCount(value) {
  const maximum = Number($("#freeCount").max);
  const next = Math.max(1, Math.min(maximum, Number(value) || 1));
  $("#freeCount").value = next;
  $("#freeSlider").value = next;
}

async function runJob(kind) {
  const payload = { sessionId: state.sessionId, kind };
  if (kind === "cleanup") payload.free = Number($("#freeCount").value);
  if (kind === "cleanup" && $("#cleanupEngine").value === "library") {
    try {
      const library = $("#scenarioLibraryFile").files[0];
      const mechanics = $("#mechanicsFile").files[0];
      const research = $("#researchFile").files[0];
      if (!library || !mechanics) throw new Error("Choose a scenario library and its mechanics manifest");
      payload.library = JSON.parse(await library.text());
      payload.mechanics = JSON.parse(await mechanics.text());
      payload.research = research ? JSON.parse(await research.text()) : null;
      payload.allowDraft = $("#allowDraftLibrary").checked;
      payload.reuse = $("#libraryReuse").checked;
      payload.trials = Number($("#libraryTrials").value);
      payload.population = Number($("#libraryPopulation").value);
      payload.timeLimit = Number($("#libraryTime").value);
      payload.kind = "library-cleanup";
    } catch (error) { toast(error.message); return; }
  }
  const overlay = $("#jobOverlay");
  overlay.classList.remove("hidden");
  $("#jobTitle").textContent = kind === "cleanup" ? "Building your review list" : "Testing upgrade outcomes";
  updateJobProgress(0, "Starting analysis");
  try {
    const response = await fetch("/api/jobs", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    let job = await response.json();
    if (!response.ok) throw new Error(job.error || "Analysis could not start");
    while (job.status === "queued" || job.status === "running") {
      updateJobProgress(job.progress, job.message);
      await new Promise((resolve) => window.setTimeout(resolve, 800));
      const poll = await fetch(`/api/jobs/${job.id}`);
      job = await poll.json();
      if (!poll.ok) throw new Error(job.error || "Analysis was interrupted");
    }
    if (job.status === "failed") throw new Error(job.error || "Analysis could not be completed");
    updateJobProgress(1, "Ready to review");
    if (kind === "cleanup") {
      if (payload.kind === "library-cleanup") {
        state.libraryCleanup = job.result;
        renderLibraryCleanup(job.result);
      } else {
        state.cleanup = job.result;
        renderCleanup(job.result);
      }
    } else {
      state.upgrades = job.result;
      renderUpgrades(job.result);
    }
  } catch (error) {
    toast(error.message);
  } finally {
    window.setTimeout(() => overlay.classList.add("hidden"), 300);
  }
}

function updateJobProgress(value, message) {
  const amount = Math.max(0, Math.min(1, Number(value || 0)));
  $("#jobProgress").style.width = `${amount * 100}%`;
  $("#jobPercent").textContent = `${Math.round(amount * 100)}%`;
  $("#jobMessage").textContent = message || "Working locally";
}

function artifactSearchText(item) {
  return [item.setLabel, item.slotLabel, item.mainStatLabel, item.id, item.location, ...(item.substats || []).map((stat) => stat.label)].join(" ").toLowerCase();
}

function substatLine(item) {
  return (item.substats || []).map((stat) => `${stat.label} ${stat.value}${stat.percentage ? "%" : ""}`).join(" · ");
}

function renderUpgrades(result) {
  $("#upgradeEmpty").classList.add("hidden");
  $("#upgradeResults").classList.remove("hidden");
  $("#upgradeResultCount").textContent = result.summary.count;
  notices($("#upgradeNotices"), result.warnings);
  filterUpgrades();
}

function filterUpgrades() {
  if (!state.upgrades) return;
  const query = $("#upgradeSearch").value.trim().toLowerCase();
  const items = state.upgrades.artifacts.filter((item) => !query || artifactSearchText(item).includes(query));
  $("#upgradeList").innerHTML = items.length ? items.map((item) => `
    <article class="artifact-card">
      <div class="artifact-title">
        <span class="artifact-gem">${escapeHtml(item.slotLabel.slice(0, 1))}</span>
        <p><strong>${escapeHtml(item.setLabel)}</strong><small>${escapeHtml(item.slotLabel)} · Main: ${escapeHtml(item.mainStatLabel)} · +${item.currentLevel} → +${item.nextLevel}<br>Substats: ${escapeHtml(substatLine(item))}</small></p>
        <span class="chance"><b>${percent(item.usefulChance, 0)}</b><small>useful chance</small></span>
      </div>
      <div class="artifact-meta"><span>Expected gain <b>${percent(item.expectedGain, 2)}</b></span><span>EXP <b>${formatNumber.format(item.expCost)}</b></span>${item.worthTrying ? '<span class="worth-chip">Worth trying</span>' : ""}</div>
    </article>`).join("") : '<div class="notice">No artifacts match that search.</div>';
}

function renderCleanup(result) {
  $("#libraryCleanupResults").classList.add("hidden");
  $("#cleanupSetup").classList.add("hidden");
  $("#cleanupResults").classList.remove("hidden");
  $("#cleanupResultCount").textContent = result.summary.count;
  const cacheNote = result.summary.cacheStatus === "hit" ? " · Loaded from previous analysis" : "";
  $("#cleanupLoss").textContent = `${percent(result.summary.worstEstimatedLoss, 3)} worst estimated build impact${cacheNote}`;
  $("#cleanupOrder").textContent = result.summary.orderExplanation;
  notices($("#cleanupNotices"), result.warnings);
  filterCleanup();
}

function renderLibraryCleanup(result) {
  $("#cleanupSetup").classList.add("hidden");
  $("#cleanupResults").classList.add("hidden");
  $("#libraryCleanupResults").classList.remove("hidden");
  notices($("#libraryCleanupNotices"), [
    ...(result.draft ? ["Draft scenario or sampling inputs: these lists are diagnostics, not validated game-coverage recommendations."] : []),
    result.coverage,
    "Ordinary, strong, and exceptional references use whole-slot percentiles of 80%, 95%, and 99%. Exceptional value cannot outweigh either primary objective.",
  ]);
  if (result.cacheStatistics) {
    $("#libraryCleanupNotices").innerHTML += `<details><summary>Cache reuse</summary><pre>${escapeHtml(JSON.stringify(result.cacheStatistics, null, 2))}</pre></details>`;
  }
  const views = new Map(result.artifactViews.map((item) => [item.id, item]));
  $("#libraryReviewLists").innerHTML = Object.entries(result.selections).map(([scope, selection]) => {
    const losses = selection.worstLoss === null ? "Performance unresolved" : `${percent(selection.worstLoss, 3)} worst loss · ${percent(selection.familyAverage, 3)} family average`;
    const gaps = selection.gaps.map((gap) => `<li>${escapeHtml(gap.reason)}</li>`).join("");
    const excluded = selection.excludedTargets || [];
    const excludedScenarios = [...new Set(excluded.flatMap((item) => item.scenarioIds))];
    const rows = selection.deletedArtifactIds.map((id) => {
      const item = views.get(id);
      return `<tr><td>${escapeHtml(id)}</td><td>${escapeHtml(item?.setLabel)}</td><td>${escapeHtml(item?.slotLabel)}</td><td>${escapeHtml(item?.mainStatLabel)}</td><td>${escapeHtml(item?.level)}</td></tr>`;
    }).join("");
    return `<article class="panel"><h2>${scope === "established" ? "Established coverage" : "Established + speculative coverage"}</h2>
      <p>${escapeHtml(selection.status)} · ${selection.deletedArtifactIds.length} candidates · ${escapeHtml(losses)}</p>
      ${gaps ? `<ul>${gaps}</ul>` : ""}
      ${excluded.length ? `<p>${excluded.length} targets excluded because their baseline is not positive. Scenarios: ${excludedScenarios.map(escapeHtml).join(", ")}.</p><details><summary>Excluded targets</summary><pre>${escapeHtml(JSON.stringify(excluded, null, 2))}</pre></details>` : ""}
      ${rows ? `<div class="table-wrap"><table><thead><tr><th>ID</th><th>Set</th><th>Slot</th><th>Main stat</th><th>Level</th></tr></thead><tbody>${rows}</tbody></table></div>` : "<p>No review list was produced.</p>"}
      <details><summary>Target losses and qualification frequencies</summary><pre>${escapeHtml(JSON.stringify({targets: selection.targets, qualification: selection.qualification}, null, 2))}</pre></details>
    </article>`;
  }).join("");
}

function filterCleanup() {
  if (!state.cleanup) return;
  const query = $("#cleanupSearch").value.trim().toLowerCase();
  const items = state.cleanup.artifacts.filter((item) => !query || artifactSearchText(item).includes(query));
  $("#cleanupTable").innerHTML = items.map((item) => `
    <tr>
      <td><span class="review-rank">${item.reviewOrder}</span></td>
      <td><span class="table-artifact"><strong>${escapeHtml(item.setLabel)}</strong><small>${escapeHtml(item.slotLabel)} · Main: ${escapeHtml(item.mainStatLabel)}<br>${item.rarity}★${item.locked ? " · Locked" : ""} · Substats: ${escapeHtml(substatLine(item))}${item.location ? ` · Equipped to ${escapeHtml(item.location)}` : ""}</small></span></td>
      <td><ul class="reason-list">${item.evidence.reasons.map((reason) => `<li>${escapeHtml(reason)}</li>`).join("")}</ul></td>
      <td><span class="evidence-value"><strong>${item.evidence.topBuildUse} / ${item.evidence.targetCount}</strong><small>top builds use it</small></span></td>
      <td><span class="evidence-value"><strong>${item.evidence.upgradeShortlisted ? percent(item.evidence.usefulChance, 1) : "Not shortlisted"}</strong><small>${item.level < 20 ? "after upgrading" : "already +20"}</small></span></td>
      <td><span class="level-chip">+${item.level}</span></td>
    </tr>`).join("");
}

function download(name, type, content) {
  const link = document.createElement("a");
  link.href = URL.createObjectURL(new Blob([content], { type }));
  link.download = name;
  link.click();
  window.setTimeout(() => URL.revokeObjectURL(link.href), 1000);
  toast(`Download requested: ${name}. Check your browser’s downloads.`);
}

function exportCleanupJson() {
  if (!state.cleanup) return;
  const output = {
    format: "artifact-sort-review",
    version: 1,
    warning: "Review in-game before destroying any artifact.",
    artifactIds: state.cleanup.artifacts.map((item) => item.id),
    artifacts: state.cleanup.artifacts,
  };
  download("artifact-review.json", "application/json", `${JSON.stringify(output, null, 2)}\n`);
}

function exportCleanupCsv() {
  if (!state.cleanup) return;
  const quote = (value) => `"${String(value ?? "").replaceAll('"', '""')}"`;
  const rows = [["ID", "Set", "Slot", "Main stat", "Level", "Rarity"]];
  state.cleanup.artifacts.forEach((item) => rows.push([item.id, item.setLabel, item.slotLabel, item.mainStatLabel, item.level, item.rarity]));
  download("artifact-review.csv", "text/csv", `${rows.map((row) => row.map(quote).join(",")).join("\n")}\n`);
}

$("#fileInput").addEventListener("change", (event) => readFiles(event.target.files));
$("#dropzone").addEventListener("dragover", (event) => { event.preventDefault(); event.currentTarget.classList.add("dragging"); });
$("#dropzone").addEventListener("dragleave", (event) => event.currentTarget.classList.remove("dragging"));
$("#dropzone").addEventListener("drop", (event) => { event.preventDefault(); event.currentTarget.classList.remove("dragging"); readFiles(event.dataTransfer.files); });
$("#fileQueue").addEventListener("click", (event) => {
  const button = event.target.closest("[data-remove-file]");
  if (!button) return;
  state.files.splice(Number(button.dataset.removeFile), 1);
  classifyFiles();
  renderFileQueue();
});
$("#importButton").addEventListener("click", importInventory);
$("#pasteGoButton").addEventListener("click", pasteGoDatabase);
$("#usePaste").addEventListener("click", () => usePastedDatabase($("#pasteInput").value));
$("#cancelPaste").addEventListener("click", () => {
  $("#pasteInput").value = "";
  $("#pasteError").classList.add("hidden");
  $("#pastePanel").classList.add("hidden");
});
$("#replaceFiles").addEventListener("click", resetImport);
$$(".replace-trigger").forEach((item) => item.addEventListener("click", resetImport));
$$(".nav-item").forEach((item) => item.addEventListener("click", () => switchView(item.dataset.view)));
$$('[data-go]').forEach((item) => item.addEventListener("click", () => switchView(item.dataset.go)));
$("#freeCount").addEventListener("input", (event) => setFreeCount(event.target.value));
$("#freeSlider").addEventListener("input", (event) => setFreeCount(event.target.value));
$("#freeMinus").addEventListener("click", () => setFreeCount(Number($("#freeCount").value) - 10));
$("#freePlus").addEventListener("click", () => setFreeCount(Number($("#freeCount").value) + 10));
$("#runCleanup").addEventListener("click", () => runJob("cleanup"));
$("#cleanupEngine").addEventListener("change", () => $("#libraryInputs").classList.toggle("hidden", $("#cleanupEngine").value !== "library"));
$("#exportLibraryJson").addEventListener("click", () => {
  if (state.libraryCleanup) download("scenario-library-deletion.json", "application/json", JSON.stringify(state.libraryCleanup, null, 2));
});
$("#editLibraryAnalysis").addEventListener("click", () => {
  $("#libraryCleanupResults").classList.add("hidden");
  $("#cleanupSetup").classList.remove("hidden");
});
$("#runUpgrades").addEventListener("click", () => runJob("upgrades"));
$$(".run-upgrade-trigger").forEach((item) => item.addEventListener("click", () => runJob("upgrades")));
$("#upgradeSearch").addEventListener("input", filterUpgrades);
$("#cleanupSearch").addEventListener("input", filterCleanup);
$("#exportJson").addEventListener("click", exportCleanupJson);
$("#exportCsv").addEventListener("click", exportCleanupCsv);
