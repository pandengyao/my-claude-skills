---
name: go-codereviewer
description: Automated Go code review based on Baidu Go coding standards. Use when reviewing Go code changes in git staging area for compliance with coding standards, providing fix suggestions, automatically applying fixes after confirmation, and submitting code with code review requests to specified reviewers via iCode. Triggers on requests like "review my Go code", "check Go code standards", "review staged files", or when user wants to commit and create code review with automatic standards checking.
---

# Go Code Reviewer

Automated Go code review tool based on Baidu Go Coding Standards v1.3. Performs comprehensive code review on git staging area, provides detailed fix suggestions, applies fixes after confirmation, and facilitates code submission with review requests.

## Core Workflow

### Phase 1: Automated Code Review

1. **Identify Staged Go Files**
   - Run bash command to get staged files: `git diff --cached --name-only --diff-filter=ACM | grep '\.go$'`
   - If no Go files staged, inform user and exit

2. **Review Each File**
   - Read each staged Go file
   - Apply Baidu Go coding standards (see [references/baidu-go-coding-standard.md](references/baidu-go-coding-standard.md))
   - Check for violations across all categories:
     - Naming conventions (Rule001-Rule006)
     - File structure (Rule101-Rule105)
     - Language specifications (Rule201-Rule213)
     - Code style (Rule301-Rule310)
     - Best practices (Advice level rules)

3. **Generate Review Report**
   - For each violation found, document:
     - File path and line number
     - Rule ID and level (Rule/Advice)
     - Violation description
     - Code snippet showing the issue
     - Specific fix suggestion
   - Organize by severity: Rule violations first, then Advice

4. **Present Findings to User**
   - Display comprehensive review report
   - Summarize: X Rule violations, Y Advice suggestions
   - Ask user: "Would you like me to automatically fix these issues?"

### Phase 2: Automatic Fix (After User Confirmation)

1. **Apply Fixes**
   - For each fixable violation:
     - Use Edit tool to apply the fix
     - Document what was changed
   - Some violations may require manual intervention - clearly mark these

2. **Verify Fixes**
   - Re-read modified files to confirm fixes applied correctly
   - Run `go fmt` on modified files if needed
   - Report completion status

3. **Stage Fixed Files**
   - Run: `git add <fixed-files>`
   - Confirm all fixes are staged

### Phase 3: Code Submission and Review Request (After User Confirmation)

#### 百度Git提交规范（Baidu Git Workflow）

**基本提交流程**:

1. **Check Status** - `git status` 查看当前状态
2. **Add Files** - `git add .` (全部文件) 或 `git add <file>` (指定文件)
3. **Commit** - `git commit -m "message"` 提交到本地仓库
4. **Pull with Rebase** - `git pull origin <branch> --rebase` 拉取远程更新
5. **Push for Review** - `git push origin HEAD:refs/for/<branch>` 推送到Gerrit进行评审

**追加提交**: 如需修改评审，使用 `git commit --amend` 追加到原commit

#### Skill执行步骤

1. **Commit Changes**
   - Ask user for commit message (or suggest based on changes)
   - Create commit with standard format:
     ```
     <commit-message>

     Co-Authored-By: Ducc (Baidu Go Code Reviewer) <noreply@baidu.com>
     ```
   - Run: `git commit -m "<message>"`

2. **Pull Remote Updates**
   - Get current branch name
   - Run: `git pull origin <branch-name> --rebase`
   - Handle any conflicts if they occur

3. **Push to Remote (Gerrit)**
   - **IMPORTANT**: 百度使用Gerrit评审系统，必须使用特殊推送格式
   - Run: `git push origin HEAD:refs/for/<branch-name>`
   - This automatically creates code review in iCode
   - Extract change number from push output

4. **Add Reviewers via iCode API**
   - Ask user: "Who should review this code? (Enter reviewer usernames, comma-separated)"
   - Use iCode REST API to add reviewers:
     ```
     POST http://icode.baidu.com/rest/review/api/changes/{changeNumber}/reviewer/{reviewers}/batchadd
     ```
   - Required Headers:
     - X-AUTH-CLIENT-ID: Third-party app client ID
     - X-AUTH-CLIENT-SECRET: Third-party app client secret
     - X-AUTH-USER: Authorized username (commit author)
     - X-AUTH-TOKEN: Authorized user token (base64 encoded)
   - If API credentials not available, provide manual instructions:
     - "Please add reviewers manually at iCode review page"
     - "Review URL: <review-url>"
     - "Suggested reviewers: <reviewers>"

## Review Categories and Key Rules

### Critical Rules (Must Fix - Rule Level)

**Naming (Rule001-006):**
- Use camelCase for variables, constants, functions
- Common abbreviations must be uppercase: HTTP, ID, URL, JSON, etc.
- Error variables must have `err/Err` prefix
- No `this/self` in receivers
- Receiver names must be consistent
- Package names lowercase, no underscores
- No package name prefix on exported types

**File Structure (Rule101-105):**
- Filenames: lowercase, `[a-z0-9_]+.go`
- UTF-8 encoding only
- Max 160 characters per line
- Test data in `testdata/` directory
- Must use `go mod` with go.mod/go.sum

**Language (Rule201-213):**
- Must pass `go vet`
- No bool comparison in if/for (`if ok`, not `if ok == true`)
- No unnecessary `else` - use early returns
- Error always last return parameter
- Must handle returned errors (except defer)
- Wrap errors with `fmt.Errorf` and `%w`
- Context.Context always first parameter
- No copying locks (use pointer for struct with sync.Mutex)
- No pointer receivers for map/func/chan
- No defer in for loops
- Max cyclomatic complexity: 30
- Must specify struct field names

**Style (Rule301-310):**
- Use tabs for indentation
- Exported types must have comments starting with type name
- Group same-type constants/variables
- Package comments start with "Package "
- 1 blank line between functions and type definitions
- Import groups: stdlib, third-party, project (separated by blank lines)
- No dot imports
- Comment underscore imports
- Error strings lowercase, no trailing punctuation

### Recommendations (Advice Level)

- Single file < 2000 lines
- Struct methods in same file
- Package docs in doc.go
- Use pointers for large structs, values for small ones
- Pre-allocate slice capacity when size known
- Max 1 embedded struct
- Function params ≤ 5, returns ≤ 3
- Use `//` comments over `/* */`
- Copyright at file top
- No grouped var/const in functions

## Tool Integration

### Required Tools

1. **Git** - for staging area inspection and commit operations
2. **Go tools** - `go vet`, `go fmt` for validation
3. **iCode CLI** (optional) - for automated review request creation

### Recommended Tools (mention if not present)

- `golangci-lint` - comprehensive linting
- `staticcheck` - advanced static analysis
- `gorgeous` - auto-formatting modified files

## Example Usage

**User request:** "Review my Go code changes"

**Agent actions:**
1. Check staging area → find 3 Go files
2. Review files → find 5 Rule violations, 8 Advice suggestions
3. Present detailed report with fix recommendations
4. After user confirms → apply all fixable changes
5. Stage fixed files
6. After user confirms → commit with message
7. Push to origin
8. Ask for reviewers → create review request

**User request:** "Review and submit for review by zhangsan,lisi"

**Agent actions:**
1-6. Same as above
7. Skip asking for reviewers (already provided)
8. Create review request with zhangsan,lisi as reviewers

## Important Notes

- Always read the full file before suggesting fixes - never propose changes without reading
- Respect `//nolint` comments - skip rules marked for exemption
- Provide specific line numbers and code snippets in violation reports
- Some violations require context - use judgment for Advice level rules
- If unsure about a fix, mark as "requires manual review"
- Always verify fixes were applied correctly before proceeding
- Use batch operations when multiple files need same fix type

## Reference Documentation

- [baidu-go-coding-standard.md](references/baidu-go-coding-standard.md) - Complete Baidu Go Coding Standards v1.3 with detailed rules, examples, and best practices
- [baidu-git-workflow.md](references/baidu-git-workflow.md) - Baidu Git workflow and Gerrit code review process, including commit conventions, push formats, and reviewer management
