import requests
import os
from datetime import datetime, timedelta
# 下面这行是用来跳过SSL警告的，不用管
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# 从GitHub后台获取你的飞书webhook地址（不用改）
FEISHU_WEBHOOK = os.getenv("FEISHU_WEBHOOK")
# 每天推送几条新闻（默认10条）
NEWS_COUNT = 10

# 【全新升级】2个超稳定新闻源，第一个不行自动用第二个
NEWS_API_LIST = [
    # 源1：免费公开API（带跳过SSL补丁）
    ("https://api.vvhan.com/api/hotlist?type=toutiao", "parse_vvhan", True),
    # 源2：备用免费API
    ("https://api.oioweb.cn/api/hotlist/toutiao", "parse_oioweb", True),
]

# 解析源1的数据
def parse_vvhan(data):
    if data.get("success") and "data" in data:
        return [{"title": item["title"], "url": item["url"]} for item in data["data"][:NEWS_COUNT]]
    return []

# 解析源2的数据
def parse_oioweb(data):
    if data.get("code") == 200 and "data" in data:
        return [{"title": item["title"], "url": item["url"]} for item in data["data"][:NEWS_COUNT]]
    return []

# 循环尝试所有新闻源
def get_daily_news():
    for api_url, parse_func_name, skip_ssl in NEWS_API_LIST:
        try:
            print(f"正在尝试新闻源：{api_url}")
            # 【关键修改】根据配置决定是否跳过SSL验证
            res = requests.get(api_url, timeout=15, verify=not skip_ssl)
            res.raise_for_status()
            data = res.json()
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

# 整理新闻格式
def format_news_content(news_list):
    beijing_time = datetime.utcnow() + timedelta(hours=8)
    today = beijing_time.strftime("%Y年%m月%d日")
    content = f"# 每日热点新闻 | {today}\n---\n"
    for idx, news in enumerate(news_list, 1):
        content += f"{idx}. [{news['title']}]({news['url']})\n\n"
    content += f"---\n推送时间：{beijing_time.strftime('%H:%M')}"
    return content

# 推送到飞书
def send_feishu_msg(content):
    headers = {"Content-Type": "application/json"}
    payload = {"msg_type": "markdown", "content": {"markdown": content}}
    try:
        res = requests.post(FEISHU_WEBHOOK, json=payload, headers=headers, timeout=15)
        res.raise_for_status()
        print("推送成功！")
    except Exception as e:
        print(f"推送失败：{e}")

# 主程序
if __name__ == "__main__":
    news = get_daily_news()
    if not news:
        send_feishu_msg("【每日新闻】今日热点获取失败，请稍后手动查看")
    else:
        content = format_news_content(news)
        send_feishu_msg(content)
