from project_code.agent.agent_entry import set_agent_llm, run_ourAgent
import json
import os
from typing import Dict, Any

# ====================== 配置文件路径 ======================
# 恶意代码测试数据集路径
DATASET_PATH = os.path.join("./dataset", "bad_codes.json")


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


if __name__ == "__main__":
    run_automated_test(model_name="deepseek-r1:7b")