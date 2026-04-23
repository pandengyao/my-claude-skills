Kotlin编码规范

# 1 源文件规范
## 1.1 文件编码
* 所有源文件必须使用UTF-8进行编码

## 1.2 文件命名
* 所有源文件必须使用`.kt`作为扩展名
* 如一个源码文件仅包含一个顶级类，则该文件应当以这个定级类的类名作为文件名，如包含多个顶级定义，请选择一个能够描述该文件内容的名字作为文件名

## 1.3 特殊字符
### 1.3.1 空格
* 除了换行符之外，ASCII空格（0x20）是唯一合法的空格字符
    * 所有在源代码中（包括字符、字符串以及注释中）出现的其他空格字符都需要转义
    * Tab不可以用于缩进


### 1.3.2 特殊转义字符
* 任何含有特殊意义的转义字符，如：`\b`、`\n`、`\r`、`\t`、`\'`、`\''`、`\\`、`\$`等，不可以使用Unicode进行转义

### 1.3.3 非ASCII字符
* 对于其他的非ASCII字符，建议使用其实际字符，如：`∞`，应尽最大可能保证代码的可读性
* 任何时候，包括所有代码、注释、文档中，都不推荐使用Unicode编码进行转义

|**示例**|**说明**|
|-|-|
|`val unitAbbrev = "μs"`|最佳写法，不使用注释也可以看懂|
|`val unitAbbrev = "\u03bcs" // μs`|不推荐的写法，使用转义字符没有任何意义|
|`val unitAbbrev = "\u03bcs"`|禁止的写法，读者完全无法理解意义|
|`return "\ufeff" + content // byte order mark`|不错的写法，可打印字符使用转义字符，并添加了必要的注释|

### 1.3.4 文件结构
* 一个以`.kt`结尾的文件必须按照以下顺序填充并组织内容：

    1. 版权（Copyright）及许可证（License）头部声明（可选）
    2. 文件级的注解
    3. package声明语句
    4. import语句
    5. 顶级定义

以上各项内容间，使用一个空行分隔

#### 1.3.4.1 版权/许可证
* 建议使用如下格式声明版权信息，并添加作者信息：

```
/*
 * Copyright 2018 Baidu, Inc. All Rights Reserved.
 *
 * zhangsan created at 2018/1/26 19:08
 */
```
#### 2.3.4.2 文件级注解
* 文件级注释请参考Kotlin官方文档（[https://kotlinlang.org/docs/reference/annotations.html#annotation-use-site-targets](https://kotlinlang.org/docs/reference/annotations.html#annotation-use-site-targets)），根据相应的类型来合理使用注解，但必须在版权/许可证之后，package声明语句之前

```
@file:JvmName("Foo")

package org.jetbrains.demo
```
#### 1.3.4.3 Package声明语句
* package（包）声明语句不受列数限制，并且永远不会换行

#### 1.3.4.4 Import语句
* import语句可以用于导入类、方法、属性，它们集合在一个列表之内，应按包名的ASCII顺序排序
* import语句和package语句一样，不受列数限制，不进行折行
* 禁止使用通配符
* 未使用的import语句，应及时删除，但在使用Kotlin Android Extensions时，请注意不要删除IDE误报的import语句

#### 1.3.4.5 顶级（Top-Level）定义
* 一个`.kt`文件中可以定义一个或多个顶级类型、方法、属性、类别名
* 一个源文件中的内容必须针对同一个主题，不相干的声明必须拆分到其各自所属的文件中去，使一个文件尽量变小
* 对文件内容的数量和顺序没有严格的规定，但应最大程度保证文件的可阅读性
* 每个类都应该以业务逻辑顺序排列，而不应仅仅按时间顺序添加在最末尾

#### 1.3.4.6 类成员顺序
* 成员顺序要求，与顶级定义中的顺序要求保持一致

# 2 格式
## 2.1 花括号
### 2.1.1 基本使用
* 单行的`when`语句分支、单行的`if`语句（用于代替三目运算符）不强制要求添加花括号

```
if (string.isEmpty()) return

val value = if (a == b) 0 else 1

when (value) {
    0 -> return
    // …
}
```
* 除以上情况外，任何使用`if`、`when`、`for`、`do`、`while`语句时，对于其有效作用域，都必须使用花括号，即使其中只有一行代码

```
// Good
val myValue = if (condition) {
    0
} else {
    1
}

// Bad
val myValue = if (condition) 
    0
else 
    1
```
### 2.1.2 非空代码块情况
* 在非空代码块中使用花括号时要遵循K&R风格（Kernighan and Ritchie Style）：
    * 左花括号（`{`）前不能换行，在其后换行
    * 在右花括号（`}`）前要有换行
    * 如果右花括号是一句语句，或者一个方法、构造函数、非匿名类的结尾，其后需要换行，其他情况不进行换行，如右花括号后是`else`或者逗号的情况


```
return Runnable {
    while (condition()) {
        foo()
    }
}

return object : MyClass() {
    override fun foo() {
        if (condition()) {
            try {
                something()
            } catch (e: ProblemException) {
                recover()
            }
        } else if (otherCondition()) {
            somethingElse()
        } else {
            lastThing()
        }
    }
}
```
### 2.1.2 空代码块情况
* 空的代码块、构造方法也必须遵循K&R风格

```
try {
    doSomething()
} catch (e: Exception) {} // WRONG!
```
```
try {
    doSomething()
} catch (e: Exception) {
} // Okay
```
## 2.2 缩进
* 每次开始书写一个新的代码块时，使用4个空格进行缩进，在代码块结束时，恢复之前的缩进级别，该级别适用于整个块中的代码和注释

## 2.3 每行一句代码
* 每句语句后都必须使用一个换行，不使用分号

## 2.4 代码折行
* 建议代码每行不超过120字符，如过长须折行书写或进行缩减
* 例外情况：
    * 120字符无法满足的情况，如：注释中一个很长的URL
    * `package`及`import`语句
    * 注释中需要复制粘贴的shell脚本


### 2.4.1 折行规则
* 折行规则的主旨：在更高阶的语法处进行折行，最终目的是为了保证代码可读性：

    1. 非赋值运算符，在运算符前进行折行，同样适用于`.`和`::`两种符号
    2. 赋值运算符，在运算符后进行折行
    3. 方法或构造函数后的左括号，应保持在同一行
    4. `,`（逗号）与其之前的内容保持在一行
    5. Lambda箭头运算符`->`与其之前的参数列表保持在一行

### 2.4.2 连续缩进
* 换行时，第一行（每个连续行）之后的每一行至少缩进8个空格
* 如有多个连续行时，缩进可以超过8个，当且仅当它们以语法并行元素开头时，才使用同样的缩进级别

### 2.4.3 方法折行
* 当一个方法的签名无法写在一行时，请按参数定义进行折行：
    * 每行定义一个参数，同时使用比方法多4个字符的空格进行缩进
    * 右括号和返回类型的定义单独放在一行内，这一行不需要缩进


```
fun <T> Iterable<T>.joinToString(
    separator: CharSequence = ", ",
    prefix: CharSequence = "",
    postfix: CharSequence = ""
): String {
    // …
}
```
#### 2.4.3.1 表达式方法
* 当一个方法仅包含一行代码时，可以将其写为表达式方法，参考：[expression function](https://kotlinlang.org/docs/reference/functions.html#single-expression-functions)
* 表达式方法不应折行，如果需要折行，请改为普通的方法定义方式，使用`return`进行返回

```
override fun toString(): String {
    return "Hey"
}
```
```
override fun toString(): String = "Hey"
```
### 2.4.4 属性
* 属性定义时如超长，请在`=`后进行换行，并使用连续缩进的方式进行缩进

```
private val defaultCharset: Charset? =
        EncodingRegistry.getInstance().getDefaultCharsetForPropertiesFiles(file)
```
* 重写`get`/`set`方法时，应当将其放在单独一行，并附加4个字符的缩进，按照普通方法的格式要求编码

```
var directory: File? = null
    set(value) {
        // …
    }
```
* 只读属性，可以使用减短的语法重写`get`方法，并保持在一行

```
val defaultExtension: String get() = "kt"
```
## 2.5 空格
### 2.5.1 空白换行
* 在一个类中的属性、构造函数、方法、内部类等成员之间，应添加一个空白换行。例外情况：
    * 两个连续的属性之间（没有其他代码）不强制要求添加空行，但建议根据业务逻辑，使用空行进行分组隔离


```
private var groupAVar1 = 0
private var groupAVar2 = 0
private var groupAVar3 = 0

private var groupBVar1 = 1
private var groupBVar2 = 1
private var groupBVar3 = 1
```
    * 枚举常量之间

* 各语句之间，根据业务逻辑建议添加空白换行进行分隔
* 第一个类成员前建议添加一个空白换行
* 允许连续的空行，但不建议这么做

### 2.5.2 空格
1. `if`、`for`、`catch`等关键字与其后的（`(`）之间应当添加一个空格

```
// WRONG!
for(i in 0..1) {
}
```
```
// Okay
for (i in 0..1) {
}
```
2. `else`、`catch`等关键字与其后的（`}`）之间应当添加一个空格

```
// WRONG!
}else {
}
```
```
// Okay
} else {
}
```
3. 左花括号（`{`）前应当添加一个空格.

```
// WRONG!
if (list.isEmpty()){
}
```
```
// Okay
if (list.isEmpty()) {
}
```
4. 双目运算符的左右各添加一个空格.

```
// WRONG!
val two = 1+1
```
```
// Okay
val two = 1 + 1
```
    * 对于类似的运算符同样适用:
        * Lambda表达式箭头运算符（`->`）


```
// WRONG!
ints.map { value->value.toString() }
```
```
// Okay
ints.map { value -> value.toString() }
```
    * 例外情况（不应在其左右添加空格）:
        * 使用双冒号运算符（`::`）引用类成员时


```
// WRONG!
val toString = Any :: toString
```
```
// Okay
val toString = Any::toString
```
        * 点运算符（`.`）

```
// WRONG
it . toString()
```
```
// Okay
it.toString()
```
        * 范围运算符（`..`）

```
// WRONG
for (i in 1 .. 4) print(i)
```
```
// Okay
for (i in 1..4) print(i)
```
5. 当且仅当在类定义（继承、实现）及泛型中使用`where`约束的冒号前（`:`）应当添加一个空格

```
// WRONG!
class Foo: Runnable
```
```
// Okay
class Foo : Runnable
```
```
// WRONG
fun <T: Comparable> max(a: T, b: T)
```
```
// Okay
fun <T : Comparable> max(a: T, b: T)
```
```
// WRONG
fun <T> max(a: T, b: T) where T: Comparable<T>
```
```
// Okay
fun <T> max(a: T, b: T) where T : Comparable<T>
```
6. 逗号（`,`）及冒号（`:`）之后，应当添加一个空格

```
// WRONG!
val oneAndTwo = listOf(1,2)
```
```
// Okay
val oneAndTwo = listOf(1, 2)
```
```
// WRONG!
class Foo :Runnable
```
```
// Okay
class Foo : Runnable
```
7. 行尾双斜杠（`//`）注释的左右各添加至少一个空格

```
// WRONG!
var debugging = false//disabled by default
```
```
// Okay
var debugging = false // disabled by default
```
## 2.6 特殊结构
### 2.6.1 枚举类
* 无函数及文档的常量枚举类，可以定义在一行

```
enum class Answer { YES, NO, MAYBE }
```
* 当常量定义在多行时，不强制要求添加空行，但含有body的定义除外

```
enum class Answer {
    YES,
    NO,

    MAYBE {
        override fun toString() = """¯\_(ツ)_/¯"""
    }
}
```
* 其他情况参照普通类的要求

### 2.6.2 注解
* 含有参数的注解，各占一行

```
@Retention(SOURCE)
@Target(FUNCTION, PROPERTY_SETTER, FIELD)
annotation class Global
```
* 无参数的注解，可以写在一行

```
@JvmField @Volatile
var disposable: Disposable? = null
```
* 如仅有一个无参数的注解，可以将其与其修饰内容的定义放在一行

```
@Volatile var disposable: Disposable? = null

@Test fun selectAll() {
    // …
}
```
### 2.6.3 隐式返回类型及属性类型
* 如果函数的返回值、属性初始化的值可以直观的判断出其类型时，类型声明可以省略，其他情况不可省略类型定义

```
override fun toString(): String = "Hey"
// becomes
override fun toString() = "Hey"
```
```
private val ICON: Icon = IconLoader.getIcon("/icons/kotlin.png")
// becomes
private val ICON = IconLoader.getIcon("/icons/kotlin.png")
```
* 编写类库代码时，`public`接口建议保留显示的类型声明，以便使用者阅读

# 3 命名
* 所有标识符的命名只可以使用ASCII字母及数字，极少数情况下会使用到下划线，符合`\w+`正则
* 除实现备用属性（Backing properties）外，不建议使用特殊前缀或后缀，如：`s_name`、`mName`

## 3.1 包名
* 包名必须使用小写字母，连续单词直接拼接即可，不允许使用下划线

```
// Okay
package com.example.deepspace
// WRONG!
package com.example.deepSpace
// WRONG!
package com.example.deep_space
```
## 3.2 类名
* 类名（包括接口名）必须使用首字母大写的驼峰式命名（PascalCase）
* 类名和接口名建议使用名词或名词短语（例：`Character`、`List`），但接口名有时候可为形容词或形容词短语（例：`Callable`）
* 测试类建议以`Test`作为后缀名

## 3.3 方法名
* 方法名必须使用首字母小写驼峰式命名（camelCase），通常为动词或动词短语（例：`stop`、`handleMessage`）
* 仅在测试方法用于区分逻辑时可以使用下划线，其他情况不允许使用下划线命名

```
@Test fun pop_emptyStack() {
    // …
}
```
## 3.4 常量名
* 常量命名全部大写，使用下划线连接各单词，通常为名词或名词短语
* 常量定义的标准：使用`val`定义，无自定义`get`方法，内容不可变且无其他影响的属性，包括不可变类型、不可变类型的集合，及使用`const`修饰的纯量和字符串

```
const val NUMBER = 5
val NAMES = listOf("Alice", "Bob")
val AGES = mapOf("Alice" to 35, "Bob" to 32)
val COMMA_JOINER = Joiner.on(',') // Joiner is immutable
val EMPTY_ARRAY = arrayOf<SomeMutableType>()
```
* 常量的定义：

    1. 建议使用top-level的形式，直接定义在`.kt`文件中
    2. 纯量和字符串形式的常量，必须使用`const`修饰
    3. 不建议在`object`或`companion object`中定义常量，避免开辟不必要的内存空间

```
// Good
private const val SAMPLE_CONST = 100
class TestClass {
    // Some things
}
// Not Good
class TestClass {
    companion object {
        const val SAMPLE_CONST = 100
    }
}
// Forbidden
class TestClass {
    companion object {
        val SAMPLE_CONST = 100
    }
}
```
## 3.5 非常量名
* 非常量以首字母小写的驼峰式命名（camelCase），适用于实例属性、本地属性和参数名，通常为名词及名词短语

```
val variable = "var"
val nonConstScalar = "non-const"
val mutableCollection: MutableSet<String> = HashSet()
val mutableElements = listOf(mutableInstance)
val mutableValues = mapOf("Alice" to mutableInstance, "Bob" to mutableInstance2)
val logger = Logger.getLogger(MyClass::class.java.name)
val nonEmptyArray = arrayOf("these", "can", "change")
```
### 3.5.1 备用属性（Backing properties）名
* [备用属性](https://kotlinlang.org/docs/reference/properties.html#backing-properties)命名和普通属性的命名规则保持一致，并在最前面添加一个下划线作为前缀

```
private var _table: Map<String, Int>? = null

val table: Map<String, Int>
    get() {
        if (_table == null) {
            _table = HashMap()
        }
        return _table ?: throw AssertionError()
    }
```
## 3.6 类型变量名（用于泛型）
* 两种风格：

    1. 单大写字母，后面可加数字，如：`E`、`T`、`X`、`T2`
    2. 一种类的命名形式，并附加一个大写字母`T`，例：`RequestT`, `FooBarT`

## 3.7 驼峰命名方式定义
* 通常有多种方式将短语组织成驼峰方式，像一些缩写词：IPv6、iOS等。为了统一，必须遵循以下几点规则。
* 将字符全部转换为ASCII字符，并且去掉’等符号。例如，Müller's algorithm被转换为Muellers algorithm
    * 在空格和标点符号处对上一步的结果进行切分，组成一个词组。
    * 推荐：一些已经是驼峰命名的词语，也应该在这个时候被拆分。（例如 AdWords 被拆分为 ad words）。但是- 例如iOS之类的词语，它其实不是一个驼峰形式的词语，而是人们惯例使用的一个词语，因此不用做拆分。
    * 经过上面两步后，先将所有的字母转换为小写，再把每个词语的第一个字母转换为大写。


最后，将所有词语连在一起，形成一个标识符。

注意：词语原来的大小写规则，应该被完全忽略。以下是一些例子：

|原始短语|正确写法|非法写法|
|-|-|-|
|"XML Http Request"|`XmlHttpRequest`|`XMLHTTPRequest`|
|"new customer ID"|`newCustomerId`|`newCustomerID`|
|"inner stopwatch"|`innerStopwatch`|`innerStopWatch`|
|"supports IPv6 on iOS"|`supportsIpv6OnIos`|`supportsIPv6OnIOS`|
|"YouTube importer"|`YouTubeImporter`
`YoutubeImporter`*||

[*]号表示可以接受，但是不建议使用。

* 注意：有些词语在英文中，可以用[-]连接使用，也可以不使用[-]直接使用，例如：`nonempty`和`non-empty`都可以，因此方法名字为`checkNonempty`或者`checkNonEmpty`都是合法的写法

# 4 注释
## 4.1 格式
* 建议使用如下的基本的KDoc形式或单行注释

```
/**
 * A func for other use.
 * 
 * @param aParam The first parameter, Type: String?
 * @param bParam The second parameter, Type: Int
 * @return Boolean The result
 */
fun exportFunc(aParam: String?, bParam: Int) : Boolean {
    return false
}
```
```
/** An especially short bit of KDoc. */
```
* 未实现、未完成的方法、类，如需要提交代码，建议添加`TODO`

```
fun incompleteFunc() {
    // TODO To be finished.
}
```
* public方法、变量、常量（即对外部暴露的内容）建议用doc的形式编写注释，私有内容不做强制要求，方法建议对参数、返回值进行说明，以便使用者参考，尽快理解含义

### 4.1.1 段落
* 每段注释，使用一个带有`*`的前缀空行分隔

### 4.1.2 注释块标签
* 可使用如下标签对相关内容进行标注：`@constructor`、`@receiver`、`@param`、`@property`、`@return`、`@throws`、`@see`，同时必须包含描述
* 当块标签无法放在一行时，其第二行从（`@`）位置起偏移8个空格

# 5 编程实践
## 5.1 安全性
### 5.1.1 `try-catch`的使用
* 对于Java中要求强制加try-catch的场景，编译器不会自动提示，需要我们自己加上，如：`new JSONObject("xxx")，xx.toInt()`等
* 大量不会出现异常的代码段，加入了`try-catch`保护，避免不必要的性能开销
* catch住的Exception应当正确处理，如throw给上层调用，或`printStackTrace`，不应直接忽略
* I/O操作及加锁操作或可能出现内存泄露的场景，必须使用`finally`语句进行处理

### 5.1.2 可空（Nullable）类型作为参数
* 方法里的参数要声明为可空类型，防止由于运行时数据为空或Kotlin与Java代码相互调用产生`IllegalStateException`异常导致Crash

### 5.1.3 类型强制转换`as`的使用
* 建议所有进行类型转换的操作，都使用`as?`，以防止类型不匹配导致的异常问题

```
class MyFragment : Fragment() {
    // Good
    (context as? Activity)?.finish()

    // Not Good
    (context as Activity).finish()
}
```
### 5.1.4 `!!`的使用
* 所有场景，如果不能100%确认某个值的类型及是否可能为空，禁止使用`!!`修饰，例外：使用`TextUtils.isEmpty()`校验字符串后，IDE误报

```
val myValue: String? = getValueFromJavaOrNativeMethod()    // myValue may be null

// Forbidden
val noNullValue: String = myValue!!

// Good
val noNullValue: String = myValue ?: ""

// Good
myValue?.let {
    noNullValue = it
}

// Good
if (!TextUtils.isEmpty(myValue)) {
    noNullValue = myValue
}
```
### 5.1.5 成员变量懒加载
* 尽量不要使用`lateinit`来定义不可空类型的变量，可能会在使用时出现null的情况
* 只读变量可以使用`by lazy { }`实现懒加载，可变变量`var`需要重写其中的方法，不推荐

```
private val lazyImmutableValue: String by lazy {
    "Hello"
}
```
* 可变变量可以使用改写`get`方法的形式实现懒加载

```
private var lazyValue: Fragment? = null
    get() {
        if (field == null) {
            field = Fragment()
        }
        return field
    }
```
## 5.2 可读性
### 5.2.1 模板字符串
* 需要拼接变量的字符串，建议使用模板字符串，不要使用`+`
* 过长的、需要换行的、含有特殊的字符串，建议使用三个引号的模板字符串，不要使用`+`拼接，也可以避免使用转义符号，更容易阅读

```
// Good
    var templateString = "My name is $myName"
    var jsonString = """
        {
            "status": 0,
            "data": {
                "dataList": [{
                    "id": 378,
                    "author": {
                    "id": 192,
                    "userName": "user"
                    }
                }]
            }
        }
    """
```
```
// Not Good
    var plusString = "My Name is " + myName
    var jsonStr = "{\n" +
        "\t\"status\": 0,\n" +
        "\t\"data\": {\n" +
        "\t\t\"dataList\": [{\n" +
        "\t\t\t\"id\": 378,\n" +
        "\t\t\t\"author\": {\n" +
        "\t\t\t\t\"id\": 192,\n" +
        "\t\t\t\t\"userName\": \"user\"\n" +
        "\t\t\t}\n" +
        "\t\t}]\n" +
        "\t}\n" +
        "}"
```
### 5.2.2 闭包（Block）的使用
* 回调状态比较少的情况，建议使用闭包，不建议使用`interface`，以减少代码复杂度
* 闭包嵌套层级不要超过3层，如层数过多，建议将Block单独提出来使用，以增加代码可读性

```
// Bad
fun blockFunc() {
    a { 
        b {
            c {
                // Somethings
            }
        }
    }
}
```
* 闭包的回调参数，如未使用，建议不要使用`_`隐藏，防止后继使用时难以理解代码

```
// Good
fun blockFunc() {
    a { v1, v2 -> {
            // TODO
        } 
    }
}

// Not Good
fun blockFunc() {
    a { _, _ -> {
            // TODO
        } 
    }
}
```
## 5.3 性能
### 5.3.1 纯工具静态方法的使用
* 直接写到`.kt`文件里，即Top-Level Function的形式
* 在类里的`companion object`中定义，会有额外开销，如不得不在伴生对象中实现静态方法，请添加`@JvmStatic`注解
* 禁止在`object`里定义，避免额外创建单例

```
// Good	
// SimpleClass.kt
fun myUtilMethod() {
    // Some things
}

// Not Good
// SimpleClass.kt 
class SimpleClass {
    companion object {
    fun myUtilMethod() {
    }
    }
}

// Forbidden
// SimpleClass.kt 
object SimpleClass {
    fun myUtilMethod() {
    }
}
```
### 5.3.2 容器的添加操作
* Kotlin容器如`list`、`set`、`map`等，定义初始化元素时不要直接声明，应一个一个添加，否则会有性能损耗

```
// Not Good
	val list = listOf("a", "b")
```