#!/usr/bin/env node

/**
 * 扫描日志分析脚本
 * 自动获取 ~/.comate-engine/log/kernel-{date}.log 中与扫描相关的日志并进行分析
 */

import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import { dirname } from 'path';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

// 日志目录
const LOG_DIR = path.join(process.env.HOME || process.env.USERPROFILE, '.comate-engine', 'log');

// 关键词过滤器
const KEYWORDS = ['ScanScheduler', 'ConfigManager', 'IcrExecutor', 'ScanTriggerManager', 'StateManager', 'IcrInstaller'];

/**
 * 获取今天的日志文件路径
 */
function getTodayLogFilePath() {
    const today = new Date();
    const yyyy = today.getFullYear();
    const mm = String(today.getMonth() + 1).padStart(2, '0');
    const dd = String(today.getDate()).padStart(2, '0');
    return path.join(LOG_DIR, `kernel-${yyyy}-${mm}-${dd}.log`);
}

/**
 * 获取指定日期的日志文件路径
 */
function getDateLogFilePath(dateStr) {
    // 支持 yyyy-mm-dd 格式
    if (/^\d{4}-\d{2}-\d{2}$/.test(dateStr)) {
        return path.join(LOG_DIR, `kernel-${dateStr}.log`);
    }
    throw new Error(`Invalid date format: ${dateStr}. Expected yyyy-mm-dd`);
}

/**
 * 列出可用的日志文件
 */
function listAvailableLogs() {
    try {
        if (!fs.existsSync(LOG_DIR)) {
            console.log(`日志目录不存在: ${LOG_DIR}`);
            return [];
        }
        const files = fs.readdirSync(LOG_DIR)
            .filter(f => f.startsWith('kernel-') && f.endsWith('.log'))
            .sort()
            .reverse();
        return files;
    } catch (err) {
        console.error(`读取日志目录失败: ${err.message}`);
        return [];
    }
}

/**
 * 读取并过滤日志文件
 */
function readAndFilterLogs(filePath, keywords) {
    if (!fs.existsSync(filePath)) {
        console.error(`日志文件不存在: ${filePath}`);
        return '';
    }

    const content = fs.readFileSync(filePath, 'utf-8');
    const lines = content.split('\n');

    // 过滤包含关键词的行
    const filteredLines = lines.filter(line => {
        if (!line.trim()) return false;
        return keywords.some(keyword => line.includes(keyword));
    });

    return filteredLines.join('\n');
}

/**
 * 查找关联的错误日志（不包含关键词但可能相关）
 */
function findRelatedErrors(filePath) {
    if (!fs.existsSync(filePath)) {
        return '';
    }

    const content = fs.readFileSync(filePath, 'utf-8');
    const lines = content.split('\n');

    // 查找错误日志
    const errorLines = lines.filter(line => {
        if (!line.trim()) return false;
        return line.includes('[error]') || line.includes('[warn]') || line.includes('Failed to') || line.includes('Error');
    });

    return errorLines.join('\n');
}

/**
 * 生成分析报告
 */
function generateAnalysisReport(scanLogs, errorLogs) {
    const analysis = [];

    analysis.push('## 扫描日志分析报告\n');
    analysis.push('### 执行状态摘要\n');

    // 检查初始化状态
    const hasScanTriggerManager = scanLogs.includes('[ScanTriggerManager] Initialized');
    const hasScanScheduler = scanLogs.includes('[ScanScheduler] Initialized');
    const hasIcrExecutor = scanLogs.includes('[IcrExecutor] Initialized');
    const hasIcrBinary = scanLogs.includes('icrBinaryPath') && !scanLogs.includes('ICR binary not found');

    analysis.push(`- 初始化状态: ${hasScanTriggerManager && hasScanScheduler ? '✅' : '❌'} ` +
        `(ScanTriggerManager: ${hasScanTriggerManager ? '✅' : '❌'}, ` +
        `ScanScheduler: ${hasScanScheduler ? '✅' : '❌'}, ` +
        `IcrExecutor: ${hasIcrExecutor ? '✅' : '❌'})`);

    // 检查配置加载状态
    const hasRemoteConfig = scanLogs.includes('[ConfigManager] Remote config loaded successfully');
    const noUserId = scanLogs.includes('[ConfigManager] No userId available');
    const configFailed = scanLogs.includes('[ConfigManager] Failed to load remote config');
    const noGrayRelease = scanLogs.includes('[ConfigManager] User not in gray release');

    let configStatus = '✅';
    if (noUserId || configFailed || noGrayRelease) configStatus = '❌';
    else if (!hasRemoteConfig) configStatus = '⚠️';

    analysis.push(`- 配置加载状态: ${configStatus}`);

    if (noUserId) analysis.push(`  - ⚠️ 用户ID不可用`);
    if (configFailed) analysis.push(`  - ⚠️ 远端配置加载失败`);
    if (noGrayRelease) analysis.push(`  - ⚠️ 用户未在灰度列表`);

    // 检查任务触发状态
    const hasScanRequest = scanLogs.includes('[ScanTriggerManager] Scan request result');
    const hasPlansGenerated = scanLogs.includes('[ScanScheduler] Generated') && scanLogs.includes('plans');
    const planCountMatch = scanLogs.match(/Generated (\d+) plans/);
    const planCount = planCountMatch ? parseInt(planCountMatch[1]) : 0;
    const hasDuplicateEvent = scanLogs.includes('[ScanScheduler] Duplicate event');

    analysis.push(`- 任务触发状态: ${hasScanRequest ? '✅' : '❌'} ` +
        `(生成计划数: ${planCount}, 重复事件: ${hasDuplicateEvent ? '是' : '否'})`);

    // 检查执行状态
    const hasExecutingPlan = scanLogs.includes('[IcrExecutor] Executing plan');
    const hasProcessSpawned = scanLogs.includes('[IcrExecutor] ICR process spawned successfully');
    const hasTaskCompleted = scanLogs.includes('[IcrExecutor] ICR task completed');
    const hasTaskFailed = scanLogs.includes('[IcrExecutor] ICR task failed');
    const hasScanResult = scanLogs.includes('[ScanTriggerManager] Scan result received');

    let execStatus = '✅';
    if (hasTaskFailed) execStatus = '❌';
    else if (!hasTaskCompleted && !hasScanResult) execStatus = '⚠️';

    analysis.push(`- 执行状态: ${execStatus}`);

    if (hasTaskFailed) analysis.push(`  - ⚠️ ICR 任务执行失败`);
    if (!hasProcessSpawned && hasExecutingPlan) analysis.push(`  - ⚠️ ICR 进程未成功启动`);

    analysis.push('\n### 详细分析\n');

    // 初始化检查
    analysis.push('#### 1. 初始化检查\n');
    analysis.push(`- ScanTriggerManager: ${hasScanTriggerManager ? '✅ 已初始化' : '❌ 未检测到初始化日志'}`);
    analysis.push(`- ScanScheduler: ${hasScanScheduler ? '✅ 已初始化' : '❌ 未检测到初始化日志'}`);
    analysis.push(`- IcrExecutor: ${hasIcrExecutor ? '✅ 已初始化' : '❌ 未检测到初始化日志'}`);
    if (hasIcrExecutor) {
        analysis.push(`  - ICR 二进制: ${hasIcrBinary ? '✅ 已找到' : '❌ 未找到或不可用'}`);
    }

    // 配置检查
    analysis.push('\n#### 2. 配置检查\n');
    if (noUserId) analysis.push(`- 用户ID: ❌ 不可用`);
    else analysis.push(`- 用户ID: ✅ 可用`);
    analysis.push(`- 远端配置: ${hasRemoteConfig ? '✅ 加载成功' : '❌ 未检测到加载成功日志'}`);
    if (noGrayRelease) analysis.push(`- 灰度状态: ❌ 未在灰度列表`);
    else if (hasRemoteConfig) analysis.push(`- 灰度状态: ✅ 已命中灰度`);

    // 任务触发检查
    analysis.push('\n#### 3. 任务触发检查\n');
    const triggerEnabled = scanLogs.includes('[ScanTriggerManager] File save watcher setup completed');
    const triggerDisabled = scanLogs.includes('[ScanTriggerManager] file-save trigger is disabled');
    if (triggerEnabled) analysis.push(`- 触发器设置: ✅ 文件保存监听已启用`);
    else if (triggerDisabled) analysis.push(`- 触发器设置: ❌ 文件保存触发器未启用`);
    else analysis.push(`- 触发器设置: ⚠️ 状态未知`);
    analysis.push(`- 计划生成: ${planCount > 0 ? `✅ 生成 ${planCount} 个计划` : '❌ 未生成计划'}`);
    if (hasDuplicateEvent) analysis.push(`- 事件去重: ⚠️ 检测到重复事件`);

    // 执行检查
    analysis.push('\n#### 4. 执行检查\n');
    if (hasExecutingPlan) {
        analysis.push(`- ICR 进程: ${hasProcessSpawned ? '✅ 已启动' : '❌ 未启动'}`);
    } else {
        analysis.push(`- ICR 进程: ⚠️ 未检测到执行请求`);
    }
    if (hasTaskCompleted) {
        analysis.push(`- 任务完成: ✅ ICR 任务已完成`);
        // 提取结果
        const summaryMatch = scanLogs.match(/summary.*?({.*?})/s);
        if (summaryMatch) analysis.push(`  - 摘要: ${summaryMatch[1].substring(0, 100)}...`);
    } else if (hasTaskFailed) {
        analysis.push(`- 任务完成: ❌ ICR 任务失败`);
        const errorMatch = scanLogs.match(/error.*?["'](.*?)["']/s);
        if (errorMatch) analysis.push(`  - 错误: ${errorMatch[1]}`);
    } else {
        analysis.push(`- 任务完成: ⚠️ 未检测到完成日志`);
    }
    analysis.push(`- 结果接收: ${hasScanResult ? '✅ 已接收扫描结果' : '❌ 未接收结果'}`);

    // 统计 issues
    const issueMatches = scanLogs.match(/\[IcrExecutor\] ICR issue received/g);
    const issueCount = issueMatches ? issueMatches.length : 0;
    analysis.push(`\n- 发现问题数: ${issueCount}`);

    // 问题诊断
    analysis.push('\n### 发现的问题\n');

    const problems = [];

    if (noUserId) {
        problems.push({
            level: 'ERROR',
            message: '用户ID不可用，扫描功能被禁用',
            suggestion: '检查用户登录状态，确保 kernel.config.username 有值'
        });
    }

    if (configFailed) {
        problems.push({
            level: 'ERROR',
            message: '远端配置加载失败',
            suggestion: '检查网络连接和接口地址，确认 http://icodeqa.baidu.com/rest/ai/icode-cli/api/cli/comate/config 可访问'
        });
    }

    if (noGrayRelease) {
        problems.push({
            level: 'WARN',
            message: '用户未在灰度列表，扫描功能未启用',
            suggestion: '联系后台配置灰度或等待灰度开放'
        });
    }

    if (!hasIcrBinary && hasIcrExecutor) {
        problems.push({
            level: 'ERROR',
            message: 'ICR 二进制未找到',
            suggestion: '检查 ICODE_CLI_INSTALL_DIR 环境变量或运行 ICR 安装脚本'
        });
    }

    if (planCount === 0 && hasScanRequest) {
        problems.push({
            level: 'WARN',
            message: '收到扫描请求但未生成计划',
            suggestion: '检查任务配置，确认 triggers 和 scopeFilter 配置正确'
        });
    }

    if (hasTaskFailed) {
        problems.push({
            level: 'ERROR',
            message: 'ICR 任务执行失败',
            suggestion: '检查 stderr 输出和 ICR 输入参数'
        });
    }

    if (!hasScanResult && hasTaskCompleted) {
        problems.push({
            level: 'WARN',
            message: '任务完成但未收到结果',
            suggestion: '检查通知机制，确认 scan/result 通知正常发送'
        });
    }

    if (problems.length === 0) {
        problems.push({
            level: 'INFO',
            message: '未发现明显问题，扫描流程正常运行',
            suggestion: null
        });
    }

    problems.forEach(p => {
        const emoji = p.level === 'ERROR' ? '❌' : p.level === 'WARN' ? '⚠️' : 'ℹ️';
        analysis.push(`${emoji} **${p.level}**: ${p.message}`);
        if (p.suggestion) {
            analysis.push(`   建议: ${p.suggestion}`);
        }
        analysis.push('');
    });

    // 错误日志
    if (errorLogs) {
        analysis.push('\n### 关联的错误日志\n');
        analysis.push('```');
        analysis.push(errorLogs.substring(0, 2000));
        if (errorLogs.length > 2000) {
            analysis.push('\n... (日志过长，已截断)');
        }
        analysis.push('```\n');
    }

    // 过滤后的扫描日志
    analysis.push('\n### 过滤后的扫描日志\n');
    analysis.push('```');
    analysis.push(scanLogs.substring(0, 5000));
    if (scanLogs.length > 5000) {
        analysis.push('\n... (日志过长，已截断)');
    }
    analysis.push('```\n');

    analysis.push('\n### 相关代码文件\n');
    analysis.push('- `packages/kernel/src/service/ScanScheduler/index.ts` - 主调度器');
    analysis.push('- `packages/kernel/src/service/ScanScheduler/ConfigManager.ts` - 配置管理');
    analysis.push('- `packages/kernel/src/service/ScanScheduler/StateManager.ts` - 状态管理');
    analysis.push('- `packages/kernel/src/service/ScanScheduler/IcrExecutor.ts` - ICR 执行器');
    analysis.push('- `packages/kernel/src/service/ScanScheduler/IcrInstaller.ts` - ICR 安装器');
    analysis.push('- `packages/vscode/src/services/ScanTriggerManager.ts` - 触发管理器');

    return analysis.join('\n');
}

/**
 * 主函数
 */
function main() {
    const args = process.argv.slice(2);
    let logFilePath;

    // 解析参数
    if (args.length === 0) {
        // 默认使用今天的日志
        logFilePath = getTodayLogFilePath();
    } else if (args[0] === 'list' || args[0] === '-l' || args[0] === '--list') {
        // 列出可用日志
        console.log('可用的日志文件:\n');
        const logs = listAvailableLogs();
        if (logs.length === 0) {
            console.log('没有找到日志文件');
        } else {
            logs.forEach(f => console.log(`  ${f}`));
        }
        return;
    } else if (args[0] === 'help' || args[0] === '-h' || args[0] === '--help') {
        // 显示帮助
        console.log(`
扫描日志分析脚本

用法:
  node scripts/analyze-scan-log.js              # 分析今天的日志
  node scripts/analyze-scan-log.js <date>        # 分析指定日期的日志 (yyyy-mm-dd)
  node scripts/analyze-scan-log.js <file>        # 分析指定的日志文件
  node scripts/analyze-scan-log.js list          # 列出可用的日志文件
  node scripts/analyze-scan-log.js help         # 显示帮助信息

示例:
  node scripts/analyze-scan-log.js              # 分析 2026-03-03 的日志
  node scripts/analyze-scan-log.js 2026-03-02   # 分析 2026-03-02 的日志
  node scripts/analyze-scan-log.js list         # 列出所有日志文件
`);
        return;
    } else if (/^\d{4}-\d{2}-\d{2}$/.test(args[0])) {
        // 日期格式
        logFilePath = getDateLogFilePath(args[0]);
    } else {
        // 文件路径
        logFilePath = args[0];
    }

    console.log(`分析日志文件: ${logFilePath}\n`);

    // 读取并过滤日志
    const scanLogs = readAndFilterLogs(logFilePath, KEYWORDS);
    const errorLogs = findRelatedErrors(logFilePath);

    if (!scanLogs) {
        console.log('未找到相关的扫描日志');
        return;
    }

    // 生成分析报告
    const report = generateAnalysisReport(scanLogs, errorLogs);

    console.log(report);

    // 可选：写入报告文件
    const reportPath = path.join(process.cwd(), 'scan-log-analysis.md');
    fs.writeFileSync(reportPath, report);
    console.log(`\n分析报告已保存到: ${reportPath}`);
}

// 运行主函数
main();
