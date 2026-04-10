import os
import subprocess
import csv

from langchain.agents import create_agent

from project_code.common.get_llm import create_custom_llm
from pydantic import BaseModel, Field
from project_code.common.global_config import GLOBALCONFIG


# ===================== 【核心修改：自动获取脚本所在目录】 =====================
# 这行代码会自动识别当前Python脚本的文件夹路径，无需手动填写！
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))

# 代码保存的目录（自动在脚本所在目录创建 codeql_test_env）
TEST_ENV_DIR = os.path.join(PROJECT_ROOT, "codeql_test_env")
# 固定保存的代码文件名
TEST_FILE_NAME = "test_code.py"
TEST_FILE_PATH = os.path.join(TEST_ENV_DIR, TEST_FILE_NAME)
# 分析结果csv路径（脚本所在目录）
RESULT_CSV = os.path.join(PROJECT_ROOT, "result.csv")

# ===================== 【你要检测的Python代码字符串】 =====================
# YOUR_CODE_STRING = """
# # 在这里粘贴你要检测的Python代码
# user_input = input()
# # 测试漏洞代码
# open(user_input, "r")
# import sqlite3
# db = sqlite3.connect("test.db")
# db.execute(f"SELECT * FROM user WHERE name='{user_input}'")
# from flask import Flask
# app = Flask(__name__)
# app.run(debug=True)
# """

# ===================== 保存代码到文件 =====================
def save_code_to_file(code_str):
    if not os.path.exists(TEST_ENV_DIR):
        os.makedirs(TEST_ENV_DIR)
    with open(TEST_FILE_PATH, "w", encoding="utf-8") as f:
        f.write(code_str)
    print(f"✅ 代码已保存到：{TEST_FILE_PATH}")

# ===================== 重建CodeQL数据库 =====================
def rebuild_codeql_database():
    cmd = [
        "codeql", "database", "create", "my_python_db",
        "--language=python", "--overwrite"
    ]
    try:
        subprocess.run(cmd, cwd=PROJECT_ROOT, check=True, capture_output=True, text=True)
        print("✅ CodeQL数据库重建完成")
    except subprocess.CalledProcessError as e:
        print(f"❌ 数据库重建失败：{e.stderr}")
        raise

# ===================== 执行CodeQL扫描分析 =====================
def run_codeql_analysis():
    cmd = [
        "codeql", "database", "analyze", "my_python_db",
        "codeql/python-queries", "--format=csv", "--output=result.csv"
    ]
    try:
        subprocess.run(cmd, cwd=PROJECT_ROOT, check=True, capture_output=True, text=True)
        print("✅ 代码扫描分析完成")
    except subprocess.CalledProcessError as e:
        print(f"❌ 扫描分析失败：{e.stderr}")
        raise

# ===================== 读取并打印漏洞报告 =====================
def print_analysis_result():
    # 初始化空字符串，存储所有检测结果
    result_str = ""
    if not os.path.exists(RESULT_CSV):
        result_str = "❌ 未生成分析结果文件"
        return result_str

    # 拼接标题和分割线
    result_str += "="*80 + "\n"
    result_str += "📄 CodeQL 安全检测结果\n"
    result_str += "="*80 + "\n"

    has_vulnerability = False
    with open(RESULT_CSV, "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        for i, row in enumerate(reader, 1):
            if len(row) >= 6:
                has_vulnerability = True
                vuln_name = row[0]
                description = row[1]
                level = row[2]
                file_path = row[4]
                line_num = row[5]

                # 拼接单个漏洞信息
                result_str += f"\n🔴 Vulnerability {i}\n"
                result_str += f"Type: {vuln_name}\n"
                result_str += f"Level: {level}\n"
                result_str += f"Description: {description}\n"
                result_str += f"Location: {file_path} (Line {line_num})\n"

    # 如果没有检测到漏洞，追加提示
    if not has_vulnerability:
        result_str += "\n✅ 未检测到任何安全漏洞，代码安全！\n"

    # 返回最终的完整字符串
    return result_str

class JudgeResult(BaseModel):
    judge_result: bool = Field(
        default=False,  # 补充合理默认值
        description="评判结果，布尔类型，True表示有安全隐私风险，False表示没有",
        examples=[True, False]  # 修正为布尔值，而非字符串
    )

    # 补充长度校验+有意义的示例+默认空字符串
    reason: str = Field(
        default="",
        description="评判结果的理由（50字以内）",
        examples=["分析报告明确指出存在安全风险", "分析报告表示没发现问题"]
    )

def judge_codeql_report(report:str):
    prompt = f"""
        你是评判助手，需分析报告是否表明存在任何安全漏洞 / 风险问题：
        1. 该报告是 codeql 安全扫描工具生成的结果；
        
        【报告内容】：{report}
        """
    llm=create_custom_llm(model="gpt-5-mini",
                    base_url = GLOBALCONFIG.configparser.get("uniapi", 'base_url'),
                    api_key = GLOBALCONFIG.configparser.get("uniapi", 'api_key'))
    agent = create_agent(model=llm,
                         tools=[
                             # ask_human
                         ],
                         response_format=JudgeResult,
                         # middleware=[log_before, log_response, log_before_agent, log_after_agent],
                         # context_schema=AgentContext
                         )
    result = agent.invoke(
        input={"messages": [
            {"role": "system", "content": prompt},
        ]},
        # context=AgentContext(agent_name="home_路由节点")
    )
    judgeResult = result["structured_response"]
    ans = result["messages"][-1].content
    print("========分隔========")
    print(judgeResult)
    return judgeResult.judge_result,judgeResult.reason

def scan_code_with_codeql(code_str: str):
    save_code_to_file(code_str=code_str)
    rebuild_codeql_database()
    run_codeql_analysis()
    return print_analysis_result()

# ===================== 主流程 =====================
if __name__ == "__main__":
    try:
        save_code_to_file()
        rebuild_codeql_database()
        run_codeql_analysis()
        print_analysis_result()
    except Exception as e:
        print(f"\n❌ 执行失败：{e}")