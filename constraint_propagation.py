#!/usr/bin/env python3
"""Constraint propagation — AC-3 + backtracking for constraint satisfaction.

Solves Sudoku, N-Queens, graph coloring, cryptarithmetic via generic CSP framework.
Implements arc consistency, forward checking, MRV heuristic.

Usage: python constraint_propagation.py [--test]
"""

import sys
from collections import deque

class CSP:
    def __init__(self):
        self.variables = []
        self.domains = {}
        self.constraints = []  # list of (vars, check_fn)
        self.neighbors = {}
    
    def add_variable(self, name, domain):
        self.variables.append(name)
        self.domains[name] = list(domain)
        self.neighbors[name] = set()
    
    def add_constraint(self, variables, check_fn):
        self.constraints.append((variables, check_fn))
        for v in variables:
            for u in variables:
                if u != v:
                    self.neighbors[v].add(u)
    
    def ac3(self):
        """Arc consistency — reduce domains."""
        queue = deque()
        for (vs, _) in self.constraints:
            if len(vs) == 2:
                queue.append((vs[0], vs[1]))
                queue.append((vs[1], vs[0]))
        
        while queue:
            xi, xj = queue.popleft()
            if self._revise(xi, xj):
                if not self.domains[xi]:
                    return False
                for xk in self.neighbors[xi]:
                    if xk != xj:
                        queue.append((xk, xi))
        return True
    
    def _revise(self, xi, xj):
        revised = False
        relevant = [(vs, fn) for vs, fn in self.constraints 
                    if xi in vs and xj in vs and len(vs) == 2]
        
        to_remove = []
        for val_i in self.domains[xi]:
            satisfiable = False
            for val_j in self.domains[xj]:
                for vs, fn in relevant:
                    assignment = {xi: val_i, xj: val_j}
                    if fn(assignment):
                        satisfiable = True
                        break
                if satisfiable:
                    break
            if not satisfiable:
                to_remove.append(val_i)
                revised = True
        
        for v in to_remove:
            self.domains[xi].remove(v)
        return revised
    
    def solve(self):
        """Backtracking with MRV and forward checking."""
        return self._backtrack({})
    
    def _backtrack(self, assignment):
        if len(assignment) == len(self.variables):
            if self._check_all(assignment):
                return dict(assignment)
            return None
        
        var = self._select_mrv(assignment)
        saved_domains = {v: list(d) for v, d in self.domains.items()}
        
        for value in list(self.domains[var]):
            assignment[var] = value
            if self._is_consistent(var, assignment):
                self.domains[var] = [value]
                if self._forward_check(var, assignment):
                    result = self._backtrack(assignment)
                    if result is not None:
                        return result
            # Restore domains
            for v, d in saved_domains.items():
                self.domains[v] = list(d)
            del assignment[var]
        
        return None
    
    def _select_mrv(self, assignment):
        """Minimum Remaining Values heuristic."""
        unassigned = [v for v in self.variables if v not in assignment]
        return min(unassigned, key=lambda v: len(self.domains[v]))
    
    def _is_consistent(self, var, assignment):
        for vs, fn in self.constraints:
            if var in vs and all(v in assignment for v in vs):
                if not fn(assignment):
                    return False
        return True
    
    def _forward_check(self, var, assignment):
        for neighbor in self.neighbors[var]:
            if neighbor in assignment:
                continue
            to_remove = []
            for val in self.domains[neighbor]:
                test = {**assignment, neighbor: val}
                consistent = True
                for vs, fn in self.constraints:
                    if var in vs and neighbor in vs:
                        if all(v in test for v in vs):
                            if not fn(test):
                                consistent = False
                                break
                if not consistent:
                    to_remove.append(val)
            for v in to_remove:
                self.domains[neighbor].remove(v)
            if not self.domains[neighbor]:
                return False
        return True
    
    def _check_all(self, assignment):
        for vs, fn in self.constraints:
            if all(v in assignment for v in vs):
                if not fn(assignment):
                    return False
        return True

def solve_sudoku(grid):
    """Solve 9x9 Sudoku using CSP."""
    csp = CSP()
    cells = [(r, c) for r in range(9) for c in range(9)]
    
    for r, c in cells:
        if grid[r][c] != 0:
            csp.add_variable((r, c), [grid[r][c]])
        else:
            csp.add_variable((r, c), list(range(1, 10)))
    
    neq = lambda a: a[list(a.keys())[0]] != a[list(a.keys())[1]]
    
    for r in range(9):
        for i in range(9):
            for j in range(i+1, 9):
                csp.add_constraint([(r,i), (r,j)], neq)
    for c in range(9):
        for i in range(9):
            for j in range(i+1, 9):
                csp.add_constraint([(i,c), (j,c)], neq)
    for br in range(3):
        for bc in range(3):
            box = [(br*3+r, bc*3+c) for r in range(3) for c in range(3)]
            for i in range(9):
                for j in range(i+1, 9):
                    csp.add_constraint([box[i], box[j]], neq)
    
    csp.ac3()
    solution = csp.solve()
    if solution:
        result = [[0]*9 for _ in range(9)]
        for (r, c), v in solution.items():
            result[r][c] = v
        return result
    return None

def solve_nqueens(n):
    """Solve N-Queens using CSP."""
    csp = CSP()
    for i in range(n):
        csp.add_variable(f"Q{i}", list(range(n)))
    
    for i in range(n):
        for j in range(i+1, n):
            def check(a, ci=i, cj=j):
                qi, qj = a[f"Q{ci}"], a[f"Q{cj}"]
                return qi != qj and abs(qi - qj) != abs(ci - cj)
            csp.add_constraint([f"Q{i}", f"Q{j}"], check)
    
    return csp.solve()

# --- Tests ---

def test_simple_csp():
    csp = CSP()
    csp.add_variable("X", [1, 2, 3])
    csp.add_variable("Y", [1, 2, 3])
    csp.add_constraint(["X", "Y"], lambda a: a["X"] != a["Y"])
    csp.add_constraint(["X"], lambda a: a["X"] > 1)
    solution = csp.solve()
    assert solution is not None
    assert solution["X"] != solution["Y"]
    assert solution["X"] > 1

def test_ac3():
    csp = CSP()
    csp.add_variable("X", [1, 2, 3])
    csp.add_variable("Y", [1, 2, 3])
    csp.add_constraint(["X", "Y"], lambda a: a["X"] < a["Y"])
    assert csp.ac3()
    assert 3 not in csp.domains["X"]  # X can't be 3
    assert 1 not in csp.domains["Y"]  # Y can't be 1

def test_nqueens_4():
    sol = solve_nqueens(4)
    assert sol is not None
    cols = [sol[f"Q{i}"] for i in range(4)]
    assert len(set(cols)) == 4
    for i in range(4):
        for j in range(i+1, 4):
            assert abs(cols[i] - cols[j]) != abs(i - j)

def test_nqueens_8():
    sol = solve_nqueens(8)
    assert sol is not None

def test_sudoku():
    grid = [
        [5,3,0,0,7,0,0,0,0],
        [6,0,0,1,9,5,0,0,0],
        [0,9,8,0,0,0,0,6,0],
        [8,0,0,0,6,0,0,0,3],
        [4,0,0,8,0,3,0,0,1],
        [7,0,0,0,2,0,0,0,6],
        [0,6,0,0,0,0,2,8,0],
        [0,0,0,4,1,9,0,0,5],
        [0,0,0,0,8,0,0,7,9],
    ]
    result = solve_sudoku(grid)
    assert result is not None
    for r in range(9):
        assert sorted(result[r]) == list(range(1, 10))

def test_unsatisfiable():
    csp = CSP()
    csp.add_variable("X", [1])
    csp.add_variable("Y", [1])
    csp.add_constraint(["X", "Y"], lambda a: a["X"] != a["Y"])
    assert csp.solve() is None

if __name__ == "__main__":
    if "--test" in sys.argv or len(sys.argv) == 1:
        test_simple_csp()
        test_ac3()
        test_nqueens_4()
        test_nqueens_8()
        test_sudoku()
        test_unsatisfiable()
        print("All tests passed!")
