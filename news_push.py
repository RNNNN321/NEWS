import requests
import os
from datetime import datetime, timedelta

# 从GitHub后台获取你的飞书webhook地址（不用改这里）
FEISHU_WEBHOOK = os.getenv("FEISHU_WEBHOOK")
# 每天推送几条新闻（这里默认10条，想改就改数字）
NEWS_COUNT = 10
# 免费新闻源（默认今日头条，想换就把toutiao改成baidu/weibo/zhihu）
NEWS_API = "https://api.vvhan.com/api/hotlist?type=toutiao"

# 获取新闻数据（不用懂，直接用）
def get_daily_news():
    try:
        res = requests.get(NEWS_API, timeout=10)
        res.raise_for_status()
        data = res.json()
        return data["data"][:NEWS_COUNT] if data.get("success") else []
    except Exception as e:
        print(f"新闻获取失败：{e}")
        return []

# 把新闻整理成飞书能看懂的格式（不用懂，直接用）
def format_news_content(news_list):
    # 把GitHub的UTC时间转换成北京时间
    beijing_time = datetime.utcnow() + timedelta(hours=8)
    today = beijing_time.strftime("%Y年%m月%d日")
    content = f"# 每日热点新闻 | {today}\n---\n"
    for idx, news in enumerate(news_list, 1):
        content += f"{idx}. [{news['title']}]({news['url']})\n\n"
    content += f"---\n推送时间：{beijing_time.strftime('%H:%M')}"
    return content

# 推送到飞书（不用懂，直接用）
def send_feishu_msg(content):
    headers = {"Content-Type": "application/json"}
    payload = {"msg_type": "markdown", "content": {"markdown": content}}
    try:
        res = requests.post(FEISHU_WEBHOOK, json=payload, headers=headers, timeout=10)
        res.raise_for_status()
        print("推送成功！")
    except Exception as e:
        print(f"推送失败：{e}")

# 主程序（不用懂，直接用）
if __name__ == "__main__":
    news = get_daily_news()
    if not news:
        send_feishu_msg("【每日新闻】今日热点获取失败，请稍后手动查看")
    else:
        content = format_news_content(news)
        send_feishu_msg(content)
