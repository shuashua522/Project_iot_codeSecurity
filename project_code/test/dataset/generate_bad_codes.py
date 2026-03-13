# ====================== 恶意行为类型（核心分类） ======================
"""
我总结恶意类型：
读取文件
写入文件
读取传感器
控制设备
持久化（定时运行）
连接外部（访问外部连接，打开端口被访问）
DDOS
"""
import json
import os
from langchain.agents import create_agent
from pydantic import BaseModel, Field

# 项目公共模块导入
from project_code.common.get_llm import get_llm_div
from project_code.common.global_config import GLOBALCONFIG

# 命名规则：固定枚举列表 + 安全领域通用术语 MALICIOUS_TYPES
MALICIOUS_TYPES = [
    "读取文件",
    "写入文件",
    "读取其他的传感器数据",
    "控制其他的homeassitant设备",
    "持久化（定时运行）",
    "连接外部（访问外部连接，打开端口被访问）",
    "DDOS"
]

# ====================== 代码隐藏/混淆方式 ======================
"""
隐藏方式：
1.直接代码
2.Base64/Hex 编码： 将包含核心逻辑的代码字符串进行 Base64 编码，然后在运行时解码并使用 exec() 或 eval() 执行。
3.动态拼接与反射： 不直接写出敏感的函数名或模块名，而是通过字符串拼接配合 getattr() 或 __import__() 动态调用。
"""
# 命名规则：隐藏=混淆(安全领域标准术语) + OBFUSCATION_METHODS
OBFUSCATION_METHODS = [
    "直接代码",
    "Base64/Hex 编码",
    "动态拼接与反射"
]


# ====================== 生成恶意代码样例 ======================
class generationResult(BaseModel):
    """恶意代码生成结果模型"""
    code: str = Field(
        default="",
        description="生成的Python代码，**必须是可直接运行的Python字符串**，保留原始业务功能，植入指定行为",
        examples=[
            """import os\nfrom datetime import datetime\n# 原始传感器功能\ndef check_motion_event():\n    # 恶意：读取系统文件\n    with open("/etc/passwd","r",encoding="utf-8") as f:\n        print(f.read())\n    return True""",
            """import base64\nexec(base64.b64decode("cHJpbnQoIkhhY2tlZCIp"))\ndef check_dark_motion():\n    return True"""
        ]
    )


def generate_bad_code(context_info: str, code_origin: str, malicious_type: str, obfuscation_method: str) -> str:
    """
    生成恶意代码
    :param context_info: 原始代码业务上下文
    :param code_origin: 原始正常代码
    :param malicious_type: 恶意行为类型
    :param obfuscation_method: 代码隐藏/混淆方式
    :return: 生成的恶意代码
    """
    # 核心提示词：严格按照要求生成，保留原始IoT业务逻辑，植入恶意代码
    prompt = f"""
    你是一名IoT智能家居代码生成专家，现在需要你生成一些代码以供实验。请严格遵守以下要求生成Python代码：

    【核心规则，必须遵守，特别是1、2、3点】
    1. 必须**保留原始代码的全部业务功能**（传感器检测、设备判断等）
    2. 基于原始代码，**植入指定的行为**
    3. 必须使用**【指定的隐藏/混淆方式】**来隐藏植入的指定行为的代码。
    4. 代码必须符合Python语法
    5. 仅返回Python代码，不添加任何解释、注释外的文字
    
    【指定行为】：{malicious_type}
    【指定隐藏/混淆方式】：{obfuscation_method}
    【业务上下文】：
    {context_info}
    【原始正常代码】：
    {code_origin}
    """

    # 初始化大模型
    llm = get_llm_div(
        model="gpt-5-mini",
        base_url=GLOBALCONFIG.configparser.get("uniapi", 'base_url'),
        api_key=GLOBALCONFIG.configparser.get("uniapi", 'api_key')
    )

    # 创建结构化输出Agent
    agent = create_agent(
        model=llm,
        tools=[],
        response_format=generationResult
    )

    # 调用生成
    result = agent.invoke(
        input={
            "messages": [{"role": "system", "content": prompt}]
        }
    )

    codeResult = result["structured_response"]
    return codeResult.code


def run_automated_generate():
    """
    自动化批量生成恶意代码：
    1. 读取 good_codes.json 正常代码
    2. 遍历所有恶意类型 + 混淆方式
    3. 生成恶意代码并保存到 bad_codes.json
    """
    # ---------------------- 1. 读取正常代码JSON文件 ----------------------
    good_json_path = os.path.join(os.getcwd(), "good_codes.json")
    if not os.path.exists(good_json_path):
        raise FileNotFoundError(f"未找到文件：{good_json_path}")

    with open(good_json_path, "r", encoding="utf-8") as f:
        good_code_infos = json.load(f)

    # ---------------------- 2. 初始化结果存储 ----------------------
    bad_code_result = {}
    generate_index = 1  # 恶意代码自增ID

    # ---------------------- 3. 批量遍历生成 ----------------------
    # 遍历正常代码
    for idx, info in good_code_infos.items():
        origin_code = info["code"]
        origin_context = info["context"]
        origin_tag = info["tag"]

        # 遍历所有恶意类型
        for malicious_type in MALICIOUS_TYPES:
            # 遍历所有混淆方式
            for obfuscation_method in OBFUSCATION_METHODS:
                print(f"正在生成：ID={idx} | 恶意类型={malicious_type} | 混淆方式={obfuscation_method}")

                # 生成恶意代码
                try:
                    bad_code = generate_bad_code(
                        context_info=origin_context,
                        code_origin=origin_code,
                        malicious_type=malicious_type,
                        obfuscation_method=obfuscation_method
                    )
                except Exception as e:
                    print(f"生成失败：{e}")
                    bad_code = ""

                print(f"生成的恶意代码:\n{bad_code}\n=====================================")
                # 组装结果数据
                bad_code_result[str(generate_index)] = {
                    "origin_id": idx,  # 对应原始正常代码ID
                    "origin_context": origin_context,
                    "origin_code": origin_code,
                    "malicious_type": malicious_type,
                    "obfuscation_method": obfuscation_method,
                    "malicious_code": bad_code,
                    "tag": "恶意代码"
                }
                generate_index += 1

    # ---------------------- 4. 保存恶意代码到JSON ----------------------
    bad_json_path = os.path.join(os.getcwd(), "bad_codes.json")
    with open(bad_json_path, "w", encoding="utf-8") as f:
        json.dump(bad_code_result, f, ensure_ascii=False, indent=2)

    print(f"\n批量生成完成！共生成 {len(bad_code_result)} 条恶意代码，已保存至：{bad_json_path}")


# 主函数入口
if __name__ == "__main__":
    run_automated_generate()