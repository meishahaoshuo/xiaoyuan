# F31 卖家拒绝订单

## 所属模块

订单与交易管理

## 参与者

已登录普通用户（卖家）

## 优先级

高

## 前置条件

订单属于当前卖家且状态为待卖家确认。

## 触发条件

卖家点击拒绝。

## 输入数据

订单编号、拒绝原因 2～100 字。

## 处理流程与业务规则

### 第一步：权限校验

首先校验订单是否属于当前登录的卖家用户，确保卖家只能拒绝自己的订单。如果当前用户不是订单的卖家，直接拒绝操作并返回无权操作的提示信息。

### 第二步：订单状态校验

检查订单的当前状态，确保订单状态为待卖家确认（PENDING）。如果状态不符，拒绝拒绝操作并返回相应提示信息。

### 第三步：拒绝原因校验

校验拒绝原因是否符合要求：原因不能为空，长度必须在2～100个字符之间。如果原因缺失或长度不符合要求，拒绝操作并返回错误提示信息。

### 第四步：更新订单状态

将订单状态置为已拒绝（REJECTED），同时记录拒绝原因。

### 第五步：商品保持在售

拒绝订单后，商品保持在售状态，不做任何修改，允许其他买家继续购买该商品。

### 第六步：发送通知

向买家发送订单已被拒绝的通知，通知中包含订单编号和拒绝原因。

### 第七步：事务提交

将所有更新操作在一个数据库事务中完成，确保数据的一致性。如果任何步骤出现异常，进行事务回滚，保证数据不被破坏。

## 输出及后置条件

返回拒绝成功和订单终态。

## 异常与边界处理

### 原因缺失处理

当卖家未提供拒绝原因或原因过短或过长时，系统拒绝拒绝操作并返回原因需要2～100个字符的提示信息。

### 订单已处理处理

当订单状态不是待确认时，系统拒绝拒绝操作并返回订单当前状态无法拒绝的提示信息。

### 无权限处理

当当前用户不是订单的卖家时，系统拒绝拒绝操作并返回无权操作此订单的提示信息。

## 验收标准

待确认订单可拒绝且买家可看到原因；其他状态不能拒绝。

## 面向对象设计

### 分层架构

本功能遵循前后端分层开发逻辑，采用经典的三层架构：表现层（Controller）负责接收用户请求和返回响应；业务逻辑层（Service）负责处理核心业务规则；数据访问层（Model）负责与数据库交互。

### 核心类设计

#### OrderRejectController 类

卖家拒绝订单控制器类，负责处理卖家拒绝订单的HTTP请求，接收并验证参数，调用业务层完成拒绝操作，然后重定向到订单详情页面。

#### OrderService 类

订单服务类，负责处理卖家拒绝订单的核心业务逻辑，包含权限校验、状态校验、原因校验、状态更新、通知发送等方法。

#### Order 类

订单模型类，负责订单数据的存储和管理，包含订单状态、拒绝原因等属性，以及状态转换验证方法。

#### NotificationService 类

通知服务类，负责向买家发送订单被拒绝的通知信息。

## 伪代码

此业务流程需要绘制程序流程图、N-S 图。

```
// 表现层 - 卖家拒绝订单控制器
class OrderRejectController:
    // 处理卖家拒绝订单请求
    method handleRejectRequest(orderId, sellerId, reason):
        // 获取订单对象
        order = OrderModel.getOrderById(orderId)
        if not order:
            return redirect with error "订单不存在"
        
        // 调用业务层进行拒绝操作
        success, message = OrderService.sellerRejectOrder(order, sellerId, reason)
        
        // 根据结果返回响应
        if success:
            flash success message
        else:
            flash error message
        
        // 重定向到订单详情页
        return redirect to order detail page

// 业务逻辑层 - 订单服务
class OrderService:
    // 卖家拒绝订单核心方法
    classmethod sellerRejectOrder(order, sellerId, reason):
        try:
            // 开始数据库事务
            beginTransaction()
            
            // 步骤1：校验权限
            if order.sellerId != sellerId:
                rollbackTransaction()
                return False, "无权操作此订单"
            
            // 步骤2：校验订单状态
            if order.orderStatus != "PENDING":
                rollbackTransaction()
                return False, "订单当前状态无法拒绝"
            
            // 步骤3：校验拒绝原因
            trimmedReason = reason.trim()
            if not trimmedReason or len(trimmedReason) < 2 or len(trimmedReason) > 100:
                rollbackTransaction()
                return False, "拒绝原因需要2~100个字符"
            
            // 步骤4：更新订单状态
            order.orderStatus = "REJECTED"
            order.rejectReason = trimmedReason
            
            // 注意：商品保持在售，无需修改商品状态
            
            // 步骤5：向买家发送通知
            NotificationService.sendNotification(
                receiverId: order.buyerId,
                type: "ORDER",
                title: "订单已被拒绝",
                content: "您的订单 {order.orderNo} 已被卖家拒绝。原因：{trimmedReason}",
                relatedId: order.orderId
            )
            
            // 提交事务
            commitTransaction()
            
            // 返回成功结果
            return True, "已拒绝该订单"
            
        catch DatabaseException:
            // 数据库异常处理
            rollbackTransaction()
            return False, "拒绝失败，数据库故障，请稍后重试"
        catch Exception:
            // 其他异常处理
            rollbackTransaction()
            return False, "拒绝失败，请稍后重试"

// 数据模型层 - 订单模型
class OrderModel:
    // 属性定义
    property orderId
    property orderNo
    property productId
    property buyerId
    property sellerId
    property orderAmount
    property tradeType
    property orderStatus
    property paymentStatus
    property rejectReason
    property createdAt
    property completedAt
    property deleted
    
    // 根据ID获取订单
    classmethod getOrderById(orderId):
        return database.query("SELECT * FROM orders WHERE order_id = ?", orderId)
    
    // 保存订单更新
    method save():
        database.update("orders", this)

// 通知服务
class NotificationService:
    classmethod sendNotification(receiverId, type, title, content, relatedId):
        notification = new Notification()
        notification.receiverId = receiverId
        notification.type = type
        notification.title = title
        notification.content = content
        notification.relatedId = relatedId
        notification.createdAt = getCurrentDateTime()
        notification.save()

// 视图层 - 模板渲染逻辑
class SellerOrderListView:
    // 渲染订单列表页面，展示拒绝按钮和模态框
    method renderOrderList(orders):
        for order in orders:
            render order card
            if order.orderStatus == "PENDING":
                render reject button
                render reject modal with reason input
```
