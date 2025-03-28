const languages = {
  en: {
    welcome: 'Welcome to the Token Security Bot!',
    languagePrompt: 'Please select your language:',
    languageSelected: 'English language selected!',
    networkPrompt: 'Please select the blockchain network for token analysis:',
    networkSelected: 'You have selected {network} network.',
    commandHelp: `Available commands:
  /start - Start the bot
  /help - Show help
  /check - Check token security
  /analyze - Advanced token analysis
  /report - Generate PDF report
  /balance - View your balance
  /referral - View your referral link
  /email - Send report via email`,
    invalidSyntax: 'Invalid syntax. Use: /check <address> <blockchain>',
    analyzing: 'Analyzing token {address} on {network}... This may take a few minutes.',
    unsupportedChain: 'Unsupported blockchain. Supported blockchains: {chains}',
    inDevelopment: 'Feature is under development. Please try again later.',
    referralLink: 'Here is your referral link. Share it if you find this bot useful:\n{link}',
    referralStats: 'Your referral statistics:\n- Direct referrals (F1): {direct}\n- Indirect referrals (F2): {indirect}',
    enterAddress: 'Please enter the token contract address:',
    processingAddress: 'Processing the address...',
    selectBlockchain: 'Please select the blockchain network:',
    addressRequired: 'Please enter a valid contract address.',
    analyzingToken: 'Analyzing token {address} on {network}. Please wait, this may take some time...',
    tokenAnalysisResult: 'Token Analysis Results:',
    tokenName: 'Name: {name}',
    tokenSymbol: 'Symbol: {symbol}',
    tokenTotalSupply: 'Total Supply: {supply}',
    tokenDecimals: 'Decimals: {decimals}',
    tokenAddress: 'Contract Address: {address}',
    tokenBlockchain: 'Blockchain: {blockchain}',
    tokenOwner: 'Owner: {owner}',
    tokenRiskLevel: 'Risk Level: {level}',
    tokenSecurityIssues: 'Security Issues:',
    tokenNoSecurityIssues: 'No security issues found!',
    tokenNotFound: 'Token not found or not an ERC-20 token',
    analysisFailed: 'Analysis failed. Please try again later.',
    downloadReport: 'Download Detailed Report',
    riskLevelSafe: 'SAFE - No significant risks detected',
    riskLevelLow: 'LOW - Some minor concerns present',
    riskLevelMedium: 'MEDIUM - Several security concerns present',
    riskLevelHigh: 'HIGH - Major security risks detected',
    riskLevelCritical: 'CRITICAL - Extremely dangerous, likely scam',
    
    // Thêm chuỗi mới
    analyzingTokenAdvanced: 'Performing advanced analysis for token {address} on {network}. This may take some time...',
    tokenAnalysisResultAdvanced: 'Advanced Token Analysis Results:',
    noAnalysisAvailable: 'No token analysis available. Please analyze a token first with /check or /analyze.',
    generatingReport: 'Generating PDF report...',
    reportGenerationFailed: 'Failed to generate report. Please try again later.',
    enterEmail: 'Please enter your email address to receive the report:',
    invalidEmail: 'Invalid email address. Please enter a valid email.',
    sendingEmail: 'Sending email. This may take a moment...',
    emailSent: 'Report has been sent to your email!',
    emailSendingFailed: 'Failed to send email. Please try again later.',
    createReport: 'Would you like to create a detailed PDF report?',
    totalHolders: 'Total Holders: {count}',
    topHolderPercentage: 'Top Holder: {percentage}%',
    distributionScore: 'Distribution: {score}',
    advancedAnalysisFailed: 'Advanced analysis failed. Please try again later.',
    advancedAnalysisInfo: 'Advanced Analysis Information:'
  },
  vi: {
    welcome: 'Chào mừng đến với Bot Kiểm tra Bảo mật Token!',
    languagePrompt: 'Vui lòng chọn ngôn ngữ của bạn:',
    languageSelected: 'Đã chọn Tiếng Việt!',
    networkPrompt: 'Vui lòng chọn mạng lưới blockchain để phân tích token:',
    networkSelected: 'Bạn đã chọn mạng lưới {network}.',
    commandHelp: `Danh sách lệnh có sẵn:
  /start - Khởi động bot
  /help - Hiển thị trợ giúp
  /check - Kiểm tra token
  /analyze - Phân tích token nâng cao
  /report - Tạo báo cáo PDF
  /balance - Xem số dư của bạn
  /referral - Xem link giới thiệu của bạn
  /email - Gửi báo cáo qua email`,
    invalidSyntax: 'Cú pháp không hợp lệ. Sử dụng: /check <địa chỉ> <blockchain>',
    analyzing: 'Đang phân tích token {address} trên {network}... Quá trình này có thể mất vài phút.',
    unsupportedChain: 'Blockchain không được hỗ trợ. Các blockchain được hỗ trợ: {chains}',
    inDevelopment: 'Chức năng đang được phát triển. Vui lòng thử lại sau.',
    referralLink: 'Đây là link giới thiệu của bạn, hãy chia sẻ nếu bạn thấy Bot hữu ích:\n{link}',
    referralStats: 'Thống kê giới thiệu của bạn:\n- Giới thiệu trực tiếp (F1): {direct}\n- Giới thiệu gián tiếp (F2): {indirect}',
    enterAddress: 'Vui lòng nhập địa chỉ hợp đồng token:',
    processingAddress: 'Đang xử lý địa chỉ...',
    selectBlockchain: 'Vui lòng chọn mạng lưới blockchain:',
    addressRequired: 'Vui lòng nhập địa chỉ hợp đồng hợp lệ.',
    analyzingToken: 'Đang phân tích token {address} trên {network}. Vui lòng đợi, quá trình này có thể mất một lúc...',
    tokenAnalysisResult: 'Kết quả phân tích Token:',
    tokenName: 'Tên: {name}',
    tokenSymbol: 'Ký hiệu: {symbol}',
    tokenTotalSupply: 'Tổng cung: {supply}',
    tokenDecimals: 'Số thập phân: {decimals}',
    tokenAddress: 'Địa chỉ hợp đồng: {address}',
    tokenBlockchain: 'Blockchain: {blockchain}',
    tokenOwner: 'Chủ sở hữu: {owner}',
    tokenRiskLevel: 'Mức độ rủi ro: {level}',
    tokenSecurityIssues: 'Vấn đề bảo mật:',
    tokenNoSecurityIssues: 'Không tìm thấy vấn đề bảo mật!',
    tokenNotFound: 'Không tìm thấy token hoặc không phải là token ERC-20',
    analysisFailed: 'Phân tích thất bại. Vui lòng thử lại sau.',
    downloadReport: 'Tải báo cáo chi tiết',
    riskLevelSafe: 'AN TOÀN - Không phát hiện rủi ro đáng kể',
    riskLevelLow: 'THẤP - Có một số vấn đề nhỏ',
    riskLevelMedium: 'TRUNG BÌNH - Có một số vấn đề bảo mật',
    riskLevelHigh: 'CAO - Phát hiện rủi ro bảo mật lớn',
    riskLevelCritical: 'NGUY HIỂM - Cực kỳ nguy hiểm, có thể là lừa đảo',
    
    // Thêm chuỗi mới
    analyzingTokenAdvanced: 'Đang thực hiện phân tích nâng cao cho token {address} trên {network}. Quá trình này có thể mất một lúc...',
    tokenAnalysisResultAdvanced: 'Kết quả phân tích Token nâng cao:',
    noAnalysisAvailable: 'Chưa có phân tích token nào. Vui lòng phân tích token trước bằng lệnh /check hoặc /analyze.',
    generatingReport: 'Đang tạo báo cáo PDF...',
    reportGenerationFailed: 'Không thể tạo báo cáo. Vui lòng thử lại sau.',
    enterEmail: 'Vui lòng nhập địa chỉ email của bạn để nhận báo cáo:',
    invalidEmail: 'Địa chỉ email không hợp lệ. Vui lòng nhập email hợp lệ.',
    sendingEmail: 'Đang gửi email. Quá trình này có thể mất một lúc...',
    emailSent: 'Báo cáo đã được gửi đến email của bạn!',
    emailSendingFailed: 'Không thể gửi email. Vui lòng thử lại sau.',
    createReport: 'Bạn có muốn tạo báo cáo PDF chi tiết không?',
    downloadReport: 'Tải báo cáo PDF',
    totalHolders: 'Tổng số người giữ: {count}',
    topHolderPercentage: 'Người giữ lớn nhất: {percentage}%',
    distributionScore: 'Phân phối: {score}',
    advancedAnalysisFailed: 'Phân tích nâng cao thất bại. Vui lòng thử lại sau.',
    advancedAnalysisInfo: 'Thông tin phân tích nâng cao:'
  }
};

// Hàm lấy chuỗi ngôn ngữ với các tham số thay thế
function getText(langCode, key, params = {}) {
  if (!languages[langCode] || !languages[langCode][key]) {
    // Fallback to English if key not found
    if (!languages['en'][key]) {
      return `Missing text: ${key}`;
    }
    return languages['en'][key];
  }
  
  let text = languages[langCode][key];
  
  // Thay thế các tham số
  Object.keys(params).forEach(param => {
    text = text.replace(`{${param}}`, params[param]);
  });
  
  return text;
}

module.exports = {
  languages,
  getText
};