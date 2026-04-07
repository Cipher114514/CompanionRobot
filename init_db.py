# -*- coding: utf-8 -*-
"""
数据库初始化脚本
用于创建/重建数据库表结构
"""

import os
import sys

# 确保可以导入项目模块
sys.path.insert(0, os.path.dirname(__file__))

from flask import Flask
from models import db, User, init_db

def create_database():
    """创建数据库"""
    app = Flask(__name__)

    # 配置数据库
    app.config.update(
        SECRET_KEY='your-secret-key-change-this-in-production',
        SQLALCHEMY_DATABASE_URI='sqlite:///mental_health.db',
        SQLALCHEMY_TRACK_MODIFICATIONS=False
    )

    # 初始化数据库
    db.init_app(app)

    with app.app_context():
        # 删除所有表（如果存在）
        print("正在清理旧数据库...")
        db.drop_all()
        print("  [OK] 旧表已删除")

        # 创建所有表
        print("正在创建新数据库...")
        db.create_all()
        print("  [OK] 数据库表创建成功")

    # 创建示例用户
    with app.app_context():
        # 检查是否已有用户
        if User.query.count() == 0:
            print("\n创建示例用户...")

            # 示例患者
            patient = User(
                username='patient_demo',
                email='patient@example.com',
                role='patient'
            )
            patient.set_password('patient123')
            db.session.add(patient)

            # 示例咨询师
            counselor = User(
                username='counselor_demo',
                email='counselor@example.com',
                role='counselor'
            )
            counselor.set_password('counselor123')
            db.session.add(counselor)

            db.session.commit()
            print("[OK] 示例用户创建成功")
            print("  - 患者账号: patient_demo / patient123")
            print("  - 咨询师账号: counselor_demo / counselor123")
        else:
            print(f"\n数据库已有 {User.query.count()} 个用户，跳过示例用户创建")

    print("\n[OK] 数据库初始化完成!")
    print(f"数据库位置: {os.path.join(os.path.dirname(__file__), 'instance', 'mental_health.db')}")

def init_database_auto():
    """自动初始化数据库（非交互式）"""
    print("=" * 60)
    print("数据库初始化工具".center(60))
    print("=" * 60)
    print("\n正在创建新的数据库表结构...")
    create_database()

if __name__ == '__main__':
    # 支持命令行参数
    if len(sys.argv) > 1 and sys.argv[1] == '--auto':
        init_database_auto()
    else:
        print("=" * 60)
        print("数据库初始化工具".center(60))
        print("=" * 60)
        print("\n警告: 此脚本将创建新的数据库表结构")
        print("如果旧数据库存在，建议先删除 instance/mental_health.db\n")

        response = input("是否继续? (y/n): ").strip().lower()
        if response == 'y':
            create_database()
        else:
            print("已取消")
