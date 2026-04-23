# 格式
云端path:本地项目所在的绝对路径
## 示例
```
baidu/android-peer-pushedcode-reviewer/example:/Users/zhangsan/Desktop/projects/baidu/android-peer-pushedcode-reviewer/example
```
# 云端path和本地项目所在绝对路径


# 缺省时处理策略
如果没有找到需要的映射关系，要询问该项目所在的绝对路径，并且要提示是绝对路径并给出路径示例，当用户告知路径后要补充到当前文件（project_localpath_mapping.md）下的"云端path和本地项目所在绝对路径"模块下
## 提示模版
当没有映射关系时：
```
我没有当前评审的项目的本地路径，请提供该项目的本地绝对路径
路径示例：
Users/zhangsan/Desktop/projects/baidu/android-peer-pushedcode-reviewer/example
ps：此次提供以后我会更新到记忆文件中下次就不要提供啦
```
当项目本地路径不存在时：
```
您提供的项目路径不存在，请提供该项目真实的本地绝对路径
路径示例：
Users/zhangsan/Desktop/projects/baidu/android-peer-pushedcode-reviewer/example
ps：此次提供以后我会更新到记忆文件中下次就不要提供啦
```