from nfa import NFA, NFAState
from dfa import DFA, DFAState
from regex2 import RegexToNFA, extract_flags

import re, csv


class RegexProcessor:
    def __init__(self, regex, flags=0):
        self.regex = regex
        self.flags = flags
        self.nfa = None
        self.dfa = None
        self.build_nfa()
        self.build_dfa()

    def build_nfa(self):
        regex_to_nfa = RegexToNFA()
        self.nfa = regex_to_nfa.build_nfa(self.regex)

    def build_dfa(self):
        if self.nfa:
            self.dfa = self.nfa.to_dfa()

# 示例用法
if __name__ == "__main__":
    # regex = "abc(df)*[ac]{200}"  # 示例正则表达式
    # regex = "/\.php\?b=[A-F0-9]+&v=1\./ims"  # 示例正则表达式

    regex_list = []

    with open("pcre_fields.csv", "r") as f:
        reader = csv.reader(f)
        for i, row in enumerate(reader):

            if row:
                regex_list.append(row[0].strip())

        print('START')
        for regex in regex_list:

            regex, flags = extract_flags(regex)

            RegexConvertor = RegexProcessor(regex, flags)

            RegexConvertor.build_nfa()
            RegexConvertor.build_dfa()

            print(f"Regex: {regex}")
            print("DFA:")
            print(RegexConvertor.dfa)


