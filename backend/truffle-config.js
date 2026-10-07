module.exports = {
  networks: {
    development: {
      host: "127.0.0.1",     // Localhost (default)
      port: 7545,            // Standard Ganache GUI port (change to 8545 if using Ganache CLI)
      network_id: "*",       // Match any network id
    },
  },

  // Configure your compilers
  compilers: {
    solc: {
      version: "0.8.20",     // Matches the pragma version in your EduLocker.sol contract
      optimizer: {
        enabled: true,
        runs: 200
      }
    }
  },
};