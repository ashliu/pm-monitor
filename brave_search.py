#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Brave Search API 客户端
简单的命令行搜索工具
"""

import requests
import json
import os
import sys
import urllib.parse


class BraveSearch:
    """Brave Search 客户端"""
    
    BASE_URL = "https://api.search.brave.com/res/v1/web/search"
    
    def __init__(self, api_key=None):
        self.api_key = api_key or self._load_key()
        if not self.api_key:
            raise ValueError("API Key not found")
    
    def _load_key(self):
        """加载 API Key"""
        key_file = os.path.expanduser("~/.openclaw/workspace/.brave_key")
        if os.path.exists(key_file):
            with open(key_file, 'r') as f:
                return f.read().strip()
        return os.environ.get("BRAVE_API_KEY")
    
    def search(self, query, count=10, offset=0, country="us", language="en"):
        """
        执行搜索
        
        Args:
            query: 搜索关键词
            count: 返回结果数量 (1-20)
            offset: 结果偏移量（分页）
            country: 国家代码
            language: 语言代码
        """
        headers = {
            "X-Subscription-Token": self.api_key,
            "Accept": "application/json"
        }
        
        params = {
            "q": query,
            "count": min(count, 20),
            "offset": offset,
            "country": country,
            "search_lang": language
        }
        
        try:
            response = requests.get(
                self.BASE_URL,
                headers=headers,
                params=params,
                timeout=30
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {"error": str(e)}
    
    def print_results(self, data):
        """格式化打印结果"""
        if "error" in data:
            print(f"❌ 错误: {data['error']}")
            return
        
        query_info = data.get("query", {})
        web_results = data.get("web", {}).get("results", [])
        
        print("\n" + "="*60)
        print(f"🔍 Brave Search: {query_info.get('original', 'Unknown')}")
        print("="*60)
        
        if not web_results:
            print("\n未找到结果")
            return
        
        print(f"\n找到 {len(web_results)} 条结果:\n")
        
        for i, result in enumerate(web_results, 1):
            title = result.get("title", "无标题")
            url = result.get("url", "")
            desc = result.get("description", "")[:200]
            
            print(f"  {i}. {title}")
            print(f"     🔗 {url}")
            if desc:
                print(f"     📝 {desc}...")
            print()


def main():
    if len(sys.argv) < 2:
        print("Brave Search CLI")
        print("="*40)
        print("Usage: python3 brave_search.py <查询>")
        print("Example: python3 brave_search.py 'Python 3.12 新特性'")
        sys.exit(1)
    
    query = " ".join(sys.argv[1:])
    
    try:
        client = BraveSearch()
        print(f"搜索: {query}")
        results = client.search(query, count=5)
        client.print_results(results)
    except Exception as e:
        print(f"❌ 错误: {e}")


if __name__ == "__main__":
    main()
