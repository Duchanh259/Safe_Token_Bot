const { ethers } = require('ethers');
const { Web3 } = require('web3');
const NodeCache = require('node-cache');
const config = require('../config/config');
const logger = require('../utils/logger');

// Cache để lưu trữ các provider và kết quả truy vấn
const providerCache = new NodeCache({ stdTTL: 600, checkperiod: 120 });
const resultCache = new NodeCache({ stdTTL: 300, checkperiod: 60 });

class BlockchainProvider {
  constructor() {
    this.providers = {};
    this.web3Instances = {};
    this.initializeProviders();
  }

  initializeProviders() {
    try {
      // Khởi tạo các provider cho blockchain tương thích EVM
      const evmBlockchains = ['ethereum', 'bsc', 'polygon', 'arbitrum', 'optimism', 'avalanche', 'base'];
      
      evmBlockchains.forEach(chain => {
        if (config.rpcUrls[chain]) {
          try {
            this.providers[chain] = new ethers.JsonRpcProvider(config.rpcUrls[chain]);
            this.web3Instances[chain] = new Web3(config.rpcUrls[chain]);
            logger.info(`Khởi tạo kết nối thành công đến ${chain}`);
          } catch (error) {
            logger.error(`Lỗi khi khởi tạo kết nối đến ${chain}:`, error);
          }
        }
      });
      
      logger.info('Khởi tạo các provider blockchain thành công');
    } catch (error) {
      logger.error('Lỗi khi khởi tạo các provider blockchain:', error);
    }
  }

  getProvider(blockchain) {
    // Kiểm tra cache trước
    const cacheKey = `provider_${blockchain}`;
    const cachedProvider = providerCache.get(cacheKey);
    
    if (cachedProvider) {
      return cachedProvider;
    }
    
    // Nếu không có trong cache, tạo mới
    if (!this.providers[blockchain]) {
      if (!config.rpcUrls[blockchain]) {
        throw new Error(`Không hỗ trợ blockchain ${blockchain}`);
      }
      
      try {
        if (['solana', 'sui'].includes(blockchain)) {
          // Xử lý đặc biệt cho Solana và Sui
          logger.warn(`Blockchain ${blockchain} chưa được hỗ trợ đầy đủ`);
          return null;
        } else {
          // Blockchain tương thích EVM
          this.providers[blockchain] = new ethers.JsonRpcProvider(config.rpcUrls[blockchain]);
          this.web3Instances[blockchain] = new Web3(config.rpcUrls[blockchain]);
        }
      } catch (error) {
        logger.error(`Lỗi khi tạo provider cho ${blockchain}:`, error);
        throw error;
      }
    }
    
    // Lưu vào cache và trả về
    providerCache.set(cacheKey, this.providers[blockchain]);
    return this.providers[blockchain];
  }

  getWeb3(blockchain) {
    // Kiểm tra cache trước
    const cacheKey = `web3_${blockchain}`;
    const cachedWeb3 = providerCache.get(cacheKey);
    
    if (cachedWeb3) {
      return cachedWeb3;
    }
    
    // Nếu không có trong cache, tạo mới
    if (!this.web3Instances[blockchain]) {
      if (!config.rpcUrls[blockchain]) {
        throw new Error(`Không hỗ trợ blockchain ${blockchain}`);
      }
      
      try {
        if (['solana', 'sui'].includes(blockchain)) {
          // Xử lý đặc biệt cho Solana và Sui
          logger.warn(`Blockchain ${blockchain} chưa được hỗ trợ đầy đủ`);
          return null;
        } else {
          // Blockchain tương thích EVM
          this.web3Instances[blockchain] = new Web3(config.rpcUrls[blockchain]);
        }
      } catch (error) {
        logger.error(`Lỗi khi tạo Web3 instance cho ${blockchain}:`, error);
        throw error;
      }
    }
    
    // Lưu vào cache và trả về
    providerCache.set(cacheKey, this.web3Instances[blockchain]);
    return this.web3Instances[blockchain];
  }

  async isContract(address, blockchain) {
    try {
      const cacheKey = `isContract_${blockchain}_${address}`;
      const cachedResult = resultCache.get(cacheKey);
      
      if (cachedResult !== undefined) {
        return cachedResult;
      }
      
      const provider = this.getProvider(blockchain);
      if (!provider) {
        throw new Error(`Không thể lấy provider cho ${blockchain}`);
      }
      
      const code = await provider.getCode(address);
      const isContract = code !== '0x';
      
      resultCache.set(cacheKey, isContract);
      return isContract;
    } catch (error) {
      logger.error(`Lỗi khi kiểm tra địa chỉ ${address} trên ${blockchain}:`, error);
      throw error;
    }
  }

  async getContractBytecode(address, blockchain) {
    try {
      const cacheKey = `bytecode_${blockchain}_${address}`;
      const cachedBytecode = resultCache.get(cacheKey);
      
      if (cachedBytecode) {
        return cachedBytecode;
      }
      
      const provider = this.getProvider(blockchain);
      if (!provider) {
        throw new Error(`Không thể lấy provider cho ${blockchain}`);
      }
      
      const bytecode = await provider.getCode(address);
      resultCache.set(cacheKey, bytecode);
      
      return bytecode;
    } catch (error) {
      logger.error(`Lỗi khi lấy bytecode của địa chỉ ${address} trên ${blockchain}:`, error);
      throw error;
    }
  }
}

// Đây là phần quan trọng - tạo và export một instance
const provider = new BlockchainProvider();

// Export object, không phải class
module.exports = provider;