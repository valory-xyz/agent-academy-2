// SPDX-License-Identifier: MIT
pragma solidity >=0.8.4 <0.9.0;

import "@defi-wonderland/keep3r-v2/solidity/interfaces/IKeep3r.sol";


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
