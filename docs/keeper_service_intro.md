

## Introduction

This keeper network is built using the [open-aea](https://open-aea.docs.autonolas.tech/) 
and [open-autonomy](https://docs.autonolas.network) frameworks.
We suggest new developers to read this documentation to get started.


## What is the keeper network?

The Keeper network is a decentralized DevOps platform where job posters and those willing to perform these jobs can 
exchange goods for services. 
Keepers are agents that execute the tasks required to complete specific types of job.
These jobs can range widely in terms of complexity; ranging from the automation of simple smart contract calls, such
as yield harvesting, to jobs that involve multi-party computation for increased cryptographic security or complex
machine learning tasks that cannot be performed on-chain.  


## Why use a Keepers network?

Currently, the need for human intervention - or alternatively automation using centralized operators - poses a 
limitation in the development of fully decentralized applications. 
Providing an end-to-end guarantee on how applications functions requires computation that smart contracts 
cannot perform. 
The keeper network offers a solution by integrating decentralized off-chain computation, allowing for 
process automation that is highly reliable and cryptographically secured.

Q: Why does trust minimized off-chain computation matter?
A: The system and services need to be reliable under all circumstances. That is to say, regardless of network 
congestion and gas prices, regardless of server failures and regardless of adverserial DDOS attacks or 
malicious actors attempting to exploit the system in any way.

Reasons: 
- automation
- smart contracts cannot do it
- too expensive to do on-chain
- privacy reasons
- integration of dynamic off-chain input signal

Examples:
monitoring, limit order execution, staking and fee distributions, yield farming, smart contract DevOps requests, 
liquidations, dynamic NFTs




The original Keep3r system - as devised by Andre Cronje - had an online auctioning mechanism, which led to 
what is referred to as [gas wars](https://coinmarketcap.com/alexandria/article/3-minute-tips-what-are-gas-wars).
The competition for jobs led to a system where less successful bots would be outcompeted and stop participating,
leading to a winner-takes-all scenario.
This centralization led to loss of fault tolerance in the system; inevitably the winning bot would fall over and 
nothing would happen.

The Open Autonomy framework offers a solution to this problem: 
an off-chain keeper system with an off-chain auctioning mechanism.
Because the autonomous economic agents must achieve consensus in order for the system to progress, 
this necessitates cooperation within the application. 
That is to say that a single agent cannot outfox the others; only as a collective can they succeed.
This effectively prevents perverse economic incentives that lead to gas wars.



## How does the Keeper network function?

It can execute, at minimal cost, code that was deployed on-chain and whose computation can therefor be verified by 
anyone. 
A keeper network is contract specific; it is committed to only compute code for a specific contract which provides
cryptographic assurances and transparency

