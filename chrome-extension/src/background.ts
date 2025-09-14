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
  console.log('[Background] Received message:', message);
  
  if (message.type === 'get-video-metadata') {
    chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
      console.log('[Background] Active tabs:', tabs);
      const activeTab = tabs[0];
      if (activeTab && activeTab.id && activeTab.url && activeTab.url.includes('youtube.com/watch')) {
        console.log('[Background] Executing script on tab:', activeTab.url);
        chrome.scripting.executeScript(
          {
            target: { tabId: activeTab.id },
            func: () => {
              const title = document.querySelector('h1.style-scope.ytd-watch-metadata')?.textContent || 
                          document.querySelector('h1.ytd-watch-metadata')?.textContent ||
                          document.querySelector('yt-formatted-string.style-scope.ytd-video-primary-info-renderer')?.textContent ||
                          '';
              console.log('[Page] Found title:', title);
              return { title };
            },
          },
          (injectionResults) => {
            if (chrome.runtime.lastError) {
              console.error('[Background] Script execution error:', chrome.runtime.lastError);
              sendResponse({ error: chrome.runtime.lastError.message });
              return;
            }
            console.log('[Background] Script results:', injectionResults);
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
        console.error('[Background] Not a YouTube video page:', activeTab?.url);
        sendResponse({ error: 'Not a YouTube video page.' });
      }
      return true; // Keep the message channel open for the asynchronous response
    });
    return true; // Keep the message channel open for the asynchronous response
  } else if (message.type === 'get-video-url') {
    chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
      const activeTab = tabs[0];
      if (activeTab && activeTab.url) {
        console.log('[Background] Sending URL:', activeTab.url);
        sendResponse({ url: activeTab.url });
      } else {
        sendResponse({ error: 'Could not get tab URL' });
      }
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
