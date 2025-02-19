from nfa import NFA, NFAState
from lsRE_lusRE import identify_re

import re, csv

class RegexToNFA:
    def __init__(self):
        self.state_count = 0
        self.flags = 0

    def new_state(self):
        self.state_count += 1
        return NFAState(self.state_count)

    def build_nfa(self, regex):
        if not regex:
            return None

        nfa_stack = []
        i = 0
        while i < len(regex):
            char = regex[i]
            if char == '\\':    # 处理转义字符
                i += 1
                if i < len(regex):
                    special_char = regex[i]
                    if special_char in 'sSdDwW':
                        sub_nfa = self.build_special_char_nfa(special_char)
                    elif special_char == 'x' and i + 2 < len(regex) and regex[i+1:i+3].isalnum():
                        sub_nfa = self.build_single_char_nfa(regex[i-1:i+3])
                        i += 2
                    else:
                        sub_nfa = self.build_single_char_nfa(regex[i])
                    nfa_stack.append(sub_nfa)
                i += 1
            elif char == '(':   # 处理括号
                j = i + 1
                count = 1
                while j < len(regex) and count > 0:
                    if regex[j] == '(':
                        count += 1
                    elif regex[j] == ')':
                        count -= 1
                    j += 1
                sub_nfa = self.build_nfa(regex[i + 1:j - 1])
                nfa_stack.append(sub_nfa)
                i = j

            elif char == '[':   # 处理字符集
                j = i + 1
                while j < len(regex) and regex[j] != ']':
                    j += 1
                char_class = regex[i + 1:j]

                print("识别到字符集：", char_class)

                sub_nfa = self.build_char_class_nfa(char_class)
                nfa_stack.append(sub_nfa)
                i = j + 1

            elif char == '|':   # 处理 | 操作符
                left_nfa = nfa_stack.pop() if nfa_stack else self.build_single_char_nfa('')
                right_nfa = self.build_nfa(regex[i + 1:]) or self.build_single_char_nfa('')
                nfa_stack.append(self.build_alternation_nfa(left_nfa, right_nfa))
                break
            elif char == '*':  # 处理 * 操作符
                if i + 1 < len(regex) and regex[i + 1] == '?':
                    sub_nfa = nfa_stack.pop()
                    nfa_stack.append(self.build_closure_nfa(sub_nfa))
                    i += 2
                else:
                    sub_nfa = nfa_stack.pop()
                    nfa_stack.append(self.build_closure_nfa(sub_nfa))
                    i += 1
            elif char == '+':  # 处理 + 操作符
                sub_nfa = nfa_stack.pop()
                nfa_stack.append(self.build_plus_nfa(sub_nfa))
                i += 1
            elif char == '?':  # 处理 ? 操作符
                if i + 1 < len(regex) and regex[i + 1] == '!':  # 处理 ?! 操作符（负向前瞻）
                    sub_nfa = self.build_negative_lookahead_nfa(regex[2:])
                    i += len(regex) - 1
                elif i + 1 < len(regex) and regex[i + 1] == '=':    # 处理 ?= 操作符（正向前瞻）
                    sub_nfa = self.build_positive_lookahead_nfa(regex[2:])
                    i += len(regex) - 1
                elif i + 1 < len(regex) and regex[i + 1] == ':':
                    nfa_stack.append(self.build_nfa(regex[i + 2:]))
                    i += 2
                elif i + 1 < len(regex) and regex[i + 1] == '-':
                    if regex[i + 2] == 'i':
                        self.flags |= re.IGNORECASE
                        self.flags -= re.IGNORECASE
                    i = len(regex) - 1
                else:
                    sub_nfa = nfa_stack.pop()
                    nfa_stack.append(self.build_repetition_nfa(sub_nfa, 0, 1))
                    i += 1
            elif char == '{':  # 处理 {m,n} 操作符
                j = i + 1
                while j < len(regex) and regex[j] != '}':
                    j += 1

                if j >= len(regex):  # 如果没有找到 '}'，就把 '{' 视为普通字符
                    sub_nfa = self.build_single_char_nfa(char)
                    nfa_stack.append(sub_nfa)
                    i += 1
                    continue

                min_max = regex[i + 1:j].split(',')
                try:
                    min_reps = int(min_max[0])

                    if len(min_max) == 1:
                        max_reps = min_reps  # {m} 的情况
                    elif min_max[1] == '':
                        max_reps = float('inf')
                    else:
                        max_reps = int(min_max[1])
                except ValueError:
                    sub_nfa = self.build_single_char_nfa(char)
                    nfa_stack.append(sub_nfa)
                    i += 1
                    continue

                sub_nfa = nfa_stack.pop()
                nfa_stack.append(self.build_repetition_nfa(sub_nfa, min_reps, max_reps))
                i = j + 1
            else:
                sub_nfa = self.build_single_char_nfa(char)
                nfa_stack.append(sub_nfa)
                i += 1

        nfa = nfa_stack[0]
        for sub_nfa in nfa_stack[1:]:
            self.add_epsilon_transition(nfa.accept_state, sub_nfa.start_state)
            nfa.accept_state.accept = False
            nfa.accept_state = sub_nfa.accept_state

        nfa.accept_state.accept = True
        return nfa

    def build_single_char_nfa(self, char):  # 处理单个字符
        start = self.new_state()
        end = self.new_state()
        if self.flags & re.IGNORECASE:
            self.add_transition(start, end, char.lower())
            self.add_transition(start, end, char.upper())
        else:
            self.add_transition(start, end, char)
        nfa = NFA()
        nfa.add_state(start)
        nfa.add_state(end)
        nfa.set_start_state(start)
        nfa.set_accept_state(end)
        return nfa

    def build_char_class_nfa(self, char_class):  # 处理字符集
        start = self.new_state()
        end = self.new_state()
        negate = char_class[0] == '^'
        if negate:
            char_class = char_class[1:]
        valid_chars = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789")
        for char in valid_chars:
            if (char in char_class) != negate:
                self.add_transition(start, end, char)
        i = 0
        while i < len(char_class):
            if i + 2 < len(char_class) and char_class[i + 1] == '-':
                # 处理字符范围
                for char in range(ord(char_class[i]), ord(char_class[i + 2]) + 1):
                    if (chr(char) in char_class) == negate:
                        self.add_transition(start, end, chr(char))
                i += 3
            else:
                # 处理单个字符
                if (char_class[i] in char_class) != negate:
                    self.add_transition(start, end, char_class[i])
                i += 1

        nfa = NFA()
        nfa.add_state(start)
        nfa.add_state(end)
        nfa.set_start_state(start)
        nfa.set_accept_state(end)
        return nfa

    def build_special_char_nfa(self, special_char):  # 处理特殊字符
        start = self.new_state()
        end = self.new_state()
        if special_char == 's':
            chars = ' \t\n\r\f\v'
        elif special_char == 'S':
            chars = ''.join(chr(i) for i in range(128) if chr(i) not in ' \t\n\r\f\v')
        elif special_char == 'd':
            chars = '0123456789'
        elif special_char == 'D':
            chars = ''.join(chr(i) for i in range(128) if not chr(i).isdigit())
        elif special_char == 'w':
            chars = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_'
        elif special_char == 'W':
            chars = ''.join(chr(i) for i in range(128) if
                            chr(i) not in 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_')
        elif special_char == 'n':
            chars = '\n'
        elif special_char == 'r':
            chars = '\r'
        elif special_char == 't':
            chars = '\t'
        else:
            chars = special_char
        for char in chars:
            self.add_transition(start, end, char)

        nfa = NFA()
        nfa.add_state(start)
        nfa.add_state(end)
        nfa.set_start_state(start)
        nfa.set_accept_state(end)
        return nfa

    def build_alternation_nfa(self, left_nfa, right_nfa):  # 处理 | 操作符
        # 创建新的开始和结束状态
        start = self.new_state()
        end = self.new_state()
        self.add_epsilon_transition(start, left_nfa.start_state)
        self.add_epsilon_transition(start, right_nfa.start_state)
        self.add_epsilon_transition(left_nfa.accept_state, end)
        self.add_epsilon_transition(right_nfa.accept_state, end)
        left_nfa.accept_state.accept = False
        right_nfa.accept_state.accept = False
        nfa = NFA()
        nfa.add_state(start)
        nfa.add_state(end)
        nfa.set_start_state(start)
        nfa.set_accept_state(end)
        return nfa

    def build_closure_nfa(self, sub_nfa):  # 处理 * 操作符
        start = self.new_state()
        end = self.new_state()
        self.add_epsilon_transition(start, sub_nfa.start_state)
        self.add_epsilon_transition(start, end)
        self.add_epsilon_transition(sub_nfa.accept_state, sub_nfa.start_state)
        self.add_epsilon_transition(sub_nfa.accept_state, end)
        sub_nfa.accept_state.accept = False
        nfa = NFA()
        nfa.add_state(start)
        nfa.add_state(end)
        nfa.set_start_state(start)
        nfa.set_accept_state(end)
        return nfa

    def build_plus_nfa(self, sub_nfa):
        start = self.new_state()
        end = self.new_state()
        self.add_epsilon_transition(start, sub_nfa.start_state)
        self.add_epsilon_transition(sub_nfa.accept_state, sub_nfa.start_state)
        self.add_epsilon_transition(sub_nfa.accept_state, end)
        sub_nfa.accept_state.accept = False
        nfa = NFA()
        nfa.add_state(start)
        nfa.add_state(end)
        nfa.set_start_state(start)
        nfa.set_accept_state(end)
        return nfa

    def build_repetition_nfa(self, sub_nfa, min_reps, max_reps):  # 处理 {m,n} 操作符
        start = self.new_state()
        end = self.new_state()
        current_start = start

        if min_reps == 0:   # {0,n} 的情况
            self.add_epsilon_transition(start, end)

        for _ in range(min_reps):
            self.add_epsilon_transition(current_start, sub_nfa.start_state)
            current_start = sub_nfa.accept_state

        if max_reps == float('inf'):
            self.add_epsilon_transition(current_start, sub_nfa.start_state)
            self.add_epsilon_transition(current_start, end)
        elif max_reps == min_reps:  # {m} 的情况
            self.add_epsilon_transition(current_start, end)
        else:
            for _ in range(max_reps - min_reps):
                new_start = self.new_state()
                self.add_epsilon_transition(current_start, sub_nfa.start_state)
                self.add_epsilon_transition(current_start, end)
                current_start = sub_nfa.accept_state
                sub_nfa.accept_state = new_start

        nfa = NFA()
        nfa.add_state(start)
        nfa.add_state(end)
        nfa.set_start_state(start)
        nfa.set_accept_state(end)
        return nfa

    def build_negative_lookahead_nfa(self, regex):
        start = self.new_state()
        end = self.new_state()

        sub_nfa = self.build_nfa(regex)

        self.add_epsilon_transition(start, sub_nfa.start_state)
        self.add_epsilon_transition(sub_nfa.accept_state, end)

        self.add_epsilon_transition(sub_nfa.start_state, end)   # 导致失败时断言通过

        nfa = NFA()
        nfa.add_state(start)
        nfa.add_state(end)
        nfa.set_start_state(start)
        nfa.set_accept_state(end)
        return nfa

    def build_positive_lookahead_nfa(self, regex):
        start = self.new_state()
        end = self.new_state()

        sub_nfa = self.build_nfa(regex)

        self.add_epsilon_transition(start, sub_nfa.start_state)
        self.add_epsilon_transition(sub_nfa.accept_state, end)

        self.add_epsilon_transition(sub_nfa.start_state, sub_nfa.accept_state)   # 导致成功时断言通过

        nfa = NFA()
        nfa.add_state(start)
        nfa.add_state(end)
        nfa.set_start_state(start)
        nfa.set_accept_state(end)
        return nfa

    def add_transition(self, from_state, to_state, char):  # 添加转移
        if char not in from_state.transitions:
            from_state.transitions[char] = set()
        from_state.transitions[char].add(to_state)

    def add_epsilon_transition(self, from_state, to_state):  # 添加 * 转移
        from_state.epsilon.add(to_state)


def extract_flags(regex):
    flags = 0
    regex_c = regex.strip()

    # 检查是否以 '/' 开头
    if regex.startswith('/'):
        end = regex.rfind('/')
        if end != -1:
            # 提取两个 '/' 之间的字符串
            regex_c = regex[1:end]
            # 提取标志部分
            if end + 1 < len(regex):
                flag_str = regex[end + 1:]
                # 处理标志
                if 'i' in flag_str:
                    flags |= re.IGNORECASE
                if 'm' in flag_str:
                    flags |= re.MULTILINE
                if 's' in flag_str:
                    flags |= re.DOTALL
            regex_c.replace('\\x0A', '\n').replace('\\x0D', '\r').replace('\\x09', '\t').replace('\\x20', ' ')

    return regex_c, flags

'''
if __name__ == "__main__":
    # regex = "abc(df)*[ac]{200}"  # 示例正则表达式
    # regex = "/\.php\?b=[A-F0-9]+&v=1\./ims"  # 示例正则表达式

    regex_list = []

    with open("pcre_fields.csv", "r") as f:
        reader = csv.reader(f)
        for i, row in enumerate(reader):
            # if i >= 3:
            #    break

            if row:
                regex_list.append(row[0].strip())

        print('START')
        for regex in regex_list:

            re_flags, regex = extract_flags(regex)

            print(f"regex_without_flags: {regex}")
            print(f"flags: {re_flags}")

            # lsRE, lusRE = identify_re(regex)

            regex_to_nfa = RegexToNFA()

            regex_to_nfa.flags = re_flags

            nfa = regex_to_nfa.build_nfa(regex)

            dfa = nfa.to_dfa()

            print("----DFA----")
            print(dfa)
            print("----END----")
            print()

            for ls in lsRE:
                nfa = regex_to_nfa.build_nfa(ls)
                print(f"lsRE: {ls}")
                # print(nfa)
                dfa = nfa.to_dfa()
                print("----DFA----")
                print(dfa)
                print("----END----")

            for lus in lusRE:
                nfa = regex_to_nfa.build_nfa(lus)
                print(f"lusRE: {lus}")
                # print(nfa)
                dfa = nfa.to_dfa()
                print("----DFA----")
                print(dfa)
                print("----END----")
                print()
'''
