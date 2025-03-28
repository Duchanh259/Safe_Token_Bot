// Thêm dòng này vào đầu file src/index.js
process.env.NODE_OPTIONS = '--dns-result-order=ipv4first';

const TelegramBot = require('./core/bot');
const logger = require('./utils/logger');
const { checkTelegramConnection } = require('./utils/network');

async function startBot() {
  try {
    logger.info('Đang khởi động Bot Kiểm tra Bảo mật Token...');
    
    // Kiểm tra kết nối trước khi khởi động
    const connectionOk = await checkTelegramConnection();
    if (!connectionOk) {
      logger.warn('Cảnh báo: Kết nối đến Telegram API không ổn định. Bot vẫn sẽ cố gắng khởi động...');
    }
    
    const bot = new TelegramBot();
    await bot.launch();
  } catch (error) {
    logger.error('Lỗi nghiêm trọng khi khởi động bot:', error);
    logger.info('Kiểm tra các vấn đề phổ biến:');
    logger.info('1. Kiểm tra lại token bot trong file .env');
    logger.info('2. Kiểm tra kết nối mạng');
    logger.info('3. Kiểm tra tường lửa hoặc cấu hình proxy');
    process.exit(1);
  }
}

startBot();