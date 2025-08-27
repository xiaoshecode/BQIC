#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sin函数数据生成器
用于量子计算控制系统的实时数据模拟
"""

import numpy as np
import time
import json
from datetime import datetime
import threading
import queue
from flask import Flask, jsonify, request
from flask_cors import CORS

class SinDataGenerator:
    def __init__(self):
        self.frequency = 1.0  # Hz
        self.amplitude = 1.0
        self.phase = 0.0  # 弧度
        self.start_time = time.time()
        self.is_running = False
        self.data_queue = queue.Queue(maxsize=1000)
        
    def get_current_value(self):
        """获取当前时刻的sin函数值"""
        current_time = time.time() - self.start_time
        value = self.amplitude * np.sin(2 * np.pi * self.frequency * current_time + self.phase)
        return value
    
    def get_data_point(self):
        """获取包含时间戳的数据点"""
        timestamp = time.time()
        value = self.get_current_value()
        return {
            'timestamp': timestamp,
            'time_str': datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S.%f')[:-3],
            'value': value,
            'parameters': {
                'frequency': self.frequency,
                'amplitude': self.amplitude,
                'phase': self.phase
            }
        }
    
    def update_parameters(self, frequency=None, amplitude=None, phase=None):
        """更新参数"""
        if frequency is not None:
            self.frequency = float(frequency)
        if amplitude is not None:
            self.amplitude = float(amplitude)
        if phase is not None:
            self.phase = float(phase)
        
        # 重置开始时间
        self.start_time = time.time()
        print(f"参数已更新: 频率={self.frequency}Hz, 幅度={self.amplitude}, 相位={self.phase}rad")
    
    def start_data_generation(self, sample_rate=10):
        """开始实时数据生成"""
        self.is_running = True
        
        def generate_data():
            while self.is_running:
                try:
                    data_point = self.get_data_point()
                    if not self.data_queue.full():
                        self.data_queue.put(data_point)
                    time.sleep(1.0 / sample_rate)
                except Exception as e:
                    print(f"数据生成错误: {e}")
                    break
        
        self.generation_thread = threading.Thread(target=generate_data)
        self.generation_thread.daemon = True
        self.generation_thread.start()
        print("实时数据生成已启动")
    
    def stop_data_generation(self):
        """停止数据生成"""
        self.is_running = False
        print("实时数据生成已停止")
    
    def get_latest_data(self, count=1):
        """获取最新的数据点"""
        data_points = []
        for _ in range(min(count, self.data_queue.qsize())):
            try:
                data_points.append(self.data_queue.get_nowait())
            except queue.Empty:
                break
        return data_points

# 创建全局生成器实例
generator = SinDataGenerator()

# 创建Flask应用
app = Flask(__name__)
CORS(app)  # 允许跨域请求

@app.route('/api/start', methods=['POST'])
def start_generation():
    """启动数据生成"""
    try:
        sample_rate = request.json.get('sample_rate', 10) if request.json else 10
        generator.start_data_generation(sample_rate)
        return jsonify({'status': 'success', 'message': '数据生成已启动'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/stop', methods=['POST'])
def stop_generation():
    """停止数据生成"""
    try:
        generator.stop_data_generation()
        return jsonify({'status': 'success', 'message': '数据生成已停止'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/parameters', methods=['GET', 'POST'])
def handle_parameters():
    """获取或更新参数"""
    if request.method == 'GET':
        return jsonify({
            'frequency': generator.frequency,
            'amplitude': generator.amplitude,
            'phase': generator.phase
        })
    
    elif request.method == 'POST':
        try:
            data = request.json
            generator.update_parameters(
                frequency=data.get('frequency'),
                amplitude=data.get('amplitude'),
                phase=data.get('phase')
            )
            return jsonify({'status': 'success', 'message': '参数已更新'})
        except Exception as e:
            return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/data', methods=['GET'])
def get_data():
    """获取实时数据"""
    try:
        count = int(request.args.get('count', 1))
        data_points = generator.get_latest_data(count)
        return jsonify({
            'status': 'success',
            'data': data_points,
            'count': len(data_points)
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/current', methods=['GET'])
def get_current_value():
    """获取当前值"""
    try:
        current_data = generator.get_data_point()
        return jsonify({
            'status': 'success',
            'data': current_data
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/status', methods=['GET'])
def get_status():
    """获取系统状态"""
    return jsonify({
        'is_running': generator.is_running,
        'queue_size': generator.data_queue.qsize(),
        'parameters': {
            'frequency': generator.frequency,
            'amplitude': generator.amplitude,
            'phase': generator.phase
        }
    })

def main():
    """主函数"""
    print("Sin函数数据生成器服务启动")
    print("API接口:")
    print("  POST /api/start - 启动数据生成")
    print("  POST /api/stop - 停止数据生成")
    print("  GET/POST /api/parameters - 获取/更新参数")
    print("  GET /api/data - 获取实时数据")
    print("  GET /api/current - 获取当前值")
    print("  GET /api/status - 获取系统状态")
    print("-" * 50)
    
    # 启动数据生成
    generator.start_data_generation()
    
    # 启动Flask服务
    app.run(host='0.0.0.0', port=5000, debug=True)

if __name__ == "__main__":
    main()
