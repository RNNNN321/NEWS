import requests
import os
import feedparser
from datetime import datetime, timedelta
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ===================== 配置区 =====================
FEISHU_WEBHOOK = os.getenv("FEISHU_WEBHOOK")
NEWS_COUNT = 10
# ==================================================

# 【直接使用RSS源，不依赖第三方API】
NEWS_SOURCE_LIST = [
    {
        "name": "BBC世界新闻",
        "rss_url": "https://feeds.bbci.co.uk/news/world/rss.xml"
    },
    {
        "name": "CNN国际新闻",
        "rss_url": "https://rss.cnn.com/rss/cnn_world.rss"
    },
    {
        "name": "美联社国际新闻",
        "rss_url": "https://apnews.com/rss/apf-topnews"
    }
]

# 直接解析RSS源
def get_news_from_rss(rss_url):
    try:
        print(f"正在解析RSS源：{rss_url}")
        # 使用feedparser直接解析
        feed = feedparser.parse(rss_url)
        if feed.bozo == 0:  # bozo=0表示解析成功
            news_list = []
            for entry in feed.entries[:NEWS_COUNT]:
                news_list.append({
                    "title": entry.title,
                    "url": entry.link
                })
            return news_list
        else:
            print(f"RSS解析错误：{feed.bozo_exception}")
            return None
    except Exception as e:
        print(f"RSS源访问失败：{e}")
        return None

# 循环尝试所有新闻源
def get_international_news():
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

# 格式化新闻内容
def format_news_content(news_list, source_name):
    beijing_time = datetime.utcnow() + timedelta(hours=8)
    today = beijing_time.strftime("%Y年%m月%d日")
    content = f"# 每日国际新闻 | {today}\n📰 新闻来源：{source_name}\n---\n"
    for idx, news in enumerate(news_list, 1):
        content += f"{idx}. [{news['title']}]({news['url']})\n\n"
    content += f"---\n推送时间：北京时间 {beijing_time.strftime('%H:%M')}"
    return content

# 推送到飞书
def send_to_feishu(content):
    headers = {"Content-Type": "application/json"}
    payload = {"msg_type": "markdown", "content": {"markdown": content}}
    try:
        res = requests.post(FEISHU_WEBHOOK, json=payload, headers=headers, timeout=15)
        res.raise_for_status()
        print("✅ 飞书推送成功！")
    except Exception as e:
        print(f"❌ 飞书推送失败：{e}")

if __name__ == "__main__":
    news_list, source_name = get_international_news()
    if not news_list:
        send_to_feishu("【每日国际新闻】今日热点获取失败，请稍后手动查看")
    else:
        final_content = format_news_content(news_list, source_name)
        send_to_feishu(final_content)
