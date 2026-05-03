/**
 * Background service worker for Devil's Advocate extension.
 * Handles communication between content script, popup, and the backend API.
 */

const DEFAULT_API_URL = "http://localhost:8000";

async function getApiUrl() {
  const result = await chrome.storage.local.get("apiUrl");
  return result.apiUrl || DEFAULT_API_URL;
}

// Open side panel when FAB is clicked
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === "openSidePanel" && sender.tab) {
    chrome.sidePanel.open({ tabId: sender.tab.id });
    sendResponse({ success: true });
  }
  return true;
});

// Handle analysis requests from popup/panel
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === "analyzeArticle") {
    analyzeArticle(request.data)
      .then((result) => sendResponse({ success: true, data: result }))
      .catch((err) => sendResponse({ success: false, error: err.message }));
    return true; // Keep channel open for async response
  }

  if (request.action === "checkBackendStatus") {
    checkBackendStatus()
      .then((status) => sendResponse({ success: true, data: status }))
      .catch((err) => sendResponse({ success: false, error: err.message }));
    return true;
  }

  if (request.action === "setApiUrl") {
    chrome.storage.local.set({ apiUrl: request.url });
    sendResponse({ success: true });
    return true;
  }
});

async function analyzeArticle(articleData) {
  const apiUrl = await getApiUrl();

  const response = await fetch(`${apiUrl}/api/analyze`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      title: articleData.title,
      url: articleData.url,
      text: articleData.text,
    }),
  });

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`API error (${response.status}): ${errorText}`);
  }

  return response.json();
}

async function checkBackendStatus() {
  const apiUrl = await getApiUrl();
  try {
    const response = await fetch(`${apiUrl}/api/health`, { method: "GET" });
    if (response.ok) {
      return { status: "connected", url: apiUrl };
    }
    return { status: "error", url: apiUrl, message: `HTTP ${response.status}` };
  } catch (err) {
    return { status: "disconnected", url: apiUrl, message: err.message };
  }
}

// Enable side panel for all tabs
chrome.sidePanel.setPanelBehavior({ openPanelOnActionClick: false });
