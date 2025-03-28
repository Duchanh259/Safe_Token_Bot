require('dotenv').config();

const config = {
  telegramToken: process.env.TELEGRAM_BOT_TOKEN,
  rpcUrls: {
  ethereum: process.env.ETH_RPC_URL || 'https://eth.llamarpc.com',  // Free fallback
  bsc: process.env.BSC_RPC_URL || 'https://bsc-dataseed1.binance.org',
  polygon: process.env.POLYGON_RPC_URL || 'https://polygon-rpc.com',
  arbitrum: process.env.ARB_RPC_URL || 'https://arb1.arbitrum.io/rpc',
  optimism: process.env.OP_RPC_URL || 'https://mainnet.optimism.io',
  avalanche: process.env.AVAX_RPC_URL || 'https://api.avax.network/ext/bc/C/rpc',
  base: process.env.BASE_RPC_URL || 'https://mainnet.base.org',
  solana: process.env.SOLANA_RPC_URL || 'https://api.mainnet-beta.solana.com',
  sui: process.env.SUI_RPC_URL || 'https://fullnode.mainnet.sui.io'
  },
  // Thêm thông tin hiển thị cho các blockchain
  blockchains: {
    ethereum: {
      name: 'Ethereum',
      symbol: 'ETH',
      icon: '🔷'
    },
    bsc: {
      name: 'Binance Smart Chain',
      symbol: 'BSC',
      icon: '🟡'
    },
    polygon: {
      name: 'Polygon',
      symbol: 'POL',
      icon: '🟣'
    },
    arbitrum: {
      name: 'Arbitrum',
      symbol: 'ARB',
      icon: '🔵'
    },
    optimism: {
      name: 'Optimism',
      symbol: 'OP',
      icon: '🔴'
    },
    avalanche: {
      name: 'Avalanche',
      symbol: 'AVAX',
      icon: '❄️'
    },
    base: {
      name: 'Base',
      symbol: 'BASE',
      icon: '🟢'
    },
    solana: {
      name: 'Solana',
      symbol: 'SOL',
      icon: '🟪'
    },
    sui: {
      name: 'Sui',
      symbol: 'SUI',
      icon: '🔘'
    }
  },
  email: {
    service: process.env.EMAIL_SERVICE,
    user: process.env.EMAIL_USER,
    pass: process.env.EMAIL_PASS
  },
  fees: {
    tokenCheck: 5, // USD
    referralRates: {
      level1: 5, // 5%
      level2: 1  // 1%
    }
  }
};

module.exports = config;