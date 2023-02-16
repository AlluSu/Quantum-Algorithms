from qiskit_ibm_runtime import QiskitRuntimeService
from os import getenv
from dotenv import load_dotenv

load_dotenv()

TOKEN = getenv('IBM_QUANTUM_TOKEN')

# Save an IBM Quantum account.
QiskitRuntimeService.save_account(channel="ibm_quantum", token=TOKEN)

service = QiskitRuntimeService()
program_inputs = {"iterations" : 1}
options = {"backend_name" : "ibmq_qasm_simulator"}
job = service.run(program_id="hello-world", options=options, inputs=program_inputs)
print(f"job id: {job.job_id()}")
result = job.result()
print(result)