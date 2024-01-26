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

def highlight(msg:str) -> str:
    return f"\u001b[34m{msg}\u001b[39m"

def highlight2(msg:str) -> str:
    return f"\u001b[35m{msg}\u001b[39m"

def highlight3(msg:str) -> str:
    return f"\u001b[32m{msg}\u001b[39m"

def underline(msg:str) -> str:
    return f"\u001b[4m{msg}\u001b[24m"

def bold(msg:str) -> str:
    return f"\u001b[1m{msg}\u001b[0m"

class Variable:
    def __init__(self, type: str, name:str):
        self.type = type
        self.aliases: List[str] = []
        self.name = name
        self.shares: List[Variable] = []
        self._ref = False
        self._force_show = False
    
    def add_alias(self, names:str) -> None:
        self.aliases.append(names)
    
    def __str__(self) -> str:
        return f"Variable of type '{self.type}'"
    
    def __repr__(self) -> str:
        return f"({underline(self.name)}, {', '.join(self.aliases)})"
    
    def is_referenced(self, include_force_show:bool=True) -> bool:
        return bool(len(self.aliases)) or self._ref or (include_force_show and self._force_show)

    def set_referenced(self) -> None:
        self._ref = True

    def force_show(self) -> None:
        self._force_show = True

    def referenced_shares(self, include_force_show:bool=True) -> List[Variable]:
        return list(filter(lambda var: var.is_referenced(include_force_show), self.shares))
    
    def coloured_name(self, length:int=0) -> str:
        name_length = f"{self.name:>{length}}"
        if not self.is_referenced(False) and len(self.referenced_shares(False)) == 0:
            # Not reference by anything.
            return highlight(name_length)
        else:
            return name_length

class VariableManager:
    def __init__(self, variables_count:int=28):
        # Setup variables
        self.variables: Dict[str, str | Variable] = {}
    
        # Add words
        for i in range(variables_count // 2):
            name = f"w{i}"
            self.variables[name] = Variable("word", name)
            self.variables[name].force_show()

        # Add bytes
        for i in range(variables_count):
            name = f"b{i}"
            self.variables[name] = Variable("byte", name)
            self.share_vars(self.variables[name], self.variables[f"w{i//2}"])
            self.variables[name].force_show()

        # Add bits
        for i in range(32):
            name = f"bit{i}"
            self.variables[name] = Variable("bit", name)
            self.share_vars(self.variables[name], self.variables[f"b{i//8}"])
            self.share_vars(self.variables[name], self.variables[f"w{i//16}"])


        # Add output pins
        for letter in "ABCD":
            for i in range(8):
                name = f"{letter}.{i}"
                self.variables[name] = Variable("output pin", name)
        
        # Add input pins
        for letter in "ABCD":
            for i in range(8):
                name = f"pin{letter}.{i}"
                self.variables[name] = Variable("input pin", name)

        # Special variables
        self.variables["time"] = Variable("special", "time")
        self.variables["bptr"] = Variable("special", "bptr")
        self.variables["@bptr"] = Variable("special", "@bptr")
        self.variables["@bptrinc"] = Variable("special", "@bptrinc")
    
    def share_vars(self, var1: Variable, var2: Variable) -> None:
        var1.shares.append(var2)
        var2.shares.append(var1)

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
            f"| {'Variable':>20} | {'References':50} | {'Shares':50} |",
            f"| {'-'*20}:|:{'-'*50} |:{'-'*50} |"
        ]
        for var in self.variables:
            var_obj = self.variables[var]
            if isinstance(var_obj, Variable) and var_obj.is_referenced():
                result.append(f"| {var_obj.coloured_name(20)} | {', '.join(var_obj.aliases):50} | {', '.join([i.coloured_name() for i in var_obj.referenced_shares()]):50} |")
        
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
        var.set_referenced()
        if var not in self.vars:
            self.vars.append(var)

    def get_calls(self) -> List[Subroutine]:
        result = list(set(self._get_calls_helper()))
        return result

    def _get_calls_helper(self) -> List[Subroutine]:
        result = self.calls.copy()
        for sub in self.calls:
            result.extend(sub._get_calls_helper())

        return result

    def get_nested_vars(self) -> List[Variable]:
        result = self.vars.copy()
        for sub in self.get_calls():
            result.extend(sub.vars)
        
        # Get rid of duplicates and sort
        result = list(set(result))
        return result

    def call_stack_helper(self, level) -> List[str]:
        def format_var_list(lst:List[Variable]) -> str:
            return ", ".join([repr(v) for v in sortByName(lst)])

        result = [
            bold(f"{'  '*level}{highlight(str(level) + '.')} {self.name}"),
            # f"{'  '*(level+1)}{highlight2('-')} {', '.join(self.get_nested_vars())}",
            highlight2(f"{'  '*(level+1)}- {format_var_list(self.vars)}"),
            highlight3(f"{'  '*(level+1)}> {format_var_list(self.get_nested_vars())}"),
        ]
        # print(self.get_calls())
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
    
    def __repr__(self) -> str:
        return self.name

VS = Type[Variable | Subroutine]
def sortByName(lst:List[VS]) -> List[VS]:
    return sorted(lst, key=lambda item: item.name)

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
            elif not workingline_lower.startswith("symbol"):
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