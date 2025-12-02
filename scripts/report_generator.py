#!/usr/bin/env python3
"""
生成HTML报告
"""
import json
import sys
import argparse
from datetime import datetime

def generate_html_report(analysis_data: dict, output_file: str):
    """生成HTML报告"""
    
    summary = analysis_data.get('summary', {})
    matched_issues = analysis_data.get('matched_issues', [])
    
    html = f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>MR代码修改与编译问题分析报告</title>
    <style>
        body {{ font-family: 'Segoe UI', Arial, sans-serif; margin: 40px; color: #333; }}
        .container {{ max-width: 1200px; margin: 0 auto; }}
        .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                 color: white; padding: 30px; border-radius: 10px; margin-bottom: 30px; }}
        .summary-card {{ background: white; border-radius: 8px; padding: 20px; 
                       box-shadow: 0 4px 6px rgba(0,0,0,0.1); margin-bottom: 30px; }}
        .issue-table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
        .issue-table th, .issue-table td {{ padding: 12px; text-align: left; 
                                         border-bottom: 1px solid #ddd; }}
        .issue-table th {{ background-color: #f5f5f5; font-weight: bold; }}
        .severity-high {{ color: #d32f2f; font-weight: bold; }}
        .severity-medium {{ color: #f57c00; }}
        .severity-low {{ color: #388e3c; }}
        .confidence-bar {{ width: 100px; height: 8px; background: #eee; 
                         border-radius: 4px; overflow: hidden; display: inline-block; }}
        .confidence-fill {{ height: 100%; background: #4caf50; }}
        .metrics {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); 
                  gap: 20px; margin-bottom: 30px; }}
        .metric-card {{ background: white; padding: 20px; border-radius: 8px; 
                      box-shadow: 0 2px 4px rgba(0,0,0,0.1); text-align: center; }}
        .metric-value {{ font-size: 2em; font-weight: bold; margin: 10px 0; }}
        .metric-label {{ color: #666; }}
        .change-content {{ font-family: 'Courier New', monospace; background: #f8f9fa; 
                         padding: 10px; border-radius: 4px; margin: 5px 0; }}
        .issue-message {{ color: #666; font-size: 0.9em; }}
        .filter-controls {{ margin-bottom: 20px; }}
        .filter-btn {{ margin-right: 10px; padding: 5px 15px; border: 1px solid #ddd; 
                     border-radius: 4px; background: white; cursor: pointer; }}
        .filter-btn.active {{ background: #667eea; color: white; border-color: #667eea; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🔍 MR代码修改与编译问题分析报告</h1>
            <p>生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        </div>
        
        <div class="metrics">
            <div class="metric-card">
                <div class="metric-label">总代码修改</div>
                <div class="metric-value">{summary.get('total_changes', 0)}</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">总编译问题</div>
                <div class="metric-value">{summary.get('total_issues', 0)}</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">匹配的问题</div>
                <div class="metric-value">{summary.get('matched_issues', 0)}</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">匹配率</div>
                <div class="metric-value">{summary.get('matching_rate', 0):.1%}</div>
            </div>
        </div>
        
        <div class="summary-card">
            <h2>📊 问题严重程度分布</h2>
            <div style="display: flex; gap: 20px; margin-top: 20px;">
                <div>
                    <h3 class="severity-high">🔥 高严重度问题</h3>
                    <p style="font-size: 1.5em;">{summary.get('matched_by_severity', {}).get('high', 0)}</p>
                </div>
                <div>
                    <h3 class="severity-medium">⚠️ 中严重度问题</h3>
                    <p style="font-size: 1.5em;">{summary.get('matched_by_severity', {}).get('medium', 0)}</p>
                </div>
                <div>
                    <h3 class="severity-low">ℹ️ 低严重度问题</h3>
                    <p style="font-size: 1.5em;">{summary.get('matched_by_severity', {}).get('low', 0)}</p>
                </div>
            </div>
        </div>
        
        <div class="summary-card">
            <h2>📝 匹配的详细问题</h2>
            <div class="filter-controls">
                <button class="filter-btn active" onclick="filterIssues('all')">全部</button>
                <button class="filter-btn" onclick="filterIssues('high')">高严重度</button>
                <button class="filter-btn" onclick="filterIssues('medium')">中严重度</button>
                <button class="filter-btn" onclick="filterIssues('low')">低严重度</button>
            </div>
            
            <table class="issue-table" id="issuesTable">
                <thead>
                    <tr>
                        <th>文件</th>
                        <th>行号</th>
                        <th>修改类型</th>
                        <th>问题类型</th>
                        <th>严重度</th>
                        <th>修改内容</th>
                        <th>问题描述</th>
                        <th>置信度</th>
                    </tr>
                </thead>
                <tbody>
    """
    
    for issue in matched_issues:
        severity_class = f"severity-{issue['issue_severity']}"
        
        html += f"""
                    <tr class="issue-row" data-severity="{issue['issue_severity']}">
                        <td>{issue['file']}</td>
                        <td>{issue['change_line']}</td>
                        <td>{issue['change_type']}</td>
                        <td>{issue['issue_type']}</td>
                        <td class="{severity_class}">{issue['issue_severity'].upper()}</td>
                        <td><div class="change-content">{issue['change_content']}</div></td>
                        <td><div class="issue-message">{issue['issue_message']}</div></td>
                        <td>
                            <div class="confidence-bar">
                                <div class="confidence-fill" style="width: {issue['confidence']*100}%"></div>
                            </div>
                            {issue['confidence']:.0%}
                        </td>
                    </tr>
        """
    
    html += """
                </tbody>
            </table>
        </div>
    </div>
    
    <script>
        function filterIssues(severity) {
            // 更新按钮状态
            document.querySelectorAll('.filter-btn').forEach(btn => {
                btn.classList.remove('active');
            });
            event.target.classList.add('active');
            
            // 过滤表格行
            const rows = document.querySelectorAll('.issue-row');
            rows.forEach(row => {
                if (severity === 'all' || row.dataset.severity === severity) {
                    row.style.display = '';
                } else {
                    row.style.display = 'none';
                }
            });
        }
        
        // 初始按严重度排序
        document.addEventListener('DOMContentLoaded', function() {
            const table = document.getElementById('issuesTable');
            const tbody = table.querySelector('tbody');
            const rows = Array.from(tbody.querySelectorAll('tr'));
            
            // 按严重度排序：high > medium > low
            const severityOrder = {high: 0, medium: 1, low: 2};
            rows.sort((a, b) => {
                const severityA = severityOrder[a.dataset.severity];
                const severityB = severityOrder[b.dataset.severity];
                return severityA - severityB;
            });
            
            // 重新插入排序后的行
            rows.forEach(row => tbody.appendChild(row));
        });
    </script>
</body>
</html>
    """
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html)
    
    print(f"HTML报告已生成: {output_file}")

def main():
    parser = argparse.ArgumentParser(description='生成HTML报告')
    parser.add_argument('--analysis', required=True, help='分析结果JSON文件')
    parser.add_argument('--output', required=True, help='输出HTML文件')
    
    args = parser.parse_args()
    
    # 加载分析结果
    with open(args.analysis, 'r') as f:
        analysis_data = json.load(f)
    
    # 生成HTML报告
    generate_html_report(analysis_data, args.output)

if __name__ == "__main__":
    main()