// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

// Structure for voting escrow points
// The struct size is two storage slots of 2 * uint256 (128 + 128 + 64 + 64 + 128)
struct PointVoting {
  // w(i) = at + b (bias)
  int128 bias;

  // dw / dt = a (slope)
  int128 slope;
  // Timestamp. It will never practically be bigger than 2^64 - 1

  uint64 ts;
  // Block number. It will not be bigger than the timestamp
  uint64 blockNumber;

  // Token amount. It will never practically be bigger. Initial OLAS cap is 1 bn tokens, or 1e27.
  // After 10 years, the inflation rate is 2% per year. It would take 1340+ years to reach 2^128 - 1
  uint128 balance;
}
