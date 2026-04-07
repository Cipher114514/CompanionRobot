# -*- coding: utf-8 -*-
"""
综合测试运行脚本

一键运行所有测试并生成汇总报告

运行方式：
    python tests/run_all_tests.py
"""

import sys
import os
import subprocess
import json
from datetime import datetime

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class ComprehensiveTestRunner:
    """综合测试运行器"""

    def __init__(self):
        """初始化测试运行器"""
        self.test_scripts = [
            {
                "name": "危机检测模块测试",
                "script": "tests/crisis_detection/test_crisis_detection.py",
                "description": "测试危机关键词识别、等级判定、干预机制",
                "priority": "high"
            },
            {
                "name": "情绪分析功能测试",
                "script": "tests/sentiment_analysis/test_sentiment_analysis.py",
                "description": "测试情绪识别准确性、置信度",
                "priority": "high"
            },
            {
                "name": "文本对话功能测试",
                "script": "tests/dialogue/test_text_dialogue.py",
                "description": "测试对话生成、响应质量、处理速度（无RAG）",
                "priority": "high"
            },
            {
                "name": "报告生成功能测试",
                "script": "tests/profile_page/test_report_generation.py",
                "description": "测试报告生成器、模块推荐、年龄适配",
                "priority": "medium"
            },
            {
                "name": "咨询师仪表盘测试",
                "script": "tests/dashboard_report/test_counselor_dashboard.py",
                "description": "测试患者管理、数据查看、报告导出",
                "priority": "medium"
            }
        ]

        self.test_results = {}
        self.start_time = datetime.now()

    def print_header(self):
        """打印标题"""
        print("\n" + "="*80)
        print("元气充能陪伴平台 - 综合测试套件")
        print("="*80)
        print(f"开始时间: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"测试数量: {len(self.test_scripts)}")
        print("="*80)

    def print_footer(self):
        """打印总结"""
        end_time = datetime.now()
        duration = (end_time - self.start_time).total_seconds()

        print("\n" + "="*80)
        print("测试完成")
        print("="*80)
        print(f"结束时间: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"总耗时: {duration:.1f}秒")
        print("="*80)

    def run_single_test(self, test_config: dict) -> dict:
        """
        运行单个测试脚本

        参数:
            test_config: 测试配置字典

        返回:
            测试结果字典
        """
        test_name = test_config["name"]
        script_path = test_config["script"]

        print(f"\n{'='*80}")
        print(f"运行: {test_name}")
        print(f"描述: {test_config['description']}")
        print(f"脚本: {script_path}")
        print(f"{'='*80}\n")

        result = {
            "name": test_name,
            "script": script_path,
            "success": False,
            "exit_code": -1,
            "output": "",
            "error": "",
            "start_time": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "end_time": None,
            "duration": 0
        }

        try:
            # 设置环境变量，强制子进程使用UTF-8
            env = os.environ.copy()
            env['PYTHONIOENCODING'] = 'utf-8'

            # 运行测试脚本
            process = subprocess.Popen(
                [sys.executable, script_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding='utf-8',
                errors='replace',
                env=env
            )

            # 等待进程完成
            stdout, stderr = process.communicate()

            result["exit_code"] = process.returncode
            result["output"] = stdout
            result["error"] = stderr
            result["end_time"] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

            # 计算耗时
            start = datetime.strptime(result["start_time"], '%Y-%m-%d %H:%M:%S')
            end = datetime.strptime(result["end_time"], '%Y-%m-%d %H:%M:%S')
            result["duration"] = (end - start).total_seconds()

            # 判断是否成功
            result["success"] = (process.returncode == 0)

            if result["success"]:
                print(f"[OK] {test_name} 测试通过 (耗时: {result['duration']:.1f}秒)")
            else:
                print(f"[ERROR] {test_name} 测试失败 (退出码: {process.returncode})")
                if stderr:
                    print(f"错误信息:\n{stderr[:500]}")

        except Exception as e:
            result["end_time"] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            result["error"] = str(e)
            print(f"[ERROR] {test_name} 执行异常: {str(e)}")

        return result

    def run_all_tests(self):
        """运行所有测试"""
        self.print_header()

        for i, test_config in enumerate(self.test_scripts, 1):
            print(f"\n[进度: {i}/{len(self.test_scripts)}]")
            result = self.run_single_test(test_config)
            self.test_results[test_config["name"]] = result

        self.print_footer()

    def generate_summary_report(self) -> str:
        """
        生成汇总报告

        返回:
            报告内容（Markdown格式）
        """
        total_tests = len(self.test_results)
        passed_tests = sum(1 for r in self.test_results.values() if r["success"])
        failed_tests = total_tests - passed_tests
        total_duration = sum(r["duration"] for r in self.test_results.values())

        report = []
        report.append("# 元气充能陪伴平台 - 综合测试报告\n")
        report.append(f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        report.append("---\n")

        # 测试概览
        report.append("## 测试概览\n")
        report.append(f"- **测试套件数**: {total_tests}")
        report.append(f"- **通过数**: {passed_tests}")
        report.append(f"- **失败数**: {failed_tests}")
        report.append(f"- **通过率**: {(passed_tests/total_tests)*100:.1f}%")
        report.append(f"- **总耗时**: {total_duration:.1f}秒\n")

        # 总体状态
        if failed_tests == 0:
            report.append("[OK] **总体状态**: 所有测试通过！\n")
        elif failed_tests <= 1:
            report.append("[WARN] **总体状态**: 部分测试失败，需要检查\n")
        else:
            report.append("[ERROR] **总体状态**: 多个测试失败，系统需要修复\n")

        # 各测试套件详情
        report.append("## 各测试套件详情\n")

        for test_name, result in self.test_results.items():
            status = "[OK] 通过" if result["success"] else "[ERROR] 失败"
            report.append(f"### {test_name} - {status}\n")
            report.append(f"- **脚本**: {result['script']}\n")
            report.append(f"- **开始时间**: {result['start_time']}\n")
            report.append(f"- **结束时间**: {result['end_time']}\n")
            report.append(f"- **耗时**: {result['duration']:.1f}秒\n")

            if result["exit_code"] != -1:
                report.append(f"- **退出码**: {result['exit_code']}\n")

            if result["error"]:
                report.append(f"\n**错误信息**:\n```\n{result['error'][:500]}\n```\n")

            report.append("\n---\n")

        # 快速链接
        report.append("## 详细报告链接\n")

        for test_name, result in self.test_results.items():
            script_name = os.path.basename(result["script"]).replace(".py", "")
            report.append(f"- [{test_name}](results/{script_name}_report_*.md)\n")

        # 结论与建议
        report.append("## 测试结论\n")

        if failed_tests == 0:
            report.append("[OK] **所有测试通过！系统功能正常。**\n")
        else:
            report.append(f"[ERROR] **{failed_tests}个测试套件失败**，需要关注以下问题:\n\n")

            for test_name, result in self.test_results.items():
                if not result["success"]:
                    report.append(f"#### {test_name}\n")
                    if result["error"]:
                        report.append(f"- {result['error'][:200]}\n")
                    report.append("\n")

        # 改进建议
        report.append("## 改进建议\n")

        if failed_tests > 0:
            report.append("1. **修复失败的测试**\n")
            report.append("   - 查看详细报告了解失败原因\n")
            report.append("   - 检查相关模块代码\n")
            report.append("   - 运行单个测试进行调试\n\n")

        report.append("2. **持续集成**\n")
        report.append("   - 定期运行测试套件\n")
        report.append("   - 在代码修改后运行相关测试\n")
        report.append("   - 保持测试通过率在90%以上\n\n")

        report.append("3. **扩展测试**\n")
        report.append("   - 添加更多边界测试用例\n")
        report.append("   - 增加性能压力测试\n")
        report.append("   - 添加用户场景测试\n")

        report.append("\n---\n")
        report.append("*综合测试报告由测试套件自动生成*\n")

        return "\n".join(report)

    def save_summary_report(self, report_content: str):
        """保存汇总报告"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_dir = "tests/results"

        # 确保目录存在
        os.makedirs(report_dir, exist_ok=True)

        # 保存Markdown报告
        md_path = f"{report_dir}/comprehensive_test_summary_{timestamp}.md"
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(report_content)

        # 保存JSON结果
        json_path = f"{report_dir}/comprehensive_test_results_{timestamp}.json"
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(self.test_results, f, ensure_ascii=False, indent=2)

        print(f"\n[OK] 汇总报告已保存:")
        print(f"  - Markdown: {md_path}")
        print(f"  - JSON: {json_path}")

        return md_path


def main():
    """主函数"""
    runner = ComprehensiveTestRunner()
    runner.run_all_tests()

    # 生成汇总报告
    print("\n[生成汇总报告]")
    report = runner.generate_summary_report()
    runner.save_summary_report(report)

    # 打印最终总结
    print("\n" + "="*80)
    print("测试套件执行完成")
    print("="*80)

    passed = sum(1 for r in runner.test_results.values() if r["success"])
    total = len(runner.test_results)

    print(f"通过: {passed}/{total}")
    print(f"失败: {total-passed}/{total}")
    print(f"通过率: {(passed/total)*100:.1f}%")
    print("="*80)

    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
