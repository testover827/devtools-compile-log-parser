#!/usr/bin/env python3
"""
解析MR中的增量代码修改
"""
import subprocess
import json
import re
import sys
import argparse
from pathlib import Path
from dataclasses import dataclass
from typing import List, Dict, Optional
import hashlib

@dataclass
class CodeChange:
    """代码修改信息"""
    file_path: str
    old_line: int
    new_line: int
    change_type: str  # 'added', 'modified', 'deleted'
    content: str
    change_hash: str
    context_before: Optional[str] = None
    context_after: Optional[str] = None

class GitDiffParser:
    """解析Git差异"""
    
    def __init__(self, repo_path: str = "."):
        self.repo_path = Path(repo_path).absolute()
        self.changes: List[CodeChange] = []
        
    def get_diff(self, source_branch: str, target_branch: str) -> str:
        """获取两个分支之间的差异"""
        cmd = [
            "git", "-C", str(self.repo_path), "diff",
            "--no-color",
            "--unified=3",  # 显示3行上下文
            f"{target_branch}...{source_branch}"  # 三点语法获取MR内容
        ]
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True
            )
            return result.stdout
        except subprocess.CalledProcessError as e:
            print(f"Git diff失败: {e.stderr}")
            return ""
    
    def parse_diff(self, diff_text: str):
        """解析差异文本"""
        lines = diff_text.split('\n')
        current_file = None
        current_hunk = None
        line_num_old = 0
        line_num_new = 0
        in_hunk = False
        hunk_header = None
        
        i = 0
        while i < len(lines):
            line = lines[i]
            
            # 文件头
            if line.startswith('diff --git'):
                current_file = None
                current_hunk = None
                i += 1
                continue
            
            # 新文件路径
            elif line.startswith('+++'):
                # +++ b/path/to/file.cpp
                if line.startswith('+++ b/'):
                    current_file = line[6:]  # 移除'+++ b/'
                i += 1
                continue
            
            # Hunk头
            elif line.startswith('@@'):
                # @@ -1,5 +1,7 @@
                match = re.match(r'@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@', line)
                if match and current_file:
                    line_num_old = int(match.group(1))
                    line_num_new = int(match.group(3))
                    in_hunk = True
                    hunk_header = line
                i += 1
                continue
            
            # 差异行
            elif in_hunk and current_file:
                change_type = None
                content = None
                
                if line.startswith('+') and not line.startswith('++'):
                    # 新增行
                    change_type = 'added'
                    content = line[1:]
                    self._add_change(
                        file_path=current_file,
                        line_num_new=line_num_new,
                        content=content,
                        change_type=change_type
                    )
                    line_num_new += 1
                    
                elif line.startswith('-') and not line.startswith('--'):
                    # 删除行
                    change_type = 'deleted'
                    content = line[1:]
                    self._add_change(
                        file_path=current_file,
                        line_num_old=line_num_old,
                        content=content,
                        change_type=change_type
                    )
                    line_num_old += 1
                    
                elif line.startswith(' '):
                    # 未修改行
                    line_num_old += 1
                    line_num_new += 1
                    
                elif line.strip() == '':
                    # 空行
                    pass
                
                # 检查是否结束hunk
                i += 1
                if i < len(lines) and lines[i].startswith('@@'):
                    in_hunk = False
                    current_hunk = None
                continue
                
            i += 1
    
    def _add_change(self, file_path: str, **kwargs):
        """添加修改记录"""
        change_hash = hashlib.md5(
            f"{file_path}:{json.dumps(kwargs, sort_keys=True)}".encode()
        ).hexdigest()[:8]
        
        change = CodeChange(
            file_path=file_path,
            change_hash=change_hash,
            **kwargs
        )
        self.changes.append(change)
    
    def get_file_changes(self) -> Dict[str, List[CodeChange]]:
        """按文件分组返回修改"""
        result = {}
        for change in self.changes:
            if change.file_path not in result:
                result[change.file_path] = []
            result[change.file_path].append(change)
        return result
    
    def export_json(self, output_file: str):
        """导出为JSON"""
        data = {
            "summary": {
                "total_changes": len(self.changes),
                "files_modified": len(set(c.file_path for c in self.changes)),
                "changes_by_type": {
                    "added": len([c for c in self.changes if c.change_type == "added"]),
                    "modified": len([c for c in self.changes if c.change_type == "modified"]),
                    "deleted": len([c for c in self.changes if c.change_type == "deleted"]),
                }
            },
            "changes": [
                {
                    "file": c.file_path,
                    "old_line": c.old_line,
                    "new_line": c.new_line,
                    "type": c.change_type,
                    "content": c.content,
                    "hash": c.change_hash
                }
                for c in self.changes
            ]
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        return data

def main():
    parser = argparse.ArgumentParser(description='解析MR增量代码修改')
    parser.add_argument('--source', required=True, help='源分支')
    parser.add_argument('--target', required=True, help='目标分支')
    parser.add_argument('--repo', default='.', help='仓库路径')
    parser.add_argument('--output', required=True, help='输出JSON文件')
    
    args = parser.parse_args()
    
    parser = GitDiffParser(args.repo)
    
    print(f"分析分支差异: {args.source} -> {args.target}")
    
    # 获取差异
    diff_text = parser.get_diff(args.source, args.target)
    if not diff_text:
        print("没有差异或获取失败")
        sys.exit(1)
    
    # 解析差异
    parser.parse_diff(diff_text)
    
    # 导出结果
    data = parser.export_json(args.output)
    
    print(f"分析完成:")
    print(f"  总修改行数: {data['summary']['total_changes']}")
    print(f"  修改文件数: {data['summary']['files_modified']}")
    print(f"  新增行: {data['summary']['changes_by_type']['added']}")
    print(f"  删除行: {data['summary']['changes_by_type']['deleted']}")
    print(f"  结果已保存到: {args.output}")

if __name__ == "__main__":
    main()