#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Vietnamese language strings
"""

VI_STRINGS = {
    # Common
    'welcome': 'Chào mừng đến với Bot Kiểm tra Bảo mật Token!',
    'language_prompt': 'Vui lòng chọn ngôn ngữ của bạn:',
    'language_selected': 'Đã chọn Tiếng Việt!',
    'start_message': 'Bot này giúp bạn phân tích bảo mật token trên nhiều blockchain.',
    'blockchain_prompt': 'Vui lòng chọn mạng lưới blockchain để phân tích token:',
    'blockchain_selected': 'Bạn đã chọn mạng lưới {network}.',
    
    # Commands help
    'command_help': """Danh sách lệnh:
/start - Khởi động bot
/help - Hiển thị trợ giúp
/check - Kiểm tra bảo mật token
/report - Tạo báo cáo PDF
/balance - Xem số dư của bạn
/referral - Xem link giới thiệu của bạn
/email - Gửi báo cáo qua email
/language - Thay đổi ngôn ngữ""",
    
    # Errors and messages
    'invalid_syntax': 'Cú pháp không hợp lệ. Vui lòng thử lại.',
    'unsupported_blockchain': 'Blockchain không được hỗ trợ. Các blockchain được hỗ trợ: {chains}',
    'feature_in_development': 'Tính năng này đang được phát triển. Vui lòng thử lại sau.',
    
    # Referral
    'referral_link': 'Đây là link giới thiệu của bạn, hãy chia sẻ nếu bạn thấy Bot hữu ích:\n{link}',
    'referral_stats': 'Thống kê giới thiệu của bạn:\n- Giới thiệu trực tiếp (F1): {direct}\n- Giới thiệu gián tiếp (F2): {indirect}',
    
    # Token analysis
    'enter_address': 'Vui lòng nhập địa chỉ hợp đồng token:',
    'processing_address': 'Đang xử lý địa chỉ...',
    'address_required': 'Vui lòng nhập địa chỉ hợp đồng hợp lệ.',
    'analyzing_token': 'Đang phân tích token {address} trên mạng {network}. Vui lòng đợi, quá trình này có thể mất một lúc...',
    'security_check_results': '🔒 KẾT QUẢ KIỂM TRA BẢO MẬT 🔒\n\n✅ Không phát hiện honeypot\n✅ Hợp đồng đã được xác minh\n✅ Không có hàm tự hủy\n✅ Không có hàm danh sách đen\n✅ Không có hàm tạo thêm token\n\nĐiểm bảo mật tổng thể: 95/100',
    'advanced_analysis_results': '📊 KẾT QUẢ PHÂN TÍCH NÂNG CAO 📊\n\nPhân phối Token:\n- 10 người sở hữu lớn nhất nắm giữ 35% tổng cung\n- Ví nhà phát triển nắm giữ 3% tổng cung\n- Thanh khoản đã được khóa trong 365 ngày\n\nTác động khi Swap (1 ETH):\n- Thuế mua: 2%\n- Thuế bán: 3%\n- Ảnh hưởng giá: 0.5%\n\nĐánh giá rủi ro: THẤP',
    'token_analysis_result': 'Kết quả phân tích Token:',
    'token_name': 'Tên',
    'token_symbol': 'Ký hiệu',
    'token_total_supply': 'Tổng cung',
    'token_decimals': 'Số thập phân',
    'token_address': 'Địa chỉ hợp đồng',
    'token_blockchain': 'Blockchain',
    'token_owner': 'Chủ sở hữu',
    'token_risk_level': 'Mức độ rủi ro',
    'token_security_issues': 'Vấn đề bảo mật:',
    'token_no_security_issues': 'Không tìm thấy vấn đề bảo mật!',
    'token_not_found': 'Không tìm thấy token hoặc không phải là token hợp lệ',
    'analysis_failed': 'Phân tích thất bại. Vui lòng thử lại sau.',
    
    # Reports
    'download_report': 'Tải báo cáo PDF',
    'no_analysis_available': 'Chưa có phân tích token nào. Vui lòng phân tích token trước bằng lệnh /check.',
    'generating_report': 'Đang tạo báo cáo PDF...',
    'report_generation_failed': 'Không thể tạo báo cáo. Vui lòng thử lại sau.',
    
    # Email
    'enter_email': 'Vui lòng nhập địa chỉ email của bạn để nhận báo cáo:',
    'invalid_email': 'Địa chỉ email không hợp lệ. Vui lòng nhập email hợp lệ.',
    'sending_email': 'Đang gửi email. Quá trình này có thể mất một lúc...',
    'email_sent': 'Báo cáo đã được gửi đến email của bạn!',
    'email_sending_failed': 'Không thể gửi email. Vui lòng thử lại sau.',
    
    # Risk levels
    'risk_level_safe': 'ÍT RỦI RO',
    'risk_level_low': 'ÍT RỦI RO',
    'risk_level_medium': 'RỦI RO TRUNG BÌNH',
    'risk_level_high': 'RỦI RO CAO',
    'risk_level_critical': 'CỰC KỲ RỦI RO',
    
    # Payment
    'payment_required': 'Tính năng này yêu cầu thanh toán để sử dụng.',
    'payment_instructions': 'Vui lòng gửi {amount} USDT đến địa chỉ sau:',
    'payment_waiting': 'Đang đợi xác nhận thanh toán...',
    'payment_confirmed': 'Đã xác nhận thanh toán! Bạn có thể sử dụng tính năng ngay bây giờ.',
    'payment_failed': 'Xác minh thanh toán thất bại. Vui lòng thử lại hoặc liên hệ hỗ trợ.',
    'insufficient_balance': 'Số dư của bạn không đủ. Số dư hiện tại: {balance} USDT',
    
    # Balance
    'balance_info': 'Số dư hiện tại của bạn: {balance} USDT\nThu nhập từ giới thiệu: {referral} USDT',
    
    # Admin panel
    'admin_panel': 'Bảng điều khiển Admin - Chọn một tùy chọn:',
    'admin_prices': 'Cài đặt giá',
    'admin_users': 'Quản lý người dùng',
    'admin_stats': 'Thống kê',
    'admin_access_denied': 'Truy cập bị từ chối. Bạn không được phép sử dụng lệnh admin.',
    
    # Command list
    'command_list': "Danh sách lệnh:\n" \
                 "/start - Khởi động bot\n" \
                 "/help - Hiển thị trợ giúp\n" \
                 "/check - Kiểm tra bảo mật và phân tích token nâng cao\n" \
                 "/report - Tạo báo cáo PDF\n" \
                 "/balance - Xem số dư của bạn\n" \
                 "/referral - Xem link giới thiệu của bạn\n" \
                 "/email - Gửi báo cáo qua email\n" \
                 "/language - Thay đổi ngôn ngữ",
    'command_list_intro': "Đây là các lệnh để sử dụng Bot:",
    
    # Security analysis header
    'security_analysis_header': 'PHÂN TÍCH SMART CONTRACT',
    'token_info_header': 'THÔNG TIN TOKEN',
    'dangerous_functions': 'CÁC CHỨC NĂNG NGUY HIỂM',
    'risk_assessment': 'ĐÁNH GIÁ',
    
    # Token info
    'total_supply': 'Tổng cung',
    'holder_count': 'Tổng số ví Holder',
    'dex_liquidity': 'Bể thanh khoản (DEX)',
    'transaction_tax': 'Thuế giao dịch',
    'tax_info': 'Mua {buy} / Bán {sell}',
    'contract_owner': 'Ví chủ hợp đồng',
    
    # Dangerous functions
    'has_mint_warning': 'Có thể phát hành thêm Token vô hạn',
    'has_blacklist_warning': 'Hợp đồng có chức năng khóa ví người dùng',
    'has_pause_warning': 'Chủ hợp đồng có thể tạm dừng giao dịch (chỉ mua được, không bán được)',
    'has_revoke_warning': 'Chủ hợp đồng có thể sửa đổi số dư từ ví người dùng',
    'has_self_destruct_warning': 'Hợp đồng có chức năng tự hủy',
    'honeypot_warning': 'Có khả năng là honeypot',
    'no_dangerous_functions': 'Không phát hiện chức năng nguy hiểm trong hợp đồng này',
    'contract_not_verified_warning': 'Hợp đồng chưa được xác minh trên Etherscan',
    
    # Risk assessment
    'critical_risk': 'CỰC KỲ RỦI RO',
    'critical_risk_description': 'CỰC KỲ RỦI RO: Hợp đồng này chứa lỗ hổng rất nguy hiểm, nguy cơ bị lừa đảo khi đầu tư rất cao, hãy cân nhắc thật kỹ',
    'high_risk': 'RỦI RO CAO',
    'high_risk_description': 'RỦI RO CAO: Hợp đồng tích hợp những chức năng có khả năng gây thiệt hại cho NĐT, hãy tìm hiểu thật kỹ về dự án trước khi ra quyết định đầu tư',
    'low_risk_description': 'Không phát hiện các chức năng nguy hiểm trong hợp đồng này, tìm hiểu kỹ các yếu tố khác trước khi quyết định đầu tư',
    
    # Check result
    'check_failed': 'Kiểm tra token thất bại. Vui lòng thử lại sau.',
    
    # Status
    'not_verified': 'Chưa xác minh',
    
    # Disclaimer
    'analysis_disclaimer': 'Ghi chú: Bot tổng hợp và đánh giá độ rủi ro dựa vào source code trực tiếp trên Blockchain, thông tin mang tính chất tham khảo. Người dùng tự cân nhắc và chịu trách nhiệm với quyết định đầu tư của mình!',
} 