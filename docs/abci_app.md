

## The keeper service as an ABCI Application

At a high-level, the ABCI application can be divided into five parts.

### The `AgentRegistrationAbciApp`
Implements the registration of agents to partake in the behaviour scheduled in subsequent rounds.

### The `SafeDeploymentAbciApp`
Implements the deployment of a [Gnosis safe](https://gnosis-safe.io/) contract, 
which is a multisig smart contract wallet that requires a minimum number of agents to approve a transaction 
before it can occur. This assures that no single agent can compromise the funds contained within it.

### The `Keep3rJobAbciApp`
Implements the keeper network specific tasks, namely, identifying a suitable, profitable job to execute 
and proceed to its execution.

1. `JobSelectionRound` <br/>
   The agents examine the Keep3r Network job registry and agree on a job to be selected. 
   The job selection algorithm must be deterministic so that at least 2/3 of the agents can agree on a selection.

2. `IsWorkableRound` <br/>
   The agents individually determine if the job is workable by executing the appropriate method present on 
   the job contract interface. 
   The agents must reach consensus on the outcome hereof before proceeding.

3. `IsProfitableRound` <br/>
   The agents individually determine if the job is profitable according to a criterion specified by the developer. 
   Customization of this metric allows tailoring to suit the application. 
   For example, whether the job execution reward outweighs the gas costs multiplied by some variable
   that encapsulates the success ratio, or some more complex method to determine its profitability. 
   The agents collectively agree whether the job is profitable enough to proceed.

4. `DoWorkRound` <br/>
   The agent execute the specified task required by the job. 
   This may consist of one or more contract calls as specified by the job, and can additionally involve
   off-chain computation by the individual agents.
   Once consensus is reached the agents can move to the final stage of this ABCI application; 
   the preparation of the transaction containing the result of their computation

5. `FinishedPrepareTxRound` <br/> 
   Default final state that indicates that the job has been executed, and in which the agents prepare the 
   transaction containing the result of their for on-chain transaction submission.

### The `TransactionSubmissionAbciApp`
Implements the functionality of selecting an agent, which is tasked with on-chain transaction submission
of the result for record-keeping, ensuring that it becomes part of the next block that is mined.

### The `ResetPauseABCIApp`
New periods are automatically created when the application traverses the `ResetAndPauseRound`. 
The application allocates a new slot for the `SynchronizedData` to store new values for the variables stored within it.

### Implementation of the `Keep3rAbciApp`
In the final implementation the Keep3rAbciApp is then assembled from its constituent parts.
In order to combine the individual ABCI applications listed above, we defined a transition mapping 
that connect their states.

