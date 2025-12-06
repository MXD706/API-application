#!/usr/bin/env python3
"""
完全可用的 Gemini CLI 工具
使用 gemini-2.5-flash 模型
支援：互動模式、檔案處理、批量處理
"""

import requests
import json
import sys
import os
import argparse
import time
from datetime import datetime

# 你的 API 金鑰
API_KEY = "AIzaSyDD-lq7XRYrxIydgP9olo5rz4ShMRtGoQc"

# 可用的模型（根據偵測結果）
WORKING_MODEL = "gemini-2.5-flash"
BASE_URL = "https://generativelanguage.googleapis.com/v1beta/models"


def call_gemini(prompt, model=WORKING_MODEL, temperature=0.7, max_tokens=2000):
    """呼叫 Gemini API"""
    url = f"{BASE_URL}/{model}:generateContent?key={API_KEY}"

    headers = {"Content-Type": "application/json"}

    data = {
        "contents": [{
            "parts": [{"text": prompt}]
        }],
        "generationConfig": {
            "temperature": temperature,
            "maxOutputTokens": max_tokens,
        }
    }

    try:
        response = requests.post(url, headers=headers, json=data, timeout=30)
        response.raise_for_status()

        result = response.json()
        if "candidates" in result and result["candidates"]:
            return result["candidates"][0]["content"]["parts"][0]["text"]
        else:
            return "錯誤：API 回傳格式不正確"

    except requests.exceptions.RequestException as e:
        return f"網路錯誤: {e}"
    except Exception as e:
        return f"未知錯誤: {type(e).__name__}: {e}"


def interactive_chat():
    """互動聊天模式"""
    print(f"💬 Gemini CLI 互動模式 (模型: {WORKING_MODEL})")
    print("輸入 'exit' 退出, 'clear' 清除對話, 'help' 查看指令")
    print("=" * 60)

    conversation_history = []

    while True:
        try:
            user_input = input("\n你: ").strip()

            if not user_input:
                continue

            if user_input.lower() in ['exit', 'quit', '退出']:
                print("結束對話")
                break
            elif user_input.lower() == 'clear':
                conversation_history = []
                print("對話已清除")
                continue
            elif user_input.lower() == 'help':
                print("\n可用指令:")
                print("  exit/quit/退出 - 結束程式")
                print("  clear - 清除對話歷史")
                print("  help - 顯示此幫助")
                print("  summary - 總結對話")
                print("  save - 儲存對話記錄")
                continue
            elif user_input.lower() == 'summary':
                if conversation_history:
                    summary_prompt = "總結以下對話:\n" + "\n".join(conversation_history[-10:])
                    summary = call_gemini(summary_prompt)
                    print(f"\n📝 對話總結: {summary}")
                else:
                    print("對話歷史為空")
                continue
            elif user_input.lower() == 'save':
                if conversation_history:
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    filename = f"chat_history_{timestamp}.txt"
                    with open(filename, 'w', encoding='utf-8') as f:
                        f.write("\n".join(conversation_history))
                    print(f"對話已儲存到 {filename}")
                else:
                    print("對話歷史為空")
                continue

            # 顯示思考中動畫
            print("AI 思考中...", end="", flush=True)

            # 建立包含歷史的提示
            full_prompt = "\n".join(conversation_history[-5:] + [user_input]) if conversation_history else user_input

            # 呼叫 API
            response = call_gemini(full_prompt)

            # 清除"思考中"訊息
            print("\r" + " " * 30 + "\r", end="")

            # 顯示回應
            print(f"AI: {response}")

            # 儲存到歷史
            conversation_history.append(f"你: {user_input}")
            conversation_history.append(f"AI: {response}")

        except KeyboardInterrupt:
            print("\n\n程式被中斷")
            break
        except Exception as e:
            print(f"\n錯誤: {e}")


def process_file(input_file, instruction, output_file=None):
    """處理檔案內容"""
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            content = f.read()

        print(f"讀取檔案: {input_file} ({len(content)} 字符)")
        print(f"執行指令: {instruction}")
        print("處理中...", end="", flush=True)

        prompt = f"{instruction}\n\n檔案內容：\n{content}"
        result = call_gemini(prompt)

        print("\r" + " " * 30 + "\r", end="")

        if output_file:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(result)
            print(f"✅ 結果已儲存到: {output_file}")
        else:
            print("=" * 60)
            print("處理結果:")
            print("=" * 60)
            print(result)

        return result

    except FileNotFoundError:
        print(f"❌ 找不到檔案: {input_file}")
    except Exception as e:
        print(f"❌ 處理錯誤: {e}")


def batch_process(input_dir, instruction, output_dir=None):
    """批量處理多個檔案"""
    if not os.path.exists(input_dir):
        print(f"❌ 目錄不存在: {input_dir}")
        return

    files = [f for f in os.listdir(input_dir) if f.endswith('.txt')]

    if not files:
        print(f"❌ 目錄中沒有 .txt 檔案: {input_dir}")
        return

    print(f"找到 {len(files)} 個檔案")

    for i, filename in enumerate(files, 1):
        input_path = os.path.join(input_dir, filename)

        if output_dir:
            os.makedirs(output_dir, exist_ok=True)
            output_path = os.path.join(output_dir, f"processed_{filename}")
        else:
            output_path = None

        print(f"\n[{i}/{len(files)}] 處理: {filename}")
        process_file(input_path, instruction, output_path)

        # 避免 API 限制，每次處理間隔 1 秒
        time.sleep(1)


def quick_query(query):
    """快速單次查詢"""
    print(f"問題: {query}")
    print("-" * 40)

    response = call_gemini(query)

    print(f"回答: {response}")
    print("=" * 60)

    return response


def main():
    """主程式"""
    parser = argparse.ArgumentParser(
        description="Gemini CLI 工具 - 無程式碼 AI 代理人",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用範例:
  %(prog)s "用三句話介紹人工智慧"
  %(prog)s -i  # 進入互動模式
  %(prog)s -f input.txt -c "總結這個檔案"
  %(prog)s -f input.txt -c "翻譯成英文" -o output.txt
  %(prog)s -b ./documents -c "提取關鍵字"
        """
    )

    parser.add_argument("query", nargs="?", help="直接輸入問題")
    parser.add_argument("-i", "--interactive", action="store_true", help="進入互動模式")
    parser.add_argument("-f", "--file", help="處理指定檔案")
    parser.add_argument("-c", "--command", help="對檔案執行的指令")
    parser.add_argument("-o", "--output", help="輸出檔案")
    parser.add_argument("-b", "--batch", help="批量處理目錄")
    parser.add_argument("-m", "--model", default=WORKING_MODEL, help=f"指定模型 (預設: {WORKING_MODEL})")

    args = parser.parse_args()

    # 顯示標題
    print("=" * 60)
    print("🤖 Gemini CLI 工具 v2.0")
    print(f"📊 模型: {WORKING_MODEL}")
    print("=" * 60)

    # 處理各種模式
    if args.interactive:
        interactive_chat()
    elif args.batch and args.command:
        batch_process(args.batch, args.command, args.output)
    elif args.file:
        if args.command:
            process_file(args.file, args.command, args.output)
        else:
            print("請使用 -c 參數指定處理指令")
    elif args.query:
        quick_query(args.query)
    else:
        # 預設進入互動模式
        interactive_chat()


if __name__ == "__main__":
    main()