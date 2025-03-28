const etherscanApi = require('./api_client');
const tokenAnalyzer = require('./token_analyzer');
const logger = require('../utils/logger');
const NodeCache = require('node-cache');

// Cache để lưu trữ kết quả phân tích
const advancedCache = new NodeCache({ stdTTL: 600, checkperiod: 120 });

/**
 * Class AdvancedTokenAnalyzer - Phân tích nâng cao token bằng Etherscan API
 */
class AdvancedTokenAnalyzer {
  constructor() {
    this.tokenAnalyzer = tokenAnalyzer;
  }
  
  /**
   * Phân tích token nâng cao
   * @param {string} address - Địa chỉ token
   * @param {string} network - Tên mạng blockchain
   */
  async analyzeTokenAdvanced(address, network) {
    try {
      // Kiểm tra cache
      const cacheKey = `advancedAnalysis_${network}_${address}`;
      const cachedAnalysis = advancedCache.get(cacheKey);
      if (cachedAnalysis) {
        return cachedAnalysis;
      }
      
      // Lấy phân tích cơ bản trước
      const basicAnalysis = await this.tokenAnalyzer.analyzeToken(address, network);
      
      // Lấy thêm thông tin về giao dịch gần đây
      const recentTransactions = await this.getRecentTransactions(address, network);
      
      // Phân tích lưu lượng giao dịch
      const liquidityAnalysis = await this.analyzeLiquidity(address, network);
      
      // Phân tích phân phối token
      const distributionAnalysis = await this.analyzeTokenDistribution(address, network);
      
      // Tổng hợp kết quả phân tích nâng cao
      const advancedAnalysis = {
        ...basicAnalysis,
        recentTransactions,
        liquidityAnalysis,
        distributionAnalysis,
        socialMetrics: await this.getSocialMetrics(address, network)
      };
      
      // Lưu vào cache và trả về kết quả
      advancedCache.set(cacheKey, advancedAnalysis);
      return advancedAnalysis;
    } catch (error) {
      logger.error(`Lỗi khi phân tích nâng cao token (${address}, ${network}):`, error);
      // Trả về phân tích cơ bản nếu có lỗi
      return this.tokenAnalyzer.analyzeToken(address, network);
    }
  }
  
  /**
   * Lấy các giao dịch gần đây
   * @param {string} address - Địa chỉ token
   * @param {string} network - Tên mạng blockchain
   */
  async getRecentTransactions(address, network) {
    try {
      // Gọi API để lấy giao dịch gần đây
      const response = await etherscanApi.callApi(network, {
        module: 'account',
        action: 'tokentx',
        contractaddress: address,
        page: 1,
        offset: 10,
        sort: 'desc'
      });
      
      if (response.status === '0' && response.message === 'No transactions found') {
        return [];
      }
      
      return response.result.map(tx => ({
        hash: tx.hash,
        from: tx.from,
        to: tx.to,
        value: tx.value,
        timestamp: tx.timeStamp
      }));
    } catch (error) {
      logger.error(`Lỗi khi lấy giao dịch gần đây (${address}, ${network}):`, error);
      return [];
    }
  }
  
  /**
   * Phân tích thanh khoản
   * @param {string} address - Địa chỉ token
   * @param {string} network - Tên mạng blockchain
   */
  async analyzeLiquidity(address, network) {
    // Đây là phương thức giả để mở rộng sau này
    // Trong triển khai thực tế, bạn sẽ cần phân tích các DEX và pool thanh khoản
    return {
      hasLiquidity: true,
      liquidityLocked: true,
      liquidityAmount: 'Unknown',
      lockPeriod: 'Unknown'
    };
  }
  
  /**
   * Phân tích phân phối token
   * @param {string} address - Địa chỉ token
   * @param {string} network - Tên mạng blockchain
   */
  async analyzeTokenDistribution(address, network) {
    try {
      // Lấy danh sách người giữ token
      const holders = await etherscanApi.getTokenHolders(address, network, 1, 50);
      
      if (!holders || holders.length === 0) {
        return {
          totalHolders: 0,
          topHolderPercentage: 0,
          top10HolderPercentage: 0,
          distribution: 'Unknown'
        };
      }
      
      // Tính toán thống kê phân phối
      const topHolder = holders[0];
      const top10HolderPercentage = holders.slice(0, 10).reduce((sum, holder) => sum + parseFloat(holder.share || 0), 0);
      
      let distribution = 'Balanced';
      if (top10HolderPercentage > 80) {
        distribution = 'Highly Concentrated';
      } else if (top10HolderPercentage > 50) {
        distribution = 'Moderately Concentrated';
      }
      
      return {
        totalHolders: holders.length,
        topHolderPercentage: parseFloat(topHolder.share || 0),
        top10HolderPercentage,
        distribution
      };
    } catch (error) {
      logger.error(`Lỗi khi phân tích phân phối token (${address}, ${network}):`, error);
      return {
        totalHolders: 0,
        topHolderPercentage: 0,
        top10HolderPercentage: 0,
        distribution: 'Unknown'
      };
    }
  }
  
  /**
   * Lấy số liệu xã hội về token
   * @param {string} address - Địa chỉ token
   * @param {string} network - Tên mạng blockchain
   */
  async getSocialMetrics(address, network) {
    // Đây là phương thức giả để mở rộng sau này
    // Trong triển khai thực tế, bạn có thể tích hợp với các API xã hội
    return {
      twitterFollowers: 'Unknown',
      telegramMembers: 'Unknown',
      discordMembers: 'Unknown'
    };
  }
}

// Export instance
module.exports = new AdvancedTokenAnalyzer();