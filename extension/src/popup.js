/**
 * Popup script for Devil's Advocate extension.
 */

const analyzeBtn = document.getElementById("analyzeBtn");
const statusDot = document.getElementById("statusDot");
const statusText = document.getElementById("statusText");
const articleInfo = document.getElementById("articleInfo");
const articleTitle = document.getElementById("articleTitle");
const articleMeta = document.getElementById("articleMeta");
const loading = document.getElementById("loading");
const error = document.getElementById("error");
const errorText = document.getElementById("errorText");
const retryBtn = document.getElementById("retryBtn");
const settingsBtn = document.getElementById("settingsBtn");
const settingsPanel = document.getElementById("settingsPanel");
const apiUrlInput = document.getElementById("apiUrlInput");
const saveApiUrl = document.getElementById("saveApiUrl");

let extractedArticle = null;

// Check backend status on popup open
async function checkStatus() {
  try {
    const response = await chrome.runtime.sendMessage({
      action: "checkBackendStatus",
    });
    if (response.success && response.data.status === "connected") {
      statusDot.className = "status-dot connected";
      statusText.textContent = "Backend connected";
      return true;
    } else {
      statusDot.className = "status-dot disconnected";
      statusText.textContent = "Backend not running — start it with: research-agent --serve";
      return false;
    }
  } catch {
    statusDot.className = "status-dot disconnected";
    statusText.textContent = "Cannot reach backend";
    return false;
  }
}

// Extract article from current tab
async function extractArticle() {
  try {
    const [tab] = await chrome.tabs.query({
      active: true,
      currentWindow: true,
    });
    if (!tab) return null;

    const response = await chrome.tabs.sendMessage(tab.id, {
      action: "extractArticle",
    });
    return response;
  } catch {
    return null;
  }
}

// Initialize popup
async function init() {
  const isConnected = await checkStatus();

  extractedArticle = await extractArticle();

  if (extractedArticle && extractedArticle.text) {
    articleInfo.classList.remove("hidden");
    articleTitle.textContent = extractedArticle.title || "Untitled Article";
    articleMeta.textContent = `${extractedArticle.wordCount} words detected`;
    analyzeBtn.disabled = !isConnected;
  } else {
    articleInfo.classList.remove("hidden");
    articleTitle.textContent = "No article detected";
    articleMeta.textContent =
      "Navigate to a news article or opinion piece to analyze it";
    analyzeBtn.disabled = true;
  }

  // Load saved API URL
  const result = await chrome.storage.local.get("apiUrl");
  if (result.apiUrl) {
    apiUrlInput.value = result.apiUrl;
  }
}

// Analyze button click
analyzeBtn.addEventListener("click", async () => {
  if (!extractedArticle) return;

  analyzeBtn.classList.add("hidden");
  error.classList.add("hidden");
  loading.classList.remove("hidden");

  try {
    const response = await chrome.runtime.sendMessage({
      action: "analyzeArticle",
      data: extractedArticle,
    });

    if (response.success) {
      // Store results and open side panel
      await chrome.storage.local.set({
        lastAnalysis: response.data,
        lastArticle: extractedArticle,
      });

      // Open side panel
      const [tab] = await chrome.tabs.query({
        active: true,
        currentWindow: true,
      });
      if (tab) {
        chrome.sidePanel.open({ tabId: tab.id });
      }
      window.close();
    } else {
      throw new Error(response.error || "Analysis failed");
    }
  } catch (err) {
    loading.classList.add("hidden");
    analyzeBtn.classList.remove("hidden");
    error.classList.remove("hidden");
    errorText.textContent = err.message;
  }
});

// Retry button
retryBtn.addEventListener("click", () => {
  error.classList.add("hidden");
  analyzeBtn.click();
});

// Settings toggle
settingsBtn.addEventListener("click", () => {
  settingsPanel.classList.toggle("hidden");
});

// Save API URL
saveApiUrl.addEventListener("click", async () => {
  const url = apiUrlInput.value.trim();
  if (url) {
    await chrome.runtime.sendMessage({ action: "setApiUrl", url });
    await checkStatus();
  }
});

init();
