'''
Demonstrating Grover's search algorithm.

Scenario: We have a phone book containing names and numbers. Because the phone book is sorted alphabetically by names,
it is easy to find a persons phone number by persons name. However, a more difficult task would be if we want to find a person by a phone number.
Number-wise, if we have a million (1 000 000) entries in a phone book, we would on average have to look up half of it to find the correct entry (500 000 lookups).
Grover's algorithm provides a quadratical speed-up to unstructured search probelms. Applying Grover's algorithm to this problem would reduce the needed amount
of lookups to only 1000.

This program simulates the above scenario on a smaller scale.
'''

import random
from os import getenv
from dotenv import load_dotenv
import math
import matplotlib.pyplot as plt
from qiskit import transpile, assemble, IBMQ
from qiskit.quantum_info import Statevector
from qiskit.algorithms import AmplificationProblem, Grover
from qiskit_ibm_runtime import QiskitRuntimeService, Sampler, Session
from qiskit.tools.visualization import plot_histogram
#from qiskit.tools.monitor import job_monitor

load_dotenv()

TOKEN = getenv('IBM_QUANTUM_TOKEN')

# Function used for printing quantum circuits as matplotlib images
def print_quantum_circuits(circuits):
    #Matplotlib output, freezes the program execution until windows are closed
    for circuit in circuits:
        circuit.draw(output = 'mpl')
    plt.show()

# STEP 1: Construct and define the unstructured search problem.

random_name = random.randint(0,7) # This simulates a random person from a phone book containing 8 entries [0,..,7]. As 8 = 2³, we need 3 qubits.
random_name_formatted = format(random_name, '03b') # This formats the random person's name to a 3-bit string
oracle = Statevector.from_label(random_name_formatted) # Oracle, which is a black-box quantum circuit telling if your guess is right or wrong. We will let the oracle know the owner.

unstructured_search = AmplificationProblem(oracle, is_good_state=random_name_formatted) # Grover's algorithm uses a technique for modifying quantum states to raise the probability amplitude of the wanted value

# STEP 2: Constructing the adequate quantum circuit for the problem

grover_circuits = []

# Grover's algorithm's accuracy to find the right solution increases with the amount of iterations.
# The optimal is approximately 2.22, and if the factor is larger than 4.44 it is the worst we can get
# We have to round to integers due to implementation reasons, so best amount of iterations is 2, the worst is 4 and over.

values = [0, 1, 2, 3, 4, 5, 6, 7]
for value in range(0, len(values)):
    grover = Grover(iterations=values[value]) # using Grover's algorithm straight from the Qiskit library
    quantum_circuit = grover.construct_circuit(unstructured_search)
    quantum_circuit.measure_all()
    grover_circuits.append(quantum_circuit)

# print_quantum_circuits(grover_circuits)

# STEP 3: Submit the circuits to IBM Quantum Computer or run with a simulator
# NOTE: The simulator is significantly faster than the real computer
user_option = int(input("Press 1 for simulator and 2 for real hardware: "))

if user_option == 1:    
    service = QiskitRuntimeService()
    backend_simulator = "ibmq_qasm_simulator"
    with Session(service=service, backend=backend_simulator):
        sampler = Sampler()
        job = sampler.run(circuits=grover_circuits, shots=1000)
        #job_monitor(job)
        result = job.result() 
        print('===================================== RESULTS =====================================')
        print(f"{result.quasi_dists}")
        print(f"{result.metadata}")
        qubits = 3
        optimal_amount = Grover.optimal_num_iterations(1, qubits)
        print(f"The optimal amount of Grover iterations is: {optimal_amount} with {qubits} qubits")

        # STEP 4: Analysis of the results gotten from the simulator
        # Counting probabilities and doing plotting & visualization with matplotlib

        for distribution in range(0, len(result.quasi_dists)):
            results_dictionary = result.quasi_dists[distribution].binary_probabilities()
            answer = max(results_dictionary, key=results_dictionary.get)
            print(f"With {distribution + 1} iterations the following probabilities were returned: \n {result.quasi_dists[distribution]}")
            print(f"Maximum probability was for the value {answer}")
            print(f"Correct answer: {random_name_formatted}")
            print('Correct!' if answer == random_name_formatted else 'Failure!')
            print('\n')
        histogram = plot_histogram(result.quasi_dists, legend=['1 iteration', '2 iterations', '3 iterations', '4 iterations', '5 iterations', '6 iterations', '7 iterations', '8 iterations'])
        plt.xlabel("Which entry in the data [0,..,7]")
        plt.show()

elif user_option == 2:
    IBMQ.save_account(TOKEN, overwrite=True)
    provider = IBMQ.load_account()
    provider = IBMQ.get_provider(hub='ibm-q', group='open', project='main')
    backend_real_device = provider.get_backend('ibm_oslo') # for lower latency choose geographically closest one
    print(f"The used backend is: {backend_real_device}")
    mapped_circuit = transpile(grover_circuits, backend=backend_real_device)
    quantum_object = assemble(mapped_circuit, backend=backend_real_device, shots=1000)
    job = backend_real_device.run(quantum_object)
    job_monitor(job)
    later_result = provider.get_backend('ibm-oslo').retrieve_job(job.job_id())
    print(later_result)
    result = job.result()
    print(result)
    results = result.result
    print(results)

    # TODO: STEP 4, ANALYSIS OF THE RESULTS FROM THE QUANTUM COMPUTER

else:
    print("Closing program!")
    exit()
