const nodemailer = require('nodemailer');
const config = require('../config/config');
const logger = require('../utils/logger');

/**
 * Class EmailSender - Gửi email với báo cáo
 */
class EmailSender {
  constructor() {
    // Tạo transporter
    this.transporter = nodemailer.createTransport({
      service: config.email.service,
      auth: {
        user: config.email.user,
        pass: config.email.pass
      }
    });
  }
  
  /**
   * Gửi báo cáo qua email
   * @param {string} recipient - Địa chỉ email người nhận
   * @param {string} reportPath - Đường dẫn đến file báo cáo
   * @param {object} tokenAnalysis - Thông tin phân tích token
   * @param {string} language - Ngôn ngữ email (en/vi)
   */
  async sendReport(recipient, reportPath, tokenAnalysis, language = 'en') {
    try {
      // Thiết lập tiêu đề và nội dung email dựa trên ngôn ngữ
      const subject = language === 'vi'
        ? `Báo cáo phân tích token ${tokenAnalysis.symbol}`
        : `Token Analysis Report for ${tokenAnalysis.symbol}`;
      
      const bodyText = language === 'vi'
        ? `
          Kính gửi người dùng,
          
          Đính kèm là báo cáo phân tích bảo mật chi tiết cho token ${tokenAnalysis.name} (${tokenAnalysis.symbol}).
          
          Địa chỉ token: ${tokenAnalysis.address}
          Blockchain: ${tokenAnalysis.network}
          Mức độ rủi ro: ${tokenAnalysis.riskLevel}
          
          Vui lòng xem file đính kèm để biết thêm chi tiết.
          
          Trân trọng,
          Bot Kiểm tra Bảo mật Token
        `
        : `
          Dear User,
          
          Attached is your detailed security analysis report for token ${tokenAnalysis.name} (${tokenAnalysis.symbol}).
          
          Token address: ${tokenAnalysis.address}
          Blockchain: ${tokenAnalysis.network}
          Risk level: ${tokenAnalysis.riskLevel}
          
          Please see the attached file for more details.
          
          Best regards,
          Token Security Bot
        `;
      
      // Thiết lập email
      const mailOptions = {
        from: config.email.user,
        to: recipient,
        subject,
        text: bodyText,
        attachments: [
          {
            path: reportPath
          }
        ]
      };
      
      // Gửi email
      const info = await this.transporter.sendMail(mailOptions);
      
      logger.info(`Email sent to ${recipient}: ${info.messageId}`);
      return { success: true, messageId: info.messageId };
    } catch (error) {
      logger.error(`Lỗi khi gửi email đến ${recipient}:`, error);
      throw error;
    }
  }
}

// Export instance
module.exports = new EmailSender();