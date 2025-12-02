#!/usr/bin/env python3
"""
文件匹配工具，支持 glob 模式
"""
import fnmatch
import os
import re
from pathlib import Path
from typing import List, Optional, Tuple

class FileMatcher:
    """支持 glob 模式的文件匹配器"""
    
    def __init__(self, base_dir: str = "."):
        self.base_dir = Path(base_dir).resolve()
        self.ignored_patterns: List[str] = []
        self.exception_patterns: List[str] = []
        self.ignored_issue_rules: List[dict] = []
    
    def load_config(self, config_data: dict):
        """加载配置文件"""
        ignored_config = config_data.get('ignored_files', {})
        
        # 加载忽略模式
        self.ignored_patterns = ignored_config.get('patterns', [])
        self.exception_patterns = ignored_config.get('exceptions', [])
        
        # 加载忽略的问题规则
        self.ignored_issue_rules = config_data.get('ignored_issues', {}).get('patterns', [])
    
    def is_ignored(self, file_path: str) -> bool:
        """
        检查文件是否应该被忽略
        
        Args:
            file_path: 相对或绝对文件路径
            
        Returns:
            bool: True 表示应该忽略
        """
        # 转换为相对于基础目录的路径
        try:
            rel_path = self._get_relative_path(file_path)
        except ValueError:
            # 如果无法转换为相对路径，检查是否为绝对路径匹配
            rel_path = file_path
        
        # 首先检查例外规则
        for exception_pattern in self.exception_patterns:
            if self._match_pattern(rel_path, exception_pattern):
                return False  # 即使匹配忽略模式，但例外优先
        
        # 检查忽略模式
        for ignore_pattern in self.ignored_patterns:
            if self._match_pattern(rel_path, ignore_pattern):
                return True
        
        return False
    
    def is_issue_ignored(self, file_path: str, issue_message: str) -> Tuple[bool, Optional[str]]:
        """
        检查特定文件的特定问题是否应该被忽略
        
        Args:
            file_path: 文件路径
            issue_message: 编译问题信息
            
        Returns:
            (should_ignore, reason): 是否忽略及原因
        """
        # 先检查文件是否完全忽略
        if self.is_ignored(file_path):
            return True, "文件被完全忽略"
        
        # 转换为相对路径
        try:
            rel_path = self._get_relative_path(file_path)
        except ValueError:
            rel_path = file_path
        
        # 检查问题特定规则
        for rule in self.ignored_issue_rules:
            file_pattern = rule.get('file_pattern', '')
            issue_pattern = rule.get('issue_pattern', '')
            reason = rule.get('reason', '')
            
            # 检查文件模式匹配
            if not self._match_pattern(rel_path, file_pattern):
                continue
            
            # 检查问题模式匹配
            if not issue_pattern or re.search(issue_pattern, issue_message, re.IGNORECASE):
                return True, reason
        
        return False, None
    
    def _get_relative_path(self, file_path: str) -> str:
        """获取相对于基础目录的路径"""
        path = Path(file_path)
        
        # 如果已经是相对路径，直接返回
        if not path.is_absolute():
            return str(path)
        
        # 如果是绝对路径，尝试转换为相对路径
        try:
            rel_path = path.relative_to(self.base_dir)
            return str(rel_path)
        except ValueError:
            # 如果不在基础目录下，返回原始路径
            return str(path)
    
    def _match_pattern(self, path: str, pattern: str) -> bool:
        """
        使用 glob 模式匹配路径
        
        Args:
            path: 要匹配的路径
            pattern: glob 模式
            
        Returns:
            bool: 是否匹配
        """
        # 将路径分隔符统一为 /
        normalized_path = path.replace('\\', '/')
        normalized_pattern = pattern.replace('\\', '/')
        
        # 使用 fnmatch 进行匹配
        return fnmatch.fnmatch(normalized_path, normalized_pattern)
    
    def filter_files(self, file_paths: List[str]) -> List[str]:
        """过滤掉应该忽略的文件"""
        return [fp for fp in file_paths if not self.is_ignored(fp)]
    
    def filter_issues(self, issues: List[dict]) -> List[dict]:
        """过滤掉应该忽略的问题"""
        filtered_issues = []
        
        for issue in issues:
            file_path = issue.get('file', '')
            issue_message = issue.get('message', '')
            
            should_ignore, reason = self.is_issue_ignored(file_path, issue_message)
            
            if should_ignore:
                # 添加忽略原因到问题信息中（可选）
                issue['ignored_reason'] = reason
                continue
            
            filtered_issues.append(issue)
        
        return filtered_issues

# 使用示例
if __name__ == "__main__":
    # 示例用法
    matcher = FileMatcher("/path/to/project")
    
    # 测试文件匹配
    test_files = [
        "src/main.cpp",
        "third_party/lib/src/file.cpp",
        "test/unit/test_file.cpp",
        "build/generated/file.pb.cc"
    ]
    
    for file in test_files:
        ignored = matcher.is_ignored(file)
        print(f"{file}: {'忽略' if ignored else '保留'}")