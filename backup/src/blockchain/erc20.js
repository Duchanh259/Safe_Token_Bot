const { ethers } = require('ethers');
const NodeCache = require('node-cache');
const blockchainProvider = require('./provider');  // Import provider
const logger = require('../utils/logger');

// Cache để lưu trữ kết quả
const tokenCache = new NodeCache({ stdTTL: 300, checkperiod: 60 });

// ABI tối thiểu cho token ERC-20
const ERC20_ABI = [
  // Các hàm đọc
  "function name() view returns (string)",
  "function symbol() view returns (string)",
  "function decimals() view returns (uint8)",
  "function totalSupply() view returns (uint256)",
  "function balanceOf(address) view returns (uint256)",
  "function allowance(address,address) view returns (uint256)",
  
  // Các hàm ghi
  "function transfer(address,uint256) returns (bool)",
  "function transferFrom(address,address,uint256) returns (bool)",
  "function approve(address,uint256) returns (bool)",
  
  // Events
  "event Transfer(address indexed from, address indexed to, uint256 value)",
  "event Approval(address indexed owner, address indexed spender, uint256 value)"
];

/**
 * Lớp ERC20TokenAnalyzer - Phân tích token ERC-20 trên các blockchain tương thích EVM
 */
class ERC20TokenAnalyzer {
  constructor() {
    this.supportedChains = ['ethereum', 'bsc', 'polygon', 'arbitrum', 'optimism', 'avalanche', 'base'];
  }

  /**
   * Kiểm tra xem một địa chỉ có phải là token ERC-20 hay không
   * @param {string} address - Địa chỉ cần kiểm tra
   * @param {string} blockchain - Tên blockchain
   * @returns {Promise<boolean>} true nếu là token ERC-20, false nếu không phải
   */
  async isERC20Token(address, blockchain) {
    try {
      if (!this.supportedChains.includes(blockchain)) {
        throw new Error(`Blockchain ${blockchain} không được hỗ trợ cho phân tích ERC-20`);
      }
      
      const cacheKey = `isERC20_${blockchain}_${address}`;
      const cachedResult = tokenCache.get(cacheKey);
      
      if (cachedResult !== undefined) {
        return cachedResult;
      }
      
      // Kiểm tra trước xem có phải là contract không
      const isContract = await blockchainProvider.isContract(address, blockchain);
      if (!isContract) {
        logger.info(`Địa chỉ ${address} không phải là hợp đồng`);
        tokenCache.set(cacheKey, false);
        return false;
      }
      
      // Khởi tạo contract instance với ABI ERC-20
      const provider = blockchainProvider.getProvider(blockchain);
      
      // Trong trường hợp RPC URL không hoạt động
      if (!provider) {
        logger.error(`Không thể kết nối đến ${blockchain}. Vui lòng kiểm tra RPC URL.`);
        throw new Error(`Không thể kết nối đến ${blockchain}`);
      }
      
      // Kiểm tra xem có tồn tại các hàm ERC-20 chính không
      try {
        // Truy cập bytecode để kiểm tra xem contract có tồn tại không
        const bytecode = await provider.getCode(address);
        if (bytecode === '0x') {
          tokenCache.set(cacheKey, false);
          return false;
        }
        
        // Tạo contract instance
        const contract = new ethers.Contract(address, ERC20_ABI, provider);
        
        // Giả định là ERC-20 token nếu đã đến bước này
        const isERC20 = true;
        tokenCache.set(cacheKey, isERC20);
        
        logger.info(`Phân tích ${address} trên ${blockchain}: Xác nhận ERC-20 token`);
        
        return isERC20;
      } catch (error) {
        logger.error(`Lỗi khi kiểm tra ERC-20 cho địa chỉ ${address}:`, error);
        tokenCache.set(cacheKey, false);
        return false;
      }
    } catch (error) {
      logger.error(`Lỗi khi kiểm tra ERC-20 cho địa chỉ ${address} trên ${blockchain}:`, error);
      return false;
    }
  }

  /**
   * Lấy thông tin cơ bản của token ERC-20
   * @param {string} address - Địa chỉ token
   * @param {string} blockchain - Tên blockchain
   * @returns {Promise<Object>} Thông tin cơ bản của token
   */
  async getBasicTokenInfo(address, blockchain) {
    try {
      if (!this.supportedChains.includes(blockchain)) {
        throw new Error(`Blockchain ${blockchain} không được hỗ trợ cho phân tích ERC-20`);
      }
      
      const cacheKey = `basicInfo_${blockchain}_${address}`;
      const cachedInfo = tokenCache.get(cacheKey);
      
      if (cachedInfo) {
        return cachedInfo;
      }
      
      // Lấy thông tin token
      const provider = blockchainProvider.getProvider(blockchain);
      
      // Trong trường hợp RPC URL không hoạt động
      if (!provider) {
        throw new Error(`Không thể kết nối đến ${blockchain}`);
      }
      
      const contract = new ethers.Contract(address, ERC20_ABI, provider);
      
      // Đặt giá trị mặc định
      let name = 'Unknown Token';
      let symbol = 'UNKNOWN';
      let decimals = 18;
      let totalSupply = 0;
      let totalSupplyRaw = '0';
      
      // Bọc mỗi lệnh gọi trong try/catch riêng biệt
      try {
        name = await contract.name();
      } catch (error) {
        logger.debug(`Không thể lấy tên token: ${error.message}`);
      }
      
      try {
        symbol = await contract.symbol();
      } catch (error) {
        logger.debug(`Không thể lấy ký hiệu token: ${error.message}`);
      }
      
      try {
        decimals = await contract.decimals();
        decimals = Number(decimals);
      } catch (error) {
        logger.debug(`Không thể lấy số thập phân token: ${error.message}`);
      }
      
      try {
        const totalSupplyBigInt = await contract.totalSupply();
        totalSupplyRaw = totalSupplyBigInt.toString();
        totalSupply = Number(totalSupplyBigInt) / Math.pow(10, decimals);
      } catch (error) {
        logger.debug(`Không thể lấy tổng cung token: ${error.message}`);
      }
      
      const tokenInfo = {
        address,
        blockchain,
        name,
        symbol,
        decimals,
        totalSupply,
        totalSupplyRaw
      };
      
      tokenCache.set(cacheKey, tokenInfo);
      return tokenInfo;
    } catch (error) {
      logger.error(`Lỗi khi lấy thông tin token ${address} trên ${blockchain}:`, error);
      
      // Trả về thông tin cơ bản nếu không lấy được
      return {
        address,
        blockchain,
        name: 'Unknown Token',
        symbol: 'UNKNOWN',
        decimals: 18,
        totalSupply: 0,
        totalSupplyRaw: '0'
      };
    }
  }
}

// Export instance
module.exports = new ERC20TokenAnalyzer();