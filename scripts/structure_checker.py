"""
角色模型结构合理性检测
检测：面片问题、左右不对称、比例失调、位置错误
"""

import maya.cmds as cmds


def get_selected_meshes():
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


def get_bbox_size(mesh):
    """获取模型包围盒尺寸"""
    bb = cmds.exactWorldBoundingBox(mesh)
    width = bb[3] - bb[0]   # X方向
    height = bb[4] - bb[1]  # Y方向
    depth = bb[5] - bb[2]   # Z方向
    center = [(bb[0]+bb[3])/2, (bb[1]+bb[4])/2, (bb[2]+bb[5])/2]
    return {'width': width, 'height': height, 'depth': depth, 'center': center}


def check_thin_parts(mesh):
    """检测是否是太薄的面片（厚度远小于其他两个方向）"""
    size = get_bbox_size(mesh)
    dims = sorted([size['width'], size['height'], size['depth']])
    
    # 最小维度 / 中间维度 < 0.2，就是太薄了
    if dims[0] < 0.2 * dims[1] and dims[1] > 0.3:
        return True, dims[0]
    return False, 0


def check_symmetry(meshes):
    """检测左右部件是否对称"""
    # 找名字带L和R的对应部件
    left_parts = {}
    right_parts = {}
    
    for mesh in meshes:
        transforms = cmds.listRelatives(mesh, parent=True, fullPath=True)[0]
        name = transforms.split('|')[-1]
        
        if '_L' in name:
            base_name = name.replace('_L', '')
            left_parts[base_name] = mesh
        elif '_R' in name:
            base_name = name.replace('_R', '')
            right_parts[base_name] = mesh
    
    asymmetry = []
    for base_name in left_parts:
        if base_name in right_parts:
            left_mesh = left_parts[base_name]
            right_mesh = right_parts[base_name]
            
            left_size = get_bbox_size(left_mesh)
            right_size = get_bbox_size(right_mesh)
            
            left_vol = left_size['width'] * left_size['height'] * left_size['depth']
            right_vol = right_size['width'] * right_size['height'] * right_size['depth']
            
            if left_vol > 0:
                ratio = right_vol / left_vol
                # 体积差超过30%就算不对称
                if ratio < 0.7 or ratio > 1.3:
                    asymmetry.append({
                        'part': base_name,
                        'left_vol': round(left_vol, 2),
                        'right_vol': round(right_vol, 2),
                        'ratio': round(ratio, 2)
                    })
    
    return asymmetry


def check_proportions(meshes):
    """检测头身比等基本比例"""
    head_height = 0
    body_height = 0
    
    for mesh in meshes:
        transforms = cmds.listRelatives(mesh, parent=True, fullPath=True)[0]
        name = transforms.split('|')[-1]
        size = get_bbox_size(mesh)
        
        if 'Head' in name:
            head_height = size['height']
        elif 'Body' in name:
            body_height = size['height']
    
    issues = []
    
    # 头身比检测（Q版大概是1:1到1:2之间）
    if head_height > 0 and body_height > 0:
        ratio = head_height / body_height
        if ratio < 0.3:
            issues.append(f"头身比异常：头太小（头:{head_height:.2f} / 身体:{body_height:.2f} = {ratio:.2f}）")
        elif ratio > 3:
            issues.append(f"头身比异常：头太大（头:{head_height:.2f} / 身体:{body_height:.2f} = {ratio:.2f}）")
    
    return issues


def run_structure_check():
    """运行完整结构检测"""
    meshes = get_selected_meshes()
    if not meshes:
        return
    
    print("=" * 60)
    print("🔍 角色模型结构合理性检测")
    print("=" * 60)
    
    structure_issues = []
    
    # 1. 面片检测
    print("\n1️⃣  厚度检测（是否有面片问题）:")
    for mesh in meshes:
        transforms = cmds.listRelatives(mesh, parent=True, fullPath=True)[0]
        name = transforms.split('|')[-1]
        
        is_thin, thickness = check_thin_parts(mesh)
        size = get_bbox_size(mesh)
        
        print(f"   {name}: 宽={size['width']:.2f}, 高={size['height']:.2f}, 厚={size['depth']:.2f}")
        
        if is_thin:
            print(f"      🔴 警告：太薄了，像面片！厚度只有{thickness:.2f}")
            structure_issues.append({
                'type': 'thin',
                'mesh': mesh,
                'name': name,
                'desc': f'{name} 是面片（厚度{thickness:.2f}），不是实体',
                'fix': f'把{name}替换成圆柱体/立方体实体'
            })
    
    # 2. 对称检测
    print("\n2️⃣  左右对称性检测:")
    asymmetry = check_symmetry(meshes)
    if not asymmetry:
        print("   ✅ 左右对称良好")
    else:
        for item in asymmetry:
            print(f"   🔴 {item['part']} 不对称：左侧体积{item['left_vol']} / 右侧体积{item['right_vol']}（比例{item['ratio']}）")
            structure_issues.append({
                'type': 'asymmetry',
                'name': item['part'],
                'desc': f'{item["part"]} 左右不对称',
                'fix': f'调整{item["part"]}右侧，和左侧匹配'
            })
    
    # 3. 比例检测
    print("\n3️⃣  头身比例检测:")
    prop_issues = check_proportions(meshes)
    if not prop_issues:
        print("   ✅ 头身比例正常")
    else:
        for iss in prop_issues:
            print(f"   🟡 {iss}")
            structure_issues.append({
                'type': 'proportion',
                'desc': iss,
                'fix': '调整头部和身体比例'
            })
    
    # 总结
    print("\n" + "=" * 60)
    print(f"📊 共发现 {len(structure_issues)} 个结构问题")
    print("=" * 60)
    for i, iss in enumerate(structure_issues):
        print(f"   {i+1}. {iss['desc']}")
        print(f"      → 建议: {iss['fix']}")
    print("=" * 60)


# 运行检测
run_structure_check()
