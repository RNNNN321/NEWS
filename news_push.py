import requests
import os
from datetime import datetime, timedelta
import urllib3
# 屏蔽不必要的警告，不影响功能
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ===================== 小白可修改的配置区 =====================
# 从GitHub后台获取你的飞书webhook地址，这里不用改
FEISHU_WEBHOOK = os.getenv("FEISHU_WEBHOOK")
# 每天推送的新闻条数，默认10条，想改直接改数字就行
NEWS_COUNT = 10
# ==============================================================

# 【3个超稳定国际新闻源】自动切换，GitHub海外服务器完美访问，免密钥免费
NEWS_SOURCE_LIST = [
    # 源1：BBC 世界新闻（全球最权威，更新最快）
    {
        "name": "BBC世界新闻",
        "api_url": "https://api.rss2json.com/v1/api.json?rss_url=http://feeds.bbci.co.uk/news/world/rss.xml",
        "parse_func": "parse_rss_json"
    },
    # 源2：CNN 国际新闻（美国主流，突发新闻快）
    {
        "name": "CNN国际新闻",
        "api_url": "https://api.rss2json.com/v1/api.json?rss_url=http://rss.cnn.com/rss/cnn_world.rss",
        "parse_func": "parse_rss_json"
    },
    # 源3：路透社 全球新闻（财经+时政双权威）
    {
        "name": "路透社全球新闻",
        "api_url": "https://api.rss2json.com/v1/api.json?rss_url=http://feeds.reuters.com/reuters/worldNews",
        "parse_func": "parse_rss_json"
    }
]

# 解析新闻数据（不用懂，直接用）
def parse_rss_json(data):
    if data.get("status") == "ok" and "items" in data:
        return [
            {
                "title": item["title"],
                "url": item["link"],
                "pub_date": item["pubDate"]
            } 
            for item in data["items"][:NEWS_COUNT]
        ]
    return []

# 循环尝试所有新闻源，直到成功获取
def get_international_news():
    for source in NEWS_SOURCE_LIST:
        try:
            print(f"正在尝试新闻源：{source['name']}")
            # 15秒超时，避免卡住
            res = requests.get(source["api_url"], timeout=15, verify=False)
            res.raise_for_status()
            data = res.json()
            # 调用解析函数
            parse_func = locals()[source["parse_func"]]
            news_list = parse_func(data)
            if news_list:
                print(f"✅ 成功从【{source['name']}】获取国际新闻")
                return news_list, source['name']
        except Exception as e:
            print(f"❌ 新闻源【{source['name']}】获取失败：{e}")
            continue
    print("所有新闻源都获取失败了")
    return [], None

# 把新闻整理成飞书能正常显示的格式（自带“新闻”关键词，确保能推送成功）
def format_news_content(news_list, source_name):
    # 把GitHub的UTC时间转换成北京时间，不会出现时间不对的问题
    beijing_time = datetime.utcnow() + timedelta(hours=8)
    today = beijing_time.strftime("%Y年%m月%d日")
    # 内容模板，自带“新闻”关键词，飞书推送必过
    content = f"# 每日国际新闻 | {today}\n📰 新闻来源：{source_name}\n---\n"
    for idx, news in enumerate(news_list, 1):
        content += f"{idx}. [{news['title']}]({news['url']})\n\n"
    content += f"---\n推送时间：北京时间 {beijing_time.strftime('%H:%M')}"
    return content

# 推送到飞书群
def send_to_feishu(content):
    headers = {"Content-Type": "application/json"}
    payload = {
        "msg_type": "markdown",
        "content": {"markdown": content}
    }
    try:
        res = requests.post(FEISHU_WEBHOOK, json=payload, headers=headers, timeout=15)
        res.raise_for_status()
        print("✅ 飞书推送成功！")
    except Exception as e:
        print(f"❌ 飞书推送失败：{e}")

# 主程序，不用懂，直接用
if __name__ == "__main__":
    news_list, source_name = get_international_news()
    # 没有获取到新闻，推送失败提醒
    if not news_list or not source_name:
        send_to_feishu("【每日国际新闻】今日热点获取失败，请稍后手动查看")
    else:
        # 格式化内容并推送
        final_content = format_news_content(news_list, source_name)
        send_to_feishu(final_content)
