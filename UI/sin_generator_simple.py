#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sin函数数据生成器 - 简化版本
无需额外依赖，可直接运行
"""

import math
import time
import json
from datetime import datetime

class SinDataGenerator:
    def __init__(self):
        self.frequency = 1.0  # Hz
        self.amplitude = 1.0
        self.phase = 0.0  # 弧度
        self.start_time = time.time()
        
    def get_current_value(self):
        """获取当前时刻的sin函数值"""
        current_time = time.time() - self.start_time
        value = self.amplitude * math.sin(2 * math.pi * self.frequency * current_time + self.phase)
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
    
    def generate_data_stream(self, duration=10, sample_rate=10):
        """生成指定时长的数据流"""
        data_points = []
        total_samples = int(duration * sample_rate)
        
        print(f"开始生成数据流: 时长={duration}秒, 采样率={sample_rate}Hz")
        print(f"参数设置: 频率={self.frequency}Hz, 幅度={self.amplitude}, 相位={self.phase}rad")
        print("-" * 70)
        
        for i in range(total_samples):
            data_point = self.get_data_point()
            data_points.append(data_point)
            
            print(f"[{i+1:3d}/{total_samples}] {data_point['time_str']} | 值: {data_point['value']:8.4f}")
            
            if i < total_samples - 1:  # 最后一次不需要等待
                time.sleep(1.0 / sample_rate)
        
        return data_points
    
    def save_data_to_file(self, data_points, filename=None):
        """保存数据到JSON文件"""
        if filename is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"sin_data_{timestamp}.json"
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data_points, f, indent=2, ensure_ascii=False)
        
        print(f"\n数据已保存到文件: {filename}")
        return filename

def interactive_demo():
    """交互式演示"""
    generator = SinDataGenerator()
    
    print("=" * 70)
    print("Sin函数数据生成器 - 交互式演示")
    print("=" * 70)
    
    while True:
        print("\n请选择操作:")
        print("1. 查看当前参数")
        print("2. 修改参数")
        print("3. 生成实时数据 (10秒)")
        print("4. 生成数据并保存到文件")
        print("5. 获取当前值")
        print("0. 退出")
        
        try:
            choice = input("\n请输入选择 (0-5): ").strip()
            
            if choice == '0':
                print("退出程序。")
                break
                
            elif choice == '1':
                print(f"\n当前参数:")
                print(f"  频率: {generator.frequency} Hz")
                print(f"  幅度: {generator.amplitude}")
                print(f"  相位: {generator.phase} rad")
                
            elif choice == '2':
                print("\n修改参数 (直接回车保持当前值):")
                
                freq_input = input(f"频率 (当前: {generator.frequency} Hz): ")
                if freq_input.strip():
                    generator.frequency = float(freq_input)
                
                amp_input = input(f"幅度 (当前: {generator.amplitude}): ")
                if amp_input.strip():
                    generator.amplitude = float(amp_input)
                
                phase_input = input(f"相位 (当前: {generator.phase} rad): ")
                if phase_input.strip():
                    generator.phase = float(phase_input)
                
                generator.start_time = time.time()  # 重置开始时间
                print("参数更新完成！")
                
            elif choice == '3':
                print("\n开始生成10秒实时数据...")
                generator.generate_data_stream(duration=10, sample_rate=5)
                
            elif choice == '4':
                duration_input = input("生成时长 (秒, 默认10): ")
                duration = float(duration_input) if duration_input.strip() else 10
                
                rate_input = input("采样率 (Hz, 默认10): ")
                sample_rate = float(rate_input) if rate_input.strip() else 10
                
                data_points = generator.generate_data_stream(int(duration), int(sample_rate))
                generator.save_data_to_file(data_points)
                
            elif choice == '5':
                data_point = generator.get_data_point()
                print(f"\n当前时刻数据:")
                print(f"  时间: {data_point['time_str']}")
                print(f"  值: {data_point['value']:.6f}")
                
            else:
                print("无效选择，请重新输入。")
                
        except (ValueError, KeyboardInterrupt) as e:
            if isinstance(e, KeyboardInterrupt):
                print("\n\n用户中断，退出程序。")
                break
            else:
                print(f"输入错误: {e}")

def main():
    """主函数 - 自动演示"""
    print("Sin函数数据生成器启动")
    print("自动演示模式")
    print("=" * 50)
    
    # 创建生成器实例
    generator = SinDataGenerator()
    
    # 演示1: 默认参数
    print("\n[演示1] 默认参数 (频率=1Hz, 幅度=1, 相位=0)")
    data1 = generator.generate_data_stream(duration=5, sample_rate=5)
    
    # 演示2: 修改频率
    print("\n[演示2] 高频率 (频率=2Hz)")
    generator.update_parameters(frequency=2.0)
    data2 = generator.generate_data_stream(duration=5, sample_rate=5)
    
    # 演示3: 修改幅度
    print("\n[演示3] 大幅度 (幅度=2)")
    generator.update_parameters(amplitude=2.0)
    data3 = generator.generate_data_stream(duration=5, sample_rate=5)
    
    # 演示4: 修改相位
    print("\n[演示4] 相位偏移 (相位=π/2)")
    generator.update_parameters(phase=math.pi/2)
    data4 = generator.generate_data_stream(duration=5, sample_rate=5)
    
    print("\n自动演示完成！")
    print("\n要进行交互式演示，请取消注释下面的代码行:")
    print("# interactive_demo()")

if __name__ == "__main__":
    main()
    # 如果要运行交互式演示，请取消下面的注释
    interactive_demo()
