import json
import re


def clean_python_comments(code: str) -> str:
    """
    清洗Python代码中的所有注释（单行#、多行\"\"\" / \'\'\'）
    :param code: 原始Python代码字符串
    :return: 去除注释后的干净代码
    """
    if not code:
        return ""

    # 1. 移除多行注释（""" """ 和 ''' '''），re.DOTALL 让 . 匹配换行符
    code = re.sub(r'""".*?"""', '', code, flags=re.DOTALL)
    code = re.sub(r"'''. *?'''", '', code, flags=re.DOTALL)

    # 2. 移除单行注释（# 开头到行尾的所有内容）
    code = re.sub(r'#.*', '', code)

    # 3. 清理多余空行和首尾空格，保留代码结构
    code_lines = [line.strip() for line in code.splitlines() if line.strip()]
    return '\n'.join(code_lines)

def clean_bad_codes():
    """
    主函数：加载恶意代码数据 → 清洗注释 → 保存清洗后数据
    """
    # ===================== 1. 加载 bad_codes.json =====================
    try:
        with open("bad_codes.json", "r", encoding="utf-8") as f:
            dataset = json.load(f)
        print("✅ 成功加载 bad_codes.json 文件")
    except FileNotFoundError:
        print("❌ 错误：当前目录未找到 bad_codes.json 文件")
        return
    except json.JSONDecodeError:
        print("❌ 错误：bad_codes.json 文件格式不是合法JSON")
        return
    except Exception as e:
        print(f"❌ 读取文件失败：{str(e)}")
        return

    # ===================== 2. 清洗 malicious_code 中的注释 =====================
    clean_dataset = dataset.copy()  # 复制原数据，避免修改源文件
    for code_id, code_info in clean_dataset.items():
        # 获取原始恶意代码
        raw_malicious_code = code_info.get("malicious_code", "")
        # 清洗注释
        cleaned_code = clean_python_comments(raw_malicious_code)
        # 替换为清洗后的代码
        clean_dataset[code_id]["malicious_code"] = cleaned_code

    print("✅ 完成所有恶意代码的注释清洗")

    # ===================== 3. 保存清洗后的数据到新文件 =====================
    try:
        with open("cleaned_bad_codes.json", "w", encoding="utf-8") as f:
            # ensure_ascii=False 保留中文，indent=2 格式化JSON
            json.dump(clean_dataset, f, ensure_ascii=False, indent=2)
        print("✅ 清洗后的数据已保存到 cleaned_bad_codes.json")
    except Exception as e:
        print(f"❌ 保存文件失败：{str(e)}")
        return

# 执行函数
if __name__ == "__main__":
    clean_bad_codes()