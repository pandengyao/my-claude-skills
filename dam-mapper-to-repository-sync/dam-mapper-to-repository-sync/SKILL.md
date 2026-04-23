---
name: dam-mapper-to-repository-sync
description: 针对 dam-whale 项目的数据库表变更需求，自动完成 SQL、PO、PO Example、Mapper、SqlProvider、Convertor、Entity 的同步修改。
---

# mapper-to-repository-sync

## 功能概述

本 Skill 专门为 **dam-whale 项目** 设计，当在 Mapper 类（如 `WarnOrderMapper`）中新增自定义查询方法后，自动同步在对应的 Repository 类（如 `WarnOrderRepository`）和 Gateway 接口（如 `WarnOrderGateway`）中添加对应的方法，确保三层架构的一致性。

## 适用场景

在 Mapper 类中新增了自定义查询方法后，需要在 Repository 层和 Gateway 接口中同步添加对应的方法。

例如：
- 在 `WarnOrderMapper` 中新增 `selectByIdAndShopIdAndCreateTimeAfter` 方法
- 需要在 `WarnOrderGateway` 接口中添加对应方法
- 需要在 `WarnOrderRepository` 实现类中添加对应实现

## 文件映射关系

| Mapper 类 | Gateway 接口 | Repository 实现 |
|-----------|--------------|-----------------|
| `WarnOrderMapper.java` | `WarnOrderGateway.java` | `WarnOrderRepository.java` |
| `XxxMapper.java` | `XxxGateway.java` | `XxxRepository.java` |

## 操作流程

### 1. 定位相关文件

根据 Mapper 类名推断对应的 Gateway 和 Repository：

```
Mapper: WarnOrderMapper
  ↓
Gateway: WarnOrderGateway (位于 domain/aggregate/{module}/gateway/)
  ↓
Repository: WarnOrderRepository (位于 infrastructure/repository/{module}/)
```

### 2. 在 Gateway 接口中添加方法

在 `XxxGateway.java` 中添加对应的方法声明：

```java
// WarnOrderGateway.java
List<WarnOrder> selectByIdAndShopIdAndCreateTimeAfter(Long id, Long shopId, Date createTime);
```

### 3. 在 Repository 实现类中添加方法

在 `XxxRepository.java` 中添加对应实现：

```java
// WarnOrderRepository.java
@Override
public List<WarnOrder> selectByIdAndShopIdAndCreateTimeAfter(Long id, Long shopId, Date createTime) {
    if (id == null || shopId == null || createTime == null) {
        throw new RuntimeException("查询预警单，参数不能为空");
    }
    List<WarnOrderPo> warnOrderPos = warnOrderMapper.selectByIdAndShopIdAndCreateTimeAfter(id, shopId, createTime);
    return warnOrderInfraConvertor.convert2WarnOrders(warnOrderPos);
}
```

注意：
- 参数校验：添加必要的参数校验
- 调用 Mapper 方法
- 使用 Convertor 将 PO 转换为 Entity
- 返回领域模型列表

## 示例

### Mapper 中新增方法

```java
// WarnOrderMapper.java
@Select({
    "select * from tb_warn_order",
    "where id = #{id} and shop_id = #{shopId} and create_time > #{createTime}"
})
@Results({...})
List<WarnOrderPo> selectByIdAndShopIdAndCreateTimeAfter(
    @Param("id") Long id,
    @Param("shopId") Long shopId,
    @Param("createTime") Date createTime
);
```

### Gateway 中添加声明

```java
// WarnOrderGateway.java
List<WarnOrder> selectByIdAndShopIdAndCreateTimeAfter(Long id, Long shopId, Date createTime);
```

### Repository 中添加实现

```java
// WarnOrderRepository.java
@Override
public List<WarnOrder> selectByIdAndShopIdAndCreateTimeAfter(Long id, Long shopId, Date createTime) {
    if (id == null || shopId == null || createTime == null) {
        throw new RuntimeException("查询预警单，参数不能为空");
    }
    List<WarnOrderPo> warnOrderPos = warnOrderMapper.selectByIdAndShopIdAndCreateTimeAfter(id, shopId, createTime);
    return warnOrderInfraConvertor.convert2WarnOrders(warnOrderPos);
}
```

## 代码规范

1. **参数校验**：在 Repository 方法开头进行参数校验，抛出有意义的异常信息
2. **返回类型**：Gateway 接口返回领域模型 `List<Entity>`，而非 PO
3. **转换逻辑**：使用 InfraConvertor 将 PO 转换为 Entity
4. **方法命名**：保持 Mapper、Gateway、Repository 三者方法名一致

## 常见问题

**Q: Mapper 返回单个对象而 Gateway 返回列表怎么办？**
A: 如果 Mapper 返回单个对象，Repository 可以直接转换为 Entity 并包装为列表返回，或者根据业务需求返回单个对象。

**Q: 如何处理分页查询？**
A: 分页查询通常使用 Example 方式实现，Repository 层直接调用 `selectByExample` 方法即可。