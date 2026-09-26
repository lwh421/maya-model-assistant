"""
演示脚本：创建测试模型并运行质量检测
在Maya中运行此脚本即可看到完整效果
"""

import maya.cmds as cmds
import sys
import os

# 添加脚本路径
script_dir = os.path.dirname(os.path.abspath(__file__))
if script_dir not in sys.path:
    sys.path.append(script_dir)

from model_quality_checker import run_quality_check


def create_demo_model():
    """创建一个带测试问题的演示模型"""
    
    print("🔨 正在创建演示模型...")
    
    # 清理场景
    cmds.file(new=True, force=True)
    
    # 1. 创建一个基础球体（标准拓扑）
    sphere = cmds.polySphere(name='Demo_Sphere', radius=2, subdivisionsAxis=20, subdivisionsHeight=15)
    print(f"   ✅ 创建标准球体: {sphere[0]}")
    
    # 2. 创建一个立方体
    cube = cmds.polyCube(name='Demo_Cube', width=3, height=3, depth=3)
    print(f"   ✅ 创建立方体: {cube[0]}")
    
    # 3. 故意创建一个有问题的平面（低分段，会有N-gon）
    plane = cmds.polyPlane(name='Demo_ProblemPlane', width=5, height=5, subdivisionsX=1, subdivisionsY=1)
    print(f"   ⚠️ 创建有问题的平面（单段，N-gon面）: {plane[0]}")
    
    # 4. 移动模型分开排列
    cmds.move(-4, 0, 0, sphere)
    cmds.move(4, 0, 0, cube)
    cmds.move(0, 0, 4, plane)
    
    # 选中所有模型
    cmds.select([sphere[0], cube[0], plane[0]])
    
    print("\n📦 演示模型创建完成！")
    print("   - Demo_Sphere: 标准球体，20x15细分")
    print("   - Demo_Cube: 标准立方体")
    print("   - Demo_ProblemPlane: 1x1段平面（有N-gon问题）")
    
    return [sphere[0], cube[0], plane[0]]


if __name__ == '__main__':
    # 创建演示模型
    create_demo_model()
    
    print("\n" + "=" * 50)
    
    # 运行质量检测
    run_quality_check()
