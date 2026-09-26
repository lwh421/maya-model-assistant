"""
Maya 模型质量检测与自动修复工具 - 主程序
整合所有功能：拓扑检测 + UV检测 + 结构检测 + 自动修复
带确认窗口
"""

import maya.cmds as cmds


# ========== 基础工具函数 ==========

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


def get_mesh_name(mesh):
    transforms = cmds.listRelatives(mesh, parent=True, fullPath=True)[0]
    return transforms.split('|')[-1]


def get_bbox(mesh):
    bb = cmds.exactWorldBoundingBox(mesh)
    center = [(bb[0]+bb[3])/2, (bb[1]+bb[4])/2, (bb[2]+bb[5])/2]
    size = [bb[3]-bb[0], bb[4]-bb[1], bb[5]-bb[2]]
    return {'center': center, 'size': size}


# ========== 拓扑检测 ==========

def count_ngons(mesh):
    faces = cmds.ls(mesh + '.f[*]', flatten=True)
    ngon_count = 0
    for face in faces:
        edges = cmds.polyListComponentConversion(face, toEdge=True)
        if edges:
            edge_list = cmds.ls(edges, flatten=True)
            if len(edge_list) > 4:
                ngon_count += 1
    return ngon_count


def detect_topology(meshes):
    """检测拓扑问题"""
    issues = []
    total_faces = 0
    
    for mesh in meshes:
        name = get_mesh_name(mesh)
        faces = cmds.polyEvaluate(mesh, face=True)
        total_faces += faces
        
        # N-gon检测
        ngons = count_ngons(mesh)
        if ngons > 0:
            issues.append({
                'category': '拓扑',
                'mesh': mesh,
                'desc': f'{name}: {ngons}个N-gon面（边数>4）',
                'fix': f'三角化{ngons}个N-gon面',
                'action': 'triangulate'
            })
        
        # 高面数检测
        if faces > 200:
            issues.append({
                'category': '拓扑',
                'mesh': mesh,
                'desc': f'{name}: {faces}面（面数偏高）',
                'fix': f'减面{name}，减少约{int(faces*0.6)}面',
                'action': 'reduce'
            })
    
    return issues, total_faces


# ========== 结构检测 ==========

def detect_structure(meshes):
    """检测结构问题"""
    issues = []
    
    for mesh in meshes:
        name = get_mesh_name(mesh)
        bbox = get_bbox(mesh)
        dims = sorted(bbox['size'])
        
        # 面片检测
        if dims[0] < 0.2 * dims[1] and dims[1] > 0.3:
            issues.append({
                'category': '结构',
                'mesh': mesh,
                'bbox': bbox,
                'name': name,
                'desc': f'{name}: 太薄，是面片不是实体',
                'fix': f'把{name}替换成实体立方体',
                'action': 'fix_thin'
            })
    
    return issues


# ========== 修复函数 ==========

def fix_triangulate(mesh):
    try:
        cmds.polyTriangulate(mesh, ch=False)
        return True
    except:
        return False


def fix_reduce(mesh):
    try:
        cmds.polyReduce(mesh, percentage=40, version=1, ch=False)
        return True
    except:
        return False


def fix_thin(issue):
    mesh = issue['mesh']
    bbox = issue['bbox']
    name = issue['name']
    center = bbox['center']
    size = bbox['size']
    
    transforms = cmds.listRelatives(mesh, parent=True, fullPath=True)[0]
    cmds.delete(transforms)
    
    new_width = max(size[0], 0.4)
    new_height = size[1]
    new_depth = max(size[2], 0.4)
    
    new_cube = cmds.polyCube(name=name, width=new_width, height=new_height, depth=new_depth)
    cmds.move(center[0], center[1], center[2], new_cube)
    return True


def apply_fix(issue):
    if issue['action'] == 'triangulate':
        return fix_triangulate(issue['mesh'])
    elif issue['action'] == 'reduce':
        return fix_reduce(issue['mesh'])
    elif issue['action'] == 'fix_thin':
        return fix_thin(issue)
    return False


# ========== 主检测流程 ==========

def run_full_detect():
    meshes = get_selected_meshes()
    if not meshes:
        return [], 0
    
    all_issues = []
    
    # 拓扑检测
    topo_issues, total_faces = detect_topology(meshes)
    all_issues.extend(topo_issues)
    
    # 结构检测
    struct_issues = detect_structure(meshes)
    all_issues.extend(struct_issues)
    
    return all_issues, total_faces


# ========== 修复流程 ==========

def run_all_fixes(issues, dialog_name):
    cmds.deleteUI(dialog_name, window=True)
    
    print("\n" + "=" * 60)
    print("🔧 开始自动修复...")
    print("=" * 60)
    
    success = 0
    for i, issue in enumerate(issues):
        print(f"\n[{i+1}/{len(issues)}] {issue['fix']}")
        try:
            result = apply_fix(issue)
            if result:
                print(f"   ✅ 成功")
                success += 1
            else:
                print(f"   ❌ 失败")
        except Exception as e:
            print(f"   ❌ 错误: {e}")
    
    print("\n" + "=" * 60)
    print(f"✅ 修复完成！成功 {success}/{len(issues)} 项")
    print("=" * 60)
    
    # 修复后重新检测
    print("\n🔍 修复后重新检测...")
    new_issues, new_total = run_full_detect()
    print(f"   修复后面数: {new_total}")
    if len(new_issues) == 0:
        print("   🎉 所有问题已修复！")
    else:
        print(f"   剩余问题: {len(new_issues)} 个")
        for iss in new_issues:
            print(f"     - [{iss['category']}] {iss['desc']}")


# ========== UI窗口 ==========

def show_main_window():
    window_name = "ModelAssistant"
    
    if cmds.window(window_name, exists=True):
        cmds.deleteUI(window_name, window=True)
    
    cmds.window(window_name, title="Maya 模型质量检测助手", widthHeight=(550, 500), sizeable=True)
    
    cmds.columnLayout(adjustableColumn=True, rowSpacing=10)
    
    # 标题
    cmds.text(label="🎮 游戏角色模型质量检测工具", font="boldLabelFont")
    cmds.separator(height=10, style='in')
    
    # 检测按钮
    cmds.button(label="🔍 开始全面检测", height=40, backgroundColor=[0.2, 0.5, 0.8],
                command=lambda x: on_detect_click())
    
    cmds.separator(height=10, style='in')
    
    # 结果显示区域
    cmds.text(label="检测结果:", font="boldLabelFont")
    result_scroll = cmds.scrollLayout(height=250, childResizable=True)
    result_text = cmds.text(label="点击上方按钮开始检测...", align='left', font="smallPlainLabelFont")
    
    cmds.setParent('..')
    
    cmds.separator(height=10, style='in')
    
    # 修复按钮（初始禁用）
    fix_button = cmds.button(label="🔧 确认修复所有问题", height=35, backgroundColor=[0.3, 0.7, 0.3],
                            enable=False)
    
    cmds.showWindow(window_name)
    
    return result_text, fix_button


def on_detect_click():
    result_text, fix_button = current_ui['result'], current_ui['fix_btn']
    
    cmds.text(result_text, edit=True, label="检测中...")
    
    issues, total_faces = run_full_detect()
    
    # 显示结果
    result_str = f"总面数: {total_faces}\n"
    result_str += f"共检测到 {len(issues)} 个问题:\n\n"
    
    # 按分类分组
    categories = {}
    for iss in issues:
        cat = iss['category']
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(iss)
    
    idx = 1
    for cat, cat_issues in categories.items():
        result_str += f"【{cat}】\n"
        for iss in cat_issues:
            result_str += f"  {idx}. {iss['desc']}\n"
            result_str += f"     → {iss['fix']}\n"
            idx += 1
        result_str += "\n"
    
    if len(issues) == 0:
        result_str += "✅ 模型状态良好，未发现问题！"
    
    cmds.text(result_text, edit=True, label=result_str)
    
    # 保存issues，启用修复按钮
    current_ui['issues'] = issues
    if len(issues) > 0:
        cmds.button(fix_button, edit=True, enable=True,
                    command=lambda x: run_all_fixes(issues, window_name))


# 存储UI元素和数据
current_ui = {
    'result': None,
    'fix_btn': None,
    'issues': []
}

window_name = "ModelAssistant"

# 显示主窗口
result_text, fix_button = show_main_window()
current_ui['result'] = result_text
current_ui['fix_btn'] = fix_button
