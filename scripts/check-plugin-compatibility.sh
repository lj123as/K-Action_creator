#!/bin/bash
# Obsidian 插件跨平台兼容性检查脚本
# 用途：识别桌面专用插件，帮助优化多平台同步策略

echo "=================================================="
echo "  Obsidian 插件平台兼容性检查"
echo "=================================================="
echo ""

PLUGINS_DIR=".obsidian/plugins"

if [ ! -d "$PLUGINS_DIR" ]; then
    echo "❌ 错误：找不到 .obsidian/plugins 目录"
    echo "   请在 vault 根目录运行此脚本"
    exit 1
fi

echo "📱 移动端兼容插件："
echo "-----------------------------------"
mobile_count=0
for plugin_dir in "$PLUGINS_DIR"/*; do
    if [ -d "$plugin_dir" ]; then
        manifest="$plugin_dir/manifest.json"
        if [ -f "$manifest" ]; then
            plugin_name=$(basename "$plugin_dir")
            is_desktop_only=$(grep -o '"isDesktopOnly"[[:space:]]*:[[:space:]]*true' "$manifest")

            if [ -z "$is_desktop_only" ]; then
                plugin_display_name=$(grep -o '"name"[[:space:]]*:[[:space:]]*"[^"]*"' "$manifest" | cut -d'"' -f4)
                echo "  ✅ $plugin_display_name ($plugin_name)"
                mobile_count=$((mobile_count + 1))
            fi
        fi
    fi
done
echo "   共 $mobile_count 个移动端兼容插件"
echo ""

echo "🖥️  桌面专用插件（移动端不可用）："
echo "-----------------------------------"
desktop_count=0
desktop_plugins=()
for plugin_dir in "$PLUGINS_DIR"/*; do
    if [ -d "$plugin_dir" ]; then
        manifest="$plugin_dir/manifest.json"
        if [ -f "$manifest" ]; then
            plugin_name=$(basename "$plugin_dir")
            is_desktop_only=$(grep -o '"isDesktopOnly"[[:space:]]*:[[:space:]]*true' "$manifest")

            if [ -n "$is_desktop_only" ]; then
                plugin_display_name=$(grep -o '"name"[[:space:]]*:[[:space:]]*"[^"]*"' "$manifest" | cut -d'"' -f4)
                echo "  ⚠️  $plugin_display_name ($plugin_name)"
                desktop_count=$((desktop_count + 1))
                desktop_plugins+=("$plugin_name")
            fi
        fi
    fi
done
echo "   共 $desktop_count 个桌面专用插件"
echo ""

echo "=================================================="
echo "  分析和建议"
echo "=================================================="
echo ""

if [ $desktop_count -eq 0 ]; then
    echo "✅ 太好了！所有插件都兼容移动端"
    echo "   您可以安全地同步插件代码"
else
    echo "⚠️  发现 $desktop_count 个桌面专用插件"
    echo ""
    echo "💡 建议操作："
    echo "   1. 不同步插件代码目录 (.obsidian/plugins/)"
    echo "   2. 仅同步插件列表 (community-plugins.json)"
    echo "   3. 在移动端跳过以下插件："
    for plugin in "${desktop_plugins[@]}"; do
        echo "      - $plugin"
    done
    echo ""
    echo "📝 更新 .gitignore："
    echo "   echo '.obsidian/plugins/' >> .gitignore"
    echo "   echo '!.obsidian/community-plugins.json' >> .gitignore"
    echo "   echo '!.obsidian/core-plugins.json' >> .gitignore"
fi

echo ""
echo "📊 插件统计："
echo "   总插件数：$((mobile_count + desktop_count))"
echo "   移动端可用：$mobile_count ($(awk "BEGIN {printf \"%.1f\", $mobile_count/($mobile_count+$desktop_count)*100}")%)"
echo "   仅桌面端：$desktop_count ($(awk "BEGIN {printf \"%.1f\", $desktop_count/($mobile_count+$desktop_count)*100}")%)"
echo ""

# 检查当前 .gitignore 配置
echo "=================================================="
echo "  当前 .gitignore 配置检查"
echo "=================================================="
echo ""

if [ -f ".gitignore" ]; then
    if grep -q "^\.obsidian/plugins/$" .gitignore; then
        echo "✅ 插件目录已被排除 (.obsidian/plugins/)"

        if grep -q "^\!\.obsidian/community-plugins\.json$" .gitignore; then
            echo "✅ 插件列表已保留 (community-plugins.json)"
        else
            echo "⚠️  建议添加：!.obsidian/community-plugins.json"
        fi
    else
        if grep -q "\.obsidian/plugins/\*/data\.json" .gitignore; then
            echo "⚠️  当前仅排除插件数据 (data.json)"
            echo "   建议完全排除插件目录以避免跨平台问题"
        else
            echo "❌ 插件目录未被排除"
            echo "   建议添加到 .gitignore"
        fi
    fi
else
    echo "⚠️  找不到 .gitignore 文件"
fi

echo ""
echo "=================================================="
echo "  完成！"
echo "=================================================="
echo ""
echo "🔗 详细迁移指南请参阅："
echo "   .obsidian-sync-guide.md"
