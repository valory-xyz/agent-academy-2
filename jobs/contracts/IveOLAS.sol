// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;
import "./PointVoting.sol";

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

