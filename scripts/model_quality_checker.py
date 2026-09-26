"""
Maya 模型质量检测脚本
功能：检测选中模型的基础拓扑问题并给出优化建议
作者：lwh421
"""

import maya.cmds as cmds


def get_selected_meshes():
    """获取选中的所有多边形网格物体"""
    selection = cmds.ls(selection=True, long=True)
    if not selection:
        cmds.warning("请先选择要检测的模型！")
        return []
    
    meshes = []
    for node in selection:
        shapes = cmds.listRelatives(node, shapes=True, type='mesh', fullPath=True)
        if shapes:
            meshes.extend(shapes)
    
    if not meshes:
        cmds.warning("选中的物体中没有多边形网格！")
    
    return meshes


def check_poly_count(mesh):
    """检查多边形数量"""
    transforms = cmds.listRelatives(mesh, parent=True, fullPath=True)[0]
    short_name = transforms.split('|')[-1]
    
    vertices = cmds.polyEvaluate(mesh, vertex=True)
    edges = cmds.polyEvaluate(mesh, edge=True)
    faces = cmds.polyEvaluate(mesh, face=True)
    triangles = cmds.polyEvaluate(mesh, triangle=True)
    
    result = {
        'name': short_name,
        'vertices': vertices,
        'edges': edges,
        'faces': faces,
        'triangles': triangles
    }
    
    return result


def check_ngons(mesh):
    """检测大于4边的面（N-gons）"""
    ngon_count = cmds.polySelect(mesh, displayNgon=True)
    return ngon_count


def check_lamina_faces(mesh):
    """检测重叠面"""
    lamina_count = cmds.polySelect(mesh, displayLamina=True)
    return lamina_count


def check_nonmanifold_edges(mesh):
    """检测非流形边"""
    nonmanifold_count = cmds.polySelect(mesh, nonManifold=True)
    return nonmanifold_count


def check_floating_vertices(mesh):
    """检测游离顶点（不连接任何边的顶点）"""
    vertices = cmds.ls(mesh + '.vtx[*]', flatten=True)
    floating = []
    
    for vtx in vertices:
        edges = cmds.polyListComponentConversion(vtx, toEdge=True)
        if not edges or len(cmds.ls(edges, flatten=True)) == 0:
            floating.append(vtx)
    
    return len(floating)


def calculate_tri_ratio(faces, triangles):
    """计算三角面占比"""
    if faces == 0:
        return 0
    return round(triangles / faces * 100, 1)


def generate_suggestions(stats, ngons, lamina, nonmanifold, floating):
    """根据检测结果生成优化建议"""
    suggestions = []
    
    # 面数建议
    if stats['faces'] > 10000:
        suggestions.append(f"⚠️ 面数较高（{stats['faces']}面），如果是游戏模型建议优化")
    
    # N-gon建议
    if ngons > 0:
        suggestions.append(f"⚠️ 发现 {ngons} 个N-gon面（大于4边），建议三角化或合理加线")
    
    # 重叠面建议
    if lamina > 0:
        suggestions.append(f"⚠️ 发现 {lamina} 个重叠面，建议删除多余的面")
    
    # 非流形边建议
    if nonmanifold > 0:
        suggestions.append(f"⚠️ 发现 {nonmanifold} 条非流形边，检查模型拓扑结构")
    
    # 游离顶点建议
    if floating > 0:
        suggestions.append(f"⚠️ 发现 {floating} 个游离顶点，建议清理")
    
    # 健康状态
    if not suggestions:
        suggestions.append("✅ 模型基础拓扑检查通过，状态良好！")
    
    return suggestions


def run_quality_check():
    """运行完整的模型质量检测"""
    
    meshes = get_selected_meshes()
    if not meshes:
        return
    
    print("=" * 50)
    print("📊 Maya 模型质量检测报告")
    print("=" * 50)
    
    all_suggestions = []
    
    for mesh in meshes:
        stats = check_poly_count(mesh)
        ngons = check_ngons(mesh)
        lamina = check_lamina_faces(mesh)
        nonmanifold = check_nonmanifold_edges(mesh)
        floating = check_floating_vertices(mesh)
        tri_ratio = calculate_tri_ratio(stats['faces'], stats['triangles'])
        
        print(f"\n🔹 模型: {stats['name']}")
        print(f"   顶点数: {stats['vertices']}")
        print(f"   边数: {stats['edges']}")
        print(f"   面数: {stats['faces']}")
        print(f"   三角面占比: {tri_ratio}%")
        print(f"   N-gon面: {ngons}")
        print(f"   重叠面: {lamina}")
        print(f"   非流形边: {nonmanifold}")
        print(f"   游离顶点: {floating}")
        
        suggestions = generate_suggestions(stats, ngons, lamina, nonmanifold, floating)
        all_suggestions.extend([(stats['name'], s) for s in suggestions])
    
    print("\n" + "=" * 50)
    print("💡 优化建议:")
    print("=" * 50)
    
    for name, sug in all_suggestions:
        print(f"   [{name}] {sug}")
    
    print("\n" + "=" * 50)
    print("检测完成！")
    print("=" * 50)


# 运行检测
if __name__ == '__main__':
    run_quality_check()
