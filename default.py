import xbmc
import xbmcgui
import xbmcplugin
import xbmcaddon
import os
import json
import sys
import time

ADDON = xbmcaddon.Addon()
ADDON_ID = ADDON.getAddonInfo('id')
ADDON_DATA_PATH = xbmc.translatePath(ADDON.getAddonInfo('profile')).decode('utf-8')
RESUME_FILE = os.path.join(ADDON_DATA_PATH, 'resume.json')

if not os.path.exists(ADDON_DATA_PATH):
    os.makedirs(ADDON_DATA_PATH)

def save_resume_point(video_id, position, title, url):
    resume_data = load_resume_data()
    resume_data[video_id] = {'position': position, 'title': title, 'url': url, 'last_watched': xbmc.getInfoLabel('System.Date')}
    with open(RESUME_FILE, 'w') as f:
        json.dump(resume_data, f)

def load_resume_data():
    if os.path.exists(RESUME_FILE):
        with open(RESUME_FILE, 'r') as f:
            return json.load(f)
    return {}

def get_resume_point(video_id):
    resume_data = load_resume_data()
    return resume_data.get(video_id, {}).get('position', 0)

def get_recent_items():
    resume_data = load_resume_data()
    sorted_items = sorted(resume_data.items(), key=lambda item: item[1]['last_watched'], reverse=True)
    return sorted_items[:10]

def play_video(url, video_id, title):
    resume_point = get_resume_point(video_id)
    list_item = xbmcgui.ListItem(path=url)
    list_item.setProperty("ResumeTime", str(resume_point))
    xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, list_item)

    # Monitor playback and save the resume point every 2.5 minutes
    monitor = xbmc.Monitor()
    player = xbmc.Player()
    start_time = time.time()
    while not monitor.abortRequested() and player.isPlaying():
        if time.time() - start_time > 150:  # 150 seconds = 2.5 minutes
            current_position = player.getTime()
            save_resume_point(video_id, current_position, title, url)
            start_time = time.time()  # Reset the timer
        xbmc.sleep(1000)

def show_recent_items():
    items = get_recent_items()
    for video_id, data in items:
        url = f"plugin://plugin.video.resumeaddon/?action=play&video_id={video_id}&url={data['url']}&title={data['title']}"
        li = xbmcgui.ListItem(data['title'])
        li.setInfo('video', {'title': data['title'], 'plot': f"Resume from {data['position']} seconds"})
        xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=url, listitem=li, isFolder=False)
    xbmcplugin.endOfDirectory(int(sys.argv[1]))

def router(paramstring):
    params = dict(part.split('=') for part in paramstring.split('&'))
    action = params.get('action')
    if action == 'play':
        play_video(params['url'], params['video_id'], params['title'])
    else:
        show_recent_items()

if __name__ == '__main__':
    if len(sys.argv) > 1:
        router(sys.argv[2][1:])
    else:
        show_recent_items()