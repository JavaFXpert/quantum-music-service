import pyquil.quil as pq
from pyquil.parameters import Parameter, quil_sin, quil_cos
from pyquil.quilbase import DefGate
import pyquil.api as api
from pyquil.gates import *
from math import *
import numpy as np

def compute_circuit(angles_vector_in_degrees_str):
    rotation_deg_of_freedom = 28
    a = [0] * rotation_deg_of_freedom
    for i in range(rotation_deg_of_freedom):
        a[i] = radians(float(angles_vector_in_degrees_str[i]))


    theta = Parameter('theta')

    anot = np.array([[0, 1, 0, 0], [1, 0, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]])

    aary = np.array([[quil_cos(theta / 2), -1 * quil_sin(theta / 2), 0, 0, 0, 0, 0, 0],
                    [quil_sin(theta / 2), quil_cos(theta / 2), 0, 0, 0, 0, 0, 0],
                    [0, 0, 1, 0, 0, 0, 0, 0],
                    [0, 0, 0, 1, 0, 0, 0, 0],
                    [0, 0, 0, 0, 1, 0, 0, 0],
                    [0, 0, 0, 0, 0, 1, 0, 0],
                    [0, 0, 0, 0, 0, 0, 1, 0],
                    [0, 0, 0, 0, 0, 0, 0, 1]])

    ccry = np.array([[1, 0, 0, 0, 0, 0, 0, 0],
                    [0, 1, 0, 0, 0, 0, 0, 0],
                    [0, 0, 1, 0, 0, 0, 0, 0],
                    [0, 0, 0, 1, 0, 0, 0, 0],
                    [0, 0, 0, 0, 1, 0, 0, 0],
                    [0, 0, 0, 0, 0, 1, 0, 0],
                    [0, 0, 0, 0, 0, 0, quil_cos(theta / 2), -1 * quil_sin(theta / 2)],
                    [0, 0, 0, 0, 0, 0, quil_sin(theta / 2), quil_cos(theta / 2)]])

    #TODO: Ascertain what kind of gates this is?
    cary = np.array([[1, 0, 0, 0, 0, 0, 0, 0],
                    [0, 1, 0, 0, 0, 0, 0, 0],
                    [0, 0, 1, 0, 0, 0, 0, 0],
                    [0, 0, 0, quil_cos(theta / 2), -1 * quil_sin(theta / 2), 0, 0, 0],
                    [0, 0, 0, quil_sin(theta / 2), quil_cos(theta / 2), 0, 0, 0],
                    [0, 0, 0, 0, 0, 1, 0, 0],
                    [0, 0, 0, 0, 0, 0, 1, 0],
                    [0, 0, 0, 0, 0, 0, 0, 1]])

    dg_anot = DefGate('ANOT', anot)
    dg_aary = DefGate('AARY', aary, [theta])
    dg_ccry = DefGate('CCRY', ccry, [theta])
    dg_cary = DefGate('CARY', cary, [theta])

    ANOT = dg_anot.get_constructor()
    AARY = dg_aary.get_constructor()
    CCRY = dg_ccry.get_constructor()
    CARY = dg_cary.get_constructor()

    qvm = api.QVMConnection()
    p = pq.Program()

    p.inst(dg_anot)
    p.inst(dg_aary)
    p.inst(dg_ccry)
    p.inst(dg_cary)

    #p.inst(X(0))
    #p.inst(X(1))
    #p.inst(X(2))

    # CD rotation
    p.inst(AARY(a[0] * 2)(2, 1, 0))

    # CE rotation
    p.inst(AARY(a[1] * 2)(2, 0, 1))

    # CF rotation
    p.inst(CNOT(1, 0))
    p.inst(AARY(a[2] * 2)(0, 2, 1))
    p.inst(CNOT(1, 0))

    # CG rotation
    p.inst(AARY(a[3] * 2)(0, 1, 2))

    # CA rotation
    p.inst(CNOT(2, 0))
    p.inst(AARY(a[4] * 2)(0, 1, 2))
    p.inst(CNOT(2, 0))

    # CB rotation
    p.inst(CNOT(2, 1))
    p.inst(AARY(a[5] * 2)(0, 1, 2))
    p.inst(CNOT(2, 1))

    # CC' rotation
    p.inst(CNOT(1, 0))
    p.inst(CNOT(1, 2))
    p.inst(AARY(a[6] * 2)(0, 2, 1))
    p.inst(CNOT(1, 2))
    p.inst(CNOT(1, 0))

    # DE rotation
    p.inst(ANOT(1, 0))
    p.inst(AARY(a[7] * 2)(0, 2, 1))
    p.inst(ANOT(1, 0))

    # DF rotation
    p.inst(X(2))
    p.inst(CCRY(a[8] * 2)(0, 2, 1))
    p.inst(X(2))

    # DG rotation
    p.inst(ANOT(2, 0))
    p.inst(AARY(a[9] * 2)(0, 1, 2))
    p.inst(ANOT(2, 0))

    # DA rotation
    p.inst(X(1))
    p.inst(CCRY(a[10] * 2)(0, 1, 2))
    p.inst(X(1))

    # DB rotation
    p.inst(CNOT(1, 0))
    p.inst(ANOT(1, 2))
    p.inst(CCRY(a[11] * 2)(0, 2, 1))
    p.inst(ANOT(1, 2))
    p.inst(CNOT(1, 0))

    # DC' rotation
    p.inst(ANOT(1, 2))
    p.inst(CCRY(a[12] * 2)(0, 2, 1))
    p.inst(ANOT(1, 2))

    # EF rotation
    p.inst(X(2))
    p.inst(CCRY(a[13] * 2)(1, 2, 0))
    p.inst(X(2))

    # EG rotation
    p.inst(ANOT(2, 1))
    p.inst(AARY(a[14] * 2)(0, 1, 2))
    p.inst(ANOT(2, 1))

    # EA rotation
    p.inst(CNOT(0, 1))
    p.inst(ANOT(0, 2))
    p.inst(CCRY(a[15] * 2)(1, 2, 0))
    p.inst(ANOT(0, 2))
    p.inst(CNOT(0, 1))

    # EB rotation
    p.inst(X(0))
    p.inst(CCRY(a[16] * 2)(0, 1, 2))
    p.inst(X(0))

    # EC' rotation
    p.inst(ANOT(0, 2))
    p.inst(CCRY(a[17] * 2)(1, 2, 0))
    p.inst(ANOT(0, 2))

    # FG rotation
    p.inst(CARY(a[18] * 2)(2, 1, 0))

    # FA rotation
    p.inst(CNOT(2, 1))
    p.inst(CCRY(a[19] * 2)(0, 1, 2))
    p.inst(CNOT(2, 1))

    # FB rotation
    p.inst(CNOT(2, 0))
    p.inst(CCRY(a[20] * 2)(0, 1, 2))
    p.inst(CNOT(2, 0))

    # FC' rotation
    p.inst(CCRY(a[21] * 2)(0, 1, 2))

    # GA rotation
    p.inst(X(1))
    p.inst(CCRY(a[22] * 2)(1, 2, 0))
    p.inst(X(1))

    # GB rotation
    p.inst(X(0))
    p.inst(CCRY(a[23] * 2)(0, 2, 1))
    p.inst(X(0))

    # GC' rotation
    p.inst(ANOT(1, 0))
    p.inst(CCRY(a[24] * 2)(0, 2, 1))
    p.inst(ANOT(1, 0))

    # AB rotation
    p.inst(CNOT(1, 0))
    p.inst(CCRY(a[25] * 2)(0, 2, 1))
    p.inst(CNOT(1, 0))

    # AC' rotation
    p.inst(CCRY(a[26] * 2)(0, 2, 1))

    # BC' rotation
    p.inst(CCRY(a[27] * 2)(1, 2, 0))

    wavefunction = qvm.wavefunction(p)
    print(wavefunction)

    return p

