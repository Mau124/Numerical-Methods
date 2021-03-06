""" Module for Linear programming

    This file contains algorithms for linear programming. It has a basic set of 
    algorithms that are taught in a linear programming basic course. 

    The code is a mess and the next update is to merge code with linalg, so it is
    not so messy. 
"""
import copy
import re
from itertools import chain
import numpy as np
import pandas as pd

INF = 1000


def gauss_jordan_LP(A, maximize):
    #If A is a numpy array change it to a pandas data frame
    if type(A) == np.ndarray:
        row, col = A.shape
        A = pd.DataFrame(A, 
                         index=["Z"]+[f"I{i+1}" for i in range(row-1)], 
                         columns=["Z"]+[f"V{i+1}" for i in range(col-2)]+["Sol"])
    
    """ Gauss jordan with LP """
    M = copy.deepcopy(A) 
    aux_array = np.zeros(len(M.iloc[0])-2)

    print("--------- Matrix original ----------")
    print(M)

    # Eliminar M's que estan en variables artificiales
    indexes_M = abs(M.iloc[0, :-1]) == INF

    print("--------- Eliminar M's -------------")
    print()
    it = 0
    for i in range(len(indexes_M)):
        if indexes_M[i] == True:
            # Search for a value to be a pivot
            pivot = 1
            while M.iloc[pivot][i] == 0:
                pivot += 1

            print(f"Eliminar {it} M")
            tmp = M.iloc[0][i]/M.iloc[pivot][i]

            for col in range(M.shape[1]):
                M.iloc[0][col] = M.iloc[0][col] - tmp*M.iloc[pivot][col]

            print(M)
            it += 1
                   
    print("--------- Resolver -------------")
    print()
    it = 0

    if maximize:
        is_not_optimal = np.any(M.iloc[0, 1:-1] < aux_array)
    else:
        is_not_optimal = np.any(M.iloc[0, 1:-1] > aux_array)

    while is_not_optimal: 
        # Gauss jordan algo

        # Get most negative in first row to obtain the col
        if maximize:
            pivot_col = np.argmin(M.iloc[0, :-1])
        else:
            pivot_col = np.argmax(M.iloc[0,:-1])

        ratio = 10000
        pivot_row = -1

        for i in range(1, M.shape[0]):
            if M.iloc[i, pivot_col] != 0:
                tmp = M.iloc[i,-1]/M.iloc[i,pivot_col]
                if tmp >= 0 and tmp < ratio:
                    ratio = tmp
                    pivot_row = i

        # Make M.iloc[pivot_row][pivot_col] = 1
        print("Iteracion: ", it)

        tmp = M.iloc[pivot_row][pivot_col]
        if tmp != 0:
            M.iloc[pivot_row] = M.iloc[pivot_row]/tmp
            M = M.rename(index={M.index[pivot_row]:M.columns[pivot_col]}) #Change Row Name
            # DO gauss jordan with those iterators
            for row in range(M.shape[0]):
                if row != pivot_row:
                    if M.iloc[pivot_row][pivot_col] != 0:
                        tmp = M.iloc[row][pivot_col]/M.iloc[pivot_row][pivot_col]
                        for col in range(M.shape[1]):
                            M.iloc[row][col] = M.iloc[row][col] - tmp*M.iloc[pivot_row][col]

                        print(f"Row {row} = row {row} - {tmp:.2f} * row {pivot_row}")

        print(M)                     

        if maximize:
            is_not_optimal = np.any(M.iloc[0, 1:-1] < aux_array)
        else:
            is_not_optimal = np.any(M.iloc[0, 1:-1] > aux_array)

        it += 1

    return M


# ----------------------------------
#   Matrix construction functions
# ----------------------------------
pattern = "[*/+-][0-9.]*[xsa][0-9]*"


def separate(expression, index=1, pat=pattern):
    """
    Splits a string containing a polynomial into monomials, if the expression is
    a constraint, it will return the monomials and the constraint separately.
    Constraints must be added in canonical or standard form.
    Args:
        expression (String): Expression to be turn into monomials. 
        pat (String, optional): Pattern used to get the monomials splitted. 
                                Defaults to pattern.

    Returns:
        List: List of Strings that represent the monomials in the expression, if 
              expression is a constraint it will return a tuple instead. 
    """
    if not expression[0] in "+-":  # Implicit sum check
        expression = "+" + expression

    if "=" in expression:  # Is the expression a constraint?
        standard = "A" in expression.upper() or "S" in expression.upper()
        expression = re.split("([=<>])", expression, maxsplit=1)
        monomials = re.findall(pat, expression[0], re.IGNORECASE)
        if expression[1] == "=" and not standard:
            monomials.append(f"+1A{index}")
        elif expression[1] == ">":  # Is it a >= constraint?
            expression[2] = expression[2][1:]
            monomials.append(f"-1S{index}")
            monomials.append(f"+1A{index}")
        else:  # Is a <= constraint
            expression[2] = expression[2][1:]
            monomials.append(f"+1S{index}")
        constraint = expression[2]
        return(monomials, constraint)
    # Positive coeficients to negative and vice versa
    expression = expression.translate({43: 45, 45: 43})
    return re.findall(pat, expression, re.IGNORECASE)


def buildMatrix(Z, Constraints, maximize=True, nn=True):
    """
    Creates a simplex matrix based on the expressions provided.
    Constraints must be written in canonical or standard form.
    
    Args:
        Z (string): Objetive function.
        Constraints (list): List of strings that express a constraint in canonical or standard form.
    
    Returns:
        matrix (pandas.DataFrame): Simplex matrix.
    """
    # -- Variable detection --
    eVars = []  # Variables in each expression
    bVars = ["Z"]  # Base variables
    nVars = [[], []]  # Negativity allowed, Case 1
    for i in range(len(Constraints)):
        eVars.append([])
        Constraints[i] = list(separate(Constraints[i], i+1))
        eVars[i] = re.findall(
            "[xsa][0-9]*", "".join(Constraints[i][0]), re.IGNORECASE)
        bVars.append(
            f"A{i+1}" if "A" in "".join(eVars[i]).upper() else f"S{i+1}")
        if not nn:
            coef = "".join(eVars[i]).upper()
            if coef.count("X") == 1 and "A" in coef and "S" in coef:
                nVars[0].append(eVars[i][0])
                nVars[1].append(i)
    # Sorted unique variables
    uVars = list(sorted(set(chain(*eVars)),
                 key=lambda x: (x[0], -int(x[1:])), reverse=True))

    # -- Change of variable for negative allowed cases --
    if not nn:
        i = 0
        while "X" in uVars[i].upper():
            if uVars[i] in nVars[0]:  # Case 1
                # Case 1 Li
                temp = float(
                    Constraints[nVars[1][nVars[0].index(uVars[i])]][1])
                for j in range(len(Constraints)):
                    if uVars[i] in "".join(Constraints[j][0]): # Does the constraint has xi'
                        coef = eVars[j].index(uVars[i])
                        # Implicit coeficient detection
                        if not Constraints[j][0][coef][1] in "1234567890":
                            # Add 1 coeficient
                            Constraints[j][0][coef] = Constraints[j][0][coef][0]+"1"+uVars[i]
                        Constraints[j][1] = float(Constraints[j][1]) - float(
                            Constraints[j][0][coef][:-len(uVars[i])])*temp  # Modify solution value
                #Popping constraint
                temp = nVars[1][nVars[0].index(uVars[i])]  # Constraint Index
                Constraints.pop(temp)
                bVars.pop(temp+1)
                for j in range(len(eVars[temp])-1):
                    uVars.pop(uVars.index(eVars[temp][j+1]))
                eVars.pop(nVars[1][nVars[0].index(uVars[i])])
            else:  # Case 2
                uVars.insert(i+1, "x0"+uVars[i][1:])
                for con in range(len(Constraints)):
                    temp = 0  # Adjustment
                    for ele in range(len(Constraints[con][0])):
                        if uVars[i] in Constraints[con][0][ele+temp]:
                            # Coeficient of negative variable
                            coef = Constraints[con][0][ele+temp][:-
                                                                 len(uVars[i])].translate({43: 45, 45: 43})
                            Constraints[con][0].insert(
                                ele+temp+1, coef+"x0"+uVars[i][1:])  # Add negative variables
                            # Add variable to expression variable list.
                            eVars[con].insert(eVars[con].index(
                                uVars[i])+1, "x0"+uVars[i][1:])
                            temp += 1
                i += 1
            i += 1

    # -- Empty simplex matrix construction --
    # Creates an empty simplex matrix
    matrix = np.zeros((len(Constraints)+1, len(uVars)+2))
    # Assigns the columns and rows names
    matrix = pd.DataFrame(matrix, columns=["Z"] + uVars + ["Sol"], index=bVars)

    # -- Filling constraint rows --
    for row in range(len(Constraints)):
        # Fills the solution column
        matrix["Sol"][row+1] = float(Constraints[row][1])
        for col in range(len(Constraints[row][0])):
            # Is the coeficient implicit?
            if not Constraints[row][0][col][1] in "1234567890":
                Constraints[row][0][col] = Constraints[row][0][col][0] + \
                    "1"+Constraints[row][0][col][1:]  # Add 1 coeficient
            # Adds the coeficient to the matrix without de sufix
            matrix[eVars[row][col]][row +
                                    1] = float(Constraints[row][0][col][:-len(eVars[row][col])])

    # -- Filling objetive function row --
    Z = separate(Z)
    for i in range(len(uVars)):
        if uVars[i][0].upper() == "A":
            Z.append("M"+uVars[i])
    eVars = re.findall("[xsa][0-9]*", "".join(Z), re.IGNORECASE)
    matrix["Z"][0] = 1
    #Negativity allowed
    if not nn:
        temp = 0  # Adjustment
        for ele in range(len(eVars)):
            if eVars[ele+temp] not in nVars[0]:
                eVars.insert(ele+temp+1, "x0"+eVars[ele+temp][1:])
                coef = Z[ele+temp][:-len(eVars[ele+temp])
                                   ].translate({43: 45, 45: 43})
                Z.insert(ele+temp+1, coef+"x0"+eVars[ele+temp][1:])
                temp += 1
    for col in range(len(Z)):
        if Z[col][:-len(eVars[col])] == "M":
            coef = INF if maximize else -INF
        else:
            coef = Z[col][:-len(eVars[col])]
            if len(coef) == 1:
                coef += "1"
        matrix[eVars[col]][0] = float(coef)
    return(matrix)
