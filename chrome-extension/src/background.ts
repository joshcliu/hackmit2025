chrome.sidePanel
  .setPanelBehavior({ openPanelOnActionClick: true })
  .catch((error) => console.error(error));

chrome.tabs.onUpdated.addListener(async (tabId, _changeInfo, tab) => {
  if (!tab.url) return;

  const isYouTubeVideo = tab.url.startsWith('https://www.youtube.com/watch');

  await chrome.sidePanel.setOptions({
    tabId,
    path: 'src/sidepanel/index.html',
    enabled: isYouTubeVideo,
  });
});

chrome.runtime.onMessage.addListener((message, _sender, sendResponse) => {
  if (message.type === 'get-video-metadata') {
    chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
      const activeTab = tabs[0];
      if (activeTab && activeTab.id && activeTab.url && activeTab.url.includes('youtube.com/watch')) {
        chrome.scripting.executeScript(
          {
            target: { tabId: activeTab.id },
            func: () => {
              const title = document.querySelector('h1.style-scope.ytd-watch-metadata')?.textContent || '';
              return { title };
            },
          },
          (injectionResults) => {
            if (chrome.runtime.lastError) {
              sendResponse({ error: chrome.runtime.lastError.message });
              return;
            }
            for (const frameResult of injectionResults) {
              if (frameResult.result) {
                sendResponse(frameResult.result);
                return;
              }
            }
            sendResponse({ error: 'Could not retrieve metadata.' });
          }
        );
      } else {
        sendResponse({ error: 'Not a YouTube video page.' });
      }
      return true; // Keep the message channel open for the asynchronous response
    });
    return true; // Keep the message channel open for the asynchronous response
  } else if (message.type === 'seek-video') {
    chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
      const activeTab = tabs[0];
      if (activeTab && activeTab.id && activeTab.url && activeTab.url.includes('youtube.com/watch')) {
        chrome.scripting.executeScript(
          {
            target: { tabId: activeTab.id },
            func: (seconds) => {
              const video = document.querySelector('video');
              if (video) {
                video.currentTime = seconds;
                return { success: true };
              }
              return { error: 'Video element not found.' };
            },
            args: [message.seconds]
          },
          (injectionResults) => {
            if (chrome.runtime.lastError) {
              sendResponse({ error: chrome.runtime.lastError.message });
              return;
            }
            for (const frameResult of injectionResults) {
              if (frameResult.result) {
                sendResponse(frameResult.result);
                return;
              }
            }
            sendResponse({ error: 'Could not seek video.' });
          }
        );
      } else {
        sendResponse({ error: 'Not a YouTube video page.' });
      }
      return true; // Keep the message channel open for the asynchronous response
    });
    return true; // Keep the message channel open for the asynchronous response
  }
});
