---
name: test-gen
description: 自动生成测试用例，匹配项目测试框架。用户请求生成测试或写测试时自动触发。
---

# Test Generator Skill

智能生成测试用例，自动适配项目测试框架。

## 执行流程

1. **检测测试框架**
   ```bash
   # Python
   ls pytest.ini pyproject.toml setup.py

   # JavaScript/TypeScript
   ls jest.config.js vitest.config.ts package.json

   # Go
   ls go.mod
   ```

2. **分析目标代码**
   - 读取函数/类签名
   - 识别输入输出类型
   - 找边界条件和异常情况

3. **生成测试用例**

   ### 测试覆盖维度
   | 类型 | 示例 |
   |------|------|
   | 正常输入 | `test_add_positive_numbers` |
   | 边界值 | `test_add_zero`, `test_add_max_int` |
   | 异常输入 | `test_add_invalid_type` |
   | 空值处理 | `test_add_none_raises` |
   | 集成测试 | `test_api_endpoint` |

4. **框架适配**

   **Python (pytest)**:
   ```python
   import pytest
   from module import function

   def test_function_normal():
       assert function(1, 2) == 3

   def test_function_edge_case():
       with pytest.raises(ValueError):
           function(-1, -1)
   ```

   **JavaScript (Jest/Vitest)**:
   ```javascript
   import { function } from './module'

   describe('function', () => {
     test('normal case', () => {
       expect(function(1, 2)).toBe(3)
     })

     test('edge case', () => {
       expect(() => function(-1, -1)).toThrow()
     })
   })
   ```

   **Go**:
   ```go
   func TestFunction(t *testing.T) {
       tests := []struct{
           name string
           a, b int
           want int
       }{
           {"normal", 1, 2, 3},
           {"zero", 0, 0, 0},
       }
       for _, tt := range tests {
           t.Run(tt.name, func(t *testing.T) {
               if got := function(tt.a, tt.b); got != tt.want {
                   t.Errorf("got %d, want %d", got, tt.want)
               }
           })
       }
   }
   ```

## 注意事项

- 测试文件放在与源文件同目录或 `tests/` 目录
- 遵循项目现有测试命名风格
- 生成后运行测试验证
- 不修改现有测试，只添加新测试