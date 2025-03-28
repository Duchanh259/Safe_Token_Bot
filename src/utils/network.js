const axios = require('axios');
const logger = require('./logger');

/**
 * Kiểm tra kết nối đến Telegram API
 * @returns {Promise<boolean>} Trả về true nếu kết nối thành công
 */
async function checkTelegramConnection() {
  try {
    logger.info('Đang kiểm tra kết nối đến Telegram API...');
    const response = await axios.get('https://api.telegram.org', {
      timeout: 5000
    });
    logger.info('Kết nối đến Telegram API thành công!');
    return true;
  } catch (error) {
    logger.error('Không thể kết nối đến Telegram API:', error.message);
    return false;
  }
}

module.exports = {
  checkTelegramConnection
};