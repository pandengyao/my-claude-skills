#!/usr/bin/env python3
"""
加解密命令行工具
支持单个和批量加解密操作

使用方式:
    # 单个加密
    python3 crypto_cli.py encrypt --data "hello" --algorithm AES --key mykey
    
    # 单个解密
    python3 crypto_cli.py decrypt --data "encrypted" --algorithm AES --key mykey
    
    # 批量加密（从文件读取）
    python3 crypto_cli.py batch-encrypt --input data.txt --algorithm AES --key mykey
    
    # 批量解密
    python3 crypto_cli.py batch-decrypt --input encrypted.txt --algorithm AES --key mykey
    
    # 哈希密码
    python3 crypto_cli.py hash --data "password" --algorithm SHA256 --salt mysalt
    
    # 列出所有算法
    python3 crypto_cli.py list-algorithms
"""

import sys
import os
import argparse
import json
from pathlib import Path

# 添加项目根目录到Python路径（以便正确导入src模块）
sys.path.insert(0, str(Path(__file__).parent.parent))

from src import CryptoManager, encrypt, decrypt, hash_password


def cmd_encrypt(args):
    """加密单个数据"""
    try:
        # 准备额外参数
        kwargs = {}
        if args.iv:
            kwargs['iv'] = args.iv
        if args.salt:
            kwargs['salt'] = args.salt
        if args.public_key_path:
            kwargs['public_key_path'] = args.public_key_path
        
        # 执行加密
        result = encrypt(args.data, args.algorithm, args.key, **kwargs)
        
        # 输出结果
        if args.output:
            with open(args.output, 'w') as f:
                f.write(result)
            print(f"✅ 加密完成，结果已保存到: {args.output}")
        else:
            print(result)
            
    except Exception as e:
        print(f"❌ 加密失败: {e}", file=sys.stderr)
        sys.exit(1)


def cmd_decrypt(args):
    """解密单个数据"""
    try:
        # 准备额外参数
        kwargs = {}
        if args.iv:
            kwargs['iv'] = args.iv
        if args.private_key_path:
            kwargs['private_key_path'] = args.private_key_path
        
        # 执行解密
        result = decrypt(args.data, args.algorithm, args.key, **kwargs)
        
        # 输出结果
        if args.output:
            with open(args.output, 'w') as f:
                f.write(result)
            print(f"✅ 解密完成，结果已保存到: {args.output}")
        else:
            print(result)
            
    except Exception as e:
        print(f"❌ 解密失败: {e}", file=sys.stderr)
        sys.exit(1)


def cmd_batch_encrypt(args):
    """批量加密数据"""
    try:
        # 读取输入文件
        with open(args.input, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # 准备额外参数
        kwargs = {}
        if args.iv:
            kwargs['iv'] = args.iv
        if args.salt:
            kwargs['salt'] = args.salt
        if args.public_key_path:
            kwargs['public_key_path'] = args.public_key_path
        
        results = []
        success_count = 0
        fail_count = 0
        
        print(f"开始批量加密 {len(lines)} 条数据...")
        
        for i, line in enumerate(lines, 1):
            line = line.strip()
            if not line:  # 跳过空行
                continue
            
            try:
                encrypted = encrypt(line, args.algorithm, args.key, **kwargs)
                results.append(encrypted)
                success_count += 1
                if args.verbose:
                    print(f"[{i}/{len(lines)}] ✅ {line[:50]}...")
            except Exception as e:
                results.append(f"ERROR: {e}")
                fail_count += 1
                if args.verbose:
                    print(f"[{i}/{len(lines)}] ❌ 失败: {e}")
        
        # 保存结果
        output_file = args.output or f"{args.input}.encrypted"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(results))
        
        print(f"\n批量加密完成:")
        print(f"  成功: {success_count} 条")
        print(f"  失败: {fail_count} 条")
        print(f"  结果已保存到: {output_file}")
        
    except FileNotFoundError:
        print(f"❌ 文件不存在: {args.input}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"❌ 批量加密失败: {e}", file=sys.stderr)
        sys.exit(1)


def cmd_batch_decrypt(args):
    """批量解密数据"""
    try:
        # 读取输入文件
        with open(args.input, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # 准备额外参数
        kwargs = {}
        if args.iv:
            kwargs['iv'] = args.iv
        if args.private_key_path:
            kwargs['private_key_path'] = args.private_key_path
        
        results = []
        success_count = 0
        fail_count = 0
        
        print(f"开始批量解密 {len(lines)} 条数据...")
        
        for i, line in enumerate(lines, 1):
            line = line.strip()
            if not line or line.startswith('ERROR:'):  # 跳过空行和错误行
                results.append(line)
                continue
            
            try:
                decrypted = decrypt(line, args.algorithm, args.key, **kwargs)
                results.append(decrypted)
                success_count += 1
                if args.verbose:
                    print(f"[{i}/{len(lines)}] ✅ 解密成功")
            except Exception as e:
                results.append(f"ERROR: {e}")
                fail_count += 1
                if args.verbose:
                    print(f"[{i}/{len(lines)}] ❌ 失败: {e}")
        
        # 保存结果
        output_file = args.output or f"{args.input}.decrypted"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(results))
        
        print(f"\n批量解密完成:")
        print(f"  成功: {success_count} 条")
        print(f"  失败: {fail_count} 条")
        print(f"  结果已保存到: {output_file}")
        
    except FileNotFoundError:
        print(f"❌ 文件不存在: {args.input}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"❌ 批量解密失败: {e}", file=sys.stderr)
        sys.exit(1)


def cmd_hash(args):
    """哈希数据"""
    try:
        result = hash_password(args.data, args.algorithm, args.salt)
        
        if args.output:
            with open(args.output, 'w') as f:
                f.write(result)
            print(f"✅ 哈希完成，结果已保存到: {args.output}")
        else:
            print(result)
            
    except Exception as e:
        print(f"❌ 哈希失败: {e}", file=sys.stderr)
        sys.exit(1)


def cmd_list_algorithms(args):
    """列出所有可用算法"""
    algorithms = CryptoManager.list_algorithms()
    
    print("可用的加密算法:")
    print("-" * 50)
    for name, algo_type in sorted(algorithms.items()):
        info = CryptoManager.get_algorithm_info(name)
        print(f"{name:10s} | 类型: {algo_type:12s} | {info['class']}")
    print("-" * 50)
    print(f"共 {len(algorithms)} 种算法")


def cmd_generate_sample(args):
    """生成示例数据文件"""
    sample_data = """hello world
测试数据123
sensitive information
user@example.com
13800138000"""
    
    output_file = args.output or "sample_data.txt"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(sample_data)
    
    print(f"✅ 示例数据已生成: {output_file}")
    print("内容:")
    print(sample_data)


def main():
    parser = argparse.ArgumentParser(
        description='加解密命令行工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 加密单个数据
  python3 crypto_cli.py encrypt --data "hello" --algorithm AES --key mykey
  
  # 解密
  python3 crypto_cli.py decrypt --data "encrypted_text" --algorithm AES --key mykey
  
  # 批量加密
  python3 crypto_cli.py batch-encrypt --input data.txt --algorithm AES --key mykey
  
  # 批量解密
  python3 crypto_cli.py batch-decrypt --input data.txt.encrypted --algorithm AES --key mykey
  
  # 哈希密码
  python3 crypto_cli.py hash --data "password" --algorithm SHA256 --salt mysalt
  
  # 生成示例文件
  python3 crypto_cli.py generate-sample
  
  # 列出算法
  python3 crypto_cli.py list-algorithms
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='子命令')
    
    # encrypt 命令
    parser_encrypt = subparsers.add_parser('encrypt', help='加密单个数据')
    parser_encrypt.add_argument('--data', required=True, help='要加密的数据')
    parser_encrypt.add_argument('--algorithm', default='AES', help='加密算法 (默认: AES)')
    parser_encrypt.add_argument('--key', help='密钥')
    parser_encrypt.add_argument('--iv', help='初始化向量 (AES)')
    parser_encrypt.add_argument('--salt', help='盐值 (哈希算法)')
    parser_encrypt.add_argument('--public-key-path', help='公钥文件路径 (RSA)')
    parser_encrypt.add_argument('--output', '-o', help='输出文件路径')
    
    # decrypt 命令
    parser_decrypt = subparsers.add_parser('decrypt', help='解密单个数据')
    parser_decrypt.add_argument('--data', required=True, help='要解密的数据')
    parser_decrypt.add_argument('--algorithm', default='AES', help='加密算法 (默认: AES)')
    parser_decrypt.add_argument('--key', help='密钥')
    parser_decrypt.add_argument('--iv', help='初始化向量 (AES)')
    parser_decrypt.add_argument('--private-key-path', help='私钥文件路径 (RSA)')
    parser_decrypt.add_argument('--output', '-o', help='输出文件路径')
    
    # batch-encrypt 命令
    parser_batch_encrypt = subparsers.add_parser('batch-encrypt', help='批量加密')
    parser_batch_encrypt.add_argument('--input', '-i', required=True, help='输入文件（每行一条数据）')
    parser_batch_encrypt.add_argument('--algorithm', default='AES', help='加密算法 (默认: AES)')
    parser_batch_encrypt.add_argument('--key', help='密钥')
    parser_batch_encrypt.add_argument('--iv', help='初始化向量 (AES)')
    parser_batch_encrypt.add_argument('--salt', help='盐值 (哈希算法)')
    parser_batch_encrypt.add_argument('--public-key-path', help='公钥文件路径 (RSA)')
    parser_batch_encrypt.add_argument('--output', '-o', help='输出文件路径')
    parser_batch_encrypt.add_argument('--verbose', '-v', action='store_true', help='显示详细信息')
    
    # batch-decrypt 命令
    parser_batch_decrypt = subparsers.add_parser('batch-decrypt', help='批量解密')
    parser_batch_decrypt.add_argument('--input', '-i', required=True, help='输入文件（每行一条加密数据）')
    parser_batch_decrypt.add_argument('--algorithm', default='AES', help='加密算法 (默认: AES)')
    parser_batch_decrypt.add_argument('--key', help='密钥')
    parser_batch_decrypt.add_argument('--iv', help='初始化向量 (AES)')
    parser_batch_decrypt.add_argument('--private-key-path', help='私钥文件路径 (RSA)')
    parser_batch_decrypt.add_argument('--output', '-o', help='输出文件路径')
    parser_batch_decrypt.add_argument('--verbose', '-v', action='store_true', help='显示详细信息')
    
    # hash 命令
    parser_hash = subparsers.add_parser('hash', help='哈希数据')
    parser_hash.add_argument('--data', required=True, help='要哈希的数据')
    parser_hash.add_argument('--algorithm', default='SHA256', help='哈希算法 (默认: SHA256)')
    parser_hash.add_argument('--salt', help='盐值')
    parser_hash.add_argument('--output', '-o', help='输出文件路径')
    
    # list-algorithms 命令
    parser_list = subparsers.add_parser('list-algorithms', help='列出所有可用算法')
    
    # generate-sample 命令
    parser_sample = subparsers.add_parser('generate-sample', help='生成示例数据文件')
    parser_sample.add_argument('--output', '-o', help='输出文件路径')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    # 执行对应的命令
    if args.command == 'encrypt':
        cmd_encrypt(args)
    elif args.command == 'decrypt':
        cmd_decrypt(args)
    elif args.command == 'batch-encrypt':
        cmd_batch_encrypt(args)
    elif args.command == 'batch-decrypt':
        cmd_batch_decrypt(args)
    elif args.command == 'hash':
        cmd_hash(args)
    elif args.command == 'list-algorithms':
        cmd_list_algorithms(args)
    elif args.command == 'generate-sample':
        cmd_generate_sample(args)


if __name__ == '__main__':
    main()
