# F32 模拟支付订单

## 所属模块
订单与交易管理

## 参与者
已登录普通用户（买家）

## 优先级
高

## 前置条件
订单属于当前买家，交易方式为线上模拟，状态为待支付。

## 触发条件
买家点击 "模拟支付"。

## 输入数据
订单编号、支付确认。

## 处理流程与业务规则

### 第一步：权限校验
首先校验订单是否属于当前登录的买家用户，确保买家只能支付自己的订单。如果当前用户不是订单的买家，直接拒绝支付操作并返回无权操作的提示信息。

### 第二步：订单状态校验
检查订单的当前状态，确保订单状态为待支付（CONFIRMED），同时检查交易方式是否为线上模拟（ONLINE）。如果状态不符或交易方式不符合要求，拒绝支付操作并返回相应提示信息。

### 第三步：支付状态幂等校验
检查订单的支付状态，如果已经是已支付（PAID）状态，则返回原成功结果，不进行重复支付处理，确保支付操作的幂等性。

### 第四步：订单金额校验
校验订单金额是否有效，确保金额大于等于零，避免金额异常的订单进行支付操作。如果金额异常，拒绝支付并返回错误提示。

### 第五步：生成模拟支付流水号
使用唯一的流水号生成算法，为本次支付操作生成一个唯一的模拟支付流水号，用于记录和追踪支付行为。

### 第六步：更新订单状态
在数据库事务中更新订单的支付状态为已支付（PAID），记录支付时间，同时将订单状态更新为待完成（PAID）。

### 第七步：发送通知
向买家发送支付成功的通知，包含订单编号和支付流水号信息。同时向卖家发送买家已支付的通知，告知卖家订单已完成支付。

### 第八步：事务提交
将所有更新操作在一个数据库事务中完成，确保数据的一致性。如果任何步骤出现异常，进行事务回滚，保证数据不被破坏。

## 输出及后置条件
返回支付成功、流水号和新状态。

## 异常与边界处理

### 重复支付处理
当用户对同一订单重复发起支付请求时，系统检测到订单已处于已支付状态，直接返回原成功结果，不进行重复处理，确保同一订单只产生一个有效支付流水。

### 状态不符处理
当订单状态不符合支付要求时（如订单未确认、已取消、已完成等），系统拒绝支付操作并返回状态不符的提示信息。

### 金额异常处理
当订单金额小于零或存在其他异常时，系统拒绝支付操作并返回金额异常的提示信息。

### 数据库故障处理
当数据库操作出现故障时，系统进行事务回滚，拒绝支付操作并返回数据库故障的提示信息，确保数据一致性。

## 验收标准
同一订单只产生一个有效支付流水；支付成功后不能再次支付。

## 面向对象设计

### 分层架构
本功能遵循前后端分层开发逻辑，采用经典的三层架构：表现层（Controller）负责接收用户请求和返回响应；业务逻辑层（Service）负责处理核心业务规则；数据访问层（Model）负责与数据库交互。

### 核心类设计

#### PaymentService 类
支付服务类，负责处理模拟支付的核心业务逻辑，包含支付校验、流水号生成、状态更新、通知发送等方法。

#### Order 类
订单模型类，负责订单数据的存储和管理，包含订单状态、支付状态、支付时间等属性，以及状态转换验证方法。

#### NotificationService 类
通知服务类，负责向买家和卖家发送支付相关的通知信息。

## 伪代码

此业务流程需要绘制程序流程图、N-S 图。

```
// 表现层 - 支付控制器
class PaymentController:
    // 处理模拟支付请求
    method handlePaymentRequest(orderId, userId):
        // 获取订单对象
        order = OrderModel.getOrderById(orderId)
        
        // 调用业务层进行支付处理
        success, message, transactionNo, newStatus = PaymentService.simulatePayment(order, userId)
        
        // 返回响应
        return {
            success: success,
            message: message,
            transactionNo: transactionNo,
            newStatus: newStatus
        }

// 业务逻辑层 - 支付服务
class PaymentService:
    // 模拟支付核心方法
    classmethod simulatePayment(order, buyerId):
        try:
            // 开始数据库事务
            beginTransaction()
            
            // 步骤1：校验订单所属
            if order.buyerId != buyerId:
                rollbackTransaction()
                return false, "无权操作此订单", null, null
            
            // 步骤2：幂等校验 - 已支付则直接返回成功
            if order.paymentStatus == "PAID":
                commitTransaction()
                return true, "该订单已支付", order.transactionNo, order.orderStatus
            
            // 步骤3：校验订单状态
            if order.orderStatus != "CONFIRMED":
                rollbackTransaction()
                return false, "订单状态不允许支付", null, null
            
            // 步骤4：校验交易方式
            if order.tradeType != "ONLINE":
                rollbackTransaction()
                return false, "线下交易无需模拟支付", null, null
            
            // 步骤5：校验订单金额
            if order.orderAmount < 0:
                rollbackTransaction()
                return false, "订单金额异常", null, null
            
            // 步骤6：生成模拟支付流水号
            transactionNo = generateTransactionNo()
            
            // 步骤7：更新订单状态
            order.paymentStatus = "PAID"
            order.paidAt = getCurrentDateTime()
            order.orderStatus = "PAID"
            order.transactionNo = transactionNo
            
            // 步骤8：向买家发送支付成功通知
            NotificationService.sendNotification(
                receiverId: order.buyerId,
                type: "ORDER",
                title: "支付成功",
                content: "订单 {order.orderNo} 支付成功。交易编号：{transactionNo}",
                relatedId: order.orderId
            )
            
            // 步骤9：向卖家发送支付通知
            NotificationService.sendNotification(
                receiverId: order.sellerId,
                type: "ORDER",
                title: "买家已支付",
                content: "订单 {order.orderNo} 买家已完成支付。",
                relatedId: order.orderId
            )
            
            // 提交事务
            commitTransaction()
            
            // 返回成功结果
            return true, "支付成功！交易编号：{transactionNo}", transactionNo, order.orderStatus
            
        catch DatabaseException:
            // 数据库异常处理
            rollbackTransaction()
            return false, "支付失败，数据库故障，请稍后重试", null, null
        catch Exception:
            // 其他异常处理
            rollbackTransaction()
            return false, "支付失败，请稍后重试", null, null

// 数据模型层 - 订单模型
class OrderModel:
    // 属性定义
    property orderId
    property orderNo
    property buyerId
    property sellerId
    property orderAmount
    property tradeType
    property orderStatus
    property paymentStatus
    property paidAt
    property transactionNo
    
    // 根据ID获取订单
    classmethod getOrderById(orderId):
        return database.query("SELECT * FROM orders WHERE order_id = ?", orderId)
    
    // 保存订单更新
    method save():
        database.update("orders", this)

// 辅助类 - 流水号生成器
class TransactionNoGenerator:
    classmethod generate():
        // 生成唯一的支付流水号
        timestamp = getCurrentTimestamp()
        randomPart = generateRandomString(8)
        return "PAY" + timestamp + randomPart

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
```

## 页面流程设计

购买页面的提交订单点了之后，跳转到模拟支付界面。

### 模拟支付页面设计
模拟支付页面展示订单信息，包括订单编号、商品名称、订单金额等关键信息。页面提供"确认支付"按钮供买家点击。点击后，前端调用后端支付接口，完成支付流程后展示支付成功结果，包括支付流水号和新的订单状态，并提供返回订单详情或订单列表的链接。
