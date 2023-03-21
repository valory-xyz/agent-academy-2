import { ethers } from "hardhat";

async function main() {
  const keep3rAddress = process.env.KEEP3R_ADDRESS;
  const veOLASAddress =  process.env.VEOLAS_ADDRESS
  const autonolasAddress = process.env.AUTONOLAS_ADDRESS;

  if (!keep3rAddress || !veOLASAddress || !autonolasAddress) {
    throw new Error("KEEP3R_ADDRESS, VEOLAS_ADDRESS and AUTONOLAS_ADDRESS are required!");
  }

  // We get the contract to deploy
  const VeOLASJob = await ethers.getContractFactory("veOLASJob");
  const veOLASJob = await VeOLASJob.deploy(keep3rAddress, veOLASAddress, autonolasAddress);
  await veOLASJob.deployed();

  console.log(`veOLASJob: ${veOLASJob.address}`);

  const keep3r = await ethers.getContractAt("Keep3r", keep3rAddress);
  await keep3r.addJob(veOLASJob.address);

  console.log("Success");
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
