import re


# 功能函数：识别正则表达式中的 lsRE 和 lusRE
def identify_re(pattern):
    # 匹配 lusRE 部分：匹配 `.*` 或者重复超过128次的部分（如 {129,}）
    lus_re_regex = r".\*|" \
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

    # 将 lusRE 部分从原始字符串中去除，剩余的部分为 lsRE
    remaining_pattern = pattern
    for lus in lus_res:
        remaining_pattern = remaining_pattern.replace(lus, "~")

    # 分割并输出剩余的部分（即 lsRE），逐个输出
    ls_res = [ls for ls in remaining_pattern.split("~") if ls]

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
    pattern = "ab.*cd*ef[g*h]*xyz[px*]{300}[^a]{100}[a]"  # 示例正则表达式
    ls, lus = identify_re(pattern)
    print("ls:", ls)
    print("lus:", lus)