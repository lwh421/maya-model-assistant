"""
调试版检测脚本：输出详细信息，看看问题出在哪
"""

import maya.cmds as cmds


print("=" * 50)
print("🔍 调试检测脚本")
print("=" * 50)

# 获取选中的模型
selection = cmds.ls(selection=True, long=True)
print(f"\n选中的物体: {selection}")

if not selection:
    print("❌ 没有选中任何物体！")
    print("请先选中角色模型再运行")
else:
    meshes = []
    for node in selection:
        shapes = cmds.listRelatives(node, shapes=True, type='mesh', fullPath=True)
        if shapes:
            meshes.extend(shapes)
    
    print(f"\n找到的mesh: {meshes}")
    print(f"mesh数量: {len(meshes)}")
    
    for mesh in meshes:
        transforms = cmds.listRelatives(mesh, parent=True, fullPath=True)[0]
        name = transforms.split('|')[-1]
        
        print(f"\n--- 检测 {name} ---")
        
        # 基础统计
        vertices = cmds.polyEvaluate(mesh, vertex=True)
        edges = cmds.polyEvaluate(mesh, edge=True)
        faces = cmds.polyEvaluate(mesh, face=True)
        triangles = cmds.polyEvaluate(mesh, triangle=True)
        
        print(f"  顶点: {vertices}")
        print(f"  边: {edges}")
        print(f"  面: {faces}")
        print(f"  三角面: {triangles}")
        
        # N-gon检测
        print(f"\n  检测N-gon...")
        try:
            cmds.polySelect(mesh, ngon=True)
            ngon_sel = cmds.ls(selection=True, long=True)
            ngon_count = len(ngon_sel)
            print(f"    N-gon选中元素数: {ngon_count}")
            print(f"    选中的: {ngon_sel[:5]}")
            cmds.select(mesh)
        except Exception as e:
            print(f"    N-gon检测失败: {e}")
        
        # 重叠面检测
        print(f"\n  检测重叠面...")
        try:
            cmds.polySelect(mesh, lamina=True)
            lamina_sel = cmds.ls(selection=True, long=True)
            lamina_count = len(lamina_sel)
            print(f"    重叠面选中元素数: {lamina_count}")
            print(f"    选中的: {lamina_sel[:5]}")
            cmds.select(mesh)
        except Exception as e:
            print(f"    重叠面检测失败: {e}")
        
        # 非流形边检测
        print(f"\n  检测非流形边...")
        try:
            cmds.polySelect(mesh, nonManifoldEdges=True)
            nm_sel = cmds.ls(selection=True, long=True)
            nm_count = len(nm_sel)
            print(f"    非流形边选中元素数: {nm_count}")
            print(f"    选中的: {nm_sel[:5]}")
            cmds.select(mesh)
        except Exception as e:
            print(f"    非流形边检测失败: {e}")

print("\n" + "=" * 50)
print("调试完成")
print("=" * 50)
