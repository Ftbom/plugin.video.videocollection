#用于格式化Kodi Label字符串

newline = '[CR]' #换行，加在字符串末尾

#自定格式，color除外
def format(origin: str, keyword: str) -> str:
    return f"[{keyword}]{origin}[/{keyword}]"

#粗体
def bold(origin: str) -> str:
    return format(origin, "B")

#斜体
def italics(origin: str) -> str:
    return format(origin, "I")

#细体
def lighten(origin: str) -> str:
    return format(origin, "LIGHT")

#颜色
def color(origin: str, color: str) -> str:
    return f"[COLOR {color}]{origin}[/COLOR]"

#大写
def uppercase(origin: str) -> str:
    return format(origin, "UPPERCASE")

#小写
def lowercase(origin: str) -> str:
    return format(origin, "LOWERCASE")

#每个首字母大小
def capitalized(origin: str) -> str:
    return format(origin, "CAPITALIZE")

#指定数量tab
def tabs(num: int) -> str:
    return format(str(num), "TABS")