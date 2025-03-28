const { ethers } = require('ethers');
const NodeCache = require('node-cache');
const blockchainProvider = require('../blockchain/provider');
const erc20Analyzer = require('../blockchain/erc20');
const logger = require('../utils/logger');

// Cache để lưu trữ kết quả phân tích
const securityCache = new NodeCache({ stdTTL: 300, checkperiod: 60 });

// ABI mở rộng để phát hiện các chức năng nguy hiểm
const EXTENDED_ABI = [
  // Hàm mint
  "function mint(address,uint256) returns (bool)",
  "function mint(uint256) returns (bool)",
  "function mintToken(address,uint256) returns (bool)",
  
  // Hàm blacklist
  "function addToBlacklist(address) returns (bool)",
  "function removeFromBlacklist(address) returns (bool)",
  "function isBlacklisted(address) view returns (bool)",
  
  // Hàm pause
  "function pause() returns (bool)",
  "function unpause() returns (bool)",
  "function paused() view returns (bool)",
  
  // Hàm freeze
  "function freeze(address) returns (bool)",
  "function unfreeze(address) returns (bool)",
  "function freezeAccount(address) returns (bool)",
  
  // Hàm ownership
  "function owner() view returns (address)",
  "function transferOwnership(address) returns (bool)",
  "function renounceOwnership() returns (bool)",
  
  // Hàm fee/tax
  "function setTaxFee(uint256) returns (bool)",
  "function getTaxFee() view returns (uint256)",
  "function excludeFromFee(address) returns (bool)",
  "function includeInFee(address) returns (bool)",
  
  // Events
  "event OwnershipTransferred(address indexed previousOwner, address indexed newOwner)"
];

/**
 * Lớp TokenSecurityAnalyzer - Phân tích bảo mật token
 */
class TokenSecurityAnalyzer {
  constructor() {
    this.supportedChains = ['ethereum', 'bsc', 'polygon', 'arbitrum', 'optimism', 'avalanche', 'base'];
  }

  /**
   * Phân tích bảo mật của một token
   * @param {string} address - Địa chỉ token
   * @param {string} blockchain - Tên blockchain
   * @returns {Promise<Object>} Kết quả phân tích bảo mật
   */
  async analyzeTokenSecurity(address, blockchain) {
    try {
      if (!this.supportedChains.includes(blockchain)) {
        throw new Error(`Blockchain ${blockchain} không được hỗ trợ cho phân tích bảo mật`);
      }
      
      const cacheKey = `securityAnalysis_${blockchain}_${address}`;
      const cachedAnalysis = securityCache.get(cacheKey);
      
      if (cachedAnalysis) {
        return cachedAnalysis;
      }
      
      // Kiểm tra xem địa chỉ có phải là hợp đồng không
      let isContract = false;
      try {
        isContract = await blockchainProvider.isContract(address, blockchain);
        if (!isContract) {
          throw new Error(`Địa chỉ ${address} không phải là hợp đồng`);
        }
      } catch (error) {
        logger.error(`Lỗi khi kiểm tra contract: ${error.message}`);
        throw new Error(`Không thể xác minh địa chỉ ${address} là hợp đồng hợp lệ`);
      }
      
      let basicInfo;
      let isERC20 = false;
      
      try {
        // Kiểm tra nếu là ERC-20
        isERC20 = await erc20Analyzer.isERC20Token(address, blockchain);
        
        // Ngay cả khi không phải ERC-20 hoàn chỉnh, vẫn thử lấy thông tin cơ bản
        basicInfo = await erc20Analyzer.getBasicTokenInfo(address, blockchain);
      } catch (error) {
        logger.error(`Lỗi khi phân tích ERC-20: ${error.message}`);
        // Nếu không lấy được thông tin ERC-20, vẫn tiếp tục với thông tin cơ bản
        basicInfo = {
          address,
          blockchain,
          name: 'Unknown Token',
          symbol: 'UNKNOWN',
          decimals: 18,
          totalSupply: 0,
          totalSupplyRaw: '0'
        };
      }
      
      // Phân tích mã bytecode của contract
      let bytecode = '0x';
      try {
        bytecode = await blockchainProvider.getContractBytecode(address, blockchain);
      } catch (error) {
        logger.error(`Lỗi khi lấy bytecode: ${error.message}`);
        // Tiếp tục với bytecode trống
      }
      
      // Kết nối đến contract với ABI mở rộng
      const provider = blockchainProvider.getProvider(blockchain);
      const contract = new ethers.Contract(address, [...EXTENDED_ABI], provider);
      
      // Kết quả phân tích
      const securityAnalysis = {
        ...basicInfo,
        isERC20,
        securityIssues: [],
        hasMintFunction: false,
        hasBlacklistFunction: false,
        hasPauseFunction: false,
        hasFreezeFunction: false,
        ownershipRenounced: false,
        hasTaxFee: false,
        isHoneypot: false,
        owner: null,
        riskLevel: 'UNKNOWN' // LOW, MEDIUM, HIGH, CRITICAL, UNKNOWN
      };
      
      // Phân tích các hàm nguy hiểm dựa trên bytecode
      this.checkDangerousFunctionsByBytecode(securityAnalysis, bytecode);
      
      // Cố gắng phân tích ownership
      try {
        await this.checkOwnership(contract, securityAnalysis);
      } catch (error) {
        logger.error(`Lỗi khi kiểm tra ownership: ${error.message}`);
        // Tiếp tục nếu không phân tích được ownership
      }
      
      // Đánh giá mức độ rủi ro
      this.assessRiskLevel(securityAnalysis);
      
      // Lưu kết quả vào cache
      securityCache.set(cacheKey, securityAnalysis);
      
      return securityAnalysis;
    } catch (error) {
      logger.error(`Lỗi khi phân tích bảo mật token ${address} trên ${blockchain}:`, error);
      throw error;
    }
  }

  /**
   * Phân tích các hàm nguy hiểm dựa trên bytecode
   * @param {Object} analysis - Kết quả phân tích
   * @param {string} bytecode - Bytecode của contract
   */
  checkDangerousFunctionsByBytecode(analysis, bytecode) {
    // Chuyển bytecode sang lowercase để dễ tìm kiếm
    const bytecodeLC = bytecode.toLowerCase();
    
    // Kiểm tra hàm mint
    if (bytecodeLC.includes('mint') || bytecodeLC.includes('40c10f19')) { // Signature của mint(address,uint256)
      analysis.hasMintFunction = true;
      analysis.securityIssues.push('Token có hàm mint - cấp phát thêm token');
    }
    
    // Kiểm tra hàm blacklist
    if (bytecodeLC.includes('blacklist') || bytecodeLC.includes('banned') || bytecodeLC.includes('blocklist')) {
      analysis.hasBlacklistFunction = true;
      analysis.securityIssues.push('Token có hàm blacklist - chặn các địa chỉ');
    }
    
    // Kiểm tra hàm freeze
    if (bytecodeLC.includes('freeze') || bytecodeLC.includes('frozen')) {
      analysis.hasFreezeFunction = true;
      analysis.securityIssues.push('Token có hàm freeze - đóng băng giao dịch');
    }
    
    // Kiểm tra hàm pause
    if (bytecodeLC.includes('pause') || bytecodeLC.includes('paused')) {
      analysis.hasPauseFunction = true;
      analysis.securityIssues.push('Token có hàm pause - tạm dừng giao dịch');
    }
    
    // Kiểm tra phí giao dịch (tax)
    if (bytecodeLC.includes('fee') || bytecodeLC.includes('tax')) {
      analysis.hasTaxFee = true;
      analysis.securityIssues.push('Token có cơ chế tính phí giao dịch');
    }
    
    // Phát hiện honeypot
    if (
      bytecodeLC.includes('onlybuy') || 
      bytecodeLC.includes('cannotsell') || 
      bytecodeLC.includes('disableselling') || 
      bytecodeLC.includes('preventsell') ||
      (bytecodeLC.includes('onlyowner') && bytecodeLC.includes('sell'))
    ) {
      analysis.isHoneypot = true;
      analysis.securityIssues.push('Token có thể là honeypot - không thể bán sau khi mua');
      analysis.riskLevel = 'CRITICAL';
    }
  }

  /**
   * Kiểm tra vấn đề về ownership của contract
   * @param {ethers.Contract} contract - Contract instance
   * @param {Object} analysis - Kết quả phân tích
   */
  async checkOwnership(contract, analysis) {
    try {
      // Kiểm tra owner hiện tại
      try {
        const owner = await contract.owner();
        
        // Kiểm tra xem owner có phải là zero address không
        if (
          owner === '0x0000000000000000000000000000000000000000' || 
          owner.toLowerCase() === '0x0000000000000000000000000000000000000000' ||
          owner === '0x000000000000000000000000000000000000dEaD' ||
          owner.toLowerCase() === '0x000000000000000000000000000000000000dead'
        ) {
          analysis.ownershipRenounced = true;
        } else {
          analysis.owner = owner;
          analysis.securityIssues.push('Token có owner - có thể có rủi ro nếu owner có quyền lớn');
        }
      } catch (error) {
        // Không có hàm owner hoặc hàm không thể gọi được
        logger.debug(`Không thể kiểm tra owner của token: ${error.message}`);
      }
    } catch (error) {
      logger.error(`Lỗi khi kiểm tra ownership:`, error);
    }
  }

  /**
   * Đánh giá mức độ rủi ro của token
   * @param {Object} analysis - Kết quả phân tích
   */
  assessRiskLevel(analysis) {
    let score = 0;
    
    // Tính điểm rủi ro
    if (analysis.isHoneypot) {
      score += 100; // Rủi ro cao nhất
    }
    
    if (analysis.hasMintFunction && !analysis.ownershipRenounced) {
      score += 30;
    }
    
    if (analysis.hasBlacklistFunction) {
      score += 25;
    }
    
    if (analysis.hasFreezeFunction) {
      score += 25;
    }
    
    if (analysis.hasPauseFunction) {
      score += 20;
    }
    
    if (analysis.hasTaxFee) {
      score += 15;
    }
    
    if (!analysis.ownershipRenounced) {
      score += 10;
    }
    
    // Đánh giá mức độ rủi ro
    if (score >= 70) {
      analysis.riskLevel = 'CRITICAL';
    } else if (score >= 40) {
      analysis.riskLevel = 'HIGH';
    } else if (score >= 20) {
      analysis.riskLevel = 'MEDIUM';
    } else if (score > 0) {
      analysis.riskLevel = 'LOW';
    } else {
      analysis.riskLevel = 'SAFE';
    }
    
    analysis.riskScore = score;
  }
}

module.exports = new TokenSecurityAnalyzer();