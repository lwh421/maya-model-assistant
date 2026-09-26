"""
UV质量检测脚本
功能：检测模型UV展开的常见问题
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
    
    return meshes


def check_uv_count(mesh):
    """统计UV数量"""
    transforms = cmds.listRelatives(mesh, parent=True, fullPath=True)[0]
    short_name = transforms.split('|')[-1]
    
    uv_count = cmds.polyEvaluate(mesh, uv=True)
    shell_count = cmds.polyEvaluate(mesh, uvShell=True)
    
    return {
        'name': short_name,
        'uv_count': uv_count,
        'uv_shells': shell_count
    }


def check_uv_bounds(mesh):
    """检测UV是否超出0-1范围"""
    uvs = cmds.polyListComponentConversion(mesh + '.map[*]', toUV=True)
    if not uvs:
        return {'out_of_range': 0, 'min_u': 0, 'max_u': 0, 'min_v': 0, 'max_v': 0}
    
    uvs = cmds.ls(uvs, flatten=True)
    
    min_u = 999
    max_u = -999
    min_v = 999
    max_v = -999
    out_of_range = 0
    
    for uv in uvs:
        pos = cmds.polyEditUV(uv, query=True)
        u, v = pos[0], pos[1]
        
        if u < min_u: min_u = u
        if u > max_u: max_u = u
        if v < min_v: min_v = v
        if v > max_v: max_v = v
        
        if u < 0 or u > 1 or v < 0 or v > 1:
            out_of_range += 1
    
    return {
        'out_of_range': out_of_range,
        'min_u': round(min_u, 3),
        'max_u': round(max_u, 3),
        'min_v': round(min_v, 3),
        'max_v': round(max_v, 3)
    }


def check_uv_overlap(mesh):
    """检测UV重叠（简化版：检测UV壳数量和面数比例）"""
    face_count = cmds.polyEvaluate(mesh, face=True)
    shell_count = cmds.polyEvaluate(mesh, uvShell=True)
    
    if face_count == 0:
        return {'possible_overlap': False, 'note': ''}
    
    # 如果UV壳数量远小于面数，可能存在重叠
    ratio = shell_count / face_count
    
    # 经验值：正常展开的UV，壳数应该和面数有合理比例
    # 如果壳数 < 面数的10%，可能有重叠
    if ratio < 0.1 and face_count > 10:
        return {
            'possible_overlap': True,
            'note': f'UV壳数({shell_count})远少于面数({face_count})，可能存在UV重叠'
        }
    
    return {'possible_overlap': False, 'note': ''}


def check_uv_stretch(mesh):
    """检测UV拉伸（简化版：比较UV面积和模型表面积比例）"""
    try:
        # 获取模型表面积
        mesh_area = cmds.polyEvaluate(mesh, area=True)
        
        # 获取UV总面积
        uv_area = 0
        faces = cmds.ls(mesh + '.f[*]', flatten=True)
        
        for face in faces:
            uvs = cmds.polyListComponentConversion(face, toUV=True)
            if uvs:
                uvs = cmds.ls(uvs, flatten=True)
                if len(uvs) >= 3:
                    # 简化：计算UV三角形面积
                    u_positions = []
                    for uv in uvs[:3]:
                        pos = cmds.polyEditUV(uv, query=True)
                        u_positions.append(pos)
                    
                    # 三角形面积公式
                    if len(u_positions) == 3:
                        u1, v1 = u_positions[0]
                        u2, v2 = u_positions[1]
                        u3, v3 = u_positions[2]
                        area = abs((u1*(v2-v3) + u2*(v3-v1) + u3*(v1-v2)) / 2.0)
                        uv_area += area
        
        if mesh_area == 0:
            return {'stretch_ratio': 1.0, 'warning': False}
        
        # 拉伸比例：UV面积 / 模型面积
        # 正常比例应该在合理范围内
        ratio = uv_area / (mesh_area / 100)  # 归一化
        
        if ratio < 0.01 or ratio > 100:
            return {
                'stretch_ratio': round(ratio, 2),
                'warning': True,
                'note': 'UV面积与模型表面积比例异常，可能存在拉伸'
            }
        
        return {'stretch_ratio': round(ratio, 2), 'warning': False, 'note': ''}
        
    except:
        return {'stretch_ratio': -1, 'warning': False, 'note': '计算失败'}


def generate_uv_suggestions(uv_stats, bounds, overlap, stretch):
    """生成UV优化建议"""
    suggestions = []
    
    # UV边界问题
    if bounds['out_of_range'] > 0:
        suggestions.append(f"⚠️ {bounds['out_of_range']}个UV点超出0-1范围（U: {bounds['min_u']}~{bounds['max_u']}, V: {bounds['min_v']}~{bounds['max_v']}）")
    
    # UV重叠
    if overlap['possible_overlap']:
        suggestions.append(f"⚠️ {overlap['note']}")
    
    # UV拉伸
    if stretch['warning']:
        suggestions.append(f"⚠️ {stretch['note']}")
    
    # UV壳数量太少
    if uv_stats['uv_shells'] <= 1 and uv_stats['uv_count'] > 10:
        suggestions.append("⚠️ UV壳数量过少，可能需要拆分UV岛")
    
    if not suggestions:
        suggestions.append("✅ UV基础检查通过，状态良好！")
    
    return suggestions


def run_uv_check():
    """运行完整的UV质量检测"""
    
    meshes = get_selected_meshes()
    if not meshes:
        return
    
    print("=" * 50)
    print("🎨 Maya UV 质量检测报告")
    print("=" * 50)
    
    all_suggestions = []
    
    for mesh in meshes:
        uv_stats = check_uv_count(mesh)
        bounds = check_uv_bounds(mesh)
        overlap = check_uv_overlap(mesh)
        stretch = check_uv_stretch(mesh)
        
        print(f"\n🔹 模型: {uv_stats['name']}")
        print(f"   UV点数量: {uv_stats['uv_count']}")
        print(f"   UV壳数量: {uv_stats['uv_shells']}")
        print(f"   UV范围: U({bounds['min_u']} ~ {bounds['max_u']}), V({bounds['min_v']} ~ {bounds['max_v']})")
        print(f"   超出0-1范围UV点: {bounds['out_of_range']}")
        print(f"   UV拉伸指数: {stretch['stretch_ratio']}")
        
        suggestions = generate_uv_suggestions(uv_stats, bounds, overlap, stretch)
        all_suggestions.extend([(uv_stats['name'], s) for s in suggestions])
    
    print("\n" + "=" * 50)
    print("💡 UV优化建议:")
    print("=" * 50)
    
    for name, sug in all_suggestions:
        print(f"   [{name}] {sug}")
    
    print("\n" + "=" * 50)
    print("UV检测完成！")
    print("=" * 50)


if __name__ == '__main__':
    run_uv_check()
