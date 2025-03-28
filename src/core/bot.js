const { Telegraf, session, Markup, Scenes, Stage } = require('telegraf');
const config = require('../config/config');
const logger = require('../utils/logger');
const { getText } = require('../utils/languages');
const referralSystem = require('../referral/referral');
const tokenAnalyzer = require('../etherscan/token_analyzer');
const advancedAnalyzer = require('../etherscan/advanced_analyzer');
const pdfGenerator = require('../reporting/pdf_generator');
const emailSender = require('../reporting/email_sender');

class TelegramBot {
  constructor() {
    this.bot = new Telegraf(config.telegramToken);
    
    // Middleware để xử lý session
    this.bot.use(session({
      defaultSession: () => ({
        language: 'en',
        selectedBlockchain: null,
        state: null, // Lưu trạng thái hội thoại hiện tại
        waitingFor: null, // Đang đợi input gì từ người dùng
        lastAnalyzedToken: null // Lưu kết quả phân tích token gần nhất
      })
    }));
    
    // Middleware để ghi log
    this.bot.use((ctx, next) => {
      if (ctx.message) {
        const userId = ctx.message.from.id;
        const username = ctx.message.from.username || 'No username';
        const message = ctx.message.text || 'Non-text message';
        
        logger.info(`User ${userId} (${username}) sent: ${message}`);
      }
      return next();
    });
    
    // Xử lý lỗi
    this.bot.catch((err, ctx) => {
      logger.error(`Bot error for ${ctx.updateType}`, err);
      const lang = ctx.session?.language || 'en';
      ctx.reply('Đã xảy ra lỗi. Vui lòng thử lại sau hoặc liên hệ admin để được hỗ trợ.');
    });
    
    this.setupMenuCommands();
    this.registerCommandHandlers();
    this.registerMessageHandlers();
  }

  // Thiết lập Menu Commands
  async setupMenuCommands() {
    try {
      await this.bot.telegram.setMyCommands([
        { command: 'start', description: 'Start the bot' },
        { command: 'check', description: 'Check token security' },
        { command: 'analyze', description: 'Advanced token analysis' },
        { command: 'report', description: 'Generate PDF report' },
        { command: 'balance', description: 'View your balance' },
        { command: 'referral', description: 'View your referral link' },
        { command: 'email', description: 'Send report via email' },
        { command: 'help', description: 'Show help' }
      ]);
      logger.info('Bot menu commands setup successfully');
    } catch (error) {
      logger.error('Failed to setup bot menu commands', error);
    }
  }

  registerCommandHandlers() {
    // Lệnh /start - Xử lý khởi động và referral
    this.bot.start((ctx) => {
      const startPayload = ctx.startPayload;
      const userId = ctx.from.id;
      
      // Kiểm tra xem có mã giới thiệu trong startPayload không
      if (startPayload && startPayload.startsWith('ref_')) {
        const referralCode = startPayload;
        referralSystem.registerReferral(referralCode, userId);
      }

      // Hiển thị chọn ngôn ngữ
      ctx.reply(
        '🌐 Choose Language / Chọn Ngôn Ngữ:', 
        Markup.inlineKeyboard([
          Markup.button.callback('English 🇬🇧', 'lang_en'),
          Markup.button.callback('Tiếng Việt 🇻🇳', 'lang_vi')
        ])
      );
    });

    // Xử lý callback khi chọn ngôn ngữ
    this.bot.action(/lang_(.+)/, async (ctx) => {
      const langCode = ctx.match[1];
      ctx.session.language = langCode;
      
      // Xác nhận đã chọn ngôn ngữ
      await ctx.editMessageText(getText(langCode, 'languageSelected'));
      
      // 1. Hiển thị tin nhắn chào mừng theo đúng thứ tự
      await ctx.reply(getText(langCode, 'welcome'));
      
      // 2. Tạo và hiển thị link giới thiệu
      const userId = ctx.from.id;
      const botInfo = ctx.botInfo || { username: 'your_bot_username' };
      const referralLink = referralSystem.getReferralLink(userId, botInfo.username);
      await ctx.reply(getText(langCode, 'referralLink', { link: referralLink }));
      
      // 3. Hiển thị hướng dẫn sử dụng
      await ctx.reply(getText(langCode, 'commandHelp'));
      
      return ctx.answerCbQuery();
    });

    // Lệnh /check - Bắt đầu quy trình kiểm tra token
    this.bot.command('check', (ctx) => {
      const lang = ctx.session?.language || 'en';
      ctx.session.state = 'check_waiting_blockchain';
      this.showBlockchainOptions(ctx);
    });

    // Lệnh /analyze - Bắt đầu quy trình phân tích nâng cao
    this.bot.command('analyze', (ctx) => {
      const lang = ctx.session?.language || 'en';
      ctx.session.state = 'analyze_waiting_blockchain';
      this.showBlockchainOptions(ctx);
    });

    // Lệnh /report - Tạo báo cáo PDF
    this.bot.command('report', (ctx) => {
      const lang = ctx.session?.language || 'en';
      
      // Kiểm tra xem đã phân tích token trước đó chưa
      if (!ctx.session.lastAnalyzedToken) {
        return ctx.reply(
          getText(lang, 'noAnalysisAvailable')
        );
      }
      
      // Tạo và gửi báo cáo PDF
      ctx.reply(getText(lang, 'generatingReport'));
      
      // Tạo báo cáo PDF
      pdfGenerator.generateTokenReport(ctx.session.lastAnalyzedToken, lang)
        .then(report => {
          // Gửi file PDF
          ctx.replyWithDocument({ source: report.filePath });
        })
        .catch(error => {
          logger.error('Lỗi khi tạo báo cáo:', error);
          ctx.reply(getText(lang, 'reportGenerationFailed'));
        });
    });

    // Lệnh /email - Gửi báo cáo qua email
    this.bot.command('email', (ctx) => {
      const lang = ctx.session?.language || 'en';
      
      // Kiểm tra xem đã phân tích token trước đó chưa
      if (!ctx.session.lastAnalyzedToken) {
        return ctx.reply(
          getText(lang, 'noAnalysisAvailable')
        );
      }
      
      // Yêu cầu địa chỉ email
      ctx.reply(getText(lang, 'enterEmail'));
      ctx.session.state = 'waiting_email';
      ctx.session.waitingFor = 'email_address';
    });

    // Lệnh /help
    this.bot.help((ctx) => {
      const lang = ctx.session?.language || 'en';
      return ctx.reply(getText(lang, 'commandHelp'));
    });
    
    // Lệnh /referral - Hiển thị link giới thiệu và thống kê
    this.bot.command('referral', (ctx) => {
      const lang = ctx.session?.language || 'en';
      const userId = ctx.from.id;
      const botInfo = ctx.botInfo || { username: 'your_bot_username' };
      
      // Lấy link giới thiệu
      const referralLink = referralSystem.getReferralLink(userId, botInfo.username);
      
      // Lấy thống kê giới thiệu
      const referralInfo = referralSystem.getReferralInfo(userId);
      const directCount = referralInfo.referrals.direct.length;
      const indirectCount = referralInfo.referrals.indirect.length;
      
      // Gửi thông tin giới thiệu
      ctx.reply(getText(lang, 'referralLink', { link: referralLink }));
      ctx.reply(getText(lang, 'referralStats', { 
        direct: directCount, 
        indirect: indirectCount 
      }));
    });
    
    // Lệnh /balance - Hiển thị số dư (sẽ phát triển sau)
    this.bot.command('balance', (ctx) => {
      const lang = ctx.session?.language || 'en';
      ctx.reply(getText(lang, 'inDevelopment'));
    });

    // Xử lý callback khi chọn blockchain
    this.bot.action(/chain_(.+)/, async (ctx) => {
      const chainId = ctx.match[1];
      ctx.session.selectedBlockchain = chainId;
      const lang = ctx.session?.language || 'en';
      
      // Xác nhận đã chọn blockchain
      const chainName = config.blockchains[chainId]?.name || chainId;
      await ctx.editMessageText(
        getText(lang, 'networkSelected', { network: chainName })
      );
      
      // Nếu đang trong quy trình check token, yêu cầu nhập địa chỉ hợp đồng
      if (ctx.session.state === 'check_waiting_blockchain') {
        await ctx.reply(getText(lang, 'enterAddress'));
        ctx.session.state = 'check_waiting_address';
        ctx.session.waitingFor = 'token_address';
      }
      // Nếu đang trong quy trình phân tích nâng cao
      else if (ctx.session.state === 'analyze_waiting_blockchain') {
        await ctx.reply(getText(lang, 'enterAddress'));
        ctx.session.state = 'analyze_waiting_address';
        ctx.session.waitingFor = 'token_address';
      }
      
      return ctx.answerCbQuery();
    });

    // Xử lý callback khi chọn tạo báo cáo
    this.bot.action('generate_report', async (ctx) => {
      const lang = ctx.session?.language || 'en';
      
      if (!ctx.session.lastAnalyzedToken) {
        return ctx.answerCbQuery(getText(lang, 'noAnalysisAvailable'));
      }
      
      await ctx.answerCbQuery(getText(lang, 'generatingReport'));
      
      // Tạo báo cáo PDF
      pdfGenerator.generateTokenReport(ctx.session.lastAnalyzedToken, lang)
        .then(report => {
          // Gửi file PDF
          ctx.replyWithDocument({ source: report.filePath });
        })
        .catch(error => {
          logger.error('Lỗi khi tạo báo cáo:', error);
          ctx.reply(getText(lang, 'reportGenerationFailed'));
        });
    });
  }

  registerMessageHandlers() {
    // Xử lý tin nhắn văn bản dựa trên trạng thái
    this.bot.on('text', async (ctx) => {
      const lang = ctx.session?.language || 'en';
      const text = ctx.message.text;
      
      // Nếu đang đợi địa chỉ token cho lệnh check
      if (ctx.session.state === 'check_waiting_address' && ctx.session.waitingFor === 'token_address') {
        // Validate địa chỉ
        if (!text || text.trim() === '') {
          return ctx.reply(getText(lang, 'addressRequired'));
        }
        
        const tokenAddress = text.trim();
        const blockchain = ctx.session.selectedBlockchain;
        
        // Reset trạng thái
        ctx.session.state = null;
        ctx.session.waitingFor = null;
        
        // Thông báo đang phân tích
        const processingMsg = await ctx.reply(
          getText(lang, 'analyzingToken', { address: tokenAddress, network: blockchain })
        );
        
        try {
          // Phân tích token bằng Etherscan API
          const analysis = await tokenAnalyzer.analyzeToken(tokenAddress, blockchain);
          
          // Lưu kết quả phân tích cho việc tạo báo cáo sau này
          ctx.session.lastAnalyzedToken = analysis;
          
          // Hiển thị kết quả
          await ctx.reply(getText(lang, 'tokenAnalysisResult'));
          
          let riskLevelText;
          switch(analysis.riskLevel) {
            case 'SAFE': riskLevelText = getText(lang, 'riskLevelSafe'); break;
            case 'LOW': riskLevelText = getText(lang, 'riskLevelLow'); break;
            case 'MEDIUM': riskLevelText = getText(lang, 'riskLevelMedium'); break;
            case 'HIGH': riskLevelText = getText(lang, 'riskLevelHigh'); break;
            case 'CRITICAL': riskLevelText = getText(lang, 'riskLevelCritical'); break;
            default: riskLevelText = analysis.riskLevel;
          }
          
          // Tạo thông báo kết quả
          let resultMessage = `${getText(lang, 'tokenName', { name: analysis.name })}\n`;
          resultMessage += `${getText(lang, 'tokenSymbol', { symbol: analysis.symbol })}\n`;
          resultMessage += `${getText(lang, 'tokenTotalSupply', { supply: analysis.totalSupply })}\n`;
          resultMessage += `${getText(lang, 'tokenDecimals', { decimals: analysis.decimals })}\n`;
          resultMessage += `${getText(lang, 'tokenAddress', { address: analysis.address })}\n`;
          resultMessage += `${getText(lang, 'tokenBlockchain', { blockchain: analysis.network })}\n`;
          
          // Thông báo về mã nguồn
          if (analysis.sourceCodeVerified) {
            resultMessage += `✅ Mã nguồn đã được xác minh\n`;
          } else {
            resultMessage += `⚠️ Mã nguồn chưa được xác minh\n`;
          }
          
          resultMessage += `${getText(lang, 'tokenRiskLevel', { level: riskLevelText })}\n\n`;
          
          resultMessage += `${getText(lang, 'tokenSecurityIssues')}\n`;
          
          if (analysis.securityIssues.length > 0) {
            analysis.securityIssues.forEach((issue, index) => {
              resultMessage += `${index + 1}. ${issue}\n`;
            });
          } else {
            resultMessage += `${getText(lang, 'tokenNoSecurityIssues')}\n`;
          }
          
          if (analysis.holders && analysis.holders.length > 0) {
            resultMessage += `\nTop ${analysis.holders.length} người giữ token:\n`;
            analysis.holders.slice(0, 3).forEach((holder, index) => {
              resultMessage += `${index + 1}. ${holder.address.substring(0, 8)}...${holder.address.substring(36)} - ${holder.share}%\n`;
            });
          }
          
          await ctx.reply(resultMessage);
          
        } catch (error) {
          logger.error(`Lỗi khi phân tích token: ${error.message}`);
          
          // Hiển thị thông báo lỗi cụ thể hơn
          let errorMessage = getText(lang, 'analysisFailed');
          
          if (error.message.includes('Không thể kết nối')) {
            errorMessage = `⚠️ Không thể kết nối đến blockchain ${blockchain}. Vui lòng thử lại sau hoặc chọn blockchain khác.`;
          } else if (error.message.includes('không phải là hợp đồng') || error.message.includes('không phải là contract')) {
            errorMessage = `❌ Địa chỉ ${tokenAddress} không phải là smart contract hợp lệ.`;
          } else if (error.message.includes('hợp đồng hợp lệ')) {
            errorMessage = `❌ Không thể xác minh ${tokenAddress}. Vui lòng kiểm tra lại địa chỉ.`;
          } else if (error.message.includes('không phải là token ERC-20')) {
            errorMessage = `❌ Địa chỉ ${tokenAddress} không phải là token ERC-20.`;
          } else if (error.message.includes('Timeout')) {
            errorMessage = `⏱️ Quá thời gian kết nối đến blockchain. Vui lòng thử lại sau.`;
          } else if (error.message.includes('rate limit')) {
            errorMessage = `🔄 Đã vượt quá giới hạn yêu cầu đến blockchain. Vui lòng thử lại sau ít phút.`;
          } else if (error.message.includes('không được hỗ trợ')) {
            errorMessage = `❌ Blockchain ${blockchain} không được hỗ trợ với API Etherscan hiện tại.`;
          }
          
          await ctx.reply(errorMessage);
        }
      }
      // Phân tích nâng cao token
      else if (ctx.session.state === 'analyze_waiting_address' && ctx.session.waitingFor === 'token_address') {
        // Validate địa chỉ token
        if (!text || text.trim() === '') {
          return ctx.reply(getText(lang, 'addressRequired'));
        }
        
        const tokenAddress = text.trim();
        const blockchain = ctx.session.selectedBlockchain;
        
        // Reset trạng thái
        ctx.session.state = null;
        ctx.session.waitingFor = null;
        
        // Thông báo đang phân tích
        const processingMsg = await ctx.reply(
          getText(lang, 'analyzingTokenAdvanced', { address: tokenAddress, network: blockchain })
        );
        
        try {
          // Phân tích token nâng cao
          const analysis = await advancedAnalyzer.analyzeTokenAdvanced(tokenAddress, blockchain);
          
          // Lưu kết quả phân tích cho việc tạo báo cáo sau này
          ctx.session.lastAnalyzedToken = analysis;
          
          // Hiển thị kết quả
          await ctx.reply(getText(lang, 'tokenAnalysisResultAdvanced'));
          
          let riskLevelText;
          switch(analysis.riskLevel) {
            case 'SAFE': riskLevelText = getText(lang, 'riskLevelSafe'); break;
            case 'LOW': riskLevelText = getText(lang, 'riskLevelLow'); break;
            case 'MEDIUM': riskLevelText = getText(lang, 'riskLevelMedium'); break;
            case 'HIGH': riskLevelText = getText(lang, 'riskLevelHigh'); break;
            case 'CRITICAL': riskLevelText = getText(lang, 'riskLevelCritical'); break;
            default: riskLevelText = analysis.riskLevel;
          }
          
          // Tạo thông báo kết quả - tương tự như lệnh check nhưng có thêm thông tin
          let resultMessage = `${getText(lang, 'tokenName', { name: analysis.name })}\n`;
          resultMessage += `${getText(lang, 'tokenSymbol', { symbol: analysis.symbol })}\n`;
          resultMessage += `${getText(lang, 'tokenTotalSupply', { supply: analysis.totalSupply })}\n`;
          resultMessage += `${getText(lang, 'tokenDecimals', { decimals: analysis.decimals })}\n`;
          resultMessage += `${getText(lang, 'tokenAddress', { address: analysis.address })}\n`;
          resultMessage += `${getText(lang, 'tokenBlockchain', { blockchain: analysis.network })}\n`;
          
          // Thông báo về mã nguồn
          if (analysis.sourceCodeVerified) {
            resultMessage += `✅ Mã nguồn đã được xác minh\n`;
          } else {
            resultMessage += `⚠️ Mã nguồn chưa được xác minh\n`;
          }
          
          resultMessage += `${getText(lang, 'tokenRiskLevel', { level: riskLevelText })}\n\n`;
          
          resultMessage += `${getText(lang, 'tokenSecurityIssues')}\n`;
          
          if (analysis.securityIssues.length > 0) {
            analysis.securityIssues.forEach((issue, index) => {
              resultMessage += `${index + 1}. ${issue}\n`;
            });
          } else {
            resultMessage += `${getText(lang, 'tokenNoSecurityIssues')}\n`;
          }
          
          if (analysis.holders && analysis.holders.length > 0) {
            resultMessage += `\nTop ${analysis.holders.length} người giữ token:\n`;
            analysis.holders.slice(0, 3).forEach((holder, index) => {
              resultMessage += `${index + 1}. ${holder.address.substring(0, 8)}...${holder.address.substring(36)} - ${holder.share}%\n`;
            });
          }
          
          // Thêm thông tin chi tiết từ phân tích nâng cao nếu có
          if (analysis.advancedInfo) {
            resultMessage += `\n${getText(lang, 'advancedAnalysisInfo')}\n`;
            for (const [key, value] of Object.entries(analysis.advancedInfo)) {
              resultMessage += `- ${key}: ${value}\n`;
            }
          }
          
          await ctx.reply(resultMessage);
          
          // Hiển thị nút để tạo báo cáo PDF
          await ctx.reply(
            getText(lang, 'createReport'),
            Markup.inlineKeyboard([
              Markup.button.callback(getText(lang, 'downloadReport'), 'generate_report')
            ])
          );
        } catch (error) {
          logger.error(`Lỗi khi phân tích nâng cao token: ${error.message}`);
          
          // Hiển thị thông báo lỗi cụ thể hơn
          let errorMessage = getText(lang, 'advancedAnalysisFailed');
          
          if (error.message.includes('Không thể kết nối')) {
            errorMessage = `⚠️ Không thể kết nối đến blockchain ${blockchain}. Vui lòng thử lại sau hoặc chọn blockchain khác.`;
          } else if (error.message.includes('không phải là hợp đồng') || error.message.includes('không phải là contract')) {
            errorMessage = `❌ Địa chỉ ${tokenAddress} không phải là smart contract hợp lệ.`;
          } else if (error.message.includes('hợp đồng hợp lệ')) {
            errorMessage = `❌ Không thể xác minh ${tokenAddress}. Vui lòng kiểm tra lại địa chỉ.`;
          } else if (error.message.includes('không phải là token ERC-20')) {
            errorMessage = `❌ Địa chỉ ${tokenAddress} không phải là token ERC-20.`;
          } else if (error.message.includes('Timeout')) {
            errorMessage = `⏱️ Quá thời gian kết nối đến blockchain. Vui lòng thử lại sau.`;
          } else if (error.message.includes('rate limit')) {
            errorMessage = `🔄 Đã vượt quá giới hạn yêu cầu đến blockchain. Vui lòng thử lại sau ít phút.`;
          } else if (error.message.includes('không được hỗ trợ')) {
            errorMessage = `❌ Blockchain ${blockchain} không được hỗ trợ với API Etherscan hiện tại.`;
          }
          
          await ctx.reply(errorMessage);
        }
      }
      // Xử lý email
      else if (ctx.session.state === 'waiting_email' && ctx.session.waitingFor === 'email_address') {
        // Validate email
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        if (!emailRegex.test(text)) {
          return ctx.reply(getText(lang, 'invalidEmail'));
        }
        
        const email = text.trim();
        
        // Reset trạng thái
        ctx.session.state = null;
        ctx.session.waitingFor = null;
        
        // Thông báo đang gửi email
        ctx.reply(getText(lang, 'sendingEmail'));
        
        // Tạo báo cáo PDF và gửi email
        pdfGenerator.generateTokenReport(ctx.session.lastAnalyzedToken, lang)
          .then(report => {
            return emailSender.sendReport(
              email,
              report.filePath,
              ctx.session.lastAnalyzedToken,
              lang
            );
          })
          .then(() => {
            ctx.reply(getText(lang, 'emailSent'));
          })
          .catch(error => {
            logger.error('Lỗi khi gửi email:', error);
            ctx.reply(getText(lang, 'emailSendingFailed'));
          });
      }
    });
  }

  // Phương thức hiển thị danh sách blockchain
  showBlockchainOptions(ctx) {
    const lang = ctx.session?.language || 'en';
    
    // Tạo danh sách các nút cho từng blockchain, mỗi hàng 3 nút
    const blockchains = Object.keys(config.blockchains);
    const buttons = [];
    let row = [];
    
    blockchains.forEach((chain, index) => {
      const chainInfo = config.blockchains[chain];
      row.push(
        Markup.button.callback(
          `${chainInfo.icon} ${chainInfo.symbol}`, 
          `chain_${chain}`
        )
      );
      
      // Mỗi hàng 3 nút
      if (row.length === 3 || index === blockchains.length - 1) {
        buttons.push(row);
        row = [];
      }
    });
    
    return ctx.reply(
      getText(lang, 'networkPrompt'),
      Markup.inlineKeyboard(buttons)
    );
  }

  launch() {
    logger.info('Đang kiểm tra kết nối đến Telegram API...');
    this.bot.telegram.getMe()
      .then(() => {
        logger.info('Kết nối đến Telegram API thành công!');
        this.bot.launch();
        logger.info('Bot đã được khởi động!');
        
        // Bắt sự kiện SIGINT và SIGTERM để tắt bot
        process.once('SIGINT', () => this.bot.stop('SIGINT'));
        process.once('SIGTERM', () => this.bot.stop('SIGTERM'));
      })
      .catch(error => {
        logger.error('Lỗi nghiêm trọng khi khởi động bot:', error);
        logger.info('Kiểm tra các vấn đề phổ biến:');
        logger.info('1. Kiểm tra lại token bot trong file .env');
        logger.info('2. Kiểm tra kết nối mạng');
        logger.info('3. Kiểm tra tường lửa hoặc cấu hình proxy');
      });
  }
}

module.exports = TelegramBot;