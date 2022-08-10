

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


<figure markdown>
<div class="mermaid">
stateDiagram-v2
    CheckSafeExistenceRound --> JobSelectionRound: <center>DONE</center>
    CheckSafeExistenceRound --> SafeNotDeployedRound: <center>NEGATIVE</center>
    CheckSafeExistenceRound --> CheckSafeExistenceRound: <center>ROUND_TIMEOUT<br />NO_MAJORITY</center>
    IsProfitableRound --> PrepareTxRound: <center>DONE</center>
    IsProfitableRound --> NothingToDoRound: <center>NOT_PROFITABLE</center>
    IsProfitableRound --> IsProfitableRound: <center>ROUND_TIMEOUT<br />NO_MAJORITY</center>
    IsWorkableRound --> IsProfitableRound: <center>DONE</center>
    IsWorkableRound --> NothingToDoRound: <center>NOT_WORKABLE</center>
    IsWorkableRound --> IsWorkableRound: <center>ROUND_TIMEOUT<br />NO_MAJORITY</center>
    JobSelectionRound --> IsWorkableRound: <center>DONE</center>
    JobSelectionRound --> NothingToDoRound: <center>NOT_WORKABLE</center>
    JobSelectionRound --> JobSelectionRound: <center>ROUND_TIMEOUT<br />NO_MAJORITY</center>
    PrepareTxRound --> FinishedPrepareTxRound: <center>DONE</center>
    PrepareTxRound --> PrepareTxRound: <center>NO_MAJORITY</center>
    PrepareTxRound --> FailedRound: <center>ROUND_TIMEOUT</center>
</div>
<figcaption>Keep3rJobAbciApp FSM</figcaption>
</figure>


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


<figure markdown>
<div class="mermaid">
stateDiagram-v2
    RegistrationStartupRound --> CheckSafeExistenceRound: <center>FAST_FORWARD<br />DONE</center>
    CheckLateTxHashesRound --> SynchronizeLateMessagesRound: <center>CHECK_LATE_ARRIVING_MESSAGE</center>
    CheckLateTxHashesRound --> CheckLateTxHashesRound: <center>CHECK_TIMEOUT</center>
    CheckLateTxHashesRound --> ResetAndPauseRound: <center>DONE</center>
    CheckLateTxHashesRound --> FailedRound: <center>NONE<br />NO_MAJORITY<br />NEGATIVE</center>
    CheckSafeExistenceRound --> JobSelectionRound: <center>DONE</center>
    CheckSafeExistenceRound --> RandomnessSafeRound: <center>NEGATIVE</center>
    CheckSafeExistenceRound --> CheckSafeExistenceRound: <center>ROUND_TIMEOUT<br />NO_MAJORITY</center>
    CheckTransactionHistoryRound --> SynchronizeLateMessagesRound: <center>CHECK_LATE_ARRIVING_MESSAGE</center>
    CheckTransactionHistoryRound --> CheckTransactionHistoryRound: <center>NO_MAJORITY<br />CHECK_TIMEOUT</center>
    CheckTransactionHistoryRound --> ResetAndPauseRound: <center>DONE</center>
    CheckTransactionHistoryRound --> SelectKeeperTransactionSubmissionRoundB: <center>NEGATIVE</center>
    CheckTransactionHistoryRound --> FailedRound: <center>NONE</center>
    CollectSignatureRound --> FinalizationRound: <center>DONE</center>
    CollectSignatureRound --> ResetRound: <center>NO_MAJORITY</center>
    CollectSignatureRound --> CollectSignatureRound: <center>ROUND_TIMEOUT</center>
    DeploySafeRound --> SelectKeeperSafeRound: <center>FAILED<br />DEPLOY_TIMEOUT</center>
    DeploySafeRound --> ValidateSafeRound: <center>DONE</center>
    FinalizationRound --> CheckTransactionHistoryRound: <center>CHECK_HISTORY</center>
    FinalizationRound --> SynchronizeLateMessagesRound: <center>CHECK_LATE_ARRIVING_MESSAGE</center>
    FinalizationRound --> ValidateTransactionRound: <center>DONE</center>
    FinalizationRound --> SelectKeeperTransactionSubmissionRoundB: <center>FINALIZATION_FAILED<br />INSUFFICIENT_FUNDS</center>
    FinalizationRound --> SelectKeeperTransactionSubmissionRoundBAfterTimeout: <center>FINALIZE_TIMEOUT</center>
    IsProfitableRound --> PrepareTxRound: <center>DONE</center>
    IsProfitableRound --> ResetAndPauseRound: <center>NOT_PROFITABLE</center>
    IsProfitableRound --> IsProfitableRound: <center>ROUND_TIMEOUT<br />NO_MAJORITY</center>
    IsWorkableRound --> IsProfitableRound: <center>DONE</center>
    IsWorkableRound --> ResetAndPauseRound: <center>NOT_WORKABLE</center>
    IsWorkableRound --> IsWorkableRound: <center>ROUND_TIMEOUT<br />NO_MAJORITY</center>
    JobSelectionRound --> IsWorkableRound: <center>DONE</center>
    JobSelectionRound --> ResetAndPauseRound: <center>NOT_WORKABLE</center>
    JobSelectionRound --> JobSelectionRound: <center>ROUND_TIMEOUT<br />NO_MAJORITY</center>
    PrepareTxRound --> RandomnessTransactionSubmissionRound: <center>DONE</center>
    PrepareTxRound --> PrepareTxRound: <center>NO_MAJORITY</center>
    PrepareTxRound --> ResetAndPauseRound: <center>ROUND_TIMEOUT</center>
    RandomnessSafeRound --> SelectKeeperSafeRound: <center>DONE</center>
    RandomnessSafeRound --> RandomnessSafeRound: <center>ROUND_TIMEOUT<br />NO_MAJORITY</center>
    RandomnessTransactionSubmissionRound --> SelectKeeperTransactionSubmissionRoundA: <center>DONE</center>
    RandomnessTransactionSubmissionRound --> RandomnessTransactionSubmissionRound: <center>ROUND_TIMEOUT<br />NO_MAJORITY</center>
    RegistrationRound --> CheckSafeExistenceRound: <center>DONE</center>
    RegistrationRound --> RegistrationRound: <center>NO_MAJORITY</center>
    ResetAndPauseRound --> RegistrationRound: <center>DONE</center>
    ResetAndPauseRound --> RegistrationStartupRound: <center>NO_MAJORITY<br />RESET_AND_PAUSE_TIMEOUT</center>
    ResetRound --> RandomnessTransactionSubmissionRound: <center>DONE</center>
    ResetRound --> FailedRound: <center>RESET_TIMEOUT<br />NO_MAJORITY</center>
    SelectKeeperSafeRound --> DeploySafeRound: <center>DONE</center>
    SelectKeeperSafeRound --> RandomnessSafeRound: <center>ROUND_TIMEOUT<br />NO_MAJORITY</center>
    SelectKeeperTransactionSubmissionRoundA --> CollectSignatureRound: <center>DONE</center>
    SelectKeeperTransactionSubmissionRoundA --> FailedRound: <center>INCORRECT_SERIALIZATION</center>
    SelectKeeperTransactionSubmissionRoundA --> ResetRound: <center>NO_MAJORITY</center>
    SelectKeeperTransactionSubmissionRoundA --> SelectKeeperTransactionSubmissionRoundA: <center>ROUND_TIMEOUT</center>
    SelectKeeperTransactionSubmissionRoundB --> FinalizationRound: <center>DONE</center>
    SelectKeeperTransactionSubmissionRoundB --> FailedRound: <center>INCORRECT_SERIALIZATION</center>
    SelectKeeperTransactionSubmissionRoundB --> ResetRound: <center>NO_MAJORITY</center>
    SelectKeeperTransactionSubmissionRoundB --> SelectKeeperTransactionSubmissionRoundB: <center>ROUND_TIMEOUT</center>
    SelectKeeperTransactionSubmissionRoundBAfterTimeout --> CheckTransactionHistoryRound: <center>CHECK_HISTORY</center>
    SelectKeeperTransactionSubmissionRoundBAfterTimeout --> SynchronizeLateMessagesRound: <center>CHECK_LATE_ARRIVING_MESSAGE</center>
    SelectKeeperTransactionSubmissionRoundBAfterTimeout --> FinalizationRound: <center>DONE</center>
    SelectKeeperTransactionSubmissionRoundBAfterTimeout --> FailedRound: <center>INCORRECT_SERIALIZATION</center>
    SelectKeeperTransactionSubmissionRoundBAfterTimeout --> ResetRound: <center>NO_MAJORITY</center>
    SelectKeeperTransactionSubmissionRoundBAfterTimeout --> SelectKeeperTransactionSubmissionRoundBAfterTimeout: <center>ROUND_TIMEOUT</center>
    SynchronizeLateMessagesRound --> CheckLateTxHashesRound: <center>DONE</center>
    SynchronizeLateMessagesRound --> FailedRound: <center>MISSED_AND_LATE_MESSAGES_MISMATCH</center>
    SynchronizeLateMessagesRound --> SelectKeeperTransactionSubmissionRoundB: <center>NONE</center>
    SynchronizeLateMessagesRound --> SynchronizeLateMessagesRound: <center>ROUND_TIMEOUT<br />NO_MAJORITY</center>
    ValidateSafeRound --> CheckSafeExistenceRound: <center>DONE</center>
    ValidateSafeRound --> RandomnessSafeRound: <center>NONE<br />NO_MAJORITY<br />VALIDATE_TIMEOUT<br />NEGATIVE</center>
    ValidateTransactionRound --> ResetAndPauseRound: <center>DONE</center>
    ValidateTransactionRound --> CheckTransactionHistoryRound: <center>NEGATIVE</center>
    ValidateTransactionRound --> SelectKeeperTransactionSubmissionRoundB: <center>NONE<br />VALIDATE_TIMEOUT</center>
    ValidateTransactionRound --> ValidateTransactionRound: <center>NO_MAJORITY</center>
</div>
<figcaption>Keep3rAbciApp FSM</figcaption>
</figure>

