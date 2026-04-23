# 代码评审示例

## TypeScript/JavaScript 代码评审

```typescript
// TypeScript 特定问题检查

// ❌ 使用 any 破坏类型安全
function processData(data: any) {
    return data.value;
}

// ✅ 使用明确类型定义
interface DataPayload {
    value: string;
}
function processData(data: DataPayload) {
    return data.value;
}

// ❌ 未处理 async 错误
async function fetchUser(id: string) {
    const response = await fetch(`/api/users/${id}`);
    return response.json();  // 网络失败时会静默失败
}

// ✅ 完整错误处理
async function fetchUser(id: string): Promise<User> {
    try {
        const response = await fetch(`/api/users/${id}`);
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }
        return await response.json();
    } catch (error) {
        console.error('Failed to fetch user:', error);
        throw error;
    }
}

// ❌ 空代码块
if (condition) {
}

// ✅ 反转逻辑或添加注释
if (!condition) {
    return;
}
// 处理主逻辑

// ❌ 错误的命名
const d = new Date();
const uc = userCount;
const fn = (x) => x * 2;

// ✅ 清晰的命名
const createdAt = new Date();
const activeUserCount = 42;
const doubleValue = (value: number) => value * 2;
```

## San.js 代码评审

```typescript
// San.js 特定问题检查

// ❌ 生命周期方法拼写错误
attach() {
    console.log('组件挂载');  // 永远不会执行！
}

// ✅ 正确的生命周期方法名
attached() {
    console.log('组件挂载');
}

// ❌ 直接修改 Props
this.data.set('title', this.props.title);
this.props.user.name = 'new';  // 禁止！破坏单向数据流

// ✅ 通过事件通知父组件
this.fire('update:title', { title: 'new' });
this.fire('userChange', { name: 'new' });

// ❌ 内存泄漏 - 定时器未清理
attached() {
    this.timer = setInterval(() => {
        this.data.set('time', Date.now());
    }, 1000);
}
// 缺少 detached 清理！

// ✅ 在 detached 中清理资源
attached() {
    this.timer = setInterval(() => {
        this.data.set('time', Date.now());
    }, 1000);
}

detached() {
    if (this.timer) {
        clearInterval(this.timer);
        this.timer = null;
    }
}

// ❌ 直接操作 DOM
attached() {
    document.getElementById('myButton').addEventListener('click', this.handleClick);
}

// ✅ 使用 ref
template: `
    <div>
        <button s-ref="myButton" on-click="handleClick">点击</button>
    </div>
`,
attached() {
    const button = this.ref('myButton');
    // 通常不需要手动操作，使用 on-click 即可
}
```
