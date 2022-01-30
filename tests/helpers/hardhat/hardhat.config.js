/**
 * @type import('hardhat/config').HardhatUserConfig
 */

networks_address = {
    "mainnet": "https://eth-mainnet.alchemyapi.io/v2/",
    "ropsten": "https://eth-ropsten.alchemyapi.io/v2/",
    "rinkeby": "https://eth-rinkeby.alchemyapi.io/v2/"
}

module.exports = {
    defaultNetwork: 'hardhat',
    networks: {
        hardhat: {
            forking: {
                url: `${networks_address[process.env.NETWORK.toLowerCase()]}${process.env.KEY}`,
                blockNumber: parseInt(process.env.BLOCK_NUMBER)
            },
        },
        localhost: {}
    }
};

