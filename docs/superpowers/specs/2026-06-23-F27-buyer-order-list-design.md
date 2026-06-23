# F27 买家查看订单列表

## 所属模块
订单与交易管理

## 参与者
已登录普通用户（买家）

## 优先级
高

## 前置条件
用户会话有效。

## 触发条件
进入 "我买到的"。

## 输入数据
订单状态、关键词、时间范围、页码。

## 处理流程与业务规则

### 第一步：用户权限验证
首先验证用户会话是否有效，确保用户已登录。如果用户未登录或会话已过期，重定向到登录页面，要求用户重新登录。

### 第二步：参数接收与校验
接收用户输入的查询参数，包括订单状态、关键词、时间范围、页码。对订单状态参数进行合法性校验，确保传入的状态值在允许的范围内，如果状态参数非法则返回错误提示。

### 第三步：构建查询条件
仅查询 buyer_id 为当前用户的订单，确保用户只能查看自己的订单数据。根据传入的订单状态参数构建筛选条件，支持待确认、待支付、待交易、待完成、已完成、已取消、已拒绝等多种状态筛选。如果有关键词参数，则通过商品名称进行模糊搜索。如果有时间范围参数，则按订单创建时间进行范围筛选。

### 第四步：排序规则
默认按创建时间倒序排列订单，最新创建的订单显示在最前面，方便用户查看最新的订单信息。

### 第五步：分页处理
根据页码参数对查询结果进行分页处理，每页返回指定数量的订单记录，避免一次性加载过多数据影响性能。

### 第六步：关联数据加载
加载订单关联的商品信息作为商品快照，加载卖家用户信息获取卖家昵称，确保返回完整的订单摘要信息。

### 第七步：可执行操作标识
针对每个订单，根据当前用户身份、订单状态、交易方式等条件，判断用户可以执行的操作，如取消订单、支付、确认收货等，并返回相应的操作标识，供前端展示对应的操作按钮。

## 输出及后置条件
返回分页订单摘要、商品快照、卖家昵称和状态。

## 异常与边界处理

### 无数据时处理
当查询结果为空时，展示空状态页面，提示用户暂无购买记录或没有找到相关订单，并提供去逛逛的链接引导用户浏览商品。

### 非法状态参数处理
当用户传入的订单状态参数不在允许的范围内时，系统返回错误提示，告知用户状态参数非法，并使用默认的查询条件进行处理。

### 页码边界处理
当用户请求的页码超出有效范围时，系统自动调整到有效页码范围内，确保不会返回错误。

### 关键词搜索无结果处理
当使用关键词搜索没有找到匹配的订单时，展示搜索无结果的提示信息，并提供清除搜索条件的选项。

## 验收标准
用户仅能看到自己的买家订单；状态筛选和按钮权限准确。

## 面向对象设计

### 分层架构
本功能遵循前后端分层开发逻辑，采用经典的三层架构：表现层（Controller）负责接收用户请求参数和渲染页面；业务逻辑层（Service）负责处理订单查询、权限控制、操作权限判断等业务规则；数据访问层（Model）负责与数据库交互，执行查询操作。

### 核心类设计

#### BuyerOrderController 类
买家订单控制器类，负责处理买家查看订单列表的 HTTP 请求，接收并验证查询参数，调用业务层获取订单数据，然后渲染页面返回给用户。

#### BuyerOrderService 类
买家订单服务类，负责处理买家订单查询的核心业务逻辑，包括构建查询条件、权限验证、操作权限判断等方法。

#### Order 类
订单模型类，负责订单数据的存储和管理，包含订单相关的属性和查询方法。

#### Product 类
商品模型类，负责商品数据的存储和管理，提供商品快照信息。

#### User 类
用户模型类，负责用户数据的存储和管理，提供卖家昵称信息。

#### PaginationUtil 类
分页工具类，负责处理分页逻辑，生成分页数据。

## 伪代码

此业务流程需要绘制程序流程图。

```
// 表现层 - 买家订单控制器
class BuyerOrderController:
    // 处理买家查看订单列表请求
    method handleBuyerOrderListRequest():
        // 获取当前登录用户
        currentUser = getCurrentLoggedInUser()
        
        // 检查用户会话是否有效
        if not currentUser:
            return redirectToLoginPage()
        
        // 接收查询参数
        statusFilter = getRequestParameter("status")
        keyword = getRequestParameter("keyword")
        timeRangeStart = getRequestParameter("timeRangeStart")
        timeRangeEnd = getRequestParameter("timeRangeEnd")
        page = getRequestParameter("page", defaultValue=1)
        
        // 调用业务层获取订单列表
        result = BuyerOrderService.getBuyerOrderList(
            userId=currentUser.userId,
            statusFilter=statusFilter,
            keyword=keyword,
            timeRangeStart=timeRangeStart,
            timeRangeEnd=timeRangeEnd,
            page=page
        )
        
        // 渲染页面
        return renderTemplate(
            "order/buyer_list.html",
            orders=result.orders,
            pagination=result.pagination,
            currentFilter=statusFilter,
            keyword=keyword,
            timeRangeStart=timeRangeStart,
            timeRangeEnd=timeRangeEnd
        )

// 业务逻辑层 - 买家订单服务
class BuyerOrderService:
    // 允许的订单状态列表
    const ALLOWED_STATUSES = [
        "",  // 全部
        "PENDING",  // 待确认
        "CONFIRMED",  // 待交易/待支付
        "PAID",  // 待完成
        "COMPLETED",  // 已完成
        "CANCELLED",  // 已取消
        "REJECTED"  // 已拒绝
    ]
    
    // 获取买家订单列表
    classmethod getBuyerOrderList(userId, statusFilter, keyword, timeRangeStart, timeRangeEnd, page):
        // 校验状态参数合法性
        if statusFilter and statusFilter not in cls.ALLOWED_STATUSES:
            throw new IllegalArgumentException("非法的订单状态参数")
        
        // 构建查询对象
        query = Order.query()
        
        // 仅查询当前用户的订单
        query = query.filterBy(buyerId=userId)
        
        // 排除已删除的订单
        query = query.filterBy(deleted=False)
        
        // 按状态筛选
        if statusFilter and statusFilter != "":
            query = query.filterBy(orderStatus=statusFilter)
        
        // 按关键词搜索
        if keyword:
            query = query.join(Product)
            query = query.filter(Product.productName.contains(keyword))
        
        // 按时间范围筛选
        if timeRangeStart:
            query = query.filter(Order.createdAt >= timeRangeStart)
        if timeRangeEnd:
            query = query.filter(Order.createdAt <= timeRangeEnd)
        
        // 默认按创建时间倒序
        query = query.orderBy(Order.createdAt.desc())
        
        // 分页处理
        pagination = PaginationUtil.paginate(query, page=page, perPage=20)
        
        // 获取订单列表
        orders = pagination.items
        
        // 预加载关联数据（商品快照、卖家信息）
        orders = cls.preloadAssociations(orders)
        
        // 为每个订单添加可执行操作标识
        for order in orders:
            order.availableActions = cls.getAvailableActions(order, userId)
        
        // 返回结果
        return {
            orders: orders,
            pagination: pagination
        }
    
    // 预加载关联数据
    classmethod preloadAssociations(orders):
        // 获取所有订单的商品ID和卖家ID
        productIds = [order.productId for order in orders]
        sellerIds = [order.sellerId for order in orders]
        
        // 批量查询商品信息
        products = Product.query().filter(Product.productId.in_(productIds)).all()
        productMap = {product.productId: product for product in products}
        
        // 批量查询卖家信息
        sellers = User.query().filter(User.userId.in_(sellerIds)).all()
        sellerMap = {user.userId: user for user in sellers}
        
        // 关联数据
        for order in orders:
            order.product = productMap.get(order.productId)
            order.sellerRef = sellerMap.get(order.sellerId)
        
        return orders
    
    // 获取订单可执行的操作
    classmethod getAvailableActions(order, userId):
        actions = []
        
        // 只处理当前用户是买家的情况
        if order.buyerId != userId:
            return actions
        
        // 根据订单状态和交易方式判断可用操作
        if order.orderStatus in ["PENDING", "CONFIRMED"]:
            actions.append("cancel")
        
        if order.orderStatus == "CONFIRMED" and order.tradeType == "ONLINE":
            actions.append("pay")
        
        if (order.orderStatus == "PAID" and order.tradeType == "ONLINE") or \
           (order.orderStatus == "CONFIRMED" and order.tradeType == "OFFLINE"):
            actions.append("complete")
        
        return actions

// 数据模型层 - 订单模型
class Order:
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
    property buyerMessage
    property rejectReason
    property createdAt
    property paidAt
    property completedAt
    property deleted
    
    // 关联对象
    property product  // 商品对象
    property sellerRef  // 卖家用户对象
    property availableActions  // 可用操作列表
    
    // 状态显示名称映射
    const STATUS_DISPLAY = {
        "PENDING": "待确认",
        "CONFIRMED": "已确认",
        "PAID": "已支付",
        "COMPLETED": "已完成",
        "CANCELLED": "已取消",
        "REJECTED": "已拒绝"
    }
    
    // 获取状态显示名称
    method getStatusDisplay():
        return this.STATUS_DISPLAY.get(this.orderStatus, this.orderStatus)

// 数据模型层 - 商品模型
class Product:
    property productId
    property productName
    property price
    property coverImage
    property productStatus
    property sellerId
    property deleted

// 数据模型层 - 用户模型
class User:
    property userId
    property username
    property nickname
    property avatar

// 分页工具类
class PaginationUtil:
    // 分页查询
    classmethod paginate(query, page, perPage):
        // 计算总记录数
        total = query.count()
        
        // 计算总页数
        totalPages = ((total - 1) // perPage) + 1 if total > 0 else 0
        
        // 修正页码范围
        if page < 1:
            page = 1
        if page > totalPages and totalPages > 0:
            page = totalPages
        
        // 计算偏移量
        offset = (page - 1) * perPage
        
        // 查询当前页数据
        items = query.offset(offset).limit(perPage).all()
        
        // 返回分页对象
        return {
            items: items,
            page: page,
            perPage: perPage,
            total: total,
            pages: totalPages,
            hasPrev: page > 1,
            hasNext: page < totalPages,
            prevNum: page - 1,
            nextNum: page + 1
        }

// 视图层 - 模板渲染逻辑
class BuyerOrderListView:
    // 渲染订单列表页面
    method render(orders, pagination, currentFilter, keyword, timeRangeStart, timeRangeEnd):
        // 渲染页面头部
        renderPageHeader("我买到的")
        
        // 渲染搜索栏
        renderSearchBar(keyword, currentFilter)
        
        // 渲染状态筛选标签
        renderStatusFilterTabs(currentFilter)
        
        // 判断是否有订单数据
        if orders and len(orders) > 0:
            // 渲染订单列表
            for order in orders:
                renderOrderCard(order)
            
            // 渲染分页控件
            renderPagination(pagination, currentFilter, keyword, timeRangeStart, timeRangeEnd)
        else:
            // 渲染空状态
            renderEmptyState(keyword)
    
    // 渲染订单卡片
    method renderOrderCard(order):
        // 渲染商品图片
        renderProductImage(order.product)
        
        // 渲染订单信息
        renderOrderInfo(order)
        
        // 渲染卖家昵称
        renderSellerInfo(order.sellerRef)
        
        // 渲染订单状态
        renderOrderStatus(order)
        
        // 渲染操作按钮
        renderActionButtons(order)
```
