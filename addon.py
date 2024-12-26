import sys

import xbmc
import xbmcaddon
import xbmcplugin
import xbmcgui

import os
import json
import sqlite3
import base64
from urllib.parse import parse_qsl

import resources.lib.fmt as fmt

#插件信息
__url__ = sys.argv[0]
__handle__ = int(sys.argv[1])

xbmcplugin.setContent(__handle__, 'movies')

from resources.lib.vod import *

#主界面
#列出源
def mainMenu():
    menuItems = []
    #收藏
    item = xbmcgui.ListItem(label = fmt.bold(fmt.color("固定项", "red")))
    url = f'{__url__}?action=list_favorite' #action url
    menuItems.append((url, item, True))
    source_urls = xbmcplugin.getSetting(__handle__, 'source')
    for source_url in source_urls.split('#'):
        s = source_url.split("$")
        item = xbmcgui.ListItem(label = fmt.bold(fmt.color(s[0], 'yellow')))
        url = f'{__url__}?action=list_categories&source_url={s[1]}' #action url
        menuItems.append((url, item, True))
    xbmcplugin.addDirectoryItems(__handle__, menuItems, len(menuItems)) #添加条目
    xbmcplugin.addSortMethod(__handle__, xbmcplugin.SORT_METHOD_NONE) #不排序
    xbmcplugin.endOfDirectory(__handle__) #添加结束

#列出分类列表
def list_categories(source_url: str):
    #导入源
    menuItems = []
    #搜索项
    menuItem = xbmcgui.ListItem(label = fmt.color('搜索', 'yellow'))
    url = f"{__url__}?action=list_search_results&source_url={source_url}&page=1"
    menuItems.append((url, menuItem, True))
    #类别
    categories = get_categories(source_url)
    for key in categories:
        menuItem = xbmcgui.ListItem(label = str(key))
        url = f"{__url__}?action=list_videos&source_url={source_url}&cid={categories[key]}&page=1"
        menuItems.append((url, menuItem, True))
    xbmcplugin.addDirectoryItems(__handle__, menuItems, len(menuItems))
    xbmcplugin.addSortMethod(__handle__, xbmcplugin.SORT_METHOD_NONE) #不排序
    xbmcplugin.endOfDirectory (__handle__)

def add_videos(source_url: str, results: list, next_page: str):
    menuItems = []
    #添加结果
    for result in results:
        #获取图片headers
        headers_str = '|'
        for header_key in result['cover']['headers'].keys():
            headers_str = headers_str + f'{header_key}={result["cover"]["headers"][header_key]}&'
        if (headers_str == '|'):
            headers_str == ''
        else:
            headers_str.strip('&')
        cover_url = result['cover']['url'] + headers_str
        url = f"{__url__}?action=list_playlist&source_url={source_url}&vid={result['vid']}"
        menuItem = xbmcgui.ListItem(label = str(result['title']))
        menuItem.setArt({'poster': cover_url})
        menuItem.setInfo('video', {'plot': result['description']}) #显示详情
        #添加到收藏菜单
        favorite_data = {'title': str(result['title']), 'cover': cover_url, 'description': result['description'], 'url': url}
        favorite_url = f"{__url__}?action=add_favorite&data={base64.b64encode(json.dumps(favorite_data).encode('utf-8')).decode('utf-8')}"
        menuItem.addContextMenuItems([("添加到固定", f'RunPlugin({favorite_url})')])
        menuItems.append((url, menuItem, True))
    #下一页
    if len(results) > 0:
        menuItem = xbmcgui.ListItem(label = fmt.color('>>下一页', 'yellow'))
        menuItems.append((next_page, menuItem, True))
    xbmcplugin.addDirectoryItems(__handle__, menuItems, len(menuItems))
    xbmcplugin.addSortMethod(__handle__, xbmcplugin.SORT_METHOD_NONE) #不排序
    xbmcplugin.endOfDirectory (__handle__)

#列出视频列表
def list_videos(source_url: str, cid: str, page: int):
    results = get_category_list(source_url, cid, page) #获取列表
    add_videos(source_url, results, f"{__url__}?action=list_videos&source_url={source_url}&cid={cid}&page={page + 1}")

#列出搜索视频列表
def list_search_results(query, source_url: str, page: int):
    if (query == None):
        kb = xbmc.Keyboard('', '输入搜索关键词')
        kb.doModal()
        if not kb.isConfirmed():
            return
        query = kb.getText() #用户输入
    results = get_search_list(source_url, query, page)
    add_videos(source_url, results, f"{__url__}?action=list_search_results&source_url={source_url}&page={page + 1}&query={query}")

#列出所有集
def list_playlist(source_url: str, vid: str):
    results = get_detail(source_url, vid)
    #获取图片headers
    headers_str = '|'
    for header_key in results['cover']['headers'].keys():
        headers_str = headers_str + f'{header_key}={results["cover"]["headers"][header_key]}&'
    if (headers_str == '|'):
        headers_str == ''
    else:
        headers_str.strip('&')
    cover_url = results['cover']['url'] + headers_str
    #获取详情
    description = fmt.bold(results['title']) + fmt.newline + results['description']
    menuItems = []
    headers_str = '|'
    for header_key in results['play_headers'].keys():
        headers_str = headers_str + f'{header_key}={results["play_headers"][header_key]}&'
    if (headers_str == '|'):
        headers_str == ''
    else:
        headers_str.strip('&')
    for name in results['playlist'].keys():
        play_url = results['playlist'][name] + headers_str
        menuItem = xbmcgui.ListItem(label = name, path = play_url)
        menuItem.setArt({'poster': cover_url})
        menuItem.setInfo('video', {'genre': '', 'plot': description})
        menuItems.append((play_url, menuItem, False))
    xbmcplugin.addDirectoryItems(__handle__, menuItems, len(menuItems))
    xbmcplugin.addSortMethod(__handle__, xbmcplugin.SORT_METHOD_NONE) #不排序
    xbmcplugin.endOfDirectory (__handle__)

def add_favorite(data_str: str):
    data = json.loads(base64.b64decode(data_str.encode('utf-8')).decode('utf-8'))
    con = sqlite3.connect(os.path.join(xbmcaddon.Addon("plugin.video.videocollection").getAddonInfo("path"), 'resources/favorite.db'))
    cur = con.cursor()
    cur.executemany("INSERT INTO favorite VALUES(?, ?, ?, ?)",
                    [(data['title'], data['cover'], data['description'], data['url'])])
    con.commit()
    cur.close()
    con.close()

def list_favorite():
    con = sqlite3.connect(os.path.join(xbmcaddon.Addon("plugin.video.videocollection").getAddonInfo("path"), 'resources/favorite.db'))
    cur = con.cursor()
    menuItems = []
    #列出所有
    results = cur.execute("SELECT title, cover, description, url FROM favorite WHERE title like '%%'")
    for result in results.fetchall():
        url = result[3]
        menuItem = xbmcgui.ListItem(label = result[0])
        menuItem.setArt({'poster': result[1]})
        menuItem.setInfo('video', {'plot': result[2]})
        #从收藏菜单删除
        menu_url = f"{__url__}?action=remove_favorite&data={result[0]}"
        menuItem.addContextMenuItems([("从收藏移除", f'RunPlugin({menu_url})')])
        menuItems.append((url, menuItem, True))
    xbmcplugin.addDirectoryItems(__handle__, menuItems, len(menuItems))
    xbmcplugin.addSortMethod(__handle__, xbmcplugin.SORT_METHOD_NONE) #不排序
    xbmcplugin.endOfDirectory (__handle__)
    cur.close()
    con.close()

def remove_favorite(title: str):
    con = sqlite3.connect(os.path.join(xbmcaddon.Addon("plugin.video.videocollection").getAddonInfo("path"), 'resources/favorite.db'))
    cur = con.cursor()
    cur.execute(f"DELETE FROM favorite WHERE title like '{title}'")
    con.commit()
    cur.close()
    con.close()
    return

#url
def routes(paramString):
    params = dict(parse_qsl(paramString[1 :]))
    if params:
        action = params['action']
        if action == 'list_categories': #列出类别
            list_categories(params['source_url'])
        elif action == 'list_videos': #列出指定类别下条目
            try:
                list_videos(params['source_url'], params['cid'], int(params['page']))
            except:
                list_videos(params['source_url'], '', int(params['page']))
        elif action == 'list_playlist': #列出集
            list_playlist(params['source_url'], params['vid'])
        elif action == 'list_search_results': #列出搜索结果
            if 'query' in params:
                list_search_results(params['query'], params['source_url'], int(params['page'])) #用于加载下一页
            else:
                list_search_results(None, params['source_url'], int(params['page'])) #用于键盘输入搜索
        elif action == 'add_favorite':
            add_favorite(params['data'])
        elif action == 'list_favorite':
            list_favorite()
        elif action == 'remove_favorite':
            remove_favorite(params['data'])
    else:
        mainMenu()

if __name__ == '__main__' :
    routes(sys.argv[2])