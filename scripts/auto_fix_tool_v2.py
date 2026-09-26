"""
游戏角色模型自动修复工具 v2
用更可靠的检测方法，不依赖版本特定的polySelect参数
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


def count_ngons_manual(mesh):
    """手动遍历每个面，数边数>4的面"""
    faces = cmds.ls(mesh + '.f[*]', flatten=True)
    ngon_count = 0
    for face in faces:
        edges = cmds.polyListComponentConversion(face, toEdge=True)
        if edges:
            edge_list = cmds.ls(edges, flatten=True)
            if len(edge_list) > 4:
                ngon_count += 1
    return ngon_count


def detect_all_issues():
    """检测所有问题"""
    meshes = get_selected_meshes()
    if not meshes:
        return [], 0
    
    issues = []
    total_faces = 0
    
    for mesh in meshes:
        transforms = cmds.listRelatives(mesh, parent=True, fullPath=True)[0]
        name = transforms.split('|')[-1]
        
        faces = cmds.polyEvaluate(mesh, face=True)
        total_faces += faces
        
        # 1. N-gon检测（手动遍历）
        ngon_count = count_ngons_manual(mesh)
        if ngon_count > 0:
            issues.append({
                'type': 'ngon',
                'mesh': mesh,
                'name': name,
                'desc': f'{name}: {ngon_count}个N-gon面（边数>4）',
                'fix': f'三角化{ngon_count}个N-gon面',
                'action': 'triangulate_ngons'
            })
        
        # 2. 高面数检测
        if faces > 200:
            issues.append({
                'type': 'highpoly',
                'mesh': mesh,
                'name': name,
                'desc': f'{name}: {faces}面（面数偏高）',
                'fix': f'简化{name}，预计减少约{int(faces*0.6)}面',
                'action': 'reduce_poly'
            })
    
    return issues, total_faces


def fix_ngons(mesh):
    """三角化所有面（简单粗暴但有效）"""
    try:
        cmds.polyTriangulate(mesh, ch=False)
        return True
    except:
        return False


def fix_highpoly(mesh):
    """简化模型面数"""
    try:
        cmds.polySimplify(mesh, ratio=0.4, ch=False)
        return True
    except:
        return False


def run_fixes(issues, dialog_name):
    """执行修复"""
    cmds.deleteUI(dialog_name, window=True)
    
    print("\n" + "=" * 50)
    print("🔧 开始自动修复...")
    print("=" * 50)
    
    success_count = 0
    for issue in issues:
        print(f"\n修复: {issue['fix']}")
        result = False
        
        if issue['action'] == 'triangulate_ngons':
            result = fix_ngons(issue['mesh'])
        elif issue['action'] == 'reduce_poly':
            result = fix_highpoly(issue['mesh'])
        
        if result:
            print(f"   ✅ 成功")
            success_count += 1
        else:
            print(f"   ❌ 失败")
    
    print("\n" + "=" * 50)
    print(f"✅ 修复完成！成功 {success_count}/{len(issues)} 项")
    print("=" * 50)
    
    # 修复后重新检测
    print("\n🔍 修复后重新检测...")
    new_issues, new_total = detect_all_issues()
    print(f"   修复后面数: {new_total}")
    if len(new_issues) == 0:
        print("   🎉 所有问题已修复！")
    else:
        print(f"   剩余问题: {len(new_issues)} 项")
        for iss in new_issues:
            print(f"     - {iss['desc']}")


def show_confirm_dialog(issues, total_faces):
    """显示确认窗口"""
    window_name = "ModelFixDialog"
    
    if cmds.window(window_name, exists=True):
        cmds.deleteUI(window_name, window=True)
    
    cmds.window(window_name, title="模型修复方案确认", widthHeight=(500, 400), sizeable=True)
    cmds.columnLayout(adjustableColumn=True, rowSpacing=10)
    
    cmds.text(label="🔍 检测到以下建模问题", font="boldLabelFont")
    cmds.separator(height=10, style='in')
    
    if len(issues) == 0:
        cmds.text(label="✅ 未发现问题，模型状态良好！")
    else:
        cmds.text(label=f"共检测到 {len(issues)} 个问题：", align='left')
        cmds.separator(height=5, style='none')
        for i, issue in enumerate(issues):
            cmds.text(label=f"  {i+1}. {issue['desc']}", align='left')
            cmds.text(label=f"     → 修复方案: {issue['fix']}", align='left', font='smallPlainLabelFont')
    
    cmds.separator(height=10, style='in')
    cmds.text(label=f"当前总面数: {total_faces}", font="boldLabelFont")
    cmds.separator(height=10, style='in')
    
    cmds.rowLayout(numberOfColumns=2, columnWidth2=(200, 200), adjustableColumn=1)
    cmds.button(label="✅ 确认自动修复", backgroundColor=[0.3, 0.7, 0.3], 
                command=lambda x: run_fixes(issues, window_name))
    cmds.button(label="❌ 取消", backgroundColor=[0.7, 0.3, 0.3],
                command=lambda x: cmds.deleteUI(window_name, window=True))
    
    cmds.showWindow(window_name)


# ========== 主流程 ==========
print("🔍 正在检测模型问题...")
issues, total_faces = detect_all_issues()

print(f"检测完成，发现 {len(issues)} 个问题")
print(f"当前总面数: {total_faces}")

for i, iss in enumerate(issues):
    print(f"  {i+1}. {iss['desc']}")

show_confirm_dialog(issues, total_faces)
