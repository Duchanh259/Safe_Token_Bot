#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Tệp kiểm tra về việc lấy tổng số holder của token.
Được sử dụng để gỡ lỗi và xác định nguyên nhân không lấy được số holder.
"""

import os
import sys
import json
import asyncio
import logging
from dotenv import load_dotenv

# Thêm thư mục gốc vào path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Cấu hình logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

# Tải biến môi trường
load_dotenv()

from app.blockchain.eth.ethereum_client import ethereum_client

async def test_token_holders(token_address):
    """Thử lấy tổng số holder của một token."""
    print(f"\n==== Kiểm tra tổng số holder cho token: {token_address} ====\n")
    
    # Gọi phương thức get_token_holders
    result = await ethereum_client.get_token_holders(token_address)
    
    # Hiển thị kết quả
    print("\n==== KẾT QUẢ ====")
    print(f"Tổng số holder: {result.get('total_holders_count', 0)}")
    print(f"Lỗi: {result.get('error', 'Không có')}")
    
    # In thông tin debug nhưng bỏ nội dung lớn
    debug_info = result.get('debug_info', {})
    simplified_debug = {}
    
    for key, value in debug_info.items():
        if isinstance(value, dict) and len(str(value)) > 200:
            # Với dữ liệu JSON lớn, chỉ hiển thị thông tin tóm tắt
            if "response" in key.lower():
                try:
                    status = value.get("status", "N/A")
                    message = value.get("message", "N/A")
                    simplified_debug[key] = f"[Đã tóm tắt] status: {status}, message: {message}"
                    
                    # Đối với phản hồi tokenholderlist, kiểm tra cấu trúc kết quả
                    if "holder" in key.lower() and "result" in value:
                        result_data = value["result"]
                        if isinstance(result_data, list):
                            simplified_debug[f"{key}_result_count"] = len(result_data)
                            if len(result_data) > 0:
                                simplified_debug[f"{key}_sample"] = result_data[0]
                except Exception as e:
                    simplified_debug[key] = f"[Không thể tóm tắt]: {str(e)}"
            else:
                simplified_debug[key] = f"[Dữ liệu lớn, {len(str(value))} bytes]"
        else:
            simplified_debug[key] = value
    
    print("\n==== THÔNG TIN GỠ LỖI ====")
    print(json.dumps(simplified_debug, indent=2, ensure_ascii=False))
    
    # Nếu có các lỗi cụ thể, hiển thị chi tiết hơn
    if "tokenholderlist_api_response" in debug_info:
        response = debug_info["tokenholderlist_api_response"]
        if response.get("status") == "0":
            print(f"\n==== LỖI API TOKENHOLDERLIST ====")
            print(f"Message: {response.get('message', 'Không có thông báo')}")
            print(f"Result: {response.get('result', 'Không có kết quả')}")
    
    # Nếu có tokeninfo_api_response, phân tích cấu trúc
    if "tokeninfo_api_response" in debug_info:
        response = debug_info["tokeninfo_api_response"]
        if response.get("status") == "1" and "result" in response:
            print(f"\n==== CẤU TRÚC DỮ LIỆU TOKENINFO ====")
            for item in response["result"]:
                # Tìm tất cả các trường liên quan đến holder
                for key, value in item.items():
                    if "holder" in key.lower():
                        print(f"Tìm thấy trường liên quan: {key} = {value}")

async def main():
    """Hàm chính để thử nghiệm."""
    # Danh sách các token để kiểm tra
    tokens = [
        "0xd794dd1cada4cf79c9eebaab8327a1b0507ef7d4",  # Token trong ví dụ
        "0xdac17f958d2ee523a2206206994597c13d831ec7",  # USDT
        "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48",  # USDC
        "0x7d1afa7b718fb893db30a3abc0cfc608aacfebb0"   # MATIC
    ]
    
    for token in tokens:
        await test_token_holders(token)
        print("\n" + "="*50 + "\n")

if __name__ == "__main__":
    asyncio.run(main()) 