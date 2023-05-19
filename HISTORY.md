# Release History - `agent-academy-2`

## v0.3.0 (19.05.2023)
- Add `manual_gas_limit`.
- Add 4-agent mainnet service.
- Collapse IsWorkable and PerformWork rounds.
- Add `propagateWorkable` to connext propagate job contract.
- Dont try to send a tx with failing sim.
- Add unbonding round.
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
