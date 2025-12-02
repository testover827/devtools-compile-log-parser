#!/usr/bin/env python3
"""
匹配代码修改和编译问题 - 支持文件忽略的版本
"""
import json
import sys
import argparse
from pathlib import Path
from typing import List, Dict, Any

sys.path.append(str(Path(__file__).parent.parent))
from scripts.file_matcher import FileMatcher

class EnhancedResultMatcher:
    """增强的结果匹配器，支持文件忽略"""
    
    def __init__(self, config_file: str, base_dir: str = "."):
        self.config_file = config_file
        
        # 加载配置
        with open(config_file, 'r', encoding='utf-8') as f:
            self.config_data = json.load(f)
        
        # 初始化文件匹配器
        self.file_matcher = FileMatcher(base_dir)
        self.file_matcher.load_config(self.config_data)
        
        self.matched_issues: List[Dict] = []
        self.unmatched_changes: List[Dict] = []
        self.unmatched_issues: List[Dict] = []
        self.ignored_changes: List[Dict] = []  # 新增：忽略的修改
        self.ignored_issues: List[Dict] = []   # 新增：忽略的问题
    
    def match(self, changes_data: Dict, issues_data: Dict) -> Dict:
        """匹配修改和问题，应用忽略规则"""
        # 过滤掉应该忽略的修改
        all_changes = changes_data.get('changes', [])
        filtered_changes = self._filter_changes(all_changes)
        
        # 过滤掉应该忽略的问题
        all_issues = issues_data.get('issues', [])
        filtered_issues = self._filter_issues(all_issues)
        
        # 执行匹配逻辑（这里简化，实际应调用原有的匹配逻辑）
        self._perform_matching(filtered_changes, filtered_issues)
        
        return self._generate_report(
            all_changes, all_issues, 
            filtered_changes, filtered_issues
        )
    
    def _filter_changes(self, changes: List[Dict]) -> List[Dict]:
        """过滤掉应该忽略的代码修改"""
        filtered = []
        
        for change in changes:
            file_path = change.get('file', '')
            
            # 检查文件是否应该忽略
            if self.file_matcher.is_ignored(file_path):
                change['ignore_reason'] = '文件被忽略配置排除'
                self.ignored_changes.append(change)
            else:
                filtered.append(change)
        
        return filtered
    
    def _filter_issues(self, issues: List[Dict]) -> List[Dict]:
        """过滤掉应该忽略的编译问题"""
        filtered = []
        
        for issue in issues:
            file_path = issue.get('file', '')
            issue_message = issue.get('message', '')
            
            # 检查问题是否应该忽略
            should_ignore, reason = self.file_matcher.is_issue_ignored(
                file_path, issue_message
            )
            
            if should_ignore:
                issue['ignore_reason'] = reason
                self.ignored_issues.append(issue)
            else:
                filtered.append(issue)
        
        return filtered
    
    def _perform_matching(self, changes: List[Dict], issues: List[Dict]):
        """执行实际的匹配逻辑"""
        # 简化的匹配逻辑，实际应该更复杂
        for change in changes:
            matched = False
            
            for issue in issues:
                # 简单的行号匹配
                change_line = change.get('new_line') or change.get('old_line')
                issue_line = issue.get('line')
                
                if change_line and issue_line and abs(change_line - issue_line) <= 5:
                    matched_issue = {
                        **change,
                        **issue,
                        'confidence': 0.8
                    }
                    self.matched_issues.append(matched_issue)
                    matched = True
                    break
            
            if not matched:
                self.unmatched_changes.append(change)
        
        self.unmatched_issues = [
            issue for issue in issues 
            if not any(
                mi.get('change_hash') == 'fake_hash'  # 这里应该使用实际的匹配检查
                for mi in self.matched_issues
            )
        ]
    
    def _generate_report(self, all_changes: List, all_issues: List,
                        filtered_changes: List, filtered_issues: List) -> Dict:
        """生成包含忽略信息的报告"""
        return {
            "summary": {
                "total_changes": len(all_changes),
                "changes_kept": len(filtered_changes),
                "changes_ignored": len(self.ignored_changes),
                
                "total_issues": len(all_issues),
                "issues_kept": len(filtered_issues),
                "issues_ignored": len(self.ignored_issues),
                
                "matched_issues": len(self.matched_issues),
                "matching_rate": len(self.matched_issues) / max(len(filtered_issues), 1),
                
                "filter_stats": {
                    "change_filter_rate": len(self.ignored_changes) / max(len(all_changes), 1),
                    "issue_filter_rate": len(self.ignored_issues) / max(len(all_issues), 1)
                }
            },
            "matched_issues": self.matched_issues,
            "unmatched_changes": self.unmatched_changes,
            "unmatched_issues": self.unmatched_issues,
            "ignored_changes": self.ignored_changes[:50],  # 限制数量
            "ignored_issues": self.ignored_issues[:50],
            "filter_info": {
                "ignored_file_patterns": self.file_matcher.ignored_patterns,
                "exception_patterns": self.file_matcher.exception_patterns
            }
        }

def main():
    parser = argparse.ArgumentParser(description='支持文件忽略的结果匹配器')
    parser.add_argument('--changes', required=True, help='代码修改JSON文件')
    parser.add_argument('--issues', required=True, help='编译问题JSON文件')
    parser.add_argument('--output', required=True, help='输出JSON文件')
    parser.add_argument('--config', default='config/patterns.json', 
                       help='模式配置文件路径')
    parser.add_argument('--base-dir', default='.', 
                       help='基础目录，用于计算相对路径')
    
    args = parser.parse_args()
    
    # 加载数据
    with open(args.changes, 'r') as f:
        changes_data = json.load(f)
    
    with open(args.issues, 'r') as f:
        issues_data = json.load(f)
    
    # 匹配
    matcher = EnhancedResultMatcher(args.config, args.base_dir)
    report = matcher.match(changes_data, issues_data)
    
    # 保存结果
    with open(args.output, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    # 打印摘要
    summary = report['summary']
    print(f"匹配结果 (应用文件忽略规则):")
    print(f"  总代码修改: {summary['total_changes']}")
    print(f"  过滤后的修改: {summary['changes_kept']} (忽略: {summary['changes_ignored']})")
    print(f"  总编译问题: {summary['total_issues']}")
    print(f"  过滤后的问题: {summary['issues_kept']} (忽略: {summary['issues_ignored']})")
    print(f"  匹配的问题: {summary['matched_issues']}")
    print(f"  匹配率: {summary['matching_rate']:.1%}")
    print(f"  修改过滤率: {summary['filter_stats']['change_filter_rate']:.1%}")
    print(f"  问题过滤率: {summary['filter_stats']['issue_filter_rate']:.1%}")
    print(f"  结果已保存到: {args.output}")

if __name__ == "__main__":
    main()