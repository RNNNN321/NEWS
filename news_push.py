import requests
import os
import feedparser
from datetime import datetime, timedelta
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# 核心配置（不用改）
FEISHU_WEBHOOK = os.getenv("FEISHU_WEBHOOK")
NEWS_COUNT = 5

# 稳定国际新闻RSS源
NEWS_SOURCE_LIST = [
    {"name": "BBC世界新闻", "rss_url": "https://feeds.bbci.co.uk/news/world/rss.xml"},
    {"name": "CNN国际新闻", "rss_url": "https://rss.cnn.com/rss/cnn_world.rss"}
]

# 解析新闻数据
def get_international_news():
    for source in NEWS_SOURCE_LIST:
        try:
            feed = feedparser.parse(source["rss_url"])
            if feed.bozo == 0:
                news_list = [
                    {"title": entry.title, "url": entry.link} 
                    for entry in feed.entries[:NEWS_COUNT]
                ]
                return news_list, source["name"]
        except Exception as e:
            print(f"新闻源【{source['name']}】获取失败：{e}")
            continue
    return [], None

# 【关键修改1】内容开头强制带「新闻」关键词，100%命中校验
# 【关键修改2】放弃markdown，改用纯文本，彻底解决飞书格式兼容问题
def format_news_content(news_list, source_name):
    beijing_time = datetime.utcnow() + timedelta(hours=8)
    # 第一句就带「新闻」，飞书关键词校验必过
    content = f"新闻推送 | 每日国际新闻 {beijing_time.strftime('%Y年%m月%d日')}\n"
    content += f"📰 新闻来源：{source_name}\n"
    content += "------------------------\n"
    for idx, news in enumerate(news_list, 1):
        content += f"{idx}. {news['title']}\n链接：{news['url']}\n\n"
    content += f"推送时间：北京时间 {beijing_time.strftime('%H:%M')}"
    return content

# 推送到飞书
def send_to_feishu(content):
    headers = {"Content-Type": "application/json"}
    # 【关键修改3】用纯文本格式发送，飞书100%兼容
    payload = {"msg_type": "text", "content": {"text": content}}
    try:
        res = requests.post(FEISHU_WEBHOOK, json=payload, headers=headers, timeout=15)
        res.raise_for_status()
        print("✅ 飞书推送成功！")
        # 日志里打印内容预览，确认关键词确实在推送内容里
        print(f"推送内容预览：{content[:100]}")
    except Exception as e:
        print(f"❌ 飞书推送失败：{e}")

# 主程序
if __name__ == "__main__":
    news_list, source_name = get_international_news()
    if not news_list:
        send_to_feishu("新闻推送：今日国际新闻获取失败，请稍后手动查看")
    else:
        final_content = format_news_content(news_list, source_name)
        send_to_feishu(final_content)
