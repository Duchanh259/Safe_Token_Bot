const crypto = require('crypto');
const logger = require('../utils/logger');

class ReferralSystem {
  constructor() {
    // Trong thực tế, dữ liệu này sẽ được lưu vào cơ sở dữ liệu
    this.referralLinks = {};
    this.referrals = {};
  }

  // Tạo link giới thiệu dựa trên userId
  generateReferralLink(userId) {
    if (this.referralLinks[userId]) {
      return this.referralLinks[userId];
    }

    // Tạo một mã hash ngắn dựa trên userId
    const hash = crypto.createHash('md5').update(userId.toString()).digest('hex').substring(0, 8);
    const referralCode = `ref_${hash}`;
    
    // Lưu link vào bộ nhớ (trong triển khai thực tế sẽ lưu vào database)
    this.referralLinks[userId] = referralCode;
    
    logger.info(`Tạo link giới thiệu cho user ${userId}: ${referralCode}`);
    
    return referralCode;
  }

  // Lấy link giới thiệu hoàn chỉnh cho Telegram
  getReferralLink(userId, botUsername) {
    const code = this.generateReferralLink(userId);
    return `https://t.me/${botUsername}?start=${code}`;
  }

  // Đăng ký người dùng mới từ link giới thiệu
  registerReferral(referralCode, newUserId) {
    // Tìm userId của người giới thiệu
    const referrerId = Object.keys(this.referralLinks).find(
      id => this.referralLinks[id] === referralCode
    );

    if (!referrerId) {
      logger.warn(`Không tìm thấy mã giới thiệu: ${referralCode}`);
      return null;
    }

    // Lưu thông tin giới thiệu (F1)
    if (!this.referrals[referrerId]) {
      this.referrals[referrerId] = { direct: [], indirect: [] };
    }
    
    this.referrals[referrerId].direct.push(newUserId);
    
    // Kiểm tra xem người giới thiệu có người giới thiệu cấp trên không (F2)
    const grandReferrerId = Object.keys(this.referrals).find(
      id => this.referrals[id].direct.includes(referrerId)
    );
    
    if (grandReferrerId) {
      if (!this.referrals[grandReferrerId].indirect) {
        this.referrals[grandReferrerId].indirect = [];
      }
      
      this.referrals[grandReferrerId].indirect.push(newUserId);
    }
    
    logger.info(`Đăng ký giới thiệu: ${referrerId} -> ${newUserId}${grandReferrerId ? ` (F2: ${grandReferrerId})` : ''}`);
    
    return referrerId;
  }

  // Lấy thông tin giới thiệu của một người dùng
  getReferralInfo(userId) {
    return {
      referralCode: this.referralLinks[userId] || null,
      referrals: this.referrals[userId] || { direct: [], indirect: [] }
    };
  }
}

module.exports = new ReferralSystem();