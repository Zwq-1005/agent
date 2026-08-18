import sqlite3
from datetime import datetime


def init_database():
    """初始化数据库，创建表并插入模拟数据"""
    conn = sqlite3.connect("customer_service.db")
    cursor = conn.cursor()

    # ========== 创建订单表 ==========
    cursor.execute("""CREATE TABLE IF NOT EXISTS orders (
        order_id TEXT PRIMARY KEY,
        user_name TEXT NOT NULL,
        product_name TEXT NOT NULL,
        status TEXT NOT NULL,
        amount REAL NOT NULL,
        create_time TEXT NOT NULL
    )""")

    # ========== 创建工单表 ==========
    cursor.execute("""CREATE TABLE IF NOT EXISTS tickets (
        ticket_id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_name TEXT NOT NULL,
        issue_type TEXT NOT NULL,
        description TEXT NOT NULL,
        status TEXT DEFAULT '待处理',
        create_time TEXT NOT NULL
    )""")

    # ========== 插入模拟订单数据 ==========
    sample_orders = [
        ("ORD202401001", "张三", "智锐AI学习机Pro", "已发货", 2999.00, "2024-01-15 10:30:00"),
        ("ORD202401002", "李四", "智锐智能手表S1", "已完成", 1299.00, "2024-01-18 14:20:00"),
        ("ORD202401003", "王五", "智睿AI助手Mini", "待发货", 599.00, "2024-01-20 09:15:00"),
        ("ORD202401004", "赵六", "智锐AI学习机Pro", "已取消", 2999.00, "2024-01-22 16:45:00"),
        ("ORD202401005", "张三", "智锐智能音箱M3", "已发货", 899.00, "2024-01-25 11:00:00"),
        ("ORD202401006", "孙七", "智睿AI助手Mini", "已完成", 599.00, "2024-02-01 08:30:00"),
        ("ORD202401007", "李四", "智锐智能手表S1 Pro", "待发货", 1599.00, "2024-02-05 13:10:00"),
        ("ORD202401008", "周八", "智锐AI学习机Pro", "已发货", 2999.00, "2024-02-10 15:25:00"),
    ]
    cursor.executemany(
        "INSERT OR IGNORE INTO orders VALUES (?,?,?,?,?,?)", sample_orders
    )

    # ========== 插入模拟工单数据 ==========
    sample_tickets = [
        ("张三", "退货", "AI学习机Pro屏幕有亮点，申请退货", "已处理", "2024-01-20 09:00:00"),
        ("李四", "维修", "智能手表S1电池续航严重不足", "处理中", "2024-02-01 10:30:00"),
    ]
    cursor.executemany(
        "INSERT OR IGNORE INTO tickets (user_name, issue_type, description, status, create_time) VALUES (?,?,?,?,?)",
        sample_tickets,
    )

    conn.commit()
    conn.close()
    print(" 数据库初始化完成！")
    print("   - 订单表：8条模拟数据")
    print("   - 工单表：2条模拟数据")


if __name__ == "__main__":
    init_database()