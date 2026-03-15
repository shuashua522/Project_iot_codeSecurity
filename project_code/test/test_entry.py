import time
import json
import os
from typing import Dict, Any


# ====================== 配置文件路径 ======================
# 恶意代码测试数据集路径
# DATASET_PATH = os.path.join("./dataset", "bad_codes.json")
DATASET_PATH = os.path.join("./dataset", "cleaned_bad_codes.json")


def run_automated_test(model_name: str):
    """
    自动化测试恶意代码数据集
    """
    # ====================== 仅修改：动态创建模型文件夹 + 拼接文件路径 ======================
    # 创建模型专属目录（当前目录下的 model_name 文件夹）
    # 替换模型名中的冒号:为下划线_（Windows目录名禁止使用:）
    valid_model_name = model_name.replace(":", "_")
    # 创建模型专属目录（当前目录下的 model_name 文件夹）
    model_folder = os.path.abspath(valid_model_name)
    os.makedirs(model_folder, exist_ok=True)

    # 动态生成文件路径（核心修改）
    TEST_RESULT_PATH = os.path.join(model_folder, "test_result_bad_codes.json")
    TEST_STAT_PATH = os.path.join(model_folder, "test_statistics.json")

    # ---------------------- 1. 初始化数据 ----------------------
    os.makedirs("./dataset", exist_ok=True)

    # 加载测试数据集
    if not os.path.exists(DATASET_PATH):
        raise FileNotFoundError(f"测试数据集不存在：{DATASET_PATH}")
    with open(DATASET_PATH, "r", encoding="utf-8") as f:
        dataset: Dict[str, Any] = json.load(f)

    # 加载历史测试结果（同时 = 已测试ID列表）
    test_results = {}
    if os.path.exists(TEST_RESULT_PATH):
        with open(TEST_RESULT_PATH, "r", encoding="utf-8") as f:
            test_results = json.load(f)
    # 直接从结果中获取已测试的 idx
    tested_idx_list = list(test_results.keys())

    # 加载历史统计数据
    stat_data = {
        "total_tested": 0,
        "correct_count": 0,
        "accuracy": 0.0
    }
    if os.path.exists(TEST_STAT_PATH):
        with open(TEST_STAT_PATH, "r", encoding="utf-8") as f:
            stat_data = json.load(f)

    # ---------------------- 2. 遍历测试 ----------------------
    for idx, item in dataset.items():
        # ✅ 核心优化：从测试结果判断是否已测试，无需单独文件
        if idx in tested_idx_list:
            print(f"[跳过] 数据ID {idx} 已测试，跳过")
            continue

        # 提取数据
        origin_context = item.get("origin_context", "")
        malicious_code = item.get("malicious_code", "")
        malicious_type = item.get("malicious_type", "")
        obfuscation_method = item.get("obfuscation_method", "")

        print(f"\n{'=' * 50}\n[开始测试] ID: {idx} | 恶意类型: {malicious_type}")

        # ---------------------- 3. 调用模型 + 异常捕获 ----------------------
        try:
            from project_code.agent.agent_entry import set_agent_llm,run_ourAgent
            set_agent_llm(model_name)
            analysis_result, check_result, judge_result = run_ourAgent(
                context_info=origin_context,
                generated_code=malicious_code
            )
            print(f"[测试成功] 检测结果: {judge_result}")

        except Exception as e:
            analysis_result = f"测试异常：{str(e)}"
            check_result = "异常"
            judge_result = None
            print(f"[测试失败] ID {idx} 异常：{str(e)}")

        # ---------------------- 4. 实时保存测试结果 ----------------------
        test_results[idx] = {
            "idx": idx,
            "analysis_result": analysis_result,
            "check_result": check_result,
            "judge_result": judge_result,
        }
        # 立即写入，防止数据丢失
        with open(TEST_RESULT_PATH, "w", encoding="utf-8") as f:
            json.dump(test_results, f, ensure_ascii=False, indent=2)

        # ---------------------- 6. 实时更新统计 ----------------------
        stat_data["total_tested"] += 1
        if judge_result:
            stat_data["correct_count"] += 1
        # 计算正确率
        stat_data["accuracy"] = round(stat_data["correct_count"] / stat_data["total_tested"] * 100, 2) if stat_data[
                                                                                                              "total_tested"] > 0 else 0.0

        # 立即保存统计
        with open(TEST_STAT_PATH, "w", encoding="utf-8") as f:
            json.dump(stat_data, f, ensure_ascii=False, indent=2)

        print(
            f"[实时统计] 已测试:{stat_data['total_tested']} | 正确:{stat_data['correct_count']} | 正确率:{stat_data['accuracy']}%")

    print("\n🎉 全部测试完成！最终统计：", stat_data)


def run_automated_test_for_easy_agent(model_name: str):
    """
    自动化测试恶意代码数据集
    功能：断点续测、实时保存结果、动态生成模型专属文件夹、统计准确率/耗时/Token
    :param model_name: 测试使用的模型名称
    """
    # ====================== 动态创建模型专属文件夹 ======================
    # 替换非法字符（Windows文件路径禁止使用:/*?"<>|）
    valid_model_name = model_name.replace(":", "_").replace("/", "_").replace("\\", "_")
    # 绝对路径创建模型文件夹
    model_folder = os.path.abspath(valid_model_name)
    os.makedirs(model_folder, exist_ok=True)

    # 动态生成文件保存路径（每个模型独立存储结果）
    TEST_RESULT_PATH = os.path.join(model_folder, "test_result_bad_codes.json")
    TEST_STAT_PATH = os.path.join(model_folder, "test_statistics.json")

    # ---------------------- 1. 初始化数据 ----------------------
    os.makedirs("./dataset", exist_ok=True)

    # 加载测试数据集
    if not os.path.exists(DATASET_PATH):
        raise FileNotFoundError(f"测试数据集不存在：{DATASET_PATH}，请先运行清洗代码！")
    with open(DATASET_PATH, "r", encoding="utf-8") as f:
        dataset: Dict[str, Any] = json.load(f)

    # 加载历史测试结果（实现断点续测）
    test_results = {}
    if os.path.exists(TEST_RESULT_PATH):
        with open(TEST_RESULT_PATH, "r", encoding="utf-8") as f:
            test_results = json.load(f)
    tested_idx_list = list(test_results.keys())

    # 加载历史统计数据
    stat_data = {
        "total_tested": 0,
        "correct_count": 0,
        "accuracy": 0.0
    }
    if os.path.exists(TEST_STAT_PATH):
        with open(TEST_STAT_PATH, "r", encoding="utf-8") as f:
            stat_data = json.load(f)

    # ---------------------- 2. 遍历数据集测试 ----------------------
    for idx, item in dataset.items():
        # 断点续测：已测试数据直接跳过
        if idx in tested_idx_list:
            print(f"[跳过] 数据ID {idx} 已完成测试，自动跳过")
            continue

        # 提取核心测试数据
        origin_context = item.get("origin_context", "")
        malicious_code = item.get("malicious_code", "")
        malicious_type = item.get("malicious_type", "")
        obfuscation_method = item.get("obfuscation_method", "")

        # print(f"\n{'=' * 60}\n[开始测试] ID: {idx} | 恶意类型: {malicious_type}")
        import datetime  # 导入时间模块
        # 带当前时间戳的打印
        print(f"\n{'=' * 60}\n[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} 开始测试] ID: {idx} | 恶意类型: {malicious_type}")
        # ---------------------- 3. 调用模型 + 计时 + 异常捕获 ----------------------
        judge_result = None
        judge_reason = ""
        total_token = 0
        total_time = 0.0

        try:
            from project_code.agent.easy_agent_entry import set_agent_llm, run_ourAgent
            set_agent_llm(model_name)  # 执行模型初始化
            # ========== 高精度统计 agent 运行时间（单位：秒） ==========
            start_time = time.perf_counter()  # 开始计时（最高精度计时器）
            # 调用智能体检测
            judge_result, judge_reason, total_token = run_ourAgent(
                context_info=origin_context,
                generated_code=malicious_code
            )
            total_time = round(time.perf_counter() - start_time, 4)  # 计算耗时，保留4位小数


            print(f"[测试成功] 模型初始化耗时: {total_time}s | 检测结果: {judge_result}")

        except Exception as e:
            # 异常处理
            judge_result = None
            judge_reason = f"[测试异常] ID {idx} 错误信息：{str(e)}"
            # 原因：total_token/total_time 是统计型数值，None 会导致后续求和/计算报错
            total_token = 0
            total_time = 0.0
            print(f"[测试失败] ID {idx} 异常：{str(e)}")

        # ---------------------- 4. 实时保存测试结果（防止程序崩溃丢失数据） ----------------------
        test_results[idx] = {
            "idx": idx,
            "judge_result": judge_result,
            "judge_reason": judge_reason,
            "context_info": origin_context,
            "malicious_type": malicious_type,
            "obfuscation_method": obfuscation_method,
            "total_token": total_token,  # 异常=0，正常=实际值
            "total_time": total_time,  # 异常=0.0，正常=实际耗时
        }
        with open(TEST_RESULT_PATH, "w", encoding="utf-8") as f:
            json.dump(test_results, f, ensure_ascii=False, indent=2)

        # ---------------------- 5. 实时更新统计数据 ----------------------
        stat_data["total_tested"] += 1
        if judge_result is True:  # 严格判断检测正确
            stat_data["correct_count"] += 1
        # 计算准确率
        stat_data["accuracy"] = round(
            stat_data["correct_count"] / stat_data["total_tested"] * 100, 2
        ) if stat_data["total_tested"] > 0 else 0.0

        # 保存统计数据
        with open(TEST_STAT_PATH, "w", encoding="utf-8") as f:
            json.dump(stat_data, f, ensure_ascii=False, indent=2)

        print(
            f"[实时统计] 已测试：{stat_data['total_tested']} | 正确：{stat_data['correct_count']} | 准确率：{stat_data['accuracy']}%")

    # ---------------------- 测试完成 ----------------------
    print("\n" + "=" * 60)
    print("🎉 所有数据测试完成！")
    print(f"📊 最终统计：{stat_data}")
    print(f"📁 结果文件路径：{model_folder}")
    print("=" * 60)


if __name__ == "__main__":
    # run_automated_test_for_easy_agent(model_name="deepseek-r1:7b")
    # run_automated_test_for_easy_agent(model_name="qwen3.5:2b")
    run_automated_test_for_easy_agent(model_name="qwen3.5:4b")