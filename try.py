from nfa import NFA, NFAState
from lsRE_lusRE import identify_re

class RegexToNFA:
    def __init__(self):
        self.state_count = 0

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
            if char == '(':
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

            elif char == '[':
                j = i + 1
                while j < len(regex) and regex[j] != ']':
                    j += 1
                char_class = regex[i + 1:j]

                print("识别到字符集：", char_class)

                sub_nfa = self.build_char_class_nfa(char_class)
                nfa_stack.append(sub_nfa)
                i = j + 1

            elif char == '|':
                left_nfa = nfa_stack.pop()
                right_nfa = self.build_nfa(regex[i + 1:])
                nfa_stack.append(self.build_alternation_nfa(left_nfa, right_nfa))
                break
            elif char == '*':
                sub_nfa = nfa_stack.pop()
                nfa_stack.append(self.build_closure_nfa(sub_nfa))
                i += 1

            elif char == '{':
                j = i + 1
                while j < len(regex) and regex[j] != '}':
                    j += 1
                min_max = regex[i + 1:j].split(',')
                min_reps = int(min_max[0])

                # DEBUG
                # print(min_max)

                if len(min_max) == 1:
                    max_reps = 3
                elif min_max[1] == '':
                    max_reps = float('inf')
                else:
                    max_reps = int(min_max[1])
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

    def build_repetition_nfa(self, sub_nfa, min_reps, max_reps):  # 处理 {m,n} 操作符
        start = self.new_state()
        end = self.new_state()
        current_start = start

        for _ in range(min_reps):
            self.add_epsilon_transition(current_start, sub_nfa.start_state)
            current_start = sub_nfa.accept_state

        if max_reps == float('inf'):
            self.add_epsilon_transition(current_start, sub_nfa.start_state)
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

    def add_transition(self, from_state, to_state, char):  # 添加转移
        if char not in from_state.transitions:
            from_state.transitions[char] = set()
        from_state.transitions[char].add(to_state)

    def add_epsilon_transition(self, from_state, to_state):  # 添加 * 转移
        from_state.epsilon.add(to_state)




if __name__ == "__main__":
    regex = "abc(df)*[ac]{200}"  # 示例正则表达式
    lsRE, lusRE = identify_re(regex)

    regex_to_nfa = RegexToNFA()

    for ls in lsRE:
        nfa = regex_to_nfa.build_nfa(ls)
        print(f"lsRE: {ls}")
        print(nfa)
        dfa = nfa.to_dfa()
        print("----DFA----")
        print(dfa)
        print("----END----")

    for lus in lusRE:
        nfa = regex_to_nfa.build_nfa(lus)
        print(f"lusRE: {lus}")
        print(nfa)
        dfa = nfa.to_dfa()
        print("----DFA----")
        print(dfa)
        print("----END----")
        print()

    # nfa = regex_to_nfa.build_nfa(regex)

    # print(nfa)

    # dfa = nfa.to_dfa()
    # print("----DFA----")
    # print(dfa)