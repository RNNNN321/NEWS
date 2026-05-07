import requests
import os
from datetime import datetime, timedelta

# 从GitHub后台获取你的飞书webhook地址（不用改）
FEISHU_WEBHOOK = os.getenv("FEISHU_WEBHOOK")
# 每天推送几条新闻（默认10条，想改就改数字）
NEWS_COUNT = 10

# 【重点】3个备用新闻源API，自动切换，哪个能用用哪个
# 格式：(API地址, 解析函数名)
NEWS_API_LIST = [
    # 备用1：今日头条热榜（稳定优先）
    ("https://api.oioweb.cn/api/hotlist/toutiao", "parse_oioweb"),
    # 备用2：百度热搜
    ("https://api.oioweb.cn/api/hotlist/baidu", "parse_oioweb"),
    # 备用3：微博热搜
    ("https://api.oioweb.cn/api/hotlist/weibo", "parse_oioweb"),
]

# 解析备用API的新闻数据（不用懂，直接用）
def parse_oioweb(data):
    if data.get("code") == 200 and "data" in data:
        return [{"title": item["title"], "url": item["url"]} for item in data["data"][:NEWS_COUNT]]
    return []

# 循环尝试所有新闻源，直到成功获取
def get_daily_news():
    for api_url, parse_func_name in NEWS_API_LIST:
        try:
            print(f"正在尝试新闻源：{api_url}")
            res = requests.get(api_url, timeout=15)
            res.raise_for_status()
            data = res.json()
            # 调用对应的解析函数
            parse_func = locals()[parse_func_name]
            news_list = parse_func(data)
            if news_list:
                print(f"成功从 {api_url} 获取新闻")
                return news_list
        except Exception as e:
            print(f"新闻源 {api_url} 失败：{e}")
            continue
    print("所有新闻源都失败了")
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
        res = requests.post(FEISHU_WEBHOOK, json=payload, headers=headers, timeout=15)
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
