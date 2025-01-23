class DFAState:
    def __init__(self, state_id, nfa_states):
        self.state_id = state_id
        self.nfa_states = nfa_states
        self.transitions = {}
        self.accept = any(state.accept for state in nfa_states)

    def __repr__(self):
        result = f"DFAState(id={self.state_id}, accept={self.accept})\n"
        for char, target in self.transitions.items():
            result += f"{self.state_id} --{char}-> {target.state_id}\n"
        return result


class DFA:
    def __init__(self):
        self.states = []
        self.start_state = None
        self.accept_states = []

    def add_state(self, state):
        self.states.append(state)
        if state.accept:
            self.accept_states.append(state)
        return state

    def set_start_state(self, state):
        self.start_state = state

    def __repr__(self):
        result = ""
        result += f"Start State: {self.start_state.state_id}\n"
        result += "States:\n"
        for state in self.states:
            result += repr(state)
        return result