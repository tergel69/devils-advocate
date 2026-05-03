/**
 * Side panel script for Devil's Advocate extension.
 * Displays counter-arguments and sources.
 */

const emptyState = document.getElementById("emptyState");
const loadingState = document.getElementById("loadingState");
const loadingStep = document.getElementById("loadingStep");
const progressFill = document.getElementById("progressFill");
const results = document.getElementById("results");
const originalSummary = document.getElementById("originalSummary");
const originalClaims = document.getElementById("originalClaims");
const counterArguments = document.getElementById("counterArguments");
const sourcesList = document.getElementById("sourcesList");
const biasAssessment = document.getElementById("biasAssessment");
const refreshBtn = document.getElementById("refreshBtn");

function showState(state) {
  emptyState.classList.add("hidden");
  loadingState.classList.add("hidden");
  results.classList.add("hidden");

  if (state === "empty") emptyState.classList.remove("hidden");
  if (state === "loading") loadingState.classList.remove("hidden");
  if (state === "results") results.classList.remove("hidden");
}

function animateProgress() {
  const steps = [
    { text: "Extracting main arguments...", progress: 15 },
    { text: "Identifying key claims...", progress: 30 },
    { text: "Searching for counter-evidence...", progress: 50 },
    { text: "Reading counter-sources...", progress: 65 },
    { text: "Building counter-arguments...", progress: 80 },
    { text: "Assessing bias and balance...", progress: 95 },
  ];

  let i = 0;
  const interval = setInterval(() => {
    if (i >= steps.length) {
      clearInterval(interval);
      return;
    }
    loadingStep.textContent = steps[i].text;
    progressFill.style.width = steps[i].progress + "%";
    i++;
  }, 3000);

  return interval;
}

function renderResults(data) {
  // Render original summary
  originalSummary.textContent = data.original_summary || "No summary available.";

  // Render original claims
  originalClaims.innerHTML = "";
  if (data.original_claims && data.original_claims.length > 0) {
    data.original_claims.forEach((claim, idx) => {
      const el = document.createElement("div");
      el.className = "claim-tag";
      el.innerHTML = `<span class="claim-number">${idx + 1}</span><span>${escapeHtml(claim)}</span>`;
      originalClaims.appendChild(el);
    });
  }

  // Render counter-arguments
  counterArguments.innerHTML = "";
  if (data.counter_arguments && data.counter_arguments.length > 0) {
    data.counter_arguments.forEach((arg, idx) => {
      const card = document.createElement("div");
      card.className = "counter-card";

      let evidenceHtml = "";
      if (arg.evidence) {
        evidenceHtml = `
          <div class="counter-evidence">
            <strong>Evidence:</strong><br>
            ${escapeHtml(arg.evidence)}
          </div>
        `;
      }

      let sourcesHtml = "";
      if (arg.source_urls && arg.source_urls.length > 0) {
        sourcesHtml = arg.source_urls
          .map(
            (url) =>
              `<a href="${escapeHtml(url)}" target="_blank" class="counter-source-link">${truncateUrl(url)}</a>`
          )
          .join(" ");
      }

      card.innerHTML = `
        <div class="counter-card-header">
          <span class="counter-number">${idx + 1}</span>
          <h3>${escapeHtml(arg.title || "Counter-point")}</h3>
        </div>
        <div class="counter-card-body">${escapeHtml(arg.argument)}</div>
        ${evidenceHtml}
        ${sourcesHtml}
      `;

      counterArguments.appendChild(card);
    });
  }

  // Render sources
  sourcesList.innerHTML = "";
  if (data.sources && data.sources.length > 0) {
    data.sources.forEach((source, idx) => {
      const el = document.createElement("div");
      el.className = "source-item";
      el.innerHTML = `
        <span class="source-index">${idx + 1}</span>
        <div class="source-info">
          <div class="source-title">${escapeHtml(source.title || "Source")}</div>
          <a href="${escapeHtml(source.url)}" target="_blank" class="source-url">${escapeHtml(source.url)}</a>
        </div>
      `;
      sourcesList.appendChild(el);
    });
  }

  // Render bias assessment
  if (data.bias_assessment) {
    const bias = data.bias_assessment;
    const biasScore = bias.score !== undefined ? bias.score : 50;

    biasAssessment.innerHTML = `
      <div class="bias-meter">
        <div class="bias-bar">
          <div class="bias-indicator" style="left: ${biasScore}%"></div>
        </div>
      </div>
      <div class="bias-labels">
        <span>Strongly Biased</span>
        <span>Moderate</span>
        <span>Well Balanced</span>
      </div>
      <div class="bias-text">${escapeHtml(bias.explanation || "")}</div>
    `;
  }

  showState("results");
}

function escapeHtml(str) {
  if (!str) return "";
  const div = document.createElement("div");
  div.textContent = str;
  return div.innerHTML;
}

function truncateUrl(url) {
  try {
    const u = new URL(url);
    return u.hostname + (u.pathname.length > 30 ? u.pathname.substring(0, 30) + "..." : u.pathname);
  } catch {
    return url.substring(0, 50);
  }
}

// Check for stored results on load
async function init() {
  const result = await chrome.storage.local.get(["lastAnalysis", "lastArticle"]);
  if (result.lastAnalysis) {
    renderResults(result.lastAnalysis);
  } else {
    showState("empty");
  }
}

// Listen for new analysis results
chrome.storage.onChanged.addListener((changes) => {
  if (changes.lastAnalysis && changes.lastAnalysis.newValue) {
    renderResults(changes.lastAnalysis.newValue);
  }
});

// Refresh button: re-analyze current tab
refreshBtn.addEventListener("click", async () => {
  showState("loading");
  const progressInterval = animateProgress();

  try {
    const [tab] = await chrome.tabs.query({
      active: true,
      currentWindow: true,
    });
    if (!tab) throw new Error("No active tab");

    const article = await chrome.tabs.sendMessage(tab.id, {
      action: "extractArticle",
    });
    if (!article || !article.text) throw new Error("No article content found");

    const response = await chrome.runtime.sendMessage({
      action: "analyzeArticle",
      data: article,
    });

    clearInterval(progressInterval);

    if (response.success) {
      await chrome.storage.local.set({
        lastAnalysis: response.data,
        lastArticle: article,
      });
    } else {
      throw new Error(response.error || "Analysis failed");
    }
  } catch (err) {
    clearInterval(progressInterval);
    showState("empty");
    console.error("Analysis error:", err);
  }
});

init();
