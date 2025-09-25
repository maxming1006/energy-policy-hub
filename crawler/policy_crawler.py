import json
import os
import re
import datetime
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright
from config import SOURCES, ENERGY_KEYWORDS, CUTOFF_DATE

def extract_date(text):
    """从文本中提取 YYYY-MM-DD 日期"""
    match = re.search(r'(\d{4})[年\-](\d{1,2})[月\-](\d{1,2})', text)
    if match:
        return f"{match.group(1)}-{int(match.group(2)):02d}-{int(match.group(3)):02d}"
    return None

def is_energy_related(title, content):
    """判断是否能源政策"""
    text = (title + " " + content).lower()
    return any(kw in text for kw in ENERGY_KEYWORDS)

def crawl_policies():
    all_policies = []
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        for source in SOURCES:
            print(f"正在抓取: {source['name']}")
            page.goto(source['list_url'], timeout=60000)
            
            # 获取政策列表链接
            links = page.query_selector_all(source['link_selector'])
            for link in links[:20]:  # 先抓前20条（避免太多）
                try:
                    href = link.get_attribute('href')
                    title = link.text_content().strip()
                    if not href or not title:
                        continue
                    
                    full_url = urljoin(source['base_url'], href)
                    
                    # 打开详情页
                    page_detail = browser.new_page()
                    page_detail.goto(full_url, timeout=30000)
                    
                    # 提取日期
                    date_elem = page_detail.query_selector(source['date_selector'])
                    publish_date = None
                    if date_elem:
                        publish_date = extract_date(date_elem.text_content())
                    
                    # 如果没有日期，跳过
                    if not publish_date:
                        page_detail.close()
                        continue
                    
                    # 检查是否近3年
                    pub_dt = datetime.datetime.strptime(publish_date, "%Y-%m-%d")
                    if pub_dt < CUTOFF_DATE:
                        page_detail.close()
                        break  # 列表按时间倒序，后面更旧，可跳出
                    
                    # 提取正文
                    content_elem = page_detail.query_selector(source['content_selector'])
                    content = content_elem.text_content() if content_elem else ""
                    
                    # 过滤非能源政策
                    if not is_energy_related(title, content):
                        page_detail.close()
                        continue
                    
                    # 生成ID
                    from hashlib import md5
                    policy_id = "policy-" + md5(full_url.encode()).hexdigest()[:12]
                    
                    policy = {
                        "id": policy_id,
                        "title": title,
                        "type": "national",
                        "category": "other",  # 后续可AI分类
                        "publishDate": publish_date,
                        "source": source['name'],
                        "sourceUrl": full_url,
                        "region": "全国",
                        "status": "active",
                        "keywords": [],
                        "summary": content[:200] + "……",
                        "collectedAt": datetime.datetime.now().strftime("%Y-%m-%d"),
                        "verified": True
                    }
                    all_policies.append(policy)
                    print(f"✅ 抓取: {title}")
                    
                    page_detail.close()
                    
                except Exception as e:
                    print(f"❌ 跳过: {href}, 错误: {str(e)}")
                    continue
        
        browser.close()
    
    return all_policies

def save_to_json(policies, output_path="../data.json"):
    """保存为 data.json（合并去重）"""
    existing = []
    if os.path.exists(output_path):
        with open(output_path, 'r', encoding='utf-8') as f:
            existing = json.load(f)
    
    # 按 ID 去重
    existing_ids = {p['id'] for p in existing}
    new_policies = [p for p in policies if p['id'] not in existing_ids]
    
    # 合并（新政策在前）
    final_policies = new_policies + existing
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(final_policies, f, ensure_ascii=False, indent=2)
    
    print(f"新增 {len(new_policies)} 条政策，共 {len(final_policies)} 条")

if __name__ == "__main__":
    policies = crawl_policies()
    save_to_json(policies)