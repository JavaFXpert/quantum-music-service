from flask import Flask, jsonify, request
from pyquil.quil import Program
import pyquil.api as api
from pyquil.gates import *
#import numpy as np
from math import *
from gatedefs import *

app = Flask(__name__)

DEGREES_OF_FREEDOM = 28
NUM_PITCHES = 8
NUM_CIRCUIT_WIRES = 3

"""
Produces a given number of accompanying pitches for a given pitch and rotations degrees. This
function doesn't distinguish between harmonic and melodic accompaniment, as the list of degrees
supplied to this function should be conducive to producing the desired type of accompaniment.
    Parameters:
        pitch_index Index (0 - 7) of the pitch for which accompaniment is desired
        degrees Comma-delimited string containing 28 degrees that represents the rotations
        
    Returns JSON string containing:
        pitch_probabilities Array of eight probabilities, each corresponding to one of the 
                            pitch indices
        measured_pitch Pitch index (0 - 1) resulting from measurement 
            
"""
@app.route('/accompany')
def accompany():
    pitch_index = int(request.args['pitch_index'])
    print("pitch_index: ", pitch_index)

    rotation_degrees = request.args['degrees'].split(",")
    print("rotation_degrees: ", rotation_degrees)

    if (len(rotation_degrees) == DEGREES_OF_FREEDOM and
            0 <= pitch_index < NUM_PITCHES):

        gate_matrix = compute_matrix(rotation_degrees)
        pitch_probabilities_matrix = np.square(gate_matrix)[pitch_index]

        qvm = api.QVMConnection()
        prog = Program().defgate("ACCOMPANIMENT_GATE", gate_matrix)

        # Convert the pitch index to a binary string, and use it to create
        # the initial gates on the three wires of the quantum circuit,
        # least significant qubit on the lowest number wire
        qubit_string = format(pitch_index, '03b')
        for idx, qubit_char in enumerate(qubit_string):
            if (qubit_char == '0'):
                prog.inst(I(NUM_CIRCUIT_WIRES - 1 - idx))
            else:
                prog.inst(X(NUM_CIRCUIT_WIRES - 1 - idx))

        prog.inst(("ACCOMPANIMENT_GATE", 2, 1, 0))\
            .measure(0, 0).measure(1, 1)\
            .measure(2, 2)
        print(prog)

        num_runs = 1
        result = qvm.run(prog, [2, 1, 0], num_runs)
        bits = result[0]
        measured_pitch = bits[2] * 4 + bits[1] * 2 + bits[0]

        print("result: ",  result)

        pitch_probabilities = pitch_probabilities_matrix.tolist()
        rounded_pitch_probabilities = [0] * NUM_PITCHES
        for idx, pitch_prob in enumerate(pitch_probabilities[0]):
            rounded_pitch_probabilities[idx] = round(pitch_prob, 4)


        ret_dict = {"pitch_probabilities":rounded_pitch_probabilities,
                    "measured_pitch": measured_pitch}

    return jsonify(ret_dict)









if __name__ == '__main__':
    app.run()
