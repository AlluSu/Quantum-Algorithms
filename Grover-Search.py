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
import matplotlib.pyplot as plt
from qiskit import transpile, assemble, IBMQ
from qiskit.quantum_info import Statevector
from qiskit.algorithms import AmplificationProblem, Grover
from qiskit_ibm_runtime import QiskitRuntimeService, Sampler, Session
from qiskit.tools.visualization import plot_histogram
from qiskit.tools.monitor import job_monitor

load_dotenv()

TOKEN = getenv('IBM_QUANTUM_TOKEN')
USED_BACKEND = 'ibm_oslo'
FILE_TO_WRITE_NAME ='History.txt'

# Function used for printing quantum circuits as matplotlib images
def print_quantum_circuits(circuits):

    #Matplotlib output, freezes the program execution until windows are closed
    for circuit in circuits:
        circuit.draw(output = 'mpl')
    plt.show()

# Function used for connecting to the IBM quantum computer
# TODO: Remove deprecated components
def connect_to_cloud(token, backend):
    IBMQ.save_account(token, overwrite=True)
    provider = IBMQ.load_account()
    provider = IBMQ.get_provider(hub='ibm-q', group='open', project='main')
    used_backend = provider.get_backend(backend) # for lower latency choosing the geographically closest one
    print(f"The used backend is: {used_backend}")
    return used_backend

# Writing the randomized entry to see if the results are correct by the quantum computer.
# Results can be obtained from the IBM cloud with the job_id.
# TODO: Use a real database instead of a .txt-file.
def write_to_history(randomized_entry, job_id):
    results_history = open(FILE_TO_WRITE_NAME, "a")
    results_history.write("\n" + str(randomized_entry) + " " + str(job_id) + "\n")
    results_history.close()

# Run the Grover search on a simulator backend.
# TODO: Refactor logging/printing to separate component.
def run_grover_in_simulator(grover_circuits):
    service = QiskitRuntimeService()
    backend_simulator = "ibmq_qasm_simulator"
    with Session(service=service, backend=backend_simulator):
        sampler = Sampler()
        job = sampler.run(circuits=grover_circuits, shots=1000)
        job_monitor(job)
        result = job.result() 
        print('===================================== RESULTS =====================================')
        print(f"{result.quasi_dists}")
        print(f"{result.metadata}")
        qubits = 3
        optimal_amount = Grover.optimal_num_iterations(1, qubits)
        print(f"The optimal amount of Grover iterations is: {optimal_amount} with {qubits}  qubits")
        return result, job

# Run the Grover search on a real quantum computer backend.S
def run_grover_in_quantum_computer(random_name_formatted, backend, grover_circuits):
    print(f"The value, which we are looking for is: {random_name_formatted}")
    mapped_circuit = transpile(grover_circuits, backend=backend)
    quantum_object = assemble(mapped_circuit, backend=backend, shots=1000)
    job = backend.run(quantum_object)
    job_monitor(job)
    job_id = job.job_id()
    result = job.result()
    print(result)
    return result, job

# Visualize the results gotten from the simulator run.
# TODO: Refactor logging/printing to separate component.
def visualize_simulator_results(result, random_name_formatted):
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

# The real program execution starts here.
def run_grover():

    # STEP 1: Construct and define the unstructured search problem.
    random_name = random.randint(0,7) # This simulates a random person from a phone book containing 8 entries [0,..,7]. As 8 = 2³, we need 3 qubits.
    random_name_formatted = format(random_name, '03b') # This formats the random person's name to a 3-bit string
    oracle = Statevector.from_label(random_name_formatted) # Oracle, which is a black-box quantum circuit telling if your guess is right or wrong. We will let the oracle know the owner.
    unstructured_search = AmplificationProblem(oracle, is_good_state=random_name_formatted) # Grover's algorithm uses a technique for modifying quantum states to raise the probability amplitude of the wanted value

    # STEP 2: Constructing the adequate quantum circuit for the problem
    grover_circuits = []

    # Grover's algorithm's accuracy to find the right solution increases with the amount of iterations (in theory).
    values = [0, 1, 2, 3, 4, 5, 6, 7]
    for value in range(0, len(values)):
        grover = Grover(iterations=values[value]) # using Grover's algorithm straight from the Qiskit library
        quantum_circuit = grover.construct_circuit(unstructured_search)
        quantum_circuit.measure_all()
        grover_circuits.append(quantum_circuit)

    # Commented for now so the program does not freeze
    # print_quantum_circuits(grover_circuits)

    # STEP 3: Submit the circuits to IBM Quantum Computer or run with a simulator
    # NOTE: Occasionally the simulator is significantly faster than the real computer due to queue
    try:
        user_option = int(input(
            "Press \n 1 for simulator \n 2 for real hardware \n 3 for retrieving an existing job by job_id \n 4 for both simulator and real hardware \n "
            ))
    except ValueError:
        raise ValueError('Please give an integer')    

    # Simulator
    if user_option == 1:
        
        # Result from Grover's algorithm
        resul, job = run_grover_in_simulator(grover_circuits)    
        
        # Write the randomized entry and job id of the run to a file
        write_to_history(random_name_formatted, job)
    
        # Counting probabilities and doing plotting & visualization with matplotlib
        visualize_simulator_results(result, random_name_formatted)

    # Real quantum computer
    elif user_option == 2:
        # Connect to IBM cloud and get the backend provider.
        backend = connect_to_cloud(TOKEN, USED_BACKEND)
        result = run_grover_in_quantum_computer(random_name_formatted, backend, grover_circuits)

        # Write the randomized entry and job id of the run to a file
        write_to_history(random_name_formatted, result.job_id())

        # TODO: ANALYSIS OF THE RESULTS FROM THE QUANTUM COMPUTER
    
    # Due to occasional queues (45 minutes to 4 hours) in the free-tier quantum computer, it is easier to investigate and experiment by using previous runs, which can be obtained with the job id.
    elif user_option == 3:
        job_id = input("Give job id: ")
        backend = connect_to_cloud(TOKEN, USED_BACKEND)
        result = backend.retrieve_job(job_id)
        print(f"as a dict: {result.result().to_dict()}")
        all_results_as_dict = result.result().to_dict()
        print(all_results_as_dict)

        # TODO: Analysis and visualization of the results
        # hist = plot_histogram(data = all_results_data)
        # plt.show()

    # This runs the job on a simulator and on the real hardware for the same randomized value.
    # Decided to create this due to better and transparent comparison for the different systems.
    elif user_option == 4:
        result = run_grover_in_simulator(grover_circuits)
        write_to_history(random_name_formatted, result[1].job_id())
        visualize_simulator_results(result[0], random_name_formatted)
        backend = connect_to_cloud(TOKEN, USED_BACKEND)
        quantum_job_result_and_id = run_grover_in_quantum_computer(random_name_formatted, backend, grover_circuits)
        write_to_history(random_name_formatted, quantum_job_result_and_id[1].job_id())

    # Undefined input closes the program.
    else:
        print("Closing program!")
        exit()

def main():
    run_grover()

if __name__ == "__main__":
    main()
