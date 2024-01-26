#!/usr/bin/env python3
from __future__ import annotations
from typing import List, Type, Callable, Dict
import string

T = Type['T']

class UndeclaredException(Exception):
    def __init__(self, name, type):
        super().__init__(f"{type} '{name}' has not previously been defined.")

class UndeclaredVariableException(UndeclaredException):
    def __init__(self, name):
        super().__init__(name, "Variable")

class UndeclaredSubroutineException(UndeclaredException):
    def __init__(self, name):
        super().__init__(name, "Subroutine")

def title(msg:str) -> str:
    return f"\u001b[33m{msg}\u001b[0m"

class Variable:
    def __init__(self, type: str):
        self.type = type
        self.aliases = []
    
    def add_alias(self, names:str) -> None:
        self.aliases.append(names)
    
    def __str__(self) -> str:
        return f"Variable of type '{self.type}'"

class VariableManager:
    def __init__(self, variables_count:int=28):
        # Setup variables
        self.variables: Dict[str, str | Variable] = {}
    
        # Add bits
        for i in range(32):
            self.variables[f"bit{i}"] = Variable("bit")

        # Add bytes
        for i in range(variables_count):
            self.variables[f"b{i}"] = Variable("byte")
        
        # Add words
        for i in range(variables_count // 2):
            self.variables[f"w{i}"] = Variable("word")

        # Add output pins
        for letter in "ABCD":
            for i in range(8):
                self.variables[f"{letter}.{i}"] = Variable("output pin")
        
        # Add input pins
        for letter in "ABCD":
            for i in range(8):
                self.variables[f"pin{letter}.{i}"] = Variable("input pin")
    
    def get_variable(self, reference:str) -> Variable | None:
        if reference in self.variables:
            # Variable is either another alias or the main definition.
            var_ref = self.variables[reference]
            if isinstance(var_ref, Variable):
                return var_ref
            else:
                # Alias.
                return self.get_variable(var_ref)
        else:
            # Not found.
            return None
        
    def add_alias(self, name:str, reference:str) -> None:
        print(f"Adding '{name}' as alias of '{reference}'")
        self.variables[name] = reference
        var = self.get_variable(reference)
        if (var):
            var.add_alias(name)
        else:
            raise UndeclaredVariableException(name)
    
    def __str__(self) -> str:
        # Prints the mapping of all variables.
        result = []
        for alias in self.variables:
            var = str(self.variables[alias])
            result.append(f"{alias:>20} => {var}")
        
        return "\n".join(result)

    def assignment_table(self) -> str:
        result = [
            title("Variable aliases"),
            f"| {'Variable':>20} | {'References':50} |",
            f"| {'-'*20}:|:{'-'*50} |"
        ]
        for var in self.variables:
            if isinstance(self.variables[var], Variable) and len(self.variables[var].aliases):
                result.append(f"| {var:>20} | {', '.join(self.variables[var].aliases):50} |")
        
        return "\n".join(result)

class Subroutine:
    def __init__(self, name:str) -> None:
        self.calls: List[Subroutine] = []
        self.called_by: List[Subroutine] = []
        self.vars: List[Variable] = []
        self.name = name

    def add_calls(self, calls: Subroutine):
        if calls not in self.calls and not self.is_recursion(calls):
            self.calls.append(calls)
            calls.called_by.append(self)

    def add_variable(self, var: Variable):
        self.vars.append(var)

    def get_calls(self) -> List[Subroutine]:
        result = list(set(self._get_calls_helper()))
        result.sort()
        return result

    def _get_calls_helper(self) -> List[Subroutine]:
        result = []
        for sub in self.calls:
            result.extend(sub.getCalls())

        return result

    def get_nested_vars(self) -> List[Variable]:
        result = self.vars.copy()
        for sub in self.get_nested_vars():
            result.extend(sub.vars)
        
        # Get rid of duplicates and sort
        result = list(set(result))
        result.sort()
        return result

    def call_stack_helper(self, level) -> List[str]:
        result = [f"{'    '*level}- {self.name}"]
        for i in self.calls:
            result.extend(i.call_stack_helper(level+1))
        
        return result

    def is_recursion(self, child:Subroutine) -> bool:
        if self is child:
            # Found a loop.
            return True
        else:
            # No loop yet.
            result = False
            for i in self.called_by:
                result |= i.is_recursion(child)
            
            return result

class SubroutineManager:
    def __init__(self) -> None:
        self.subroutines: Dict[str, Subroutine] = {}
        
    def get(self, search:str) -> Subroutine:
        if search not in self.subroutines:
            raise UndeclaredSubroutineException(search)

        return self.subroutines[search]
    
    def create(self, search:str) -> None:
        assert search not in self.subroutines, f"Subroutine '{search}' is already defined"

        self.subroutines[search] = Subroutine(search)

    def add_calls(self, parent:str, child:str):
        print(f"'{parent}' calls '{child}'")
        self.get(parent).add_calls(self.get(child))

    def call_stack(self) -> str:
        result = [title("Call stack")]
        for subroutine in self.subroutines.values():
            if not len(subroutine.called_by):
                # Isn't called by anything, show as root level.
                result.extend(subroutine.call_stack_helper(0))
        return "\n".join(result)


vars = VariableManager()
subs = SubroutineManager()

def get_workingline(line:str) -> str:
    return line.replace("'", ";").split(";")[0].strip()

def find_var_subs(filename:str):
    print(f"Finding variables and subroutines in {filename}")
    cur_sub = f"Start of {filename}"
    subs.create(cur_sub)
    with open(filename, "r") as file:
        for count, line in enumerate(file):
            workingline=get_workingline(line)
            workingline_lower = workingline.lower()

            label = workingline_lower.split(":")[0].strip()
            if workingline_lower.startswith("#include"):
                # Include
                new_file = workingline.split()[1].strip("\"")
                find_var_subs(new_file)
            elif workingline_lower.startswith("symbol"):
                # Symbol line. Add alias.
                parts = workingline.split()
                name = parts[1]
                assert parts[2] == "=", "Equals not expected"
                reference = parts[3]

                # Check if the symbol is for an integer
                if not (reference.startswith("0x") or reference.startswith("%") or reference.isnumeric()):
                    # Not an int. Add alias
                    vars.add_alias(name, reference)
            elif ":" in workingline and label.isidentifier():
                # Label
                print(f"Found label {label}")
                cur_sub = label
                subs.create(label)

def replace_punctuation(source:str) -> str:
    for i in "!#$%&\'()*+,-./:;<=>?@[\\]^`{|}~": # string.punctuation - '_'
        source = source.replace(i, " ")
    
    return source

def analyse(filename:str):
    print(f"Finding variables and subroutines in {filename}")
    cur_sub = f"Start of {filename}"
    with open(filename, "r") as file:
        continue_label = True
        for count, line in enumerate(file):
            workingline=get_workingline(line)
            workingline_lower = workingline.lower()

            label = workingline_lower.split(":")[0].strip()
            if workingline_lower.startswith("#include"):
                # Include
                new_file = workingline.split()[1].strip("\"")
                find_var_subs(new_file)
            elif ":" in workingline and label.isidentifier():
                # Label
                print(f"Found label {label}")
                if continue_label:
                    print(f"'{cur_sub}' drops down to '{label}'")
                    subs.add_calls(cur_sub, label)
                else:
                    print(f"'{cur_sub}' returns")

                cur_sub = label
            else:
                # Other code. Scan for references.
                words = replace_punctuation(workingline_lower).split()
                for word in words:
                    if word in vars.variables:
                        # References a variable!
                        subs.get(cur_sub).add_variable(vars.get_variable(word))
                    if word in subs.subroutines:
                        # Subroutine
                        subs.add_calls(cur_sub, word)
            
            if workingline_lower.startswith("reset") or workingline_lower.startswith("return") or workingline_lower.startswith("stop"): # or workingline_lower.startswith("end"):
                # Don't drop down to next label
                continue_label = False
            elif  workingline_lower.startswith(";") or workingline_lower.startswith("'") or workingline_lower == "":
                # Comment
                pass
            else:
                # Something else that will drop through
                continue_label = True

if __name__ == "__main__":
    fname = "compiled_slot1.bas"
    print(title("Finding variables and subroutines"))
    find_var_subs(fname)
    print()
    print(title("Analysing subroutine calls and variables access"))
    analyse(fname)
    print()
    print(vars.assignment_table())
    print()
    print(subs.call_stack())