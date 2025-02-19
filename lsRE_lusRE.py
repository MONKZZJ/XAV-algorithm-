import re

# 功能函数：识别正则表达式中的 lsRE 和 lusRE
def identify_re(pattern):
    # 匹配 lusRE 部分：匹配 `.*` 或者重复超过128次的部分（如 {129,}）
    lus_re_regex = r".\*\?|"\
                   r"\\[sSwWdDnrt]\*\?|"\
                   r"\\[sSwWdDnrt]\*|"\
                   r".\*|"\
                   r"\([^\)]*\)\*\?|" \
                   r"\[[^\]]*\]\*\?|" \
                   r"\([^\)]*\)\*|" \
                   r"\[[^\]]*\]\*|" \
                   r"\[[^\]]*\]\{[^\}]*\}"

    # 识别所有符合 lusRE 的部分
    lus_res = re.findall(lus_re_regex, pattern)

    # 输出 lusRE 部分
    if lus_res:
        for lus in lus_res:
            # print(f"lusRE: {lus}")
            pass
    else:
        print("No lusRE found.")

    # 将 lusRE 部分从原始字符串中替换为特殊标记，保留逻辑符号
    remaining_pattern = pattern
    for lus in lus_res:
        remaining_pattern = remaining_pattern.replace(lus, "~LUS~")

    # 分割并输出剩余的部分（即 lsRE），逐个输出
    # 使用正则表达式分割，确保逻辑符号（如 |）不被单独割裂
    ls_res = re.split(r'(~LUS~)', remaining_pattern)
    ls_res = [ls for ls in ls_res if ls and ls != "~LUS~"]

    found_ls_re = False
    for ls in ls_res:
        if ls:  # 只输出非空的部分
            # print(f"lsRE: {ls}")
            found_ls_re = True

    if not found_ls_re:
        print("No lsRE found.")

    return ls_res, lus_res


# 测试用例
if __name__ == "__main__":
    pattern = "TO_CHAR\s*\(\s*SYSTIMESTAMP\s*,\s*(\x27[^\x27]{256}|\x22[^\x22]{256})"  # 示例正则表达式
    ls, lus = identify_re(pattern)
    print("ls:", ls)
    print("lus:", lus)