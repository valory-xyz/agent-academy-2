# Internal audit of agent-academy-2
The review has been performed based on the contract code in the following repository:<br>
`https://github.com/valory-xyz/agent-academy-2` <br>
commit: `v0.4.0` <br> 

## Objectives
The audit focused on `compensation` behavior. The audit is preliminary.

## Places that raised questions
### events loop
```python
    def _get_gas_spent(self) -> Generator[None, None, str]:
        # we start from the block the block in which the last withdraw event happened, or from the first block if we have
        # never withdrawn
        from_block = (
            0
            if latest_withdraw_event == self._NO_EVENT
            else latest_withdraw_event["block_number"]
        )
        # we end at the block in which the last unbonding event happened
        to_block = latest_unbonding_event["block_number"]
As I understand it, in this standard aglorhythm, 2 conditions must be met:
- Do not lose transactions. That is, all transactions were counted
- Do not count a transaction twice.
Typically a new "from" is previous "to"
In this case, "from" and "to" they move independently.
```

### Requires clarification of the logic of work.
```
def get_tx(self) -> Generator[None, None, str]:
        Required transactions to execute the swap and disburse:
        1. Withdraw the k3pr from the keep3r contract
        2. Approve the k3pr for the swap
        3. Swap the k3pr for eth
        4. Disburse the eth to the agents
i.e.
1. You take all available k3pr
2. Calculate how much you get ETH based on k3pr: dy = get_dy(dx), x - k3pr, y - eth
3. Swap all k3pr to ETH
4. Disburse ETH: if ETH > total_gas_spent_in_ETH for each agent => gas_spent + (ETH - total_gas_spent_in_ETH) * share_agent / len(agents)
5. go #1
Most likely this strategy is the simplest.
Alternative strategies are more complicated.
```

### Use use_eth in exchange
Ref: https://etherscan.io/address/0x21410232b484136404911780bc32756d5d1a9fa9#code#L728 <br>
Otherwise you will get back WETH tokes. Test please, on the testnet.

### min_dy too big
```python
def _get_swap_tx(
        self, pool_address: str, k3pr_amount: int, min_eth_amount: int
    ) -> Generator[None, None, Optional[Dict[str, Any]]]:
        """Swap tx."""
        contract_api_response = yield from self.get_contract_api_response(
            performative=ContractApiMessage.Performative.GET_STATE,
            contract_address=pool_address,
            contract_id=str(CurvePoolContract.contract_id),
            contract_callable="build_exchange_tx",
            dx=k3pr_amount,
            i=self._K3PR_INDEX,
            j=self._ETH_INDEX,
            min_dy=min_eth_amount,
        )
min_dy=min_eth_amount,
vs
https://curve.readthedocs.io/factory-pools.html
StableSwap.exchange(i: int128, j: int128, dx: uint256, min_dy: uint256, _receiver: address = msg.sender)→ uint256: nonpayable
Performs an exchange between two tokens.

Index values can be found using the coins public getter method, or get_coins within the factory contract.

i: Index value of the token to send.

j: Index value of the token to receive.

dx: The amount of i being exchanged.

min_dy: The minimum amount of j to receive. If the swap would result in less, the transaction will revert.

_receiver: An optional address that will receive j. If not given, defaults to the caller.

Returns the amount of j received in the exchange.

expected = pool.get_dy(0, 1, 10**18) * 0.99
pool.exchange(0, 1, 10**18, expected, {'from': alice})
```




