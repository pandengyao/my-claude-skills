# 反射使用检测指南

## 反射的性能影响

反射操作比直接调用慢 **10-100 倍**，应谨慎使用。

## 检测模式

### 1. reflect 包导入
```go
import "reflect"
```

### 2. 常见反射操作
```go
// 类型获取
reflect.TypeOf(x)
reflect.ValueOf(x)

// 字段访问
v.Field(i)
v.FieldByName("Name")

// 方法调用
v.Method(i).Call(args)
v.MethodByName("Foo").Call(args)

// 类型断言替代
v.Interface().(T)
```

## 搜索关键词

- `reflect.TypeOf`, `reflect.ValueOf`
- `reflect.Kind`, `reflect.Type`
- `.Field(`, `.FieldByName(`
- `.Method(`, `.MethodByName(`
- `.Elem()`, `.Interface()`

## 可接受的使用场景

- JSON/XML 序列化库内部
- ORM 框架内部
- 依赖注入框架
- 测试辅助工具

## 应避免的场景

- 热点路径（高频调用）
- 简单的类型判断（用 type switch）
- 已知类型的操作

## 优化建议

| 场景 | 反射方案 | 优化方案 |
|------|----------|----------|
| 类型判断 | `reflect.TypeOf(x)` | `switch x.(type)` |
| 通用容器 | `interface{}` + 反射 | Go 1.18+ 泛型 |
| 字段复制 | 反射遍历字段 | 代码生成 |
| 方法调用 | `MethodByName` | 接口 + 直接调用 |