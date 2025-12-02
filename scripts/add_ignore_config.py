#!/usr/bin/env python3
"""
添加忽略配置到现有配置文件
"""
import json
import argparse
from pathlib import Path

def add_ignore_config(config_file: str):
    """添加忽略配置到配置文件"""
    
    # 读取现有配置
    with open(config_file, 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    # 添加 ignored_files 配置
    if 'ignored_files' not in config:
        config['ignored_files'] = {
            "description": "需要忽略的文件模式（支持 glob 模式）",
            "patterns": [
                "**/third_party/**",
                "**/test/**/*.cpp",
                "**/generated/**",
                "**/build/**",
                "**/.cache/**",
                "**/external/**",
                "**/vendor/**",
                "**/*.pb.cc",
                "**/*.grpc.pb.cc"
            ],
            "exceptions": [
                "**/third_party/catch2/**",
                "**/test/main.cpp"
            ]
        }
    
    # 添加 ignored_issues 配置
    if 'ignored_issues' not in config:
        config['ignored_issues'] = {
            "description": "需要忽略的特定编译问题",
            "patterns": [
                {
                    "file_pattern": "**/third_party/**",
                    "issue_pattern": ".*",
                    "reason": "第三方库代码，不检查"
                },
                {
                    "file_pattern": "**/*.c",
                    "issue_pattern": "warning:.*ISO C.*",
                    "reason": "C语言的ISO标准警告"
                }
            ]
        }
    
    # 保存更新后的配置
    with open(config_file, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2, ensure_ascii=False)
    
    print(f"已添加忽略配置到: {config_file}")

def main():
    parser = argparse.ArgumentParser(description='添加忽略配置到配置文件')
    parser.add_argument('--config', required=True, help='配置文件路径')
    
    args = parser.parse_args()
    
    if not Path(args.config).exists():
        print(f"错误: 配置文件 {args.config} 不存在")
        return
    
    add_ignore_config(args.config)

if __name__ == "__main__":
    main()