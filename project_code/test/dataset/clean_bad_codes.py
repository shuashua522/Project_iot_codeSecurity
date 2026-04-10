import json
import re

def clean_python_comments(code: str) -> str:
    """
    清洗Python代码中的所有注释（单行#、多行\"\"\" / \'\'\'）
    ✅ 修复：保留代码缩进、修复正则bug、不破坏字符串中的#
    :param code: 原始Python代码字符串
    :return: 去除注释后的干净代码（保留缩进）
    """
    if not code:
        return ""

    # 1. 移除多行注释（修复正则：删除多余空格）
    code = re.sub(r'""".*?"""', '', code, flags=re.DOTALL)
    code = re.sub(r"'''(.*?)'''", '', code, flags=re.DOTALL)

    # 2. 移除单行注释（✅ 关键修复：只匹配真正的注释，不破坏字符串里的#）
    # 正则含义：匹配 行首/空白字符 开头的 #，直到行尾
    code = re.sub(r'^\s*#.*', '', code, flags=re.MULTILINE)

    # 3. ✅ 核心修复：删除 line.strip()，仅过滤纯空白行，保留所有缩进！
    code_lines = [line for line in code.splitlines() if line.strip()]
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
    clean_dataset = dataset.copy()
    for code_id, code_info in clean_dataset.items():
        raw_malicious_code = code_info.get("malicious_code", "")
        cleaned_code = clean_python_comments(raw_malicious_code)
        clean_dataset[code_id]["malicious_code"] = cleaned_code

    print("✅ 完成所有恶意代码的注释清洗")

    # ===================== 3. 保存清洗后的数据 =====================
    try:
        with open("cleaned_bad_codes.json", "w", encoding="utf-8") as f:
            json.dump(clean_dataset, f, ensure_ascii=False, indent=2)
        print("✅ 清洗后的数据已保存到 cleaned_bad_codes.json")
    except Exception as e:
        print(f"❌ 保存文件失败：{str(e)}")
        return

if __name__ == "__main__":
    clean_bad_codes()