const fs = require('fs');
const path = require('path');

// Đảm bảo thư mục logs tồn tại
const logsDir = path.join(__dirname, '../../logs');
if (!fs.existsSync(logsDir)) {
  fs.mkdirSync(logsDir, { recursive: true });
}

const logFilePath = path.join(logsDir, `${new Date().toISOString().split('T')[0]}.log`);

function formatLogMessage(level, message) {
  const timestamp = new Date().toISOString();
  return `[${timestamp}] [${level.toUpperCase()}] ${message}\n`;
}

function appendToLogFile(message) {
  fs.appendFileSync(logFilePath, message);
}

function info(message) {
  const formattedMessage = formatLogMessage('info', message);
  console.log(formattedMessage);
  appendToLogFile(formattedMessage);
}

function error(message, err) {
  let formattedMessage = formatLogMessage('error', message);
  
  if (err) {
    formattedMessage += `${err.stack || err}\n`;
  }
  
  console.error(formattedMessage);
  appendToLogFile(formattedMessage);
}

function warn(message) {
  const formattedMessage = formatLogMessage('warn', message);
  console.warn(formattedMessage);
  appendToLogFile(formattedMessage);
}

function debug(message) {
  const formattedMessage = formatLogMessage('debug', message);
  console.debug(formattedMessage);
  appendToLogFile(formattedMessage);
}

module.exports = {
  info,
  error,
  warn,
  debug
};