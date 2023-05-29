# Release History - `agent-academy-2`

## (TBD)
- Bumps to `tomte@v0.2.12` and cleans up the repo #178

## v0.3.0 (22.05.2023)
- Add support for manually setting the gas limit via `manual_gas_limit`.
- Add 4-agent mainnet service.
- Collapse `IsWorkable` and `PerformWork` rounds.
- Add `propagateWorkable` to connext propagate job contract.
- Don't try to send a transaction with a failing simulation.
- Add support for unbonding the K3PR we get rewarded for woking jobs.
- Add gentle reset for recovery.

## v0.2.1 (03.04.2023)
- Add service termination.
- Add mint data for the components from the autonolas on-chain protocol.
- Renamed `keep3r_job` skill to `keep3r_job_abci`. 
- Remove `arbitrum` from yearn harvest job.

## v0.2.0 (31.03.2023)
- Add support for goerli.
- Add `PhutureHarvestingJobContract`.
- Add `veOLAS` job contract.
- Add support for flashbots.
- Add `YearnFactoryHarvestJob` contract.
- Add static call checks workable. 
- Add `ConnextPropagateJob`.

## v0.1.0 (16.02.2023)
The first release of the Keep3r service, configured to run on Ethereum Mainnet. 
