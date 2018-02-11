from flask import Flask, jsonify, request
from pyquil.quil import Program
import pyquil.api as api
from pyquil.gates import *
#import numpy as np
#from math import *
from gatedefs import *

app = Flask(__name__)


@app.route('/accompany', methods=['GET'])
def accompany():
    return jsonify(request.args)


if __name__ == '__main__':
    app.run()
