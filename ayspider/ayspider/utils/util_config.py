# _*_ coding: utf-8 _*_

"""
util_config.py by xianhu
"""

__all__ = [
    "CONFIG_URLPATTERN_ALL",
    "CONFIG_URLPATTERN_FILES",
    "CONFIG_URLPATTERN_IMAGE",
    "CONFIG_URLPATTERN_VIDEO",
    "CONFIG_USERAGENT_PC",
    "CONFIG_USERAGENT_PHONE",
    "CONFIG_USERAGENT_ALL",
]


# define url_patterns, include urlpattern_all, urlpattern_files, urlpattern_image and urlpattern_video
CONFIG_URLPATTERN_ALL = r"\.(cab|iso|zip|rar|tar|gz|bz2|7z|tgz|apk|exe|app|pkg|bmg|rpm|deb|dmg|jar|jad|bin|msi|" \
                        "pdf|doc|docx|xls|xlsx|ppt|pptx|txt|md|odf|odt|rtf|py|pyc|java|c|cc|js|css|log|" \
                        "jpg|jpeg|png|gif|bmp|xpm|xbm|ico|drm|dxf|eps|psd|pcd|pcx|tif|tiff|" \
                        "mp3|mp4|swf|mkv|avi|flv|mov|wmv|wma|3gp|mpg|mpeg|mp4a|wav|ogg|rmvb)$"

CONFIG_URLPATTERN_FILES = r"\.(cab|iso|zip|rar|tar|gz|bz2|7z|tgz|apk|exe|app|pkg|bmg|rpm|deb|dmg|jar|jad|bin|msi|" \
                          "pdf|doc|docx|xls|xlsx|ppt|pptx|txt|md|odf|odt|rtf|py|pyc|java|c|cc|js|css|log)$"

CONFIG_URLPATTERN_IMAGE = r"\.(jpg|jpeg|png|gif|bmp|xpm|xbm|ico|drm|dxf|eps|psd|pcd|pcx|tif|tiff)$"

CONFIG_URLPATTERN_VIDEO = r"\.(mp3|mp4|swf|mkv|avi|flv|mov|wmv|wma|3gp|mpg|mpeg|mp4a|wav|ogg|rmvb)$"


# define user_agents, include useragent_pc, useragent_phone and useragent_all
CONFIG_USERAGENT_PC = [
    "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/52.0.2743.116 Safari/537.36",
    "Mozilla/5.0 (Windows NT 6.3; WOW64; rv:55.0) Gecko/20100101 Firefox/55.0",
]

CONFIG_USERAGENT_PHONE = [
    "Mozilla/5.0 (iPad; CPU OS 4_3_5 like Mac OS X) AppleWebKit/534.46 (KHTML, like Gecko) Mobile/9B176",
    "Mozilla/5.0 (iPad; CPU OS 5_0_1 like Mac OS X) AppleWebKit/534.46 (KHTML, like Gecko) FlyFlow/2.0 Mobile/9A405",
    "Mozilla/5.0 (iPad; CPU OS 5_0_1 like Mac OS X) AppleWebKit/534.46 (KHTML, like Gecko) Mobile/9B176",
    "Mozilla/5.0 (iPad; CPU OS 5_0 like Mac OS X) AppleWebKit/534.46 (KHTML, like Gecko) Mobile/9A334",
    "Mozilla/5.0 (iPad; CPU OS 5_1_1 like Mac OS X) AppleWebKit/534.46 (KHTML, like Gecko) FlyFlow/2.0 Mobile/9B206",
    "Mozilla/5.0 (iPad; CPU OS 6_0_1 like Mac OS X) AppleWebKit/534.46 (KHTML, like Gecko) Mobile/9B176",
    "Mozilla/5.0 (iPad; CPU OS 6_1_2 like Mac OS X) AppleWebKit/536.26 (KHTML, like Gecko) Mobile/10B146",
    "Mozilla/5.0 (iPad; CPU OS 7_0_2 like Mac OS X) AppleWebKit/534.46 (KHTML, like Gecko) Mobile/9B176",
    "Mozilla/5.0 (iPad; CPU OS 7_0_6 like Mac OS X) AppleWebKit/537.51.1 (KHTML, like Gecko) Mobile/11B651",
    "Mozilla/5.0 (iPad; CPU OS 7_1_1 like Mac OS X) AppleWebKit/537.51.2 (KHTML, like Gecko) Mobile/11D201",
]

CONFIG_USERAGENT_ALL = CONFIG_USERAGENT_PC + CONFIG_USERAGENT_PHONE


# request headers
CONFIG_HEADERS = {
    "Accept", "Accept-Charset", "Accept-Encoding", "Accept-Language", "Accept-Ranges",
    "Age", "Allow", "Authorization", "Cache-Control", "Connection",
    "Content-Encoding", "Content-Language", "Content-Length", "Content-Location", "Content-MD5", "Content-Range", "Content-Type",
    "Cookie", "Date", "ETag", "Expect", "Expires", "From", "Host",
    "If-Match", "If-Modified-Since", "If-None-Match", "If-Range", "If-Unmodified-Since",
    "Last-Modified", "Location", "Max-Forwards", "Pragma", "Proxy-Authenticate", "Proxy-Authorization", "Range", "Referer", "Retry-After",
    "Server", "TE", "Trailer", "Transfer-Encoding", "Upgrade", "User-Agent", "Vary", "Via",
    "Warning", "WWW-Authenticate", "Origin", "Upgrade-Insecure-Requests", "X_FORWARDED_FOR"
}
