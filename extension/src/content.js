/**
 * Content script for Devil's Advocate extension.
 * Extracts article text from the current web page.
 */

function extractArticleContent() {
  // Try to get article content using semantic HTML elements
  const selectors = [
    "article",
    '[role="article"]',
    ".post-content",
    ".article-content",
    ".entry-content",
    ".story-body",
    ".article-body",
    ".post-body",
    "main",
    "#content",
    ".content",
  ];

  let articleElement = null;
  for (const selector of selectors) {
    articleElement = document.querySelector(selector);
    if (articleElement && articleElement.textContent.trim().length > 200) {
      break;
    }
    articleElement = null;
  }

  // Fallback: use the largest text block
  if (!articleElement) {
    const paragraphs = document.querySelectorAll("p");
    if (paragraphs.length > 0) {
      // Find the parent with the most paragraph text
      const parentMap = new Map();
      paragraphs.forEach((p) => {
        const parent = p.parentElement;
        if (parent) {
          const current = parentMap.get(parent) || { el: parent, length: 0 };
          current.length += p.textContent.trim().length;
          parentMap.set(parent, current);
        }
      });

      let maxLength = 0;
      for (const [, value] of parentMap) {
        if (value.length > maxLength) {
          maxLength = value.length;
          articleElement = value.el;
        }
      }
    }
  }

  if (!articleElement) {
    return null;
  }

  // Extract clean text
  const clonedElement = articleElement.cloneNode(true);

  // Remove non-content elements
  const removeSelectors = [
    "script",
    "style",
    "nav",
    "header",
    "footer",
    "aside",
    ".ad",
    ".advertisement",
    ".social-share",
    ".comments",
    ".related-posts",
    ".sidebar",
    '[role="navigation"]',
    '[role="complementary"]',
  ];

  removeSelectors.forEach((sel) => {
    clonedElement.querySelectorAll(sel).forEach((el) => el.remove());
  });

  const text = clonedElement.textContent
    .replace(/\s+/g, " ")
    .replace(/\n\s*\n/g, "\n\n")
    .trim();

  return {
    title: document.title,
    url: window.location.href,
    text: text.substring(0, 15000), // Cap at 15k chars
    wordCount: text.split(/\s+/).length,
  };
}

// Listen for messages from popup/background
chrome.runtime.onMessage.addListener((request, _sender, sendResponse) => {
  if (request.action === "extractArticle") {
    const content = extractArticleContent();
    sendResponse(content);
  }
  return true;
});

// Inject the floating action button
function injectFAB() {
  if (document.getElementById("devils-advocate-fab")) return;

  const fab = document.createElement("div");
  fab.id = "devils-advocate-fab";
  fab.title = "Devil's Advocate: Generate counter-arguments";
  fab.innerHTML = `
    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
      <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 18c-4.41 0-8-3.59-8-8s3.59-8 8-8 8 3.59 8 8-3.59 8-8 8z" fill="currentColor"/>
      <path d="M15.5 11c.83 0 1.5-.67 1.5-1.5S16.33 8 15.5 8 14 8.67 14 9.5s.67 1.5 1.5 1.5zm-7 0c.83 0 1.5-.67 1.5-1.5S9.33 8 8.5 8 7 8.67 7 9.5 7.67 11 8.5 11zm3.5 6.5c2.33 0 4.31-1.46 5.11-3.5H6.89c.8 2.04 2.78 3.5 5.11 3.5z" fill="currentColor" transform="rotate(180 12 14)"/>
    </svg>
  `;

  fab.addEventListener("click", () => {
    chrome.runtime.sendMessage({ action: "openSidePanel" });
  });

  document.body.appendChild(fab);
}

// Only inject on pages that look like articles
function isArticlePage() {
  const indicators = [
    document.querySelector("article"),
    document.querySelector('[role="article"]'),
    document.querySelectorAll("p").length > 3,
    document.querySelector('meta[property="og:type"][content="article"]'),
    document.querySelector('meta[name="article:published_time"]'),
  ];
  return indicators.filter(Boolean).length >= 1;
}

if (isArticlePage()) {
  injectFAB();
}
