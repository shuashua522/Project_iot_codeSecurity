import requests
import json

from project_code.common.global_config import GLOBALCONFIG

from openai import OpenAI
from typing import Optional, Dict, Any

OPEN_WEBUI_API = GLOBALCONFIG.configparser.get("open_webui", 'base_url')
API_KEY = GLOBALCONFIG.configparser.get("open_webui", 'api_key')
MODEL_NAME = "qwen3.5:4b"
USER_PROMPT = "请介绍一下Python编程"
BASE_URL = "https://t.dothings.top:5003"  # 你的 OpenWebUI 地址
def get_openwebui_response(prompt: str, system_prompt: str = None) -> str:
    """
    【非流式】官方标准API调用，一次性返回完整结果（修复405错误）
    :param prompt: 用户提问内容
    :param system_prompt: 系统提示词（可选）
    :return: 模型响应文本
    """
    # 官方正确端点！！！
    url = f"{BASE_URL}/api/chat/completions"
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }

    # 构造消息（支持系统提示词）
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})

    data = {
        "model": MODEL_NAME,
        "messages": messages,
        "stream": False  # 非流式
    }

    try:
        # 官方标准 POST 请求
        response = requests.post(url, headers=headers, json=data, timeout=300)
        response.raise_for_status()  # 抛出HTTP错误
        result = response.json()
        return result["choices"][0]["message"]["content"].strip()

    except Exception as e:
        return f"调用失败：{str(e)}"


def stream_openwebui_response(prompt: str, system_prompt: str = None):
    """
    【流式】官方标准API调用，逐字输出（和前端界面效果一致）
    """
    url = f"{BASE_URL}/api/chat/completions"
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }

    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})

    data = {
        "model": MODEL_NAME,
        "messages": messages,
        "stream": True  # 开启流式
    }

    try:
        # 流式请求，逐块接收数据
        with requests.post(url, headers=headers, json=data, stream=True, timeout=300) as response:
            response.raise_for_status()
            print("模型响应：", end="", flush=True)
            for line in response.iter_lines():
                if line:
                    # 解析流式 SSE 数据
                    line_str = line.decode("utf-8").replace("data: ", "")
                    if line_str == "[DONE]":
                        break
                    try:
                        chunk = json.loads(line_str)
                        content = chunk["choices"][0]["delta"].get("content", "")
                        print(content, end="", flush=True)
                    except:
                        continue
            print("\n")

    except Exception as e:
        print(f"流式调用失败：{str(e)}")


# ------------------- 调用示例 -------------------
if __name__ == "__main__":
    # 你的问题
    user_question = "请介绍一下Python编程"

    # 1. 非流式调用（一次性返回结果）
    print("=== 非流式调用结果 ===")
    res = get_openwebui_response(user_question)
    print(res)

    # 2. 流式调用（推荐，逐字输出）
    print("\n=== 流式调用结果 ===")
    stream_openwebui_response(user_question)

