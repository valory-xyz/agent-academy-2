

## The challenge: end-to-end decentralisation

Smart contracts are a highly secure form of digital agreement encoded into a computer program that is hosted on a
blockchain. 
They are an essential building block for more sophisticated applications, which led to the emergence of novel
niches ranging from decentralized finance (DeFi) and insurance products to non-fungible tokens (NFTs) and 
gaming metaverses. 
Their code specifies the prerequisite conditions for execution of their functionality, which can be invoked by users
through method calls.

However, smart contracts have a limitation, which is that they are purely reactive by design. 
That is to say, they cannot execute their own functions periodically or when a predefined condition is met. 
Instead, they rely on a third party to trigger their execution, whom they incentivize to do so by offering a reward. 
This results in a system where developers and users are tasked to monitor and intervene in the process. 
One way this can be addressed is through DevOps automation, however the use of centralized infrastructure brings along 
all the drawbacks and risks that decentralized ledger technologies are trying to resolve: in leads to loss of 
fault-tolerance by introducing central points of operation that make the system prone to adversarial exploit.
Smart contracts alone therefore do simply not allow developers to build fully automated application that 
are decentralized from end-to-end.


## The solution: a Keeper Network

A solution to this problem is offered by the keeper system, a network of agents that together form a decentralized 
system that can perform the execution of smart contract functionality in a reliable, trustless and cost-efficient way. 
The [open-autonomy framework](https://docs.autonolas.network/) provides developers with the necessary tools to
design and build an agent service that implements this functionality using finite state machines.
The keeper system implemented here with the use of this framework is operated by 
[Autonomous Economic Agents](https://valory-xyz.github.io/open-aea/) (AEAs), which possess the full range of 
capabilities required to perform the necessary tasks. 
They are capable of acting proactively, executing behaviour periodically as time progresses, when specific events 
unfold, based on detection of changes in their environment, or any more intricate combination of the former logic.
The keeper system runs on off-chain infrastructure, which enables almost arbitrarily complex computation that is 
unrestricted by storage space of the blockchain and neither prohibited by expensive on-chain transaction fees. 
This enables its users, be it an individual developer, another application or a decentralized autonomous organization 
(DAO), to perform DevOps jobs in a permissionless, secure and fully-automated manner.


## Useful documentation and resources

https://docs.autonolas.network/
https://valory-xyz.github.io/open-aea/
https://keep3r.live/
https://keep3r.network/
https://docs.keep3r.network/
https://github.com/keep3r-network/cli/blob/main/README.md
https://docs.openzeppelin.com/defender/guide-keep3r
https://github.com/keep3r-network/cli
https://github.com/keep3r-network/cli-sample-jobs
https://docs.chain.link/docs/chainlink-keepers/introduction/
