"""订单与工单相关工具"""
import sqlite3
from datetime import datetime
from langchain.tools import tool


def _get_db_connection():
    """获取数据库连接"""
    conn = sqlite3.connect("customer_service.db")
    conn.row_factory = sqlite3.Row
    return conn


@tool()
def query_order(order_id: str) -> dict:
    """
    根据订单号查询订单状态和详细信息
    入参：
        order_id: 字符串类型，订单编号，格式如 ORD202401001
    """
    conn = _get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM orders WHERE order_id = ?", (order_id,))
    row = cursor.fetchone()
    conn.close()

    if row:
        return {
            "order_id": row["order_id"],
            "user_name": row["user_name"],
            "product_name": row["product_name"],
            "status": row["status"],
            "amount": row["amount"],
            "create_time": row["create_time"],
        }
    else:
        return {"error": f"未找到订单号为 {order_id} 的订单，请检查订单号是否正确"}


@tool()
def query_orders_by_name(user_name: str) -> dict:
    """
    根据用户姓名查询该用户的所有订单
    入参：
        user_name: 字符串类型，用户姓名
    """
    conn = _get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM orders WHERE user_name = ?", (user_name,))
    rows = cursor.fetchall()
    conn.close()

    if rows:
        orders = []
        for row in rows:
            orders.append({
                "order_id": row["order_id"],
                "product_name": row["product_name"],
                "status": row["status"],
                "amount": row["amount"],
                "create_time": row["create_time"],
            })
        return {"user_name": user_name, "order_count": len(orders), "orders": orders}
    else:
        return {"error": f"未找到用户 {user_name} 的订单记录"}


@tool()
def query_logistics(order_id: str) -> dict:
    """
    根据订单号查询物流信息
    入参：
        order_id: 字符串类型，订单编号
    """
    conn = _get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM orders WHERE order_id = ?", (order_id,))
    row = cursor.fetchone()
    conn.close()

    if not row:
        return {"error": f"未找到订单号为 {order_id} 的订单"}

    status = row["status"]
    if status == "待发货":
        return {
            "order_id": order_id,
            "logistics_status": "尚未发货",
            "estimated_ship_time": "预计1-2个工作日内发货",
        }
    elif status == "已发货":
        return {
            "order_id": order_id,
            "logistics_status": "运输中",
            "courier": "顺丰速运",
            "tracking_number": f"SF{order_id[-6:]}1234567890",
            "estimated_arrival": "预计2-3天到达",
        }
    elif status == "已完成":
        return {
            "order_id": order_id,
            "logistics_status": "已签收",
            "courier": "顺丰速运",
            "tracking_number": f"SF{order_id[-6:]}1234567890",
        }
    elif status == "已取消":
        return {
            "order_id": order_id,
            "logistics_status": "订单已取消，无物流信息",
        }
    else:
        return {"order_id": order_id, "logistics_status": status}


@tool()
def create_ticket(user_name: str, issue_type: str, description: str) -> dict:
    """
    创建售后工单
    入参：
        user_name: 字符串类型，用户姓名
        issue_type: 字符串类型，问题类型，可选值为：退货、换货、维修、投诉、其他
        description: 字符串类型，问题描述
    """
    valid_types = ["退货", "换货", "维修", "投诉", "其他"]
    if issue_type not in valid_types:
        return {"error": f"无效的问题类型'{issue_type}'，可选值为：{', '.join(valid_types)}"}

    conn = _get_db_connection()
    cursor = conn.cursor()
    create_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    cursor.execute(
        "INSERT INTO tickets (user_name, issue_type, description, status, create_time) VALUES (?,?,?,?,?)",
        (user_name, issue_type, description, "待处理", create_time),
    )
    conn.commit()
    ticket_id = cursor.lastrowid
    conn.close()

    return {
        "ticket_id": ticket_id,
        "user_name": user_name,
        "issue_type": issue_type,
        "description": description,
        "status": "待处理",
        "create_time": create_time,
        "message": f"工单创建成功！工单号：{ticket_id}，我们将在24小时内处理，请留意通知。",
    }


# ========== 测试 ==========
if __name__ == "__main__":
    print("=== 测试 query_order ===")
    print(query_order.invoke({"order_id": "ORD202401001"}))

    print("\n=== 测试 query_orders_by_name ===")
    print(query_orders_by_name.invoke({"user_name": "张三"}))

    print("\n=== 测试 query_logistics ===")
    print(query_logistics.invoke({"order_id": "ORD202401001"}))

    print("\n=== 测试 create_ticket ===")
    print(create_ticket.invoke({
        "user_name": "张三",
        "issue_type": "退货",
        "description": "屏幕有亮点"
    }))