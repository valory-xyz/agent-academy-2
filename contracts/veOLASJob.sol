// SPDX-License-Identifier: MIT
pragma solidity >=0.8.4 <0.9.0;

import "@defi-wonderland/keep3r-v2/solidity/interfaces/IKeep3r.sol";


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

interface IVEOLAS {

  /// @dev Gets the total number of supply points.
  /// @return numPoints Number of supply points.
  function totalNumPoints() external view returns (uint256 numPoints);

  /// @dev Gets the supply point of a specified index.
  /// @param idx Supply point number.
  /// @return sPoint Supply point.
  function mapSupplyPoints(uint256 idx) external view returns (PointVoting memory sPoint);

  /// @dev Record global data to checkpoint.
  function checkpoint() external;
}

contract veOLASJob {
  error InvalidKeeper();
  error OnlyAutonolas();
  error NotWorkable();

  address public immutable keep3r;
  address public immutable veOLAS;
  address public immutable autonolasKeep3r;
  uint256 public constant dt = 600000;

  constructor(
    address _keep3r,
    address _veOLAS,
    address _autonolasKeep3r
  ) {
    keep3r = _keep3r;
    veOLAS = _veOLAS;
    autonolasKeep3r = _autonolasKeep3r;
  }

  /// @notice Checks if the contract is workable.
  function workable() external view returns (bool) {
    uint256 totalNumPoints = IVEOLAS(veOLAS).totalNumPoints();
    PointVoting memory sPoint = IVEOLAS(veOLAS).mapSupplyPoints(totalNumPoints);
    uint256 _dt = block.timestamp - sPoint.ts;
    return _dt >= dt;
  }

  /// @notice Calls checkpoint().
  function work() external {
    if (msg.sender != autonolasKeep3r) revert OnlyAutonolas();
    if (!IKeep3r(keep3r).isKeeper(msg.sender)) revert InvalidKeeper();
    if (!this.workable()) revert NotWorkable();
    IVEOLAS(veOLAS).checkpoint();
  }
}
