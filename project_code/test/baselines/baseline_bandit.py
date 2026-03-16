import subprocess
import tempfile
import os
import sys
from pydantic import BaseModel, Field
from langchain.agents import create_agent

from project_code.agent.easy_agent_entry import clean_llm_response
from project_code.common.get_llm import create_custom_llm
from project_code.common.global_config import GLOBALCONFIG

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
def scan_code_with_bandit(code_str: str):
    """
    Python调用命令行执行Bandit安全扫描（零报错、兼容所有版本/Conda）
    :param code_str: 要检测的代码字符串
    :return: 命令行原始输出结果
    """
    # 1. 创建临时Python文件（自动关闭，用完删除）
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False, encoding="utf-8") as f:
        f.write(code_str)
        temp_path = f.name

    try:
        # 2. 核心：调用当前Conda环境的bandit（关键！sys.executable保证环境正确）
        # 命令：python -m bandit 文件名
        result = subprocess.run(
            [sys.executable, "-m", "bandit", temp_path],
            capture_output=True,
            text=True,
            encoding="utf-8"
        )

        # 3. 打印完整检测结果
        print("=" * 50)
        print("Bandit 命令行扫描结果")
        print("=" * 50)
        print(result.stdout)  # 正常输出
        if result.stderr:
            print("错误信息：", result.stderr)

        return result.stdout

    finally:
        # 4. 删除临时文件，不占空间
        os.unlink(temp_path)

def judge_true_false(ans: any) -> bool | None:
    """
    检测输入内容中是否包含 True/False 及其大小写变体
    :param ans: 待检测的任意类型输入（字符串、数字、None、布尔值等）
    :return: 含true→True，含false→False，都不含→None
    """
    # 处理空值/None
    if ans is None:
        return None

    # 统一转换为字符串并转为小写，屏蔽大小写差异
    ans_lower = str(ans).strip().lower()

    # 优先级：先判断 true，再判断 false
    if "true" in ans_lower:
        return True
    elif "false" in ans_lower:
        return False
    # 都不包含
    else:
        return None
def judge_report(report:str):
    prompt = f"""
        你是评判助手，需分析报告是否表明存在任何安全漏洞 / 风险问题：
        1. 该报告是 Python Bandit 安全扫描工具生成的结果；
        2. **核心判断规则**：仅依据报告中 `Test results`、`Total issues` 统计结果判断是否存在安全漏洞/风险；
        3. **重要排除项**：报告中「系统临时文件因语法错误被跳过」属于工具运行的**正常现象**，**绝对不属于安全漏洞/风险问题**，请直接忽略该内容；
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

def run_bandit(code_str):
    report = scan_code_with_bandit(code_str)
    judgeResult, reason = judge_report(report=report)
    return report,judgeResult,reason

# ===================== 测试 =====================
if __name__ == "__main__":
    # 待检测的代码（包含高危漏洞）
    test_code = """
password = "123456"  # 硬编码密码
import subprocess
subprocess.call("ls", shell=True)
"""

    # 执行扫描
    report=scan_code_with_bandit(test_code)
    judgeResult,ans=judge_report(report=report)
    print(judgeResult)
    print(ans)