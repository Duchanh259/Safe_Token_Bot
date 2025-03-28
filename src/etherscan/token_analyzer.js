const etherscanApi = require('./api_client');
const logger = require('../utils/logger');
const NodeCache = require('node-cache');

// Cache để lưu trữ kết quả phân tích
const analysisCache = new NodeCache({ stdTTL: 600, checkperiod: 120 });

/**
 * Class EtherscanTokenAnalyzer - Phân tích token bằng Etherscan API
 */
class EtherscanTokenAnalyzer {
  constructor() {
    this.supportedNetworks = etherscanApi.supportedNetworks;
  }
  
  /**
   * Phân tích token
   * @param {string} address - Địa chỉ token
   * @param {string} network - Tên mạng blockchain
   */
  async analyzeToken(address, network) {
    try {
      // Kiểm tra network có được hỗ trợ không
      if (!this.supportedNetworks.includes(network)) {
        throw new Error(`Mạng ${network} không được hỗ trợ cho phân tích token`);
      }
      
      // Kiểm tra cache
      const cacheKey = `tokenAnalysis_${network}_${address}`;
      const cachedAnalysis = analysisCache.get(cacheKey);
      if (cachedAnalysis) {
        return cachedAnalysis;
      }
      
      // Kiểm tra xem địa chỉ có phải là contract
      const isContract = await etherscanApi.isContract(address, network);
      if (!isContract) {
        throw new Error(`Địa chỉ ${address} không phải là contract`);
      }
      
      // Lấy thông tin token
      const tokenInfo = await etherscanApi.getTokenInfo(address, network);
      
      // Lấy mã nguồn contract
      const sourceCode = await etherscanApi.getContractSourceCode(address, network);
      
      // Lấy danh sách người giữ token
      const holders = await etherscanApi.getTokenHolders(address, network, 1, 10);
      
      // Phân tích các vấn đề bảo mật từ mã nguồn
      const securityIssues = this.analyzeSecurityIssues(sourceCode);
      
      // Tính toán mức độ rủi ro
      const riskLevel = this.calculateRiskLevel(securityIssues);
      
      // Tổng hợp kết quả phân tích
      const analysis = {
        address,
        network,
        name: tokenInfo ? tokenInfo.name : 'Unknown Token',
        symbol: tokenInfo ? tokenInfo.symbol : 'UNKNOWN',
        decimals: tokenInfo ? parseInt(tokenInfo.decimals) : 18,
        totalSupply: tokenInfo ? tokenInfo.totalSupply : '0',
        isERC20: tokenInfo ? true : false,
        sourceCodeVerified: sourceCode.ABI !== 'Contract source code not verified',
        contractType: sourceCode.ContractName || 'Unknown',
        isProxy: sourceCode.Proxy === '1',
        securityIssues: securityIssues.issues,
        riskLevel,
        hasMintFunction: securityIssues.hasMintFunction,
        hasBlacklistFunction: securityIssues.hasBlacklistFunction,
        hasPauseFunction: securityIssues.hasPauseFunction,
        hasFreezeFunction: securityIssues.hasFreezeFunction,
        ownershipRenounced: false, // Mặc định
        hasTaxFee: securityIssues.hasTaxFee,
        isHoneypot: securityIssues.isHoneypot,
        holders: holders.map(holder => ({
          address: holder.address,
          balance: holder.value,
          share: holder.share
        }))
      };
      
      // Kiểm tra ownership (nếu có mã nguồn)
      if (sourceCode && sourceCode.SourceCode) {
        analysis.ownershipRenounced = this.checkOwnershipRenounced(sourceCode);
      }
      
      // Lưu vào cache và trả về kết quả
      analysisCache.set(cacheKey, analysis);
      return analysis;
    } catch (error) {
      logger.error(`Lỗi khi phân tích token (${address}, ${network}):`, error);
      throw error;
    }
  }
  
  /**
   * Phân tích các vấn đề bảo mật từ mã nguồn
   * @param {object} sourceCode - Thông tin mã nguồn từ Etherscan
   */
  analyzeSecurityIssues(sourceCode) {
    const issues = [];
    let hasMintFunction = false;
    let hasBlacklistFunction = false;
    let hasPauseFunction = false;
    let hasFreezeFunction = false;
    let hasTaxFee = false;
    let isHoneypot = false;
    
    // Nếu không có mã nguồn được xác minh, không thể phân tích chi tiết
    if (!sourceCode || !sourceCode.SourceCode || sourceCode.ABI === 'Contract source code not verified') {
      issues.push('Mã nguồn chưa được xác minh, không thể phân tích chi tiết');
      return {
        issues,
        hasMintFunction,
        hasBlacklistFunction,
        hasPauseFunction,
        hasFreezeFunction,
        hasTaxFee,
        isHoneypot
      };
    }
    
    // Chuyển mã nguồn về chữ thường để dễ tìm kiếm
    const code = sourceCode.SourceCode.toLowerCase();
    
    // Kiểm tra hàm mint
    if (code.includes('mint') || code.includes('function mint')) {
      hasMintFunction = true;
      issues.push('Token có hàm mint - cấp phát thêm token');
    }
    
    // Kiểm tra hàm blacklist
    if (code.includes('blacklist') || code.includes('blocklist') || code.includes('banned')) {
      hasBlacklistFunction = true;
      issues.push('Token có hàm blacklist - chặn các địa chỉ');
    }
    
    // Kiểm tra hàm pause
    if (code.includes('pause') || code.includes('function pause')) {
      hasPauseFunction = true;
      issues.push('Token có hàm pause - tạm dừng giao dịch');
    }
    
    // Kiểm tra hàm freeze
    if (code.includes('freeze') || code.includes('function freeze')) {
      hasFreezeFunction = true;
      issues.push('Token có hàm freeze - đóng băng giao dịch');
    }
    
    // Kiểm tra thuế/phí giao dịch
    if (code.includes('tax') || code.includes('fee') || code.includes('reflection')) {
      hasTaxFee = true;
      issues.push('Token có thuế/phí giao dịch');
    }
    
    // Phát hiện honeypot
    if (
      code.includes('onlybuy') || 
      code.includes('cannotsell') || 
      code.includes('disableselling') || 
      code.includes('preventsell') ||
      (code.includes('onlyowner') && code.includes('sell'))
    ) {
      isHoneypot = true;
      issues.push('Token có thể là honeypot - không thể bán sau khi mua');
    }
    
    return {
      issues,
      hasMintFunction,
      hasBlacklistFunction,
      hasPauseFunction,
      hasFreezeFunction,
      hasTaxFee,
      isHoneypot
    };
  }
  
  /**
   * Kiểm tra xem ownership có bị từ bỏ hay không
   * @param {object} sourceCode - Thông tin mã nguồn từ Etherscan
   */
  checkOwnershipRenounced(sourceCode) {
    if (!sourceCode || !sourceCode.SourceCode) {
      return false;
    }
    
    const code = sourceCode.SourceCode.toLowerCase();
    
    // Kiểm tra các mẫu từ bỏ ownership phổ biến
    return (
      code.includes('renounceownership') ||
      code.includes('transferownership(address(0))') ||
      code.includes('transferownership(0x0)') ||
      code.includes('transferownership(0x000000000000000000000000000000000000dead)')
    );
  }
  
  /**
   * Tính toán mức độ rủi ro dựa trên các vấn đề bảo mật
   * @param {object} securityIssues - Kết quả phân tích các vấn đề bảo mật
   */
  calculateRiskLevel(securityIssues) {
    // Nếu là honeypot, luôn là CRITICAL
    if (securityIssues.isHoneypot) {
      return 'CRITICAL';
    }
    
    // Tính điểm rủi ro
    let riskScore = 0;
    
    if (securityIssues.hasMintFunction) riskScore += 30;
    if (securityIssues.hasBlacklistFunction) riskScore += 25;
    if (securityIssues.hasPauseFunction) riskScore += 20;
    if (securityIssues.hasFreezeFunction) riskScore += 25;
    if (securityIssues.hasTaxFee) riskScore += 15;
    
    // Xác định mức độ rủi ro dựa trên điểm
    if (riskScore >= 70) return 'CRITICAL';
    if (riskScore >= 40) return 'HIGH';
    if (riskScore >= 20) return 'MEDIUM';
    if (riskScore > 0) return 'LOW';
    return 'SAFE';
  }
}

// Export instance
module.exports = new EtherscanTokenAnalyzer();