import requests
import resources.lib.fmt as fmt

def get_urls(base_url: str) -> tuple:
    base_url = base_url.strip("/").split("/api.php")[0]
    base_url = base_url
    api_url = base_url + "/api.php/provide/vod/"
    return (base_url, api_url)
    
def get_categories(source_url) -> dict:
    urls = get_urls(source_url)
    categories = {"全部": ""}
    categories_data = requests.get(urls[1], headers = {"Referer": urls[0]}).json()
    for c in categories_data["class"]:
        categories[c["type_name"]] = str(c["type_id"])
    return categories

def list_parse(url, base_url) -> list:
    data = requests.get(url, headers = {"Referer": base_url}).json()
    results = []
    for i in data["list"]:
        description = fmt.italics(fmt.color(i["vod_sub"], "yellow")) + fmt.newline
        description = description + fmt.color(i["vod_actor"], "red") + fmt.newline
        description = description + fmt.color(i["vod_area"], "green") + fmt.newline
        description = description + fmt.color(i["vod_class"], "blue") + fmt.newline
        description = description + fmt.bold(i["vod_content"].replace("<p>", "").replace("</p>", ""))
        results.append({"vid": str(i["vod_id"]), "title": i["vod_name"], "description": description,
                        "cover": {"url": i["vod_pic"], "headers": {"Referer": base_url}}})
    return results
    
def get_category_list(source_url, category_id: str, page: int) -> list:
    urls = get_urls(source_url)
    url = urls[1] + f"?ac=videolist&pg={page}&t={category_id}"
    return list_parse(url, urls[0])

def get_search_list(source_url, query: str, page: int) -> list:
    urls = get_urls(source_url)
    url = urls[1] + f"?ac=videolist&wd={query}&pg={page}"
    return list_parse(url, urls[0])
    
def get_detail(source_url, vid: str) -> dict:
    urls = get_urls(source_url)
    url = urls[1] + f"?ac=detail&ids={vid}"
    data = requests.get(url, headers = {"Referer": urls[0]}).json()["list"][0]
    description = fmt.italics(fmt.color(data["vod_sub"], "yellow")) + fmt.newline
    description = description + fmt.color(data["vod_actor"], "red") + fmt.newline
    description = description + fmt.color(data["vod_area"], "green") + fmt.newline
    description = description + fmt.color(data["vod_class"], "blue") + fmt.newline
    description = description + fmt.bold(data["vod_content"].replace("<p>", "").replace("</p>", ""))
    if (data["vod_play_note"] != "") and (data["vod_play_note"] in data["vod_play_url"]):
        playlist_urls = data["vod_play_url"].split(data["vod_play_note"])[1].split("#")
    else:
        playlist_urls = data["vod_play_url"].split("#")
    playlist = {}
    for i in playlist_urls:
        p = i.split("$")
        playlist[p[0]] = p[1]
    return {"vid": str(data["vod_id"]), "title": data["vod_name"], "description": description, "playlist": playlist,
            "play_headers": {"Referer": urls[0]}, "cover": {"url": data["vod_pic"], "headers": {"Referer": urls[0]}}}
