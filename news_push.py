import requests
import os
import feedparser
from datetime import datetime, timedelta
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ===================== 小白可修改配置区 =====================
FEISHU_WEBHOOK = os.getenv("FEISHU_WEBHOOK")
NEWS_COUNT = 10  # 每天推送的新闻条数
# ==============================================================

# 【精选】AI/科技/投资/创业领域权威RSS源
# 涵盖国内外头部媒体、创投平台、AI专业号，自动切换，稳定优先
NEWS_SOURCE_LIST = [
    # ---------------------- 国内AI/科技 ----------------------
    {
        "name": "36氪 - 科技创投",
        "rss_url": "https://36kr.com/feed"
    },
    {
        "name": "机器之心 - AI专业",
        "rss_url": "https://www.jiqizhixin.com/rss"
    },
    {
        "name": "量子位 - AI/前沿科技",
        "rss_url": "https://www.qbitai.com/rss"
    },
    {
        "name": "虎嗅 - 科技商业",
        "rss_url": "https://www.huxiu.com/rss/0.xml"
    },
    {
        "name": "钛媒体 - 科技创投",
        "rss_url": "https://www.tmtpost.com/rss"
    },
    # ---------------------- 国外AI/科技 ----------------------
    {
        "name": "TechCrunch - 全球科技创投",
        "rss_url": "https://techcrunch.com/feed/"
    },
    {
        "name": "MIT Technology Review - 前沿科技",
        "rss_url": "https://www.technologyreview.com/feed/"
    },
    {
        "name": "Wired - 科技文化",
        "rss_url": "https://www.wired.com/feed/rss"
    },
    # ---------------------- 投资/创业 ----------------------
    {
        "name": "36氪创投 - 创业融资",
        "rss_url": "https://36kr.com/feed/column/100000"
    }
]

# 解析新闻数据
def get_news_from_rss(rss_url):
    try:
        print(f"正在解析RSS源：{rss_url}")
        feed = feedparser.parse(rss_url)
        if feed.bozo == 0:  # 解析成功
            news_list = []
            for entry in feed.entries[:NEWS_COUNT]:
                news_list.append({
                    "title": entry.title,
                    "url": entry.link
                })
            return news_list
        else:
            print(f"RSS解析警告：{feed.bozo_exception}")
            # 即使有小警告也尝试返回部分数据
            if feed.entries:
                news_list = [
                    {"title": entry.title, "url": entry.link} 
                    for entry in feed.entries[:NEWS_COUNT]
                ]
                return news_list
            return None
    except Exception as e:
        print(f"RSS源访问失败：{e}")
        return None

# 循环尝试所有新闻源，直到成功
def get_daily_news():
    for source in NEWS_SOURCE_LIST:
        try:
            print(f"正在尝试新闻源：{source['name']}")
            news_list = get_news_from_rss(source["rss_url"])
            if news_list:
                print(f"✅ 成功从【{source['name']}】获取新闻")
                return news_list, source['name']
        except Exception as e:
            print(f"❌ 新闻源【{source['name']}】失败：{e}")
            continue
    return [], None

# 格式化新闻内容（关键词前置+纯文本，飞书100%兼容）
def format_news_content(news_list, source_name):
    beijing_time = datetime.utcnow() + timedelta(hours=8)
    # 第一句强制带「新闻」，确保飞书关键词校验通过
    content = f"新闻推送 | 每日AI/科技/创投 {beijing_time.strftime('%Y年%m月%d日')}\n"
    content += f"📰 新闻来源：{source_name}\n"
    content += "------------------------\n"
    for idx, news in enumerate(news_list, 1):
        content += f"{idx}. {news['title']}\n链接：{news['url']}\n\n"
    content += f"推送时间：北京时间 {beijing_time.strftime('%H:%M')}"
    return content

# 推送到飞书
def send_to_feishu(content):
    headers = {"Content-Type": "application/json"}
    # 纯文本格式发送，飞书零兼容问题
    payload = {"msg_type": "text", "content": {"text": content}}
    try:
        res = requests.post(FEISHU_WEBHOOK, json=payload, headers=headers, timeout=15)
        res.raise_for_status()
        print("✅ 飞书推送成功！")
        print(f"推送内容预览：{content[:120]}")
    except Exception as e:
        print(f"❌ 飞书推送失败：{e}")

# 主程序
if __name__ == "__main__":
    news_list, source_name = get_daily_news()
    if not news_list:
        send_to_feishu("新闻推送：今日AI/科技/创投新闻获取失败，请稍后手动查看")
    else:
        final_content = format_news_content(news_list, source_name)
        send_to_feishu(final_content)
