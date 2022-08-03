

## Creating jobs

An owner can create jobs in 2 ways:

1. Submit a proposal via governance to include the contract as a Job by calling the function `addJob` within the 
   [`Keep3rJobManager` contract](https://github.com/keep3r-network/keep3r-network-v2/blob/main/solidity/contracts/peripherals/jobs/Keep3rJobManager.sol). 
   Adding a job to the network is permissionless, the job address of the contract for which work should be performed is 
   the only requirement. 
   The sender of the `addJob` transaction will be the owner of the job.

2. Submit a job via adding liquidity. 
   The owner will need to provide liquidity to one of the approved liquidity pairs (for example KPR-ETH). 
   You put your LP tokens in escrow and receive credit. 
   When the credit is used up, the owner can simply withdraw the LP tokens. 
   They will receive 100% of the LP tokens back that they deposited. 
   This is achieved by calling the addLiquidityToJob function within the 
   [`IKeep3rJobFundableLiquidity` contract](https://github.com/keep3r-network/keep3r-network-v2/blob/main/solidity/interfaces/peripherals/IKeep3rJobs.sol#L69)


## Managing Credit and Payments

Jobs require credit to be able to pay keepers to perform their work. 
This credit can either be paid for directly, or by being a liquidity provider in the system. 
If the owner pays directly, this is a direct expense. 
If the owner is a liquidity provider, they get all their liquidity back after they are done being a provider. The framework provides functions for adding liquidity, removing liquidity, and adding credit (ETH and non-ETH) through the contract IKeep3rV1 keep3r-network-v2/solidity/interfaces/external/IKeep3rV1.sol

There are three primary mechanisms to pay Keepers and these are based on the credit provided:
- Pay via liquidity provided tokens (based on addLiquidityToJob)
- Pay in direct ETH (based on addCreditETH)
- Pay in direct token (based on addCredit)


## Job Interface

A Keep3r job needs to provide two methods for determining if the Job is workable (i.e., if it can be executed) 
and what is the actual work to do.
The keeper agent is responsible for determining if the job is profitable for them. 
The framework classifies jobs into low-or-no risk, and risk jobs:
- Low risk jobs, which require only verification of registration to the network via the smart contract before 
  executing of work may commence.
- High risk jobs, where the job owner may require that the keeper has a minimum bond and/or a track record, 
  for example comprising a minimum number of jobs completed, a minimum keeper age, and so on.

The job contract interface 
