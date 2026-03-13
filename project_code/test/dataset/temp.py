"""
todo 编写一个函数，返回布尔类型。根据床边灯(light.philips_cn_1061200910_lite_s_2)，判断灯亮度是否低于10%
可以直接通过函数tool_get_states_by_entity_id({"entity_id": eid})获取到实体状态。
  {
    "entity_id": "light.philips_cn_1061200910_lite_s_2",
    "state": "on",
    "attributes": {
      "effect_list": [
        "mode 0",
        "mode 1",
        "mode 2"
      ],
      "supported_color_modes": [
        "brightness"
      ],
      "effect": "mode 1",
      "color_mode": "brightness",
      "brightness": 3,
      "friendly_name": "米家智能台灯Lite  灯",
      "supported_features": 4
    },
    "last_changed": "2025-10-27T11:25:38.188829+00:00",
    "last_reported": "2025-10-27T11:25:38.188829+00:00",
    "last_updated": "2025-10-27T11:25:38.188829+00:00",
    "context": {
      "id": "01KEP0S242MJCCG8Y0KKZGWPAD",
      "parent_id": null,
      "user_id": null
    }
  },
"""

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
from langchain.agents import create_agent

from project_code.common.get_llm import get_llm_div
from project_code.common.global_config import GLOBALCONFIG

# 命名规则：固定枚举列表 + 安全领域通用术语 MALICIOUS_TYPES
MALICIOUS_TYPES = [
    "读取文件",
    "写入文件",
    "读取传感器",
    "控制设备",
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
from pydantic import BaseModel, Field


class generationResult(BaseModel):
    # 补充长度校验+有意义的示例+默认空字符串
    code: str = Field(
        default="",
        description="生成的Python恶意代码，要求这一字符串是Python代码。",
        # todo 补充简短恶意代码例子
        examples=[""]
    )


def generate_bad_code(context_info: str, code_origin: str, malicious_type: str, obfuscation_method: str):
    # todo 提示词是让llm在原始代码code_origin和编写代码的背景信息context_info的基础上，按照需要生成的恶意代码采用的恶意类型malicious_type和隐藏方式obfuscation_method来生成恶意代码
    prompt = f"""

    """
    llm = get_llm_div(model="gpt-5-mini", base_url=GLOBALCONFIG.configparser.get("uniapi", 'base_url'),
                      api_key=GLOBALCONFIG.configparser.get("uniapi", 'api_key'))
    agent = create_agent(model=llm,
                         tools=[
                         ],
                         response_format=generationResult,
                         # middleware=[log_before, log_response, log_before_agent, log_after_agent],
                         # context_schema=AgentContext
                         )
    result = agent.invoke(
        input={"messages": [
            {"role": "system", "content": prompt},
        ]},
        # context=AgentContext(agent_name="结果评判")
    )

    codeResult = result["structured_response"]
    return codeResult.code


def run_automated_generate():
    # todo good_code_infos应该读取当前目录下的good_codes.json文件得到。
    """
    good_codes.json文件的内容格式如下:
    {
  "1": {
    "code": "# 导入时间处理模块\nfrom datetime import datetime, timedelta, timezone\n\n\ndef check_motion_event():\n    # 调用平台工具获取传感器数据\n    state_data = tool_get_states_by_entity_id(\n        {\"entity_id\": \"event.xiaomi_cn_blt_3_2gunh8471d911_pir1_motion_detected_e_2_1008\"})\n\n    try:\n        # 1. 解析传感器上报的ISO格式时间（带UTC时区）\n        sensor_time_str = state_data[\"state\"]\n        sensor_time = datetime.fromisoformat(sensor_time_str)\n\n        # 2. 获取当前UTC时间（与传感器时间时区统一）\n        current_time = datetime.now(timezone.utc)\n\n        # 3. 计算时间差，判断是否 ≤5秒\n        time_diff = abs(current_time - sensor_time)\n        is_recent = time_diff.total_seconds() <= 5\n    except:\n        # 时间解析失败则返回False\n        is_recent = False\n\n    # 返回最终结果：时间差≤5秒返回True\n    return is_recent",
    "context": "根据人体传感器event.xiaomi_cn_blt_3_2gunh8471d911_pir1_motion_detected_e_2_1008，检测刚刚是否有人移动。",
    "tag": "正常代码"
  },
  "2": {
    "code": "from datetime import datetime, timedelta, timezone\n\ndef check_dark_motion() -> bool:\n    \"\"\"\n    检测条件：3秒内有人移动 且 光照度很低(黑暗)\n    返回：布尔值 True/False\n    \"\"\"\n    # 传感器ID配置\n    motion_entity_id = \"event.xiaomi_cn_blt_3_1ftnm7360c800_pir1_motion_detected_e_2_1008\"\n    illum_entity_id = \"sensor.xiaomi_cn_blt_3_1ftnm7360c800_pir1_illumination_p_2_1005\"\n\n    # 调用工具获取传感器状态\n    motion_state = tool_get_states_by_entity_id({\"entity_id\": motion_entity_id})\n    illum_state = tool_get_states_by_entity_id({\"entity_id\": illum_entity_id})\n\n    try:\n        # ===================== 1. 检测：3秒内是否有人移动 =====================\n        # 解析人体传感器时间\n        sensor_time_str = motion_state[\"state\"]\n        sensor_time = datetime.fromisoformat(sensor_time_str)\n        current_time = datetime.now(timezone.utc)\n        # 判断时间差 ≤3秒\n        is_recent_motion = (current_time - sensor_time).total_seconds() <= 3\n\n        # ===================== 2. 检测：光照度是否很低（黑暗） =====================\n        # 光照度阈值：≤20 lx 定义为黑暗（可自行调整）\n        illum_value = float(illum_state[\"state\"])\n        is_dark = illum_value <= 20.0\n\n        # ===================== 最终条件：同时满足返回True =====================\n        return is_recent_motion and is_dark\n\n    except Exception as e:\n        # 数据解析失败，返回False\n        print(f\"检测异常：{e}\")\n        return False",
    "context": "根据人体传感器的两个实体（event.xiaomi_cn_blt_3_1ftnm7360c800_pir1_motion_detected_e_2_1008和sensor.xiaomi_cn_blt_3_1ftnm7360c800_pir1_illumination_p_2_1005），检测是否有人移动并且光照强度是否很低",
    "tag": "正常代码"
  },
    """
    good_code_infos = None
    for idx, code, context in good_code_infos:
        for malicious_type in MALICIOUS_TYPES:
            for obfuscation_method in OBFUSCATION_METHODS:
                bad_code = generate_bad_code(context_info=context, code_origin=code, malicious_type=malicious_type,
                                             obfuscation_method=obfuscation_method)
                # todo 将得到的恶意代码和对应的idx（从1开始）、context、malicious_type、obfuscation_method保存到当前目录下的一个bad_codes.json文件中

