# 官方政策发布页面（近3年）
SOURCES = [
    {
        "name": "国家能源局",
        "base_url": "http://www.nea.gov.cn",
        "list_url": "http://www.nea.gov.cn/policy/zcfg.htm",  # 政策法规栏目
        "link_selector": "ul.list_01 li a",                   # 列表链接选择器
        "date_selector": "span",                              # 日期位置（需调整）
        "content_selector": "div.content"                     # 正文选择器
    },
    {
        "name": "国家发改委",
        "base_url": "https://www.ndrc.gov.cn",
        "list_url": "https://www.ndrc.gov.cn/xxgk/zcfb/",    # 政策发布栏目
        "link_selector": "ul.list_02 li a",
        "date_selector": "i",
        "content_selector": "div.article-content"
    }
]

# 关键词过滤（只保留能源相关）
ENERGY_KEYWORDS = [
    '能源', '电力', '光伏', '风电', '储能', '氢能', '碳', '天然气', 'LNG',
    '可再生能源', '新能源', '电网', '电价', '消纳', '并网', '绿证'
]

# 近3年时间范围
import datetime
CUTOFF_DATE = datetime.datetime.now() - datetime.timedelta(days=3*365)