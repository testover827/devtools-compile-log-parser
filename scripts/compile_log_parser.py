#!/usr/bin/env python3
"""
解析编译日志中的错误和警告 - 支持文件忽略的版本
"""
import re
import json
import sys
import argparse
from pathlib import Path
from typing import List, Dict, Optional

# 导入文件匹配器
sys.path.append(str(Path(__file__).parent.parent))
from scripts.file_matcher import FileMatcher

class EnhancedCompileLogParser:
    """增强的编译日志解析器，支持文件忽略"""
    
    def __init__(self, config_file: str, base_dir: str = "."):
        self.config_file = config_file
        self.base_dir = base_dir
        
        # 加载配置
        with open(config_file, 'r', encoding='utf-8') as f:
            self.config_data = json.load(f)
        
        # 初始化文件匹配器
        self.file_matcher = FileMatcher(base_dir)
        self.file_matcher.load_config(self.config_data)
        
        # 初始化统计
        self.issues: List[Dict] = []
        self.ignored_issues: List[Dict] = []
        self.stats = {
            'total_issues_found': 0,
            'total_issues_kept': 0,
            'total_issues_ignored': 0,
            'files_affected': set(),
            'files_ignored': set(),
            'by_severity': {'high': 0, 'medium': 0, 'low': 0},
            'by_pattern': {},
            'ignore_reasons': {}
        }
    
    def parse_file(self, log_file: str) -> Dict:
        """解析日志文件，应用文件忽略规则"""
        with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
        
        i = 0
        while i < len(lines):
            line = lines[i].rstrip()
            
            if not line:
                i += 1
                continue
            
            # 解析问题（这里简化，实际应调用具体的解析逻辑）
            issue = self._parse_line(line, lines, i)
            
            if issue:
                self.stats['total_issues_found'] += 1
                
                # 检查是否应该忽略
                file_path = issue.get('file', '')
                issue_message = issue.get('message', '')
                
                should_ignore, reason = self.file_matcher.is_issue_ignored(
                    file_path, issue_message
                )
                
                if should_ignore:
                    # 记录忽略的问题
                    issue['ignore_reason'] = reason
                    self.ignored_issues.append(issue)
                    self.stats['total_issues_ignored'] += 1
                    self.stats['files_ignored'].add(file_path)
                    
                    # 统计忽略原因
                    self.stats['ignore_reasons'][reason] = \
                        self.stats['ignore_reasons'].get(reason, 0) + 1
                else:
                    # 保留问题
                    self.issues.append(issue)
                    self.stats['total_issues_kept'] += 1
                    self.stats['files_affected'].add(file_path)
                    
                    # 更新其他统计
                    severity = issue.get('severity', 'low')
                    self.stats['by_severity'][severity] += 1
                    
                    pattern_key = issue.get('pattern_key', 'unknown')
                    self.stats['by_pattern'][pattern_key] = \
                        self.stats['by_pattern'].get(pattern_key, 0) + 1
            
            i += 1
        
        return self._generate_report()
    
    def _parse_line(self, line: str, lines: List[str], idx: int) -> Optional[Dict]:
        """解析单行日志（简化的示例）"""
        # 这里应该调用实际的解析逻辑
        # 为了示例，使用简单的正则匹配
        patterns = [
            (r'^([^:]+):(\d+):(?:\d+:)?\s*(error|warning|note):\s*(.+)$', 
             ['file', 'line', 'type', 'message']),
            (r'^([^(]+)\((\d+)(?:,(\d+))?\)\s*:\s*(error|warning)\s+([A-Z]+\d+):\s*(.+)$',
             ['file', 'line', 'column', 'type', 'code', 'message'])
        ]
        
        for pattern, groups in patterns:
            match = re.match(pattern, line)
            if match:
                issue = {'raw_line': line}
                
                # 提取分组
                for i, group_name in enumerate(groups):
                    if i < len(match.groups()):
                        issue[group_name] = match.group(i + 1)
                
                # 设置默认值
                issue.setdefault('file', 'unknown')
                issue.setdefault('line', 0)
                issue.setdefault('type', 'unknown')
                issue.setdefault('message', '')
                
                # 确定严重程度
                issue['severity'] = self._determine_severity(
                    issue.get('type', ''), 
                    issue.get('message', '')
                )
                
                # 添加模式键
                issue['pattern_key'] = 'custom_pattern'
                
                return issue
        
        return None
    
    def _determine_severity(self, issue_type: str, message: str) -> str:
        """确定问题严重程度"""
        severity_rules = self.config_data.get('severity_rules', {})
        
        msg_lower = message.lower()
        
        # 检查关键词
        for severity, keywords in severity_rules.items():
            severity_level = severity.replace('_severity_keywords', '')
            for keyword in keywords:
                if keyword.lower() in msg_lower:
                    return severity_level
        
        # 默认
        if 'error' in issue_type.lower():
            return 'high'
        elif 'warning' in issue_type.lower():
            return 'medium'
        return 'low'
    
    def _generate_report(self) -> Dict:
        """生成包含忽略信息的报告"""
        return {
            "summary": {
                "total_issues_found": self.stats['total_issues_found'],
                "issues_kept": self.stats['total_issues_kept'],
                "issues_ignored": self.stats['total_issues_ignored'],
                "ignore_rate": self.stats['total_issues_ignored'] / 
                              max(self.stats['total_issues_found'], 1),
                "files_affected": len(self.stats['files_affected']),
                "files_ignored": len(self.stats['files_ignored']),
                "by_severity": self.stats['by_severity'],
                "by_pattern": self.stats['by_pattern'],
                "ignore_reasons": self.stats['ignore_reasons']
            },
            "issues": self.issues,
            "ignored_issues": self.ignored_issues[:100],  # 只保留前100个，避免报告过大
            "config_used": {
                "config_file": self.config_file,
                "ignored_patterns": self.file_matcher.ignored_patterns,
                "exception_patterns": self.file_matcher.exception_patterns
            }
        }

def main():
    parser = argparse.ArgumentParser(description='支持文件忽略的编译日志解析器')
    parser.add_argument('--logfile', required=True, help='编译日志文件')
    parser.add_argument('--output', required=True, help='输出JSON文件')
    parser.add_argument('--config', default='config/patterns.json', 
                       help='模式配置文件路径')
    parser.add_argument('--base-dir', default='.', 
                       help='基础目录，用于计算相对路径')
    
    args = parser.parse_args()
    
    # 检查配置文件
    if not Path(args.config).exists():
        print(f"错误: 配置文件 {args.config} 不存在")
        sys.exit(1)
    
    # 解析日志
    parser = EnhancedCompileLogParser(args.config, args.base_dir)
    report = parser.parse_file(args.logfile)
    
    # 保存报告
    with open(args.output, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    # 打印摘要
    summary = report['summary']
    print(f"编译问题分析 (使用配置: {args.config}):")
    print(f"  发现的总问题数: {summary['total_issues_found']}")
    print(f"  保留的问题数: {summary['issues_kept']}")
    print(f"  忽略的问题数: {summary['issues_ignored']}")
    print(f"  忽略率: {summary['ignore_rate']:.1%}")
    print(f"  受影响文件: {summary['files_affected']}")
    print(f"  忽略的文件: {summary['files_ignored']}")
    
    if summary['ignore_reasons']:
        print(f"  忽略原因分布:")
        for reason, count in summary['ignore_reasons'].items():
            print(f"    {reason}: {count}")
    
    print(f"  结果已保存到: {args.output}")

if __name__ == "__main__":
    main()
