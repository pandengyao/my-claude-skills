# 百度Git提交规范

本文档详细说明百度内部使用的Git提交规范和Gerrit代码评审流程。

## 基本提交用法

### 第一步：查看状态

使用 `git status` 查看当前修改状态。

```bash
git status
```

红色字体显示的是已修改但未暂存的文件。

### 第二步：添加文件到暂存区

**选项A - 添加所有修改**:
```bash
git add .
```
将所有修改的文件添加到本地git缓存区。

**选项B - 添加指定文件**:
```bash
git add <filename>
```
只添加指定文件到本地git缓存区。

### 第三步：提交到本地仓库

```bash
git commit -m "提交说明"
```

推送修改到本地git库中。**推荐本地提交一个commit**。

#### 追加提交（修改评审）

如果需要对已提交的评审进行修改，使用 `git commit --amend` 进行追加：

```bash
git commit --amend
```

这样会在原来的commit中进行信息追加，而不是创建新的commit。

**重要**: 修改评审时使用 `--amend` 可以保持同一个Change-Id，避免创建多个评审。

### 第四步：拉取远程更新

```bash
git pull <远程主机名> <远程分支名> --rebase
```

取回远程主机某个分支的更新，再与本地的指定分支合并。

**示例**:
```bash
git pull origin master --rebase
```

**为什么使用 --rebase**:
- 保持线性的提交历史
- 避免不必要的merge commit
- 与百度Gerrit评审流程配合更好

### 第五步：推送到远程（Gerrit评审）

**百度特有规范 - 推送到Gerrit进行代码评审**:

```bash
git push <远程主机名> HEAD:refs/for/<远程分支名>
```

**示例**:
```bash
git push origin HEAD:refs/for/master
```

**重要说明**:
- `HEAD:refs/for/master` 是Gerrit的特殊格式
- 这会自动在iCode平台创建代码评审请求
- 不要使用普通的 `git push origin master`，那样会直接推送代码而绕过评审

## Gerrit工作流说明

### 什么是Gerrit？

Gerrit是一个基于Git的代码评审系统，百度内部使用它来进行代码评审。

### Gerrit推送格式

```bash
git push origin HEAD:refs/for/<target-branch>
```

- `HEAD` - 当前本地分支的最新提交
- `refs/for/` - Gerrit的魔法引用，表示提交评审
- `<target-branch>` - 目标分支（如master、develop等）

### 推送成功后的输出

推送成功后，Gerrit会返回评审链接：

```
remote: SUCCESS
remote:
remote:   http://icode.baidu.com/myreview/changes/c/baidu/project/+/119822197 提交说明 [NEW]
remote:
```

其中 `119822197` 是Change Number（评审号），可用于后续API操作。

## 添加评审人

### 方法1：推送时指定（不推荐）

```bash
git push origin HEAD:refs/for/master%r=username1,r=username2
```

**限制**: 只能在首次推送时指定，修改评审时无法使用。

### 方法2：iCode网页手动添加

访问评审链接，在页面上添加评审人。

### 方法3：iCode REST API（推荐）

使用API批量添加评审人：

**接口**:
```
POST http://icode.baidu.com/rest/review/api/changes/{changeNumber}/reviewer/{reviewers}/batchadd
```

**参数**:
- `changeNumber`: 评审号（如119822197）
- `reviewers`: 评审人用户名，多个用逗号分隔（如zhangsan01,lisi02）

**Headers**:
```
X-AUTH-CLIENT-ID: <client-id>
X-AUTH-CLIENT-SECRET: <client-secret>
X-AUTH-USER: <username>
X-AUTH-TOKEN: <base64-encoded-token>
```

**示例**:
```bash
curl -X POST \
  -H "X-AUTH-CLIENT-ID: your-client-id" \
  -H "X-AUTH-CLIENT-SECRET: your-client-secret" \
  -H "X-AUTH-USER: zhangsan" \
  -H "X-AUTH-TOKEN: NmU3OTNlM2EyYWFkMDhhNmI1MDNkYWVhMTQwNTYyMDE2MzRiZTc0ZA==" \
  "http://icode.baidu.com/rest/review/api/changes/119822197/reviewer/yangmin17/batchadd"
```

**响应示例**:
```json
{
    "status": "OK",
    "message": "操作成功！",
    "data": null
}
```

## 完整工作流示例

### 场景1：提交新代码进行评审

```bash
# 1. 查看修改
git status

# 2. 添加文件
git add .

# 3. 提交到本地
git commit -m "2023-15260 实现新功能"

# 4. 拉取最新代码
git pull origin master --rebase

# 5. 推送到Gerrit评审
git push origin HEAD:refs/for/master

# 6. 添加评审人（通过API或网页）
```

### 场景2：修改评审内容

```bash
# 1. 修改代码
# ... edit files ...

# 2. 添加文件
git add .

# 3. 追加到原commit（重要！）
git commit --amend

# 4. 拉取最新代码
git pull origin master --rebase

# 5. 推送更新到同一评审
git push origin HEAD:refs/for/master
```

### 场景3：处理冲突

```bash
# 拉取时发生冲突
git pull origin master --rebase

# 手动解决冲突后
git add <resolved-files>
git rebase --continue

# 推送到评审
git push origin HEAD:refs/for/master
```

## 常见问题

### Q1: 为什么要使用 refs/for/master？

A: `refs/for/` 是Gerrit的特殊前缀，表示提交到评审系统而不是直接推送到分支。这是百度代码评审流程的必要步骤。

### Q2: 修改评审时为什么要用 --amend？

A: 使用 `--amend` 可以保持同一个Change-Id，让修改出现在同一个评审中，而不是创建新的评审。

### Q3: 如何取消一个评审？

A: 在iCode网页上，点击评审的 "Abandon" 按钮即可取消评审。

### Q4: 评审通过后如何合入代码？

A: 评审通过后，有Submit权限的人在iCode页面点击 "Submit" 按钮，代码会自动合入目标分支。

### Q5: 推送失败提示 "no new changes" 怎么办？

A: 这通常表示本地commit已经推送过了。如果要更新评审，需要先修改代码并使用 `git commit --amend`，然后再推送。

## 最佳实践

1. **本地只保留一个commit**: 使用 `git commit --amend` 修改评审，避免多个commit
2. **及时rebase**: 推送前使用 `git pull --rebase` 保持代码最新
3. **清晰的commit message**: 包含ticket号、简短描述
4. **小步提交**: 每个评审只做一件事，便于review
5. **响应评审意见**: 及时修改并amend推送

## 参考链接

- iCode平台: http://icode.baidu.com/
- Gerrit文档: https://gerrit-review.googlesource.com/Documentation/
- 第三方应用申请: https://ku.baidu-int.com/knowledge/HFVrC7hq1Q/pKzJfZczuc/ze1eJcxs1b/iJSAy8bmB-mCOV
