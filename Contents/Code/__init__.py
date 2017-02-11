from cStringIO import StringIO
import re

ATTRIBUTELISTPATTERN = re.compile(r'''((?:[^,"']|"[^"]*"|'[^']*')+)''')
ext_x_stream_inf = '#EXT-X-STREAM-INF'

TITLE = 'Austin News' # Your Channel title here
PREFIX = '/video/austinnews' # Change the 'youruniqueidhere' part

ART = 'art-default.jpg'
ICON = 'icon-default.png'

#CH7NEWS_ART = '7News-art.jpg'
#CH7NEWS_ICON = '7News-icon.jpg'
#CH7NEWS_URL = "http://stskmghstr01-i.akamaihd.net/hls/live/203185/anvato/master.m3u8"
#CH7NEWS_SUMMARY = "Live webcasts are available at the following times: \n\nMonday - Friday: 4:30 - 7:00 AM, 11:00 - 12:00 PM, 5:00 - 5:30 PM, 10:00 - 10:30 PM\n\nSaturday: 7:00 - 9:00 AM, 5:00 - 6:00 PM, 10:00 - 10:30 PM\n\nSunday: 7:00 - 10:00 AM, 5:00 - 6:00 PM, 10:00 - 11:00 PM"

KXAN_ART = 'KXAN-art.jpg'
KXAN_ICON = 'KXAN-icon.jpg'
KXAN_LIVESTREAM_SUB = "1506296"
KXAN_SUMMARY = "Live webcasts are available at the following times: \n\nUNKNOWN"

FOX7_ART = 'FOX7-art.jpg'
FOX7_ICON = 'FOX7-icon.jpg'
FOX7_LIVESTREAM_SUB = "6396024"
FOX7_SUMMARY = "Live webcasts are available at the following times: \n\nUNKNOWN"

###################################################################################################
def Start():

    ObjectContainer.art = R(ART)
    ObjectContainer.title1 = TITLE

    DirectoryObject.thumb = R(ICON)
    VideoClipObject.thumb = R(ICON)
    InputDirectoryObject.thumb = R(ICON)
    PrefsObject.thumb = R(ICON)
    NextPageObject.thumb = R(ICON)

    HTTP.CacheTime = 1
    HTTP.Headers['User-Agent'] = "Mozilla/5.0 (iPhone; U; CPU iPhone OS 4_0 like Mac OS X; en-us) AppleWebKit/532.9 (KHTML, like Gecko) Version/4.0.5 Mobile/8A293 Safari/6531.22.7"

###################################################################################################
@handler(PREFIX, TITLE, thumb=ICON, art=ART)
def MainMenu():

    oc = ObjectContainer()

    oc.add(StreamfromLiveStreamAPI(KXAN_LIVESTREAM_SUB, "KXAN News Live", KXAN_ICON, KXAN_ART, KXAN_SUMMARY))
    oc.add(StreamfromLiveStreamAPI(FOX7_LIVESTREAM_SUB, "Fox 7 News Live", FOX7_ICON, FOX7_ART, FOX7_SUMMARY))
    
    #oc.add(StreamM3U8("9 News Live - KUSA", CH9NEWS_ICON, CH9NEWS_ART, CH9NEWS_URL, CH9NEWS_SUMMARY))

    return oc
###################################################################################################
def StreamfromLiveStreamAPI(subId, title1, icon, art, summary, include_container=False):
    url = getLiveStreamAPIURL(subId)
    Log.Debug("****** FOUND livestream.com URL for %s at %s", subId, url)
    return StreamM3U8(title1, icon, art, url, summary)
###################################################################################################
def StreamM3U8(title1, icon, art, url, summary, include_container=False):
    stream = GetStreamURL(url)
    vco = VideoClipObject(
        key = Callback(StreamM3U8, title1=title1, icon=icon, art=art, url=url, summary=summary, include_container=True),
        rating_key = url,
        title = title1,
        art = R(art),
        thumb = R(icon),
        summary = summary,
        items = [
            MediaObject(
                optimized_for_streaming = True,                   
                parts = [
                    PartObject(key=HTTPLiveStreamURL(url = stream))
                ]
            )
        ]
    )

    if include_container:
        return ObjectContainer(objects=[vco])
    else:
        return vco
###################################################################################################
def GetStreamURL(url):
    content = HTTP.Request(url, cacheTime=1).content
    buf = StringIO(content)
    lines = buf.readlines()
    best_bandwidth = 0L
    best_url = '' 
    for index, line in enumerate(lines):
        bandwidth = getBandwidth(line)
        if bandwidth > best_bandwidth:
        	best_bandwidth = bandwidth
        	best_url = lines[index + 1]

    if best_url != '':
            Log.Debug("Streaming URL found = %s", best_url)
            return best_url.rstrip()
    Log.Error("Could not determine the stream from %s", url)
    Log.Error("Content = %s", url)
    return ""
###################################################################################################
def getBandwidth(line):
    params = ATTRIBUTELISTPATTERN.split(line.replace(ext_x_stream_inf + ':', ''))[1::2]
    if len(params) <= 1:
        return 0

    for param in params:
        if param.startswith('BANDWIDTH'):
            name, value = param.split('=', 1)
            return long(value)

    return 0 
###################################################################################################
def normalize_attribute(attribute):
    return attribute.replace('-', '_').lower().strip()
###################################################################################################
def getLiveStreamAPIURL(id):
    idObj = JSON.ObjectFromURL("http://api.new.livestream.com/accounts/" + id)
    events = idObj["upcoming_events"]["data"]
    eventId = getLiveStreamEventId(events)
    Log.Debug("******* ID = %s and EventID = %s",id,eventId)
    eventObj = JSON.ObjectFromURL("http://api.new.livestream.com/accounts/" + id + "/events/" + str(eventId))
    return eventObj["stream_info"]["m3u8_url"]
###################################################################################################
def getLiveStreamEventId(events):
    for event in events:
        if event["short_name"] == "live":
            return event["id"]
    Log.Error("Cannot find a live event from the livestream JSON")
    return ''
###################################################################################################
