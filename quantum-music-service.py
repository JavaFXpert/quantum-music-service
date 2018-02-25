from flask import Flask, jsonify, request
from pyquil.quil import Program
from pyquil.quilbase import RawInstr
import pyquil.api as api
from pyquil.gates import *
from math import *
from gatedefs import *

app = Flask(__name__)

DEGREES_OF_FREEDOM = 28
NUM_PITCHES = 8
NUM_CIRCUIT_WIRES = 3
NUM_MELODY_NOTES_TO_COMPUTE = 6
TOTAL_MELODY_NOTES = 7
HARMONY_NOTES_FACTOR = 2 # Number of harmony notes for each melody note
NUM_COMPOSITION_BITS = 63


###
# Produces a musical (specifically second-species counterpoint) composition for
# a given initial pitch, and melodic/harmonic rotations degrees. This operates in a degraded mode,
# in that a call to the quantum computer or simulator is made for each note in the resulting
# composition.
#    Parameters:
#        pitch_index Index (0 - 7) of the initial pitch for which a composition is desired
#        melodic_degrees Comma-delimited string containing 28 rotations in degrees for melody matrix
#        harmonic_degrees Comma-delimited string containing 28 rotations in degrees for harmony matrix
#
#    Returns JSON string containing:
#        melody_part
#            pitch_index
#            start_beat
#            pitch_probs
#        harmony_part
#            pitch_index
#            start_beat
#            pitch_probs
#
#        pitch_index is an integer from (0 - 7) resulting from measurement
#        start_beat is the beat in the entire piece for which the note was produced
#        pitch_probs is an array of eight probabilities from which the pitch_index resulted
###

@app.route('/counterpoint_degraded')
def counterpoint_degraded():
    pitch_index = int(request.args['pitch_index'])
    print("pitch_index: ", pitch_index)

    melodic_degrees = request.args['melodic_degrees'].split(",")
    print("melodic_degrees: ", melodic_degrees)

    harmonic_degrees = request.args['harmonic_degrees'].split(",")
    print("harmonic_degrees: ", harmonic_degrees)

    if (len(melodic_degrees) == DEGREES_OF_FREEDOM and
            len(harmonic_degrees) == DEGREES_OF_FREEDOM and
            0 <= pitch_index < NUM_PITCHES):

        melodic_gate_matrix = compute_matrix(melodic_degrees)
        harmonic_gate_matrix = compute_matrix(harmonic_degrees)

        qvm = api.QVMConnection()

        #p.defgate("MELODIC_GATE", melodic_gate_matrix)
        #p.defgate("HARMONIC_GATE", harmonic_gate_matrix)

        composition_bits = [0] * NUM_COMPOSITION_BITS

        # Convert the pitch index to a binary string, and place into the
        # composition_bits array, most significant bits in lowest elements of array
        qubit_string = format(pitch_index, '03b')
        for idx, qubit_char in enumerate(qubit_string):
            if qubit_char == '0':
                composition_bits[NUM_CIRCUIT_WIRES - 1 - idx] = 0
                #p.inst(I(NUM_CIRCUIT_WIRES - 1 - idx))
                #p.inst(FALSE(idx))
            else:
                composition_bits[NUM_CIRCUIT_WIRES - 1 - idx] = 1
                #p.inst(X(NUM_CIRCUIT_WIRES - 1 - idx))
                #p.inst(TRUE(idx))

        #print(p)
        num_runs = 1

        for melody_note_idx in range(0, NUM_MELODY_NOTES_TO_COMPUTE):
            p = Program()
            p.defgate("MELODIC_GATE", melodic_gate_matrix)
            for bit_idx in range(0, NUM_CIRCUIT_WIRES):
                if (composition_bits[melody_note_idx * NUM_CIRCUIT_WIRES + bit_idx] == 0):
                    p.inst(I(NUM_CIRCUIT_WIRES - 1 - bit_idx))
                    #p.inst(FALSE(bit_idx))
                else:
                    p.inst(X(NUM_CIRCUIT_WIRES - 1 - bit_idx))
                    #p.inst(TRUE(bit_idx))

            p.inst(("MELODIC_GATE", 2, 1, 0)) \
                .measure(0, 0).measure(1, 1) \
                .measure(2, 2)
            print(p)

            result = qvm.run(p, [2, 1, 0], num_runs)
            bits = result[0]
            for bit_idx in range(0, NUM_CIRCUIT_WIRES):
                composition_bits[(melody_note_idx + 1) * NUM_CIRCUIT_WIRES + bit_idx] = bits[bit_idx]

            print(composition_bits)

            measured_pitch = bits[0] * 4 + bits[1] * 2 + bits[2]
            print("melody melody_note_idx measured_pitch")
            print(melody_note_idx)
            print(measured_pitch)

            # Now compute a harmony note for the melody note
            p = Program()
            p.defgate("HARMONIC_GATE", harmonic_gate_matrix)
            for bit_idx in range(0, NUM_CIRCUIT_WIRES):
                if (composition_bits[melody_note_idx * NUM_CIRCUIT_WIRES + bit_idx] == 0):
                    p.inst(I(NUM_CIRCUIT_WIRES - 1 - bit_idx))
                    #p.inst(FALSE(bit_idx))
                else:
                    p.inst(X(NUM_CIRCUIT_WIRES - 1 - bit_idx))
                    #p.inst(TRUE(bit_idx))

            p.inst(("HARMONIC_GATE", 2, 1, 0)) \
                .measure(0, 0).measure(1, 1) \
                .measure(2, 2)
            print(p)

            result = qvm.run(p, [2, 1, 0], num_runs)
            bits = result[0]
            for bit_idx in range(0, NUM_CIRCUIT_WIRES):
                composition_bits[(melody_note_idx * NUM_CIRCUIT_WIRES) +
                                 (TOTAL_MELODY_NOTES * NUM_CIRCUIT_WIRES) + bit_idx] = bits[bit_idx]

            print(composition_bits)

            measured_pitch = bits[0] * 4 + bits[1] * 2 + bits[2]
            print("harmony melody_note_idx measured_pitch")
            print(melody_note_idx)
            print(measured_pitch)




        #res = qvm.run(p, [
        #    2, 1, 0, 5, 4, 3, 8, 7, 6, 11, 10, 9, 14, 13, 12, 17, 16, 15, 20, 19, 18,
        #    23, 22, 21, 44, 43, 42, 26, 25, 24, 47, 46, 45, 29, 28, 27, 50, 49, 48, 32, 31, 30,
        #    53, 52, 51, 35, 34, 33, 56, 55, 54, 38, 37, 36, 59, 58, 57, 41, 40, 39, 62, 61, 60
        #    ], num_runs)
        #print(res)

        all_note_nums = create_note_nums_array(composition_bits)
        melody_note_nums = all_note_nums[0:7]
        harmony_note_nums = all_note_nums[7:21]

    ret_dict = {"melody": melody_note_nums,
                "harmony": harmony_note_nums,
                "lilypond": create_lilypond(melody_note_nums, harmony_note_nums),
                "toy_piano" : create_toy_piano(melody_note_nums, harmony_note_nums)}

    return jsonify(ret_dict)

""""
DEFCIRCUIT ACTIVE-RESET q scratch_bit:
    MEASURE q scratch_bit
    JUMP-UNLESS @END-ACTIVE-SET scratch_bit
    X q
    LABEL @END-ACTIVE-SET

DEFCIRCUIT ACTIVE-SET q scratch_bit:
    MEASURE q scratch_bit
    JUMP-WHEN @END-ACTIVE-RESET scratch_bit
    X q
    LABEL @END-ACTIVE-RESET

# == Produce melody ==
# ---- Produce pitch for Lead Note #2 and replicate measurement results into qubits ----
MELODIC_GATE 2 1 0

MEASURE 2 [5]
MEASURE 1 [4]
MEASURE 0 [3]

JUMP-UNLESS @RESET-Q5 [5]
ACTIVE-SET 2 [63]
JUMP @END-Q5
LABEL @RESET-Q5
ACTIVE-RESET 5 [63]
LABEL @END-Q5 

JUMP-UNLESS @RESET-Q4 [4]
ACTIVE-SET 1 [63]
JUMP @END-Q4
LABEL @RESET-Q4
ACTIVE-RESET 4 [63]
LABEL @END-Q4 

JUMP-UNLESS @RESET-Q3 [3]
ACTIVE-SET 0 [63]
JUMP @END-Q3
LABEL @RESET-Q3
ACTIVE-RESET 3 [63]
LABEL @END-Q3 

# ---- Produce pitch for Lead Note #3 and replicate measurement results into qubits ----
MELODIC_GATE 2 1 0

MEASURE 2 [8]
MEASURE 1 [7]
MEASURE 0 [6]

JUMP-UNLESS @RESET-Q8 [8]
ACTIVE-SET 2 [63]
JUMP @END-Q8
LABEL @RESET-Q8
ACTIVE-RESET 2 [63]
LABEL @END-Q8 

JUMP-UNLESS @RESET-Q7 [7]
ACTIVE-SET 1 [63]
JUMP @END-Q7
LABEL @RESET-Q7
ACTIVE-RESET 1 [63]
LABEL @END-Q7 

JUMP-UNLESS @RESET-Q6 [6]
ACTIVE-SET 0 [63]
JUMP @END-Q6
LABEL @RESET-Q6
ACTIVE-RESET 0 [63]
LABEL @END-Q6 

# ---- Produce pitch for Lead Note #4 and replicate measurement results into qubits ----
MELODIC_GATE 2 1 0

MEASURE 2 [11]
MEASURE 1 [10]
MEASURE 0 [9]

JUMP-UNLESS @RESET-Q11 [11]
ACTIVE-SET 2 [63]
JUMP @END-Q11
LABEL @RESET-Q11
ACTIVE-RESET 2 [63]
LABEL @END-Q11 

JUMP-UNLESS @RESET-Q10 [10]
ACTIVE-SET 1 [63]
JUMP @END-Q10
LABEL @RESET-Q10
ACTIVE-RESET 1 [63]
LABEL @END-Q10 

JUMP-UNLESS @RESET-Q9 [9]
ACTIVE-SET 0 [63]
JUMP @END-Q9
LABEL @RESET-Q9
ACTIVE-RESET 0 [63]
LABEL @END-Q9 

# ---- Produce pitch for Lead Note #5 and replicate measurement results into qubits ----
MELODIC_GATE 2 1 0

MEASURE 2 [14]
MEASURE 1 [13]
MEASURE 0 [12]

JUMP-UNLESS @RESET-Q14 [14]
ACTIVE-SET 2 [63]
JUMP @END-Q14
LABEL @RESET-Q14
ACTIVE-RESET 2 [63]
LABEL @END-Q14 

JUMP-UNLESS @RESET-Q13 [13]
ACTIVE-SET 1 [63]
JUMP @END-Q13
LABEL @RESET-Q13
ACTIVE-RESET 1 [63]
LABEL @END-Q13 

JUMP-UNLESS @RESET-Q12 [12]
ACTIVE-SET 0 [63]
JUMP @END-Q12
LABEL @RESET-Q12
ACTIVE-RESET 0 [63]
LABEL @END-Q12 

# ---- Produce pitch for Lead Note #6 and replicate measurement results into qubits ----
MELODIC_GATE 2 1 0

MEASURE 2 [17]
MEASURE 1 [16]
MEASURE 0 [15]

JUMP-UNLESS @RESET-Q17 [17]
ACTIVE-SET 2 [63]
JUMP @END-Q17
LABEL @RESET-Q17
ACTIVE-RESET 2 [63]
LABEL @END-Q17 

JUMP-UNLESS @RESET-Q16 [16]
ACTIVE-SET 1 [63]
JUMP @END-Q16
LABEL @RESET-Q16
ACTIVE-RESET 1 [63]
LABEL @END-Q16 

JUMP-UNLESS @RESET-Q15 [15]
ACTIVE-SET 0 [63]
JUMP @END-Q15
LABEL @RESET-Q15
ACTIVE-RESET 0 [63]
LABEL @END-Q15 

# ---- Produce pitch for Lead Note #7 and replicate measurement results into qubits ----
MELODIC_GATE 2 1 0

MEASURE 2 [20]
MEASURE 1 [19]
MEASURE 0 [18]

# == Produce harmony ==
# ---- Retrieve pitch for Lead Note #1, replicate it into qubits, and produce pitch for Harmony Note #1a ----
JUMP-UNLESS @RESET-Q2a [2]
ACTIVE-SET 2 [63]
JUMP @END-Q2a
LABEL @RESET-Q2a
ACTIVE-RESET 2 [63]
LABEL @END-Q2a 

JUMP-UNLESS @RESET-Q1a [1]
ACTIVE-SET 1 [63]
JUMP @END-Q1a
LABEL @RESET-Q1a
ACTIVE-RESET 1 [63]
LABEL @END-Q1a 

JUMP-UNLESS @RESET-Q0a [0]
ACTIVE-SET 0 [63]
JUMP @END-Q0a
LABEL @RESET-Q0a
ACTIVE-RESET 0 [63]
LABEL @END-Q0a 

HARMONIC_GATE 2 1 0

MEASURE 2 [23]
MEASURE 1 [22]
MEASURE 0 [21]

# ---- Replicate Harmony Note #1a into qubits, and produce pitch for Harmony Note #1b ----
JUMP-UNLESS @RESET-Q23 [23]
ACTIVE-SET 2 [63]
JUMP @END-Q23
LABEL @RESET-Q23
ACTIVE-RESET 2 [63]
LABEL @END-Q23 

JUMP-UNLESS @RESET-Q22 [22]
ACTIVE-SET 1 [63]
JUMP @END-Q22
LABEL @RESET-Q22
ACTIVE-RESET 1 [63]
LABEL @END-Q22 

JUMP-UNLESS @RESET-Q21 [21]
ACTIVE-SET 0 [63]
JUMP @END-Q21
LABEL @RESET-Q21
ACTIVE-RESET 0 [63]
LABEL @END-Q21 

MELODIC_GATE 2 1 0

MEASURE 2 [44]
MEASURE 1 [43]
MEASURE 0 [42]

# ---- Retrieve pitch for Lead Note #2, replicate it into qubits, and produce pitch for Harmony Note #2a ----
JUMP-UNLESS @RESET-Q5a [5]
ACTIVE-SET 2 [63]
JUMP @END-Q5a
LABEL @RESET-Q5a
ACTIVE-RESET 2 [63]
LABEL @END-Q5a 

JUMP-UNLESS @RESET-Q4a [4]
ACTIVE-SET 1 [63]
JUMP @END-Q4a
LABEL @RESET-Q4a
ACTIVE-RESET 1 [63]
LABEL @END-Q4a 

JUMP-UNLESS @RESET-Q3a [3]
ACTIVE-SET 0 [63]
JUMP @END-Q3a
LABEL @RESET-Q3a
ACTIVE-RESET 0 [63]
LABEL @END-Q3a 

HARMONIC_GATE 2 1 0

MEASURE 2 [26]
MEASURE 1 [25]
MEASURE 0 [24]

# ---- Replicate Harmony Note #2a into qubits, and produce pitch for Harmony Note #2b ----
JUMP-UNLESS @RESET-Q26 [26]
ACTIVE-SET 2 [63]
JUMP @END-Q26
LABEL @RESET-Q26
ACTIVE-RESET 2 [63]
LABEL @END-Q26 

JUMP-UNLESS @RESET-Q25 [25]
ACTIVE-SET 1 [63]
JUMP @END-Q25
LABEL @RESET-Q25
ACTIVE-RESET 1 [63]
LABEL @END-Q25 

JUMP-UNLESS @RESET-Q24 [24]
ACTIVE-SET 0 [63]
JUMP @END-Q24
LABEL @RESET-Q24
ACTIVE-RESET 0 [63]
LABEL @END-Q24 

MELODIC_GATE 2 1 0

MEASURE 2 [47]
MEASURE 1 [46]
MEASURE 0 [45]

# ---- Retrieve pitch for Lead Note #3, replicate it into qubits, and produce pitch for Harmony Note #3a ----
JUMP-UNLESS @RESET-Q8a [8]
ACTIVE-SET 2 [63]
JUMP @END-Q8a
LABEL @RESET-Q8a
ACTIVE-RESET 2 [63]
LABEL @END-Q8a 

JUMP-UNLESS @RESET-Q7a [7]
ACTIVE-SET 1 [63]
JUMP @END-Q7a
LABEL @RESET-Q7a
ACTIVE-RESET 1 [63]
LABEL @END-Q7a 

JUMP-UNLESS @RESET-Q6a [6]
ACTIVE-SET 0 [63]
JUMP @END-Q6a
LABEL @RESET-Q6a
ACTIVE-RESET 0 [63]
LABEL @END-Q6a 

HARMONIC_GATE 2 1 0

MEASURE 2 [29]
MEASURE 1 [28]
MEASURE 0 [27]

# ---- Replicate Harmony Note #3a into qubits, and produce pitch for Harmony Note #3b ----
JUMP-UNLESS @RESET-Q29 [29]
ACTIVE-SET 2 [63]
JUMP @END-Q29
LABEL @RESET-Q29
ACTIVE-RESET 2 [63]
LABEL @END-Q29 

JUMP-UNLESS @RESET-Q28 [28]
ACTIVE-SET 1 [63]
JUMP @END-Q28
LABEL @RESET-Q28
ACTIVE-RESET 1 [63]
LABEL @END-Q28 

JUMP-UNLESS @RESET-Q27 [27]
ACTIVE-SET 0 [63]
JUMP @END-Q27
LABEL @RESET-Q27
ACTIVE-RESET 0 [63]
LABEL @END-Q27 

MELODIC_GATE 2 1 0

MEASURE 2 [50]
MEASURE 1 [49]
MEASURE 0 [48]

# ---- Retrieve pitch for Lead Note #4, replicate it into qubits, and produce pitch for Harmony Note #4a ----
JUMP-UNLESS @RESET-Q11a [11]
ACTIVE-SET 2 [63]
JUMP @END-Q11a
LABEL @RESET-Q11a
ACTIVE-RESET 2 [63]
LABEL @END-Q11a 

JUMP-UNLESS @RESET-Q10a [10]
ACTIVE-SET 1 [63]
JUMP @END-Q10a
LABEL @RESET-Q10a
ACTIVE-RESET 1 [63]
LABEL @END-Q10a 

JUMP-UNLESS @RESET-Q9a [9]
ACTIVE-SET 0 [63]
JUMP @END-Q9a
LABEL @RESET-Q9a
ACTIVE-RESET 0 [63]
LABEL @END-Q9a 

HARMONIC_GATE 2 1 0

MEASURE 2 [32]
MEASURE 1 [31]
MEASURE 0 [30]

# ---- Replicate Harmony Note #4a into qubits, and produce pitch for Harmony Note #4b ----
JUMP-UNLESS @RESET-Q32 [32]
ACTIVE-SET 2 [63]
JUMP @END-Q32
LABEL @RESET-Q32
ACTIVE-RESET 2 [63]
LABEL @END-Q32 

JUMP-UNLESS @RESET-Q31 [31]
ACTIVE-SET 1 [63]
JUMP @END-Q31
LABEL @RESET-Q31
ACTIVE-RESET 1 [63]
LABEL @END-Q31 

JUMP-UNLESS @RESET-Q30 [30]
ACTIVE-SET 0 [63]
JUMP @END-Q30
LABEL @RESET-Q30
ACTIVE-RESET 0 [63]
LABEL @END-Q30 

MELODIC_GATE 2 1 0

MEASURE 2 [53]
MEASURE 1 [52]
MEASURE 0 [51]

# ---- Retrieve pitch for Lead Note #5, replicate it into qubits, and produce pitch for Harmony Note #5a ----
JUMP-UNLESS @RESET-Q14a [14]
ACTIVE-SET 2 [63]
JUMP @END-Q14a
LABEL @RESET-Q14a
ACTIVE-RESET 2 [63]
LABEL @END-Q14a 

JUMP-UNLESS @RESET-Q13a [13]
ACTIVE-SET 1 [63]
JUMP @END-Q13a
LABEL @RESET-Q13a
ACTIVE-RESET 1 [63]
LABEL @END-Q13a 

JUMP-UNLESS @RESET-Q12a [12]
ACTIVE-SET 0 [63]
JUMP @END-Q12a
LABEL @RESET-Q12a
ACTIVE-RESET 0 [63]
LABEL @END-Q12a 

HARMONIC_GATE 2 1 0

MEASURE 2 [35]
MEASURE 1 [34]
MEASURE 0 [33]

# ---- Replicate Harmony Note #5a into qubits, and produce pitch for Harmony Note #5b ----
JUMP-UNLESS @RESET-Q35 [35]
ACTIVE-SET 2 [63]
JUMP @END-Q35
LABEL @RESET-Q35
ACTIVE-RESET 2 [63]
LABEL @END-Q35 

JUMP-UNLESS @RESET-Q34 [34]
ACTIVE-SET 1 [63]
JUMP @END-Q34
LABEL @RESET-Q34
ACTIVE-RESET 1 [63]
LABEL @END-Q34 

JUMP-UNLESS @RESET-Q33 [33]
ACTIVE-SET 0 [63]
JUMP @END-Q33
LABEL @RESET-Q33
ACTIVE-RESET 0 [63]
LABEL @END-Q33 

MELODIC_GATE 2 1 0

MEASURE 2 [56]
MEASURE 1 [55]
MEASURE 0 [54]

# ---- Retrieve pitch for Lead Note #6, replicate it into qubits, and produce pitch for Harmony Note #6a ----
JUMP-UNLESS @RESET-Q17a [17]
ACTIVE-SET 2 [63]
JUMP @END-Q17a
LABEL @RESET-Q17a
ACTIVE-RESET 2 [63]
LABEL @END-Q17a 

JUMP-UNLESS @RESET-Q16a [16]
ACTIVE-SET 1 [63]
JUMP @END-Q16a
LABEL @RESET-Q16a
ACTIVE-RESET 1 [63]
LABEL @END-Q16a 

JUMP-UNLESS @RESET-Q15a [15]
ACTIVE-SET 0 [63]
JUMP @END-Q15a
LABEL @RESET-Q15a
ACTIVE-RESET 0 [63]
LABEL @END-Q15a 

HARMONIC_GATE 2 1 0

MEASURE 2 [38]
MEASURE 1 [37]
MEASURE 0 [36]

# ---- Replicate Harmony Note #6a into qubits, and produce pitch for Harmony Note #6b ----
JUMP-UNLESS @RESET-Q38 [38]
ACTIVE-SET 2 [63]
JUMP @END-Q38
LABEL @RESET-Q38
ACTIVE-RESET 2 [63]
LABEL @END-Q38 

JUMP-UNLESS @RESET-Q37 [37]
ACTIVE-SET 1 [63]
JUMP @END-Q37
LABEL @RESET-Q37
ACTIVE-RESET 1 [63]
LABEL @END-Q37 

JUMP-UNLESS @RESET-Q36 [36]
ACTIVE-SET 0 [63]
JUMP @END-Q36
LABEL @RESET-Q36
ACTIVE-RESET 0 [63]
LABEL @END-Q36 

MELODIC_GATE 2 1 0

MEASURE 2 [59]
MEASURE 1 [58]
MEASURE 0 [57]

# ---- Retrieve pitch for Lead Note #7, replicate it into qubits, and produce pitch for Harmony Note #7a ----
JUMP-UNLESS @RESET-Q20a [20]
ACTIVE-SET 2 [63]
JUMP @END-Q20a
LABEL @RESET-Q20a
ACTIVE-RESET 2 [63]
LABEL @END-Q20a 

JUMP-UNLESS @RESET-Q19a [19]
ACTIVE-SET 1 [63]
JUMP @END-Q19a
LABEL @RESET-Q19a
ACTIVE-RESET 1 [63]
LABEL @END-Q19a 

JUMP-UNLESS @RESET-Q18a [18]
ACTIVE-SET 0 [63]
JUMP @END-Q18a
LABEL @RESET-Q18a
ACTIVE-RESET 0 [63]
LABEL @END-Q18a 

HARMONIC_GATE 2 1 0

MEASURE 2 [41]
MEASURE 1 [40]
MEASURE 0 [39]

# ---- Replicate Harmony Note #7a into qubits, and produce pitch for Harmony Note #7b ----
JUMP-UNLESS @RESET-Q41 [41]
ACTIVE-SET 2 [63]
JUMP @END-Q41
LABEL @RESET-Q41
ACTIVE-RESET 2 [63]
LABEL @END-Q41 

JUMP-UNLESS @RESET-Q40 [40]
ACTIVE-SET 1 [63]
JUMP @END-Q40
LABEL @RESET-Q40
ACTIVE-RESET 1 [63]
LABEL @END-Q40 

JUMP-UNLESS @RESET-Q39 [39]
ACTIVE-SET 0 [63]
JUMP @END-Q39
LABEL @RESET-Q39
ACTIVE-RESET 0 [63]
LABEL @END-Q39 

MELODIC_GATE 2 1 0

MEASURE 2 [62]
MEASURE 1 [61]
MEASURE 0 [60]
"""



###
# Produces a given number of accompanying pitches for a given pitch and rotations degrees. This
# function doesn't distinguish between harmonic and melodic accompaniment, as the list of degrees
# supplied to this function should be conducive to producing the desired type of accompaniment.
#    Parameters:
#        pitch_index Index (0 - 7) of the pitch for which accompaniment is desired
#        degrees Comma-delimited string containing 28 degrees that represents the rotations
#
#    Returns JSON string containing:
#        pitch_probabilities Array of eight probabilities, each corresponding to one of the
#                            pitch indices
#        measured_pitch Pitch index (0 - 1) resulting from measurement
###

@app.route('/accompany')
def accompany():
    pitch_index = int(request.args['pitch_index'])
    print("pitch_index: ", pitch_index)

    rotation_degrees = request.args['degrees'].split(",")
    print("rotation_degrees: ", rotation_degrees)

    if (len(rotation_degrees) == DEGREES_OF_FREEDOM and
            0 <= pitch_index < NUM_PITCHES):

        gate_matrix = compute_matrix(rotation_degrees)
        pitch_probabilities_matrix = np.square(np.transpose(gate_matrix)[pitch_index])

        qvm = api.QVMConnection()
        p = Program().defgate("ACCOMPANIMENT_GATE", gate_matrix)

        # Convert the pitch index to a binary string, and use it to create
        # the initial gates on the three wires of the quantum circuit,
        # least significant qubit on the lowest number wire
        qubit_string = format(pitch_index, '03b')
        for idx, qubit_char in enumerate(qubit_string):
            if (qubit_char == '0'):
                p.inst(I(NUM_CIRCUIT_WIRES - 1 - idx))
            else:
                p.inst(X(NUM_CIRCUIT_WIRES - 1 - idx))

        p.inst(("ACCOMPANIMENT_GATE", 2, 1, 0))\
            .measure(0, 0).measure(1, 1)\
            .measure(2, 2)
        print(p)

        num_runs = 1
        result = qvm.run(p, [2, 1, 0], num_runs)
        bits = result[0]
        measured_pitch = bits[0] * 4 + bits[1] * 2 + bits[2]

        print("result: ",  result)

        pitch_probabilities = pitch_probabilities_matrix.tolist()
        rounded_pitch_probabilities = [0] * NUM_PITCHES
        for idx, pitch_prob in enumerate(pitch_probabilities[0]):
            rounded_pitch_probabilities[idx] = round(pitch_prob, 4)


        ret_dict = {"pitch_probabilities":rounded_pitch_probabilities,
                    "measured_pitch": measured_pitch}

    return jsonify(ret_dict)

###
# Produces a musical (specifically second-species counterpoint) composition for
# a given initial pitch, and melodic/harmonic rotations degrees.
#    Parameters:
#        pitch_index Index (0 - 7) of the initial pitch for which a composition is desired
#        melodic_degrees Comma-delimited string containing 28 rotations in degrees for melody matrix
#        harmonic_degrees Comma-delimited string containing 28 rotations in degrees for harmony matrix
#
#    Returns JSON string containing:
#        melody_part
#            pitch_index
#            start_beat
#            pitch_probs
#        harmony_part
#            pitch_index
#            start_beat
#            pitch_probs
#
#        pitch_index is an integer from (0 - 7) resulting from measurement
#        start_beat is the beat in the entire piece for which the note was produced
#        pitch_probs is an array of eight probabilities from which the pitch_index resulted
###

@app.route('/counterpoint')
def counterpoint():
    pitch_index = int(request.args['pitch_index'])
    print("pitch_index: ", pitch_index)

    melodic_degrees = request.args['melodic_degrees'].split(",")
    print("melodic_degrees: ", melodic_degrees)

    harmonic_degrees = request.args['harmonic_degrees'].split(",")
    print("harmonic_degrees: ", harmonic_degrees)

    if (len(melodic_degrees) == DEGREES_OF_FREEDOM and
            len(harmonic_degrees) == DEGREES_OF_FREEDOM and
            0 <= pitch_index < NUM_PITCHES):

        melodic_gate_matrix = compute_matrix(melodic_degrees)
        harmonic_gate_matrix = compute_matrix(harmonic_degrees)

        qvm = api.QVMConnection()
        p = Program()

        p.defgate("MELODIC_GATE", melodic_gate_matrix)
        p.defgate("HARMONIC_GATE", harmonic_gate_matrix)

        # Convert the pitch index to a binary string, and use it to create
        # the initial gates on the three wires of the quantum circuit,
        # least significant qubit on the lowest number wire.
        # Also, place initial pitch into Lead Note #1
        qubit_string = format(pitch_index, '03b')
        for idx, qubit_char in enumerate(qubit_string):
            if qubit_char == '0':
                p.inst(I(NUM_CIRCUIT_WIRES - 1 - idx))
                p.inst(FALSE(idx))
            else:
                p.inst(X(NUM_CIRCUIT_WIRES - 1 - idx))
                p.inst(TRUE(idx))

        p.inst(RawInstr("""
DEFCIRCUIT ACTIVE-RESET q scratch_bit:
    MEASURE q scratch_bit
    JUMP-UNLESS @END-ACTIVE-SET scratch_bit
    X q
    LABEL @END-ACTIVE-SET

DEFCIRCUIT ACTIVE-SET q scratch_bit:
    MEASURE q scratch_bit
    JUMP-WHEN @END-ACTIVE-RESET scratch_bit
    X q
    LABEL @END-ACTIVE-RESET

# == Produce melody ==
# ---- Produce pitch for Lead Note #2 and replicate measurement results into qubits ----
MELODIC_GATE 2 1 0

MEASURE 2 [5]
MEASURE 1 [4]
MEASURE 0 [3]

JUMP-UNLESS @RESET-Q5 [5]
ACTIVE-SET 2 [63]
JUMP @END-Q5
LABEL @RESET-Q5
ACTIVE-RESET 5 [63]
LABEL @END-Q5 

JUMP-UNLESS @RESET-Q4 [4]
ACTIVE-SET 1 [63]
JUMP @END-Q4
LABEL @RESET-Q4
ACTIVE-RESET 4 [63]
LABEL @END-Q4 

JUMP-UNLESS @RESET-Q3 [3]
ACTIVE-SET 0 [63]
JUMP @END-Q3
LABEL @RESET-Q3
ACTIVE-RESET 3 [63]
LABEL @END-Q3 

# ---- Produce pitch for Lead Note #3 and replicate measurement results into qubits ----
MELODIC_GATE 2 1 0

MEASURE 2 [8]
MEASURE 1 [7]
MEASURE 0 [6]

JUMP-UNLESS @RESET-Q8 [8]
ACTIVE-SET 2 [63]
JUMP @END-Q8
LABEL @RESET-Q8
ACTIVE-RESET 2 [63]
LABEL @END-Q8 

JUMP-UNLESS @RESET-Q7 [7]
ACTIVE-SET 1 [63]
JUMP @END-Q7
LABEL @RESET-Q7
ACTIVE-RESET 1 [63]
LABEL @END-Q7 

JUMP-UNLESS @RESET-Q6 [6]
ACTIVE-SET 0 [63]
JUMP @END-Q6
LABEL @RESET-Q6
ACTIVE-RESET 0 [63]
LABEL @END-Q6 

# ---- Produce pitch for Lead Note #4 and replicate measurement results into qubits ----
MELODIC_GATE 2 1 0

MEASURE 2 [11]
MEASURE 1 [10]
MEASURE 0 [9]

JUMP-UNLESS @RESET-Q11 [11]
ACTIVE-SET 2 [63]
JUMP @END-Q11
LABEL @RESET-Q11
ACTIVE-RESET 2 [63]
LABEL @END-Q11 

JUMP-UNLESS @RESET-Q10 [10]
ACTIVE-SET 1 [63]
JUMP @END-Q10
LABEL @RESET-Q10
ACTIVE-RESET 1 [63]
LABEL @END-Q10 

JUMP-UNLESS @RESET-Q9 [9]
ACTIVE-SET 0 [63]
JUMP @END-Q9
LABEL @RESET-Q9
ACTIVE-RESET 0 [63]
LABEL @END-Q9 

# ---- Produce pitch for Lead Note #5 and replicate measurement results into qubits ----
MELODIC_GATE 2 1 0

MEASURE 2 [14]
MEASURE 1 [13]
MEASURE 0 [12]

JUMP-UNLESS @RESET-Q14 [14]
ACTIVE-SET 2 [63]
JUMP @END-Q14
LABEL @RESET-Q14
ACTIVE-RESET 2 [63]
LABEL @END-Q14 

JUMP-UNLESS @RESET-Q13 [13]
ACTIVE-SET 1 [63]
JUMP @END-Q13
LABEL @RESET-Q13
ACTIVE-RESET 1 [63]
LABEL @END-Q13 

JUMP-UNLESS @RESET-Q12 [12]
ACTIVE-SET 0 [63]
JUMP @END-Q12
LABEL @RESET-Q12
ACTIVE-RESET 0 [63]
LABEL @END-Q12 

# ---- Produce pitch for Lead Note #6 and replicate measurement results into qubits ----
MELODIC_GATE 2 1 0

MEASURE 2 [17]
MEASURE 1 [16]
MEASURE 0 [15]

JUMP-UNLESS @RESET-Q17 [17]
ACTIVE-SET 2 [63]
JUMP @END-Q17
LABEL @RESET-Q17
ACTIVE-RESET 2 [63]
LABEL @END-Q17 

JUMP-UNLESS @RESET-Q16 [16]
ACTIVE-SET 1 [63]
JUMP @END-Q16
LABEL @RESET-Q16
ACTIVE-RESET 1 [63]
LABEL @END-Q16 

JUMP-UNLESS @RESET-Q15 [15]
ACTIVE-SET 0 [63]
JUMP @END-Q15
LABEL @RESET-Q15
ACTIVE-RESET 0 [63]
LABEL @END-Q15 

# ---- Produce pitch for Lead Note #7 and replicate measurement results into qubits ----
MELODIC_GATE 2 1 0

MEASURE 2 [20]
MEASURE 1 [19]
MEASURE 0 [18]

# == Produce harmony ==
# ---- Retrieve pitch for Lead Note #1, replicate it into qubits, and produce pitch for Harmony Note #1a ----
JUMP-UNLESS @RESET-Q2a [2]
ACTIVE-SET 2 [63]
JUMP @END-Q2a
LABEL @RESET-Q2a
ACTIVE-RESET 2 [63]
LABEL @END-Q2a 

JUMP-UNLESS @RESET-Q1a [1]
ACTIVE-SET 1 [63]
JUMP @END-Q1a
LABEL @RESET-Q1a
ACTIVE-RESET 1 [63]
LABEL @END-Q1a 

JUMP-UNLESS @RESET-Q0a [0]
ACTIVE-SET 0 [63]
JUMP @END-Q0a
LABEL @RESET-Q0a
ACTIVE-RESET 0 [63]
LABEL @END-Q0a 

HARMONIC_GATE 2 1 0

MEASURE 2 [23]
MEASURE 1 [22]
MEASURE 0 [21]

# ---- Replicate Harmony Note #1a into qubits, and produce pitch for Harmony Note #1b ----
JUMP-UNLESS @RESET-Q23 [23]
ACTIVE-SET 2 [63]
JUMP @END-Q23
LABEL @RESET-Q23
ACTIVE-RESET 2 [63]
LABEL @END-Q23 

JUMP-UNLESS @RESET-Q22 [22]
ACTIVE-SET 1 [63]
JUMP @END-Q22
LABEL @RESET-Q22
ACTIVE-RESET 1 [63]
LABEL @END-Q22 

JUMP-UNLESS @RESET-Q21 [21]
ACTIVE-SET 0 [63]
JUMP @END-Q21
LABEL @RESET-Q21
ACTIVE-RESET 0 [63]
LABEL @END-Q21 

MELODIC_GATE 2 1 0

MEASURE 2 [44]
MEASURE 1 [43]
MEASURE 0 [42]

# ---- Retrieve pitch for Lead Note #2, replicate it into qubits, and produce pitch for Harmony Note #2a ----
JUMP-UNLESS @RESET-Q5a [5]
ACTIVE-SET 2 [63]
JUMP @END-Q5a
LABEL @RESET-Q5a
ACTIVE-RESET 2 [63]
LABEL @END-Q5a 

JUMP-UNLESS @RESET-Q4a [4]
ACTIVE-SET 1 [63]
JUMP @END-Q4a
LABEL @RESET-Q4a
ACTIVE-RESET 1 [63]
LABEL @END-Q4a 

JUMP-UNLESS @RESET-Q3a [3]
ACTIVE-SET 0 [63]
JUMP @END-Q3a
LABEL @RESET-Q3a
ACTIVE-RESET 0 [63]
LABEL @END-Q3a 

HARMONIC_GATE 2 1 0

MEASURE 2 [26]
MEASURE 1 [25]
MEASURE 0 [24]

# ---- Replicate Harmony Note #2a into qubits, and produce pitch for Harmony Note #2b ----
JUMP-UNLESS @RESET-Q26 [26]
ACTIVE-SET 2 [63]
JUMP @END-Q26
LABEL @RESET-Q26
ACTIVE-RESET 2 [63]
LABEL @END-Q26 

JUMP-UNLESS @RESET-Q25 [25]
ACTIVE-SET 1 [63]
JUMP @END-Q25
LABEL @RESET-Q25
ACTIVE-RESET 1 [63]
LABEL @END-Q25 

JUMP-UNLESS @RESET-Q24 [24]
ACTIVE-SET 0 [63]
JUMP @END-Q24
LABEL @RESET-Q24
ACTIVE-RESET 0 [63]
LABEL @END-Q24 

MELODIC_GATE 2 1 0

MEASURE 2 [47]
MEASURE 1 [46]
MEASURE 0 [45]

# ---- Retrieve pitch for Lead Note #3, replicate it into qubits, and produce pitch for Harmony Note #3a ----
JUMP-UNLESS @RESET-Q8a [8]
ACTIVE-SET 2 [63]
JUMP @END-Q8a
LABEL @RESET-Q8a
ACTIVE-RESET 2 [63]
LABEL @END-Q8a 

JUMP-UNLESS @RESET-Q7a [7]
ACTIVE-SET 1 [63]
JUMP @END-Q7a
LABEL @RESET-Q7a
ACTIVE-RESET 1 [63]
LABEL @END-Q7a 

JUMP-UNLESS @RESET-Q6a [6]
ACTIVE-SET 0 [63]
JUMP @END-Q6a
LABEL @RESET-Q6a
ACTIVE-RESET 0 [63]
LABEL @END-Q6a 

HARMONIC_GATE 2 1 0

MEASURE 2 [29]
MEASURE 1 [28]
MEASURE 0 [27]

# ---- Replicate Harmony Note #3a into qubits, and produce pitch for Harmony Note #3b ----
JUMP-UNLESS @RESET-Q29 [29]
ACTIVE-SET 2 [63]
JUMP @END-Q29
LABEL @RESET-Q29
ACTIVE-RESET 2 [63]
LABEL @END-Q29 

JUMP-UNLESS @RESET-Q28 [28]
ACTIVE-SET 1 [63]
JUMP @END-Q28
LABEL @RESET-Q28
ACTIVE-RESET 1 [63]
LABEL @END-Q28 

JUMP-UNLESS @RESET-Q27 [27]
ACTIVE-SET 0 [63]
JUMP @END-Q27
LABEL @RESET-Q27
ACTIVE-RESET 0 [63]
LABEL @END-Q27 

MELODIC_GATE 2 1 0

MEASURE 2 [50]
MEASURE 1 [49]
MEASURE 0 [48]

# ---- Retrieve pitch for Lead Note #4, replicate it into qubits, and produce pitch for Harmony Note #4a ----
JUMP-UNLESS @RESET-Q11a [11]
ACTIVE-SET 2 [63]
JUMP @END-Q11a
LABEL @RESET-Q11a
ACTIVE-RESET 2 [63]
LABEL @END-Q11a 

JUMP-UNLESS @RESET-Q10a [10]
ACTIVE-SET 1 [63]
JUMP @END-Q10a
LABEL @RESET-Q10a
ACTIVE-RESET 1 [63]
LABEL @END-Q10a 

JUMP-UNLESS @RESET-Q9a [9]
ACTIVE-SET 0 [63]
JUMP @END-Q9a
LABEL @RESET-Q9a
ACTIVE-RESET 0 [63]
LABEL @END-Q9a 

HARMONIC_GATE 2 1 0

MEASURE 2 [32]
MEASURE 1 [31]
MEASURE 0 [30]

# ---- Replicate Harmony Note #4a into qubits, and produce pitch for Harmony Note #4b ----
JUMP-UNLESS @RESET-Q32 [32]
ACTIVE-SET 2 [63]
JUMP @END-Q32
LABEL @RESET-Q32
ACTIVE-RESET 2 [63]
LABEL @END-Q32 

JUMP-UNLESS @RESET-Q31 [31]
ACTIVE-SET 1 [63]
JUMP @END-Q31
LABEL @RESET-Q31
ACTIVE-RESET 1 [63]
LABEL @END-Q31 

JUMP-UNLESS @RESET-Q30 [30]
ACTIVE-SET 0 [63]
JUMP @END-Q30
LABEL @RESET-Q30
ACTIVE-RESET 0 [63]
LABEL @END-Q30 

MELODIC_GATE 2 1 0

MEASURE 2 [53]
MEASURE 1 [52]
MEASURE 0 [51]

# ---- Retrieve pitch for Lead Note #5, replicate it into qubits, and produce pitch for Harmony Note #5a ----
JUMP-UNLESS @RESET-Q14a [14]
ACTIVE-SET 2 [63]
JUMP @END-Q14a
LABEL @RESET-Q14a
ACTIVE-RESET 2 [63]
LABEL @END-Q14a 

JUMP-UNLESS @RESET-Q13a [13]
ACTIVE-SET 1 [63]
JUMP @END-Q13a
LABEL @RESET-Q13a
ACTIVE-RESET 1 [63]
LABEL @END-Q13a 

JUMP-UNLESS @RESET-Q12a [12]
ACTIVE-SET 0 [63]
JUMP @END-Q12a
LABEL @RESET-Q12a
ACTIVE-RESET 0 [63]
LABEL @END-Q12a 

HARMONIC_GATE 2 1 0

MEASURE 2 [35]
MEASURE 1 [34]
MEASURE 0 [33]

# ---- Replicate Harmony Note #5a into qubits, and produce pitch for Harmony Note #5b ----
JUMP-UNLESS @RESET-Q35 [35]
ACTIVE-SET 2 [63]
JUMP @END-Q35
LABEL @RESET-Q35
ACTIVE-RESET 2 [63]
LABEL @END-Q35 

JUMP-UNLESS @RESET-Q34 [34]
ACTIVE-SET 1 [63]
JUMP @END-Q34
LABEL @RESET-Q34
ACTIVE-RESET 1 [63]
LABEL @END-Q34 

JUMP-UNLESS @RESET-Q33 [33]
ACTIVE-SET 0 [63]
JUMP @END-Q33
LABEL @RESET-Q33
ACTIVE-RESET 0 [63]
LABEL @END-Q33 

MELODIC_GATE 2 1 0

MEASURE 2 [56]
MEASURE 1 [55]
MEASURE 0 [54]

# ---- Retrieve pitch for Lead Note #6, replicate it into qubits, and produce pitch for Harmony Note #6a ----
JUMP-UNLESS @RESET-Q17a [17]
ACTIVE-SET 2 [63]
JUMP @END-Q17a
LABEL @RESET-Q17a
ACTIVE-RESET 2 [63]
LABEL @END-Q17a 

JUMP-UNLESS @RESET-Q16a [16]
ACTIVE-SET 1 [63]
JUMP @END-Q16a
LABEL @RESET-Q16a
ACTIVE-RESET 1 [63]
LABEL @END-Q16a 

JUMP-UNLESS @RESET-Q15a [15]
ACTIVE-SET 0 [63]
JUMP @END-Q15a
LABEL @RESET-Q15a
ACTIVE-RESET 0 [63]
LABEL @END-Q15a 

HARMONIC_GATE 2 1 0

MEASURE 2 [38]
MEASURE 1 [37]
MEASURE 0 [36]

# ---- Replicate Harmony Note #6a into qubits, and produce pitch for Harmony Note #6b ----
JUMP-UNLESS @RESET-Q38 [38]
ACTIVE-SET 2 [63]
JUMP @END-Q38
LABEL @RESET-Q38
ACTIVE-RESET 2 [63]
LABEL @END-Q38 

JUMP-UNLESS @RESET-Q37 [37]
ACTIVE-SET 1 [63]
JUMP @END-Q37
LABEL @RESET-Q37
ACTIVE-RESET 1 [63]
LABEL @END-Q37 

JUMP-UNLESS @RESET-Q36 [36]
ACTIVE-SET 0 [63]
JUMP @END-Q36
LABEL @RESET-Q36
ACTIVE-RESET 0 [63]
LABEL @END-Q36 

MELODIC_GATE 2 1 0

MEASURE 2 [59]
MEASURE 1 [58]
MEASURE 0 [57]

# ---- Retrieve pitch for Lead Note #7, replicate it into qubits, and produce pitch for Harmony Note #7a ----
JUMP-UNLESS @RESET-Q20a [20]
ACTIVE-SET 2 [63]
JUMP @END-Q20a
LABEL @RESET-Q20a
ACTIVE-RESET 2 [63]
LABEL @END-Q20a 

JUMP-UNLESS @RESET-Q19a [19]
ACTIVE-SET 1 [63]
JUMP @END-Q19a
LABEL @RESET-Q19a
ACTIVE-RESET 1 [63]
LABEL @END-Q19a 

JUMP-UNLESS @RESET-Q18a [18]
ACTIVE-SET 0 [63]
JUMP @END-Q18a
LABEL @RESET-Q18a
ACTIVE-RESET 0 [63]
LABEL @END-Q18a 

HARMONIC_GATE 2 1 0

MEASURE 2 [41]
MEASURE 1 [40]
MEASURE 0 [39]

# ---- Replicate Harmony Note #7a into qubits, and produce pitch for Harmony Note #7b ----
JUMP-UNLESS @RESET-Q41 [41]
ACTIVE-SET 2 [63]
JUMP @END-Q41
LABEL @RESET-Q41
ACTIVE-RESET 2 [63]
LABEL @END-Q41 

JUMP-UNLESS @RESET-Q40 [40]
ACTIVE-SET 1 [63]
JUMP @END-Q40
LABEL @RESET-Q40
ACTIVE-RESET 1 [63]
LABEL @END-Q40 

JUMP-UNLESS @RESET-Q39 [39]
ACTIVE-SET 0 [63]
JUMP @END-Q39
LABEL @RESET-Q39
ACTIVE-RESET 0 [63]
LABEL @END-Q39 

MELODIC_GATE 2 1 0

MEASURE 2 [62]
MEASURE 1 [61]
MEASURE 0 [60]
"""))

    print(p)

    use_simulator = True

    if use_simulator:
        num_runs = 1
        res = qvm.run(p, [
            2, 1, 0, 5, 4, 3, 8, 7, 6, 11, 10, 9, 14, 13, 12, 17, 16, 15, 20, 19, 18,
            23, 22, 21, 44, 43, 42, 26, 25, 24, 47, 46, 45, 29, 28, 27, 50, 49, 48, 32, 31, 30,
            53, 52, 51, 35, 34, 33, 56, 55, 54, 38, 37, 36, 59, 58, 57, 41, 40, 39, 62, 61, 60
            ], num_runs)
        print(res)

        all_note_nums = create_note_nums_array(res[0])
        melody_note_nums = all_note_nums[0:7]
        harmony_note_nums = all_note_nums[7:21]
    else:
        melody_note_nums =  [0,    1,    2,    3,    4,    5,    6]
        harmony_note_nums = [2, 3, 3, 4, 4, 5, 5, 6, 6, 7, 7, 4, 3, 2]

    ret_dict = {"melody": melody_note_nums,
                "harmony": harmony_note_nums,
                "lilypond": create_lilypond(melody_note_nums, harmony_note_nums),
                "toy_piano" : create_toy_piano(melody_note_nums, harmony_note_nums)}

    return jsonify(ret_dict)

def create_note_nums_array(ordered_classical_registers):
    allnotes_array = []
    cur_val = 0
    for idx, bit in enumerate(ordered_classical_registers):
        if idx % 3 == 0:
            cur_val += bit * 4
        elif idx % 3 == 1:
            cur_val += bit * 2
        else:
            cur_val += bit
            allnotes_array.append(cur_val)
            cur_val = 0
    return allnotes_array


def pitch_letter_by_index(pitch_idx):
    retval = "z"
    if pitch_idx == 0:
        retval = "c"
    elif pitch_idx == 1:
        retval = "d"
    elif pitch_idx == 2:
        retval = "e"
    elif pitch_idx == 3:
        retval = "f"
    elif pitch_idx == 4:
        retval = "g"
    elif pitch_idx == 5:
        retval = "a"
    elif pitch_idx == 6:
        retval = "b"
    elif pitch_idx == 7:
        retval = "c'"
    else:
        retval = "z"
    return retval


# Produce output for Lilypond
def create_lilypond(melody_note_nums, harmony_note_nums):
    retval = "\\version \"2.18.2\" \\paper {#(set-paper-size \"a5\")} \\header {title=\"Schrodinger's Cat\" subtitle=\"on a Keyboard\" composer = \"Rigetti QVM\"}  melody = \\absolute { \\clef \"bass\" \\numericTimeSignature \\time 4/4 \\tempo 4 = 100"
    for pitch in melody_note_nums:
        retval += " " + pitch_letter_by_index(pitch) + "2"

    # Add the same pitch to the end of the melody as in the beginning
    retval += " " + pitch_letter_by_index(melody_note_nums[0]) + "2"

    retval += "} harmony = \\absolute { \\clef \"treble\" \\numericTimeSignature \\time 4/4 "
    for pitch in harmony_note_nums:
        retval += " " + pitch_letter_by_index(pitch) + "'4"

    # Add the same pitch to the end of the harmony as in the beginning of the melody,
    # only an octave higher
    retval += " " + pitch_letter_by_index(melody_note_nums[0]) + "'2"

    retval += "} \\score { << \\new Staff \\with {instrumentName = #\"Harmony\"}  { \\harmony } \\new Staff \\with {instrumentName = #\"Melody\"}  { \\melody } >> }"
    return retval

# Produce output for toy piano
def create_toy_piano(melody_note_nums, harmony_note_nums):
    # For now, assume second-species counterpoint (two notes in harmony for each note in melody)
    quarter_note_dur = 150
    notes = []
    latest_melody_idx = 0
    latest_harmony_idx = 0
    num_pitches_in_octave = 7
    toy_piano_pitch_offset = 1

    for idx, pitch in enumerate(melody_note_nums):
        notes.append({"num": pitch + toy_piano_pitch_offset, "time": idx * quarter_note_dur * 2})
        latest_melody_idx = idx

    # Add the same pitch to the end of the melody as in the beginning
    notes.append({"num": melody_note_nums[0] + toy_piano_pitch_offset, "time": (latest_melody_idx + 1) * quarter_note_dur * 2})

    for idx, pitch in enumerate(harmony_note_nums):
        notes.append({"num": pitch + num_pitches_in_octave + toy_piano_pitch_offset, "time": idx * quarter_note_dur})
        latest_harmony_idx = idx

    # Add the same pitch to the end of the harmony as in the beginning of the melody,
    # only an octave higher
    notes.append({"num": melody_note_nums[0] + num_pitches_in_octave + toy_piano_pitch_offset, "time": (latest_harmony_idx + 1) * quarter_note_dur})

    # Sort the array of dictionaries by time
    sorted_notes = sorted(notes, key=lambda k: k['time'])

    return sorted_notes

if __name__ == '__main__':
    app.run()
