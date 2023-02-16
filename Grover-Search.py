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
import matplotlib.pyplot as plt
from qiskit.quantum_info import Statevector
from qiskit.algorithms import AmplificationProblem, Grover
from qiskit_ibm_runtime import QiskitRuntimeService, Sampler, Session
from qiskit.tools.visualization import plot_histogram

# STEP 1: Construct and define the unstructured search problem.

random_name = random.randint(0,7) # This simulates a random person from a phone book containing 8 entries [0,..,7]
random_name_formatted = format(random_name, '03b') # This formats the random person's name to a 3-bit string
oracle = Statevector.from_label(random_name_formatted) # Oracle, which is a black-box quantum circuit telling if your guess is right or wrong. We will let the oracle know the owner.

unstructured_search = AmplificationProblem(oracle, is_good_state=random_name_formatted) # Grover's algorithm uses a technique for modifying quantum states to raise the probability amplitude of the wanted value

# STEP 2: Constructing the adequate quantum circuit for the problem

grover_circuits = []
# We will make 2 Grover's circuits, with one having 1 iteration and the other having 2. Grover's algorithms accuracy to finding the right solution increases with the amount of iterations.
for iteration in range(1,3):
    grover = Grover(iterations=iteration)
    quantum_circuit = grover.construct_circuit(unstructured_search)
    quantum_circuit.measure_all()
    grover_circuits.append(quantum_circuit)

#plt.ion()
#plt.show()

# First circuit with 1 iteration
figure_1 = grover_circuits[0].draw(output='mpl')
plt.show()
#plt.pause(0.001)

# Second circuit with 2 iterations
figure_2 = grover_circuits[1].draw(output='mpl')
plt.show()
#plt.pause(0.001)

# STEP 3: Submit the circuits to IBM Quantum Computer via cloud
service = QiskitRuntimeService()
backend = "ibmq_qasm_simulator"

with Session(service=service, backend=backend):
    sampler = Sampler()
    job = sampler.run(circuits=grover_circuits, shots=1000)
    result = job.result() 
    print('===================================== RESULTS =====================================')
    print(f"{result.quasi_dists}")
    print(f"{result.metadata}")

# STEP 4: Analysis of the results
results_dictionary = result.quasi_dists[1].binary_probabilities()
answer = max(results_dictionary, key=results_dictionary.get)
figure_3 = plot_histogram(result.quasi_dists, legend=['1 iteration', '2 iterations'])
plt.show()

print(f"Quantum computer returned: {answer}")
print(f"Correct answer: {random_name_formatted}")
print('Correct!' if answer == random_name_formatted else 'Failure!')