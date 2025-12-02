#!/bin/bash
set -e

# 配置
SOURCE_BRANCH=$1
TARGET_BRANCH=$2
REPO_PATH=${3:-.}
REPORT_DIR=${4:-./reports}
CONFIG_DIR=${5:-./config}
BASE_DIR=${6:-.}  # 新增：基础目录参数
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")

echo "=== MR 代码修改与编译警告分析 (支持文件忽略) ==="
echo "源分支: $SOURCE_BRANCH"
echo "目标分支: $TARGET_BRANCH"
echo "仓库路径: $REPO_PATH"
echo "配置目录: $CONFIG_DIR"
echo "基础目录: $BASE_DIR"
echo "时间戳: $TIMESTAMP"

# 创建目录
mkdir -p $REPORT_DIR

# 检查配置文件
if [ ! -f "$CONFIG_DIR/patterns.json" ]; then
    echo "警告: 配置文件 $CONFIG_DIR/patterns.json 不存在"
    echo "正在创建默认配置..."
    python3 scripts/create_default_config.py --output $CONFIG_DIR/patterns.json
fi

# 检查是否包含 ignored_files 配置
if ! grep -q '"ignored_files"' "$CONFIG_DIR/patterns.json"; then
    echo "警告: 配置文件缺少 ignored_files 配置"
    echo "将添加默认的忽略配置..."
    python3 scripts/add_ignore_config.py --config "$CONFIG_DIR/patterns.json"
fi

# 切换到仓库目录
cd $REPO_PATH

# 1. 获取MR增量修改
echo "步骤1: 分析MR增量修改..."
python3 scripts/git_diff_parser.py \
    --source $SOURCE_BRANCH \
    --target $TARGET_BRANCH \
    --repo . \
    --output ${REPORT_DIR}/mr_changes_${TIMESTAMP}.json

# 2. 编译测试
echo "步骤2: 本地合并并编译测试..."
# ... [编译代码部分保持不变] ...

# 3. 解析编译日志（应用文件忽略）
echo "步骤3: 解析编译日志（应用文件忽略规则）..."
python3 scripts/compile_log_parser.py \
    --logfile $BUILD_LOG \
    --output ${REPORT_DIR}/compile_issues_${TIMESTAMP}.json \
    --config ${CONFIG_DIR}/patterns.json \
    --base-dir "$BASE_DIR"

# 4. 匹配修改和编译问题（应用文件忽略）
echo "步骤4: 匹配代码修改和编译问题（应用文件忽略规则）..."
python3 scripts/result_matcher.py \
    --changes ${REPORT_DIR}/mr_changes_${TIMESTAMP}.json \
    --issues ${REPORT_DIR}/compile_issues_${TIMESTAMP}.json \
    --config ${CONFIG_DIR}/patterns.json \
    --base-dir "$BASE_DIR" \
    --output ${REPORT_DIR}/mr_analysis_${TIMESTAMP}.json

# 5. 生成增强的报告
echo "步骤5: 生成增强的HTML报告..."
python3 scripts/report_generator.py \
    --analysis ${REPORT_DIR}/mr_analysis_${TIMESTAMP}.json \
    --config ${CONFIG_DIR}/patterns.json \
    --output ${REPORT_DIR}/mr_report_${TIMESTAMP}.html

# 6. 生成忽略统计报告
echo "步骤6: 生成忽略统计报告..."
python3 scripts/ignore_report.py \
    --analysis ${REPORT_DIR}/mr_analysis_${TIMESTAMP}.json \
    --output ${REPORT_DIR}/ignore_stats_${TIMESTAMP}.html

echo "=== 分析完成 ==="
echo "详细报告: ${REPORT_DIR}/mr_analysis_${TIMESTAMP}.json"
echo "HTML报告: ${REPORT_DIR}/mr_report_${TIMESTAMP}.html"
echo "忽略统计: ${REPORT_DIR}/ignore_stats_${TIMESTAMP}.html"
echo "编译日志: $BUILD_LOG"