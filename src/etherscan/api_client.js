const axios = require('axios');
const NodeCache = require('node-cache');
const logger = require('../utils/logger');

// Cache để lưu trữ kết quả API
const apiCache = new NodeCache({ stdTTL: 600, checkperiod: 120 });

/**
 * Danh sách URL API cho các mạng được hỗ trợ
 */
const API_BASE_URLS = {
  ethereum: 'https://api.etherscan.io/api',
  bsc: 'https://api.bscscan.com/api',
  polygon: 'https://api.polygonscan.com/api',
  arbitrum: 'https://api.arbiscan.io/api',
  optimism: 'https://api.optimistic.etherscan.io/api',
  avalanche: 'https://api.snowtrace.io/api',
  base: 'https://api.basescan.org/api',
  // Solana và Sui không được Etherscan hỗ trợ
};

/**
 * Class EtherscanApiClient - Quản lý kết nối và gọi API đến các Etherscan APIs
 */
class EtherscanApiClient {
  constructor() {
    this.apiKeys = {
      ethereum: process.env.ETHERSCAN_API_KEY,
      bsc: process.env.BSCSCAN_API_KEY,
      polygon: process.env.POLYGONSCAN_API_KEY,
      arbitrum: process.env.ARBISCAN_API_KEY,
      optimism: process.env.OPTIMISM_API_KEY,
      avalanche: process.env.SNOWTRACE_API_KEY,
      base: process.env.BASESCAN_API_KEY,
    };
    
    this.supportedNetworks = Object.keys(API_BASE_URLS);
    this.initializeApiClients();
  }
  
  /**
   * Khởi tạo các API clients
   */
  initializeApiClients() {
    // Kiểm tra các API key đã cấu hình
    this.supportedNetworks.forEach(network => {
      if (this.apiKeys[network]) {
        logger.info(`API Etherscan đã cấu hình cho ${network}`);
      } else {
        logger.warn(`Thiếu API key cho ${network}, một số chức năng có thể bị giới hạn`);
      }
    });
  }
  
  /**
   * Kiểm tra xem một mạng có được hỗ trợ không
   * @param {string} network - Tên mạng blockchain
   */
  isNetworkSupported(network) {
    return this.supportedNetworks.includes(network);
  }
  
  /**
   * Lấy URL API cho một mạng
   * @param {string} network - Tên mạng blockchain
   */
  getApiBaseUrl(network) {
    if (!this.isNetworkSupported(network)) {
      throw new Error(`Mạng ${network} không được hỗ trợ bởi API Etherscan`);
    }
    
    return API_BASE_URLS[network];
  }
  
  /**
   * Lấy API key cho một mạng
   * @param {string} network - Tên mạng blockchain
   */
  getApiKey(network) {
    if (!this.isNetworkSupported(network)) {
      throw new Error(`Mạng ${network} không được hỗ trợ bởi API Etherscan`);
    }
    
    if (!this.apiKeys[network]) {
      logger.warn(`Thiếu API key cho ${network}, một số yêu cầu có thể bị giới hạn`);
    }
    
    return this.apiKeys[network] || '';
  }
  
  /**
   * Thực hiện gọi API với cache
   * @param {string} network - Tên mạng blockchain
   * @param {object} params - Tham số API
   * @param {string} cacheKey - Khóa cache (nếu không cung cấp, sẽ tự động tạo)
   */
  async callApi(network, params, cacheKey = null) {
    try {
      // Tạo cache key nếu không được cung cấp
      if (!cacheKey) {
        cacheKey = `${network}_${JSON.stringify(params)}`;
      }
      
      // Kiểm tra cache
      const cachedResult = apiCache.get(cacheKey);
      if (cachedResult) {
        return cachedResult;
      }
      
      // Lấy URL API và API key
      const baseUrl = this.getApiBaseUrl(network);
      const apiKey = this.getApiKey(network);
      
      // Thêm API key vào params
      const requestParams = { ...params, apikey: apiKey };
      
      // Gọi API
      const response = await axios.get(baseUrl, { params: requestParams });
      
      // Kiểm tra lỗi API
      if (response.data.status === '0' && response.data.message !== 'No transactions found') {
        throw new Error(`Lỗi API Etherscan: ${response.data.message}`);
      }
      
      // Lưu vào cache và trả về kết quả
      apiCache.set(cacheKey, response.data);
      return response.data;
    } catch (error) {
      logger.error(`Lỗi khi gọi API Etherscan (${network}):`, error);
      throw error;
    }
  }
  
  /**
   * Kiểm tra xem một địa chỉ có phải là contract hay không
   * @param {string} address - Địa chỉ cần kiểm tra
   * @param {string} network - Tên mạng blockchain
   */
  async isContract(address, network) {
    try {
      const cacheKey = `isContract_${network}_${address}`;
      
      // Kiểm tra cache
      const cachedResult = apiCache.get(cacheKey);
      if (cachedResult !== undefined) {
        return cachedResult;
      }
      
      // Gọi API để lấy bytecode
      const response = await this.callApi(network, {
        module: 'proxy',
        action: 'eth_getCode',
        address: address,
        tag: 'latest'
      });
      
      // Nếu bytecode khác '0x', đây là contract
      const isContract = response.result !== '0x';
      
      // Lưu vào cache và trả về kết quả
      apiCache.set(cacheKey, isContract);
      return isContract;
    } catch (error) {
      logger.error(`Lỗi khi kiểm tra contract (${address}, ${network}):`, error);
      return false;
    }
  }
  
  /**
   * Lấy thông tin token
   * @param {string} address - Địa chỉ token
   * @param {string} network - Tên mạng blockchain
   */
  async getTokenInfo(address, network) {
    try {
      // Gọi API để lấy thông tin token
      const response = await this.callApi(network, {
        module: 'token',
        action: 'tokeninfo',
        contractaddress: address
      }, `tokenInfo_${network}_${address}`);
      
      if (response.status === '0') {
        if (response.message === 'No token found') {
          return null;
        }
        throw new Error(`Lỗi khi lấy thông tin token: ${response.message}`);
      }
      
      return response.result[0];
    } catch (error) {
      logger.error(`Lỗi khi lấy thông tin token (${address}, ${network}):`, error);
      return null;
    }
  }
  
  /**
   * Lấy mã nguồn và ABI của contract
   * @param {string} address - Địa chỉ contract
   * @param {string} network - Tên mạng blockchain
   */
  async getContractSourceCode(address, network) {
    try {
      // Gọi API để lấy mã nguồn
      const response = await this.callApi(network, {
        module: 'contract',
        action: 'getsourcecode',
        address: address
      }, `sourceCode_${network}_${address}`);
      
      return response.result[0];
    } catch (error) {
      logger.error(`Lỗi khi lấy mã nguồn (${address}, ${network}):`, error);
      return {
        SourceCode: '',
        ABI: 'Contract source code not verified',
        ContractName: 'Unknown',
        Implementation: '',
        Proxy: '0'
      };
    }
  }
  
  /**
   * Lấy danh sách người giữ token
   * @param {string} address - Địa chỉ token
   * @param {string} network - Tên mạng blockchain
   * @param {number} page - Trang (mặc định: 1)
   * @param {number} offset - Số lượng kết quả mỗi trang (mặc định: 10)
   */
  async getTokenHolders(address, network, page = 1, offset = 10) {
    try {
      // Gọi API để lấy danh sách người giữ token
      const response = await this.callApi(network, {
        module: 'token',
        action: 'tokenholderlist',
        contractaddress: address,
        page: page,
        offset: offset
      }, `tokenHolders_${network}_${address}_${page}_${offset}`);
      
      if (response.status === '0' && !response.result) {
        return [];
      }
      
      return response.result;
    } catch (error) {
      logger.error(`Lỗi khi lấy danh sách người giữ token (${address}, ${network}):`, error);
      return [];
    }
  }
}

// Export instance
module.exports = new EtherscanApiClient();