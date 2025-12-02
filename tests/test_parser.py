# test_compatibility.py
import unittest
import json
from src.parser import CompileLogParser

class TestCompatibility(unittest.TestCase):
    
    def setUp(self):
        # 加载完整的配置
        with open('config/patterns.json', 'r') as f:
            self.full_config = json.load(f)
    
    def test_basic_parsing(self):
        """测试基本解析功能"""
        parser = CompileLogParser('config/patterns.json')
        
        # 测试日志
        test_log = """
        main.cpp:10:5: error: 'x' was not declared in this scope
        utils.cpp:15:3: warning: unused variable 'y' [-Wunused-variable]
        """
        
        issues = parser.parse(test_log)
        self.assertEqual(len(issues), 2)
    
    def test_ignored_files(self):
        """测试文件忽略功能"""
        parser = CompileLogParser('config/patterns.json')
        
        # 第三方库的错误应该被忽略
        test_log = """
        third_party/old_lib.cpp:20:10: warning: deprecated declaration
        src/main.cpp:5:3: error: syntax error
        """
        
        issues = parser.parse(test_log)
        # 应该只找到一个错误（第三方库的警告被忽略）
        self.assertEqual(len(issues), 1)