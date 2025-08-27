# 量子计算控制系统 UI

这是一个基于Vue.js的量子计算控制系统用户界面，包含实时数据显示和参数管理功能。

## 功能特性

### 🎯 四大功能模块
1. **任务执行和提交区** - 量子计算任务管理
2. **实时数据显示** - Sin函数实时波形显示
3. **参数库** - Sin函数参数配置和Python代码生成
4. **操作面板** - 系统控制中心

### 📊 实时数据显示
- 实时显示Sin函数波形图
- 显示当前值、频率、幅度、相位等参数
- 平滑的动画效果和响应式图表

### ⚙️ 参数库功能
- 可调节Sin函数的频率、幅度、初始相位
- 实时参数验证和范围限制
- 自动生成对应的Python后端代码
- 支持参数实时应用

## 文件结构

```
UI/
├── index.html                 # 主页面文件 (Vue.js + Chart.js)
├── sin_data_generator.py      # Python后端服务 (Flask版本)
├── sin_generator_simple.py    # Python数据生成器 (简化版本)
├── requirements.txt           # Python依赖包
└── README.md                  # 说明文档
```

## 快速开始

### 1. 运行前端页面
直接用浏览器打开 `index.html` 文件即可。

### 2. 运行Python后端 (可选)

#### 方法1: 使用Flask服务 (推荐)
```bash
# 安装依赖
pip install -r requirements.txt

# 运行Flask服务
python sin_data_generator.py
```

#### 方法2: 使用简化版本
```bash
# 直接运行，无需额外依赖
python sin_generator_simple.py
```

## 使用说明

### 实时数据显示
1. 点击"实时数据显示"卡片
2. 查看实时Sin函数波形图
3. 观察当前值和参数显示
4. 图表会自动更新，显示最近100个数据点

### 参数库操作
1. 点击"参数库"卡片
2. 调整以下参数：
   - **频率**: 0.1-10 Hz
   - **幅度**: 0.1-5
   - **初始相位**: 0-2π 弧度
3. 点击"应用参数"更新Sin函数
4. 点击"生成后端代码"获取Python代码

### 生成的Python代码特性
- 完整的Sin函数数据生成器类
- 支持参数动态更新
- 包含时间戳和格式化时间
- 提供数据流生成功能
- 包含使用示例和文档

## 技术栈

### 前端
- **Vue.js 3** - 响应式前端框架
- **Chart.js** - 图表库
- **CSS3** - 现代化样式和动画
- **HTML5** - 语义化标记

### 后端
- **Python 3** - 核心语言
- **Flask** - Web框架 (完整版)
- **NumPy** - 数值计算 (Flask版本)
- **内置math库** - 数学计算 (简化版本)

## 浏览器兼容性
- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+

## 开发说明

### 自定义参数范围
在 `index.html` 中修改参数输入范围：
```html
<input 
    type="number" 
    v-model.number="tempParams.frequency"
    step="0.1"
    min="0.1"    <!-- 最小值 -->
    max="10"     <!-- 最大值 -->
>
```

### 修改采样率
在实时数据显示中，采样率默认为60fps。可以在 `updateData` 函数中调整：
```javascript
// 降低采样率示例
setTimeout(() => {
    if (this.showModal && this.currentModule === 'realtime') {
        this.animationId = requestAnimationFrame(updateData);
    }
}, 100); // 100ms = 10fps
```

### 扩展后端功能
在 `sin_data_generator.py` 中添加新的API端点：
```python
@app.route('/api/custom', methods=['POST'])
def custom_function():
    # 自定义功能
    return jsonify({'status': 'success'})
```

## 故障排除

### Q: 图表不显示
A: 检查网络连接，确保Chart.js CDN可以访问

### Q: 参数更新不生效
A: 确保参数值在有效范围内，检查浏览器控制台错误信息

### Q: Python后端无法启动
A: 检查Python版本(需要3.6+)，安装所需依赖包

## 许可证
MIT License

## 贡献
欢迎提交Issue和Pull Request来改进这个项目。
