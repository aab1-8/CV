export default {
    solidity: {
        version: "0.8.20",
        settings: {
            optimizer: {
                enabled: true,
                runs: 200,
            },
        },
    },
    networks: {
        ganache: {
            url: "http://127.0.0.1:8546",
        }
    },
    paths: {
        sources: "./contracts",
        artifacts: "./artifacts"
    }
};
