const { PDFDocument, rgb } = require('pdf-lib');
const fs = require('fs');
const path = require('path');
const logger = require('../utils/logger');

/**
 * Class PDFReportGenerator - Tạo báo cáo PDF
 */
class PDFReportGenerator {
  /**
   * Tạo báo cáo PDF từ kết quả phân tích token
   * @param {object} tokenAnalysis - Kết quả phân tích token
   * @param {string} language - Ngôn ngữ báo cáo (en/vi)
   */
  async generateTokenReport(tokenAnalysis, language = 'en') {
    try {
      // Tạo document PDF mới
      const pdfDoc = await PDFDocument.create();
      const page = pdfDoc.addPage([595.28, 841.89]); // A4 size
      
      // Lấy font mặc định
      const font = await pdfDoc.embedFont(PDFDocument.StandardFonts.Helvetica);
      const boldFont = await pdfDoc.embedFont(PDFDocument.StandardFonts.HelveticaBold);
      
      // Thiết lập các tham số
      const margin = 50;
      const titleSize = 24;
      const subtitleSize = 18;
      const textSize = 12;
      const lineHeight = 20;
      
      let y = page.getHeight() - margin;
      
      // Tiêu đề báo cáo
      page.drawText(language === 'vi' ? 'Báo Cáo Phân Tích Token' : 'Token Analysis Report', {
        x: margin,
        y,
        size: titleSize,
        font: boldFont,
        color: rgb(0, 0, 0)
      });
      
      // Ngày báo cáo
      y -= lineHeight * 1.5;
      page.drawText(language === 'vi' ? `Ngày: ${new Date().toLocaleDateString()}` : `Date: ${new Date().toLocaleDateString()}`, {
        x: margin,
        y,
        size: textSize,
        font
      });
      
      // Thông tin cơ bản
      y -= lineHeight * 2;
      page.drawText(language === 'vi' ? 'Thông tin cơ bản:' : 'Basic Information:', {
        x: margin,
        y,
        size: subtitleSize,
        font: boldFont
      });
      
      y -= lineHeight;
      page.drawText(`${language === 'vi' ? 'Tên:' : 'Name:'} ${tokenAnalysis.name}`, {
        x: margin,
        y,
        size: textSize,
        font
      });
      
      y -= lineHeight;
      page.drawText(`${language === 'vi' ? 'Ký hiệu:' : 'Symbol:'} ${tokenAnalysis.symbol}`, {
        x: margin,
        y,
        size: textSize,
        font
      });
      
      y -= lineHeight;
      page.drawText(`${language === 'vi' ? 'Địa chỉ:' : 'Address:'} ${tokenAnalysis.address}`, {
        x: margin,
        y,
        size: textSize,
        font
      });
      
      y -= lineHeight;
      page.drawText(`${language === 'vi' ? 'Blockchain:' : 'Blockchain:'} ${tokenAnalysis.network}`, {
        x: margin,
        y,
        size: textSize,
        font
      });
      
      y -= lineHeight;
      page.drawText(`${language === 'vi' ? 'Tổng cung:' : 'Total Supply:'} ${tokenAnalysis.totalSupply}`, {
        x: margin,
        y,
        size: textSize,
        font
      });
      
      // Mức độ rủi ro
      y -= lineHeight * 2;
      page.drawText(language === 'vi' ? 'Mức độ rủi ro:' : 'Risk Level:', {
        x: margin,
        y,
        size: subtitleSize,
        font: boldFont
      });
      
      // Màu dựa trên mức độ rủi ro
      let riskColor;
      switch (tokenAnalysis.riskLevel) {
        case 'SAFE':
          riskColor = rgb(0, 0.7, 0); // Green
          break;
        case 'LOW':
          riskColor = rgb(0.5, 0.7, 0); // Light green
          break;
        case 'MEDIUM':
          riskColor = rgb(0.9, 0.7, 0); // Yellow
          break;
        case 'HIGH':
          riskColor = rgb(0.9, 0.4, 0); // Orange
          break;
        case 'CRITICAL':
          riskColor = rgb(0.9, 0, 0); // Red
          break;
        default:
          riskColor = rgb(0, 0, 0); // Black
      }
      
      y -= lineHeight;
      page.drawText(tokenAnalysis.riskLevel, {
        x: margin,
        y,
        size: textSize + 2,
        font: boldFont,
        color: riskColor
      });
      
      // Các vấn đề bảo mật
      y -= lineHeight * 2;
      page.drawText(language === 'vi' ? 'Các vấn đề bảo mật:' : 'Security Issues:', {
        x: margin,
        y,
        size: subtitleSize,
        font: boldFont
      });
      
      y -= lineHeight;
      if (tokenAnalysis.securityIssues && tokenAnalysis.securityIssues.length > 0) {
        tokenAnalysis.securityIssues.forEach((issue, index) => {
          page.drawText(`${index + 1}. ${issue}`, {
            x: margin,
            y,
            size: textSize,
            font
          });
          y -= lineHeight;
        });
      } else {
        page.drawText(language === 'vi' ? 'Không tìm thấy vấn đề bảo mật!' : 'No security issues found!', {
          x: margin,
          y,
          size: textSize,
          font
        });
        y -= lineHeight;
      }
      
      // Thông tin về người giữ token
      y -= lineHeight;
      page.drawText(language === 'vi' ? 'Thông tin người giữ token:' : 'Token Holders:', {
        x: margin,
        y,
        size: subtitleSize,
        font: boldFont
      });
      
      y -= lineHeight;
      if (tokenAnalysis.holders && tokenAnalysis.holders.length > 0) {
        tokenAnalysis.holders.forEach((holder, index) => {
          page.drawText(`${index + 1}. ${holder.address.substring(0, 12)}...${holder.address.substring(30)} - ${holder.share}%`, {
            x: margin,
            y,
            size: textSize,
            font
          });
          y -= lineHeight;
        });
      } else {
        page.drawText(language === 'vi' ? 'Không có thông tin về người giữ token.' : 'No holder information available.', {
          x: margin,
          y,
          size: textSize,
          font
        });
        y -= lineHeight;
      }
      
      // Chân trang
      y = margin;
      page.drawText(language === 'vi' ? 'Báo cáo được tạo bởi Bot Kiểm tra Bảo mật Token' : 'Report generated by Token Security Bot', {
        x: margin,
        y,
        size: textSize - 2,
        font,
        color: rgb(0.5, 0.5, 0.5)
      });
      
      // Xuất PDF
      const pdfBytes = await pdfDoc.save();
      
      // Tạo tên file
      const fileName = `token_report_${tokenAnalysis.address.substring(0, 8)}_${Date.now()}.pdf`;
      const filePath = path.join(__dirname, '../..', 'reports', fileName);
      
      // Đảm bảo thư mục reports tồn tại
      const reportsDir = path.join(__dirname, '../..', 'reports');
      if (!fs.existsSync(reportsDir)) {
        fs.mkdirSync(reportsDir, { recursive: true });
      }
      
      // Ghi file
      fs.writeFileSync(filePath, pdfBytes);
      
      return {
        fileName,
        filePath
      };
    } catch (error) {
      logger.error('Lỗi khi tạo báo cáo PDF:', error);
      throw error;
    }
  }
}

// Export instance
module.exports = new PDFReportGenerator();