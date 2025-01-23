from dfa import DFA, DFAState

class NFAState:
    def __init__(self, state_id):
        self.state_id = state_id
        self.transitions = {}
        self.epsilon = set()
        self.backtrack_transitions = {}  # 用于存储反向边
        self.accept = False

    def __repr__(self, visited=None):  # 递归打印 NFA 状态
        if visited is None:
            visited = set()
        if self in visited:
            return ""
        visited.add(self)
        result = f"NFAState(id={self.state_id}, accept={self.accept})\n"
        for char, targets in self.transitions.items():
            for target in targets:
                result += f"（{self.state_id} --{char}-> {target.state_id})\n"
                result += target.__repr__(visited)
        for target in self.epsilon:
            result += f"（{self.state_id} --ε-> {target.state_id})\n"
            result += target.__repr__(visited)
        for char, target in self.backtrack_transitions.items():
            result += f"（{self.state_id} --{char}-> {target.state_id}) (backtrack)\n"
            result += target.__repr__(visited)

        return result


class NFA:
    def __init__(self):
        self.states = []
        self.start_state = None
        self.accept_state = None

    def add_state(self, state):
        self.states.append(state)
        return state

    def set_start_state(self, state):
        self.start_state = state

    def set_accept_state(self, state):
        self.accept_state = state

    def add_transition(self, from_state, to_state, char):
        if char not in from_state.transitions:
            from_state.transitions[char] = set()
        from_state.transitions[char].add(to_state)

    def add_epsilon_transition(self, from_state, to_state):
        from_state.epsilon.add(to_state)

    def add_backtrack_transition(self, from_state, to_state, char):
        from_state.backtrack_transitions[char] = to_state

    def to_dfa(self):
        from collections import deque

        def get_epsilon_closure(nfa_states):  # 计算 NFA 状态集合的 ε-闭包
            stack = list(nfa_states)
            closure = set(nfa_states)
            while stack:
                state = stack.pop()
                for next_state in state.epsilon:
                    if next_state not in closure:
                        closure.add(next_state)
                        stack.append(next_state)
            return closure

        def move(nfa_states, char):  # 计算 NFA 状态集合在输入字符上的转移
            next_states = set()
            for state in nfa_states:
                if char in state.transitions:
                    next_states.update(state.transitions[char])
            return next_states

        dfa = DFA()
        state_map = {}
        state_count = 0

        start_closure = get_epsilon_closure({self.start_state})
        start_state = DFAState(state_count, start_closure)
        dfa.set_start_state(start_state)
        dfa.add_state(start_state)
        state_map[frozenset(start_closure)] = start_state
        state_count += 1

        queue = deque([start_state])
        while queue:
            current_dfa_state = queue.popleft()
            nfa_states = current_dfa_state.nfa_states
            all_chars = set(char for state in nfa_states for char in state.transitions)

            for char in all_chars:
                next_nfa_states = get_epsilon_closure(move(nfa_states, char))
                if frozenset(next_nfa_states) not in state_map:
                    new_dfa_state = DFAState(state_count, next_nfa_states)
                    dfa.add_state(new_dfa_state)
                    state_map[frozenset(next_nfa_states)] = new_dfa_state
                    state_count += 1
                    queue.append(new_dfa_state)
                current_dfa_state.transitions[char] = state_map[frozenset(next_nfa_states)]

        return dfa

    def __repr__(self):
        return f"----NFA----\n " \
               f"(start=\n" \
               f"{self.start_state}, accept={self.accept_state})"

