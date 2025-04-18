# Bot Kiểm Tra Bảo Mật Token (Token Security Bot)

Bot Telegram cho phép kiểm tra bảo mật của Smart Contract Token trên nhiều blockchain, phát hiện các lỗ hổng bảo mật và phân tích tokenomics.

## Tiến độ phát triển hiện tại

### Đã hoàn thành
- ✅ Cấu trúc cơ bản của dự án
- ✅ Hệ thống đa ngôn ngữ (Anh/Việt)
- ✅ Cấu hình kết nối cho nhiều blockchain
- ✅ Cơ chế referral 2 cấp (F1, F2)
- ✅ Bot Telegram lõi với xử lý command cơ bản
- ✅ Hệ thống ghi log
- ✅ Phân tích và kiểm tra token trên ETH blockchain (lấy source code, phát hiện lỗ hổng)
- ✅ Hiển thị chủ hợp đồng (Contract Owner)
- ✅ Lấy danh sách top 5 ví Holder lớn nhất từ Etherscan
- ✅ Hiển thị thông báo theo ngôn ngữ người dùng đã chọn

### Đang phát triển
- 🔄 Phân tích và kiểm tra token trên các blockchain khác (BSC, ARB, POL, TRC, SUI)
- 🔄 Hệ thống thanh toán crypto
- 🔄 Cấu hình thanh toán bằng USDT
- 🔄 Tạo báo cáo PDF
- 🔄 Theo dõi token theo thời gian thực
- 🔄 Cơ chế fallback khi API Etherscan bị lỗi (sử dụng phân tích giao dịch Transfer)
- 🔄 Phát hiện honeypot bằng kiểm tra hàm và kiểm tra giao dịch lịch sử

### Chưa bắt đầu
- ⏳ Panel quản trị dành cho admin
- ⏳ Gửi báo cáo qua email
- ⏳ Phân tích chi tiết tokenomics

## Tính năng chính

- ✅ Bot hỗ trợ đa ngôn ngữ Anh-Việt, người dùng chọn ngôn ngữ khi khởi động bot
- ✅ Hệ thống thanh toán bằng crypto để sử dụng dịch vụ
- ✅ Hệ thống referral với cơ chế hoa hồng (3% F1, 2% F2)
- ✅ Kiểm tra Token trên các blockchain: ETH, BSC, ARB, POL, TRC, SUI
- ✅ Phân tích thông tin cơ bản (tên, ký hiệu, tổng cung, etc.)
- ✅ Phát hiện lỗ hổng bảo mật (mint function, blacklist, etc.)
- ✅ Kiểm tra phân bổ Tokenomic theo dữ liệu Onchain
- ✅ Hiển thị top 5 holder lớn nhất và tỷ lệ nắm giữ
- ✅ Theo dõi biến động ví holder theo thời gian thực
- ✅ Tạo báo cáo PDF và gửi qua email

## Cấu trúc dự án hiện tại

```
├── app/                      # Thư mục chính của ứng dụng
│   ├── __init__.py           # Package initializer
│   ├── main.py               # Entry point của ứng dụng
│   ├── core/                 # Lõi của bot Telegram
│   │   ├── __init__.py
│   │   ├── bot.py            # Khởi tạo và cấu hình bot
│   ├── blockchain/           # Module xử lý blockchain
│   │   ├── __init__.py
│   │   ├── arb/              # Arbitrum blockchain
│   │   ├── bsc/              # Binance Smart Chain
│   │   ├── eth/              # Ethereum
│   │   │   ├── ethereum_client.py # Xử lý các request đến Ethereum blockchain
│   │   ├── pol/              # Polygon
│   │   ├── sui/              # Sui
│   │   └── trc/              # Tron
│   ├── i18n/                 # Hỗ trợ đa ngôn ngữ
│   │   ├── __init__.py
│   │   ├── text_provider.py  # Quản lý đa ngôn ngữ
│   │   ├── en/               # Tiếng Anh
│   │   │   ├── strings.py    # Các chuỗi tiếng Anh
│   │   └── vi/               # Tiếng Việt
│   │       ├── strings.py    # Các chuỗi tiếng Việt
│   ├── payment/              # Hệ thống thanh toán
│   │   ├── __init__.py
│   │   └── crypto/           # Xử lý thanh toán crypto
│   ├── referral/             # Hệ thống giới thiệu
│   │   ├── __init__.py
│   │   └── referral_system.py # Quản lý referral và hoa hồng
│   ├── security/             # Kiểm tra bảo mật
│   │   ├── __init__.py
│   │   └── checker_manager.py # Quản lý và điều phối các token checker
│   ├── utils/                # Các tiện ích
│   │   ├── __init__.py
│   │   └── logger.py         # Hệ thống ghi log
│   ├── admin/                # Panel quản trị
│   │   └── __init__.py
│   └── reporting/            # Tạo báo cáo
│       ├── __init__.py
│       └── report_generator.py # Sinh báo cáo
├── config/                   # Cấu hình hệ thống
│   ├── __init__.py
│   └── config.py             # Cấu hình biến môi trường
├── data/                     # Lưu trữ dữ liệu
├── logs/                     # Log hệ thống
├── reports/                  # Báo cáo được tạo
├── requirements.txt          # Phụ thuộc Python
├── .env                      # File cấu hình môi trường
└── README.md                 # Tài liệu dự án
```

## Cấu hình môi trường (.env)

File `.env` chứa các thông tin cấu hình quan trọng:

- Telegram Bot Token
- API Keys cho các blockchain khác nhau
- Thông tin ví thanh toán
- Cấu hình MongoDB
- Cài đặt giá dịch vụ
- Cấu hình hệ thống referral

## Yêu cầu hệ thống

- Python 3.8+
- MongoDB (đã cấu hình sẵn)
- Kết nối internet để tương tác với các blockchain

## Thiết lập môi trường

1. Tạo và kích hoạt môi trường ảo Python:
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```

2. Cài đặt các phụ thuộc:
```bash
pip install -r requirements.txt
```

3. Khởi động bot:
```bash
python -m app.main
```

## Phát triển tiếp theo

Các tính năng sẽ được phát triển thêm trong giai đoạn tiếp theo:

1. Hoàn thiện phân tích bảo mật token trên tất cả các blockchain
2. Triển khai hệ thống thanh toán crypto đầy đủ
3. Cải tiến giao diện người dùng trên Telegram
4. Hoàn thiện hệ thống báo cáo và giám sát token
5. Xây dựng bảng điều khiển quản trị cho admin
6. Bổ sung thêm các tính năng phát hiện lỗ hổng nâng cao
7. Kiểm tra thanh khoản DEX chính xác
8. Phát hiện scam token dựa trên phân tích mẫu
