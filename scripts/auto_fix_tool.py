"""
游戏角色模型自动修复工具
带确认窗口：检测问题 → 显示修复方案 → 用户确认 → 自动修复
"""

import maya.cmds as cmds


# ========== 检测函数 ==========

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


def detect_all_issues():
    """检测所有问题，返回问题列表"""
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
        
        # 1. N-gon检测
        ngon_count = 0
        try:
            cmds.polySelect(mesh, ngon=True)
            sel = cmds.ls(selection=True, long=True)
            ngon_count = len([s for s in sel if mesh in s])
            cmds.select(mesh)
        except:
            pass
        
        if ngon_count > 0:
            issues.append({
                'type': 'ngon',
                'mesh': mesh,
                'name': name,
                'desc': f'{name}: {ngon_count}个N-gon面',
                'fix': f'三角化{ngon_count}个N-gon面',
                'action': 'triangulate_ngons'
            })
        
        # 2. 重叠面检测
        lamina_count = 0
        try:
            cmds.polySelect(mesh, lamina=True)
            sel = cmds.ls(selection=True, long=True)
            lamina_count = len([s for s in sel if mesh in s])
            cmds.select(mesh)
        except:
            pass
        
        if lamina_count > 0:
            issues.append({
                'type': 'lamina',
                'mesh': mesh,
                'name': name,
                'desc': f'{name}: {lamina_count}个重叠面',
                'fix': f'删除{lamina_count}个重叠面',
                'action': 'delete_lamina'
            })
        
        # 3. 高面数检测（超过500面的部件）
        if faces > 500:
            issues.append({
                'type': 'highpoly',
                'mesh': mesh,
                'name': name,
                'desc': f'{name}: {faces}面（面数过高）',
                'fix': f'降低{name}的细分，预计可减少约{int(faces*0.7)}面',
                'action': 'reduce_poly'
            })
    
    return issues, total_faces


# ========== 修复函数 ==========

def fix_ngons(mesh):
    """自动三角化N-gon面"""
    try:
        cmds.polySelect(mesh, ngon=True)
        cmds.polyTriangulate(ch=True)
        return True
    except:
        return False


def fix_lamina(mesh):
    """自动删除重叠面"""
    try:
        cmds.polySelect(mesh, lamina=True)
        cmds.delete()
        return True
    except:
        return False


def fix_highpoly(mesh):
    """简化高面数模型"""
    try:
        cmds.polySimplify(mesh, ratio=0.3, ch=False)
        return True
    except:
        return False


def run_fixes(issues, dialog_name):
    """执行所有修复"""
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
        elif issue['action'] == 'delete_lamina':
            result = fix_lamina(issue['mesh'])
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


# ========== UI窗口 ==========

def show_confirm_dialog(issues, total_faces):
    """显示确认修复窗口"""
    
    window_name = "ModelFixDialog"
    
    # 如果窗口已存在，先删除
    if cmds.window(window_name, exists=True):
        cmds.deleteUI(window_name, window=True)
    
    # 创建窗口
    cmds.window(window_name, title="模型修复方案确认", widthHeight=(500, 400), sizeable=True)
    
    cmds.columnLayout(adjustableColumn=True, rowSpacing=10)
    
    # 标题
    cmds.text(label="🔍 检测到以下建模问题", font="boldLabelFont")
    cmds.separator(height=10, style='in')
    
    # 问题列表
    if len(issues) == 0:
        cmds.text(label="✅ 未发现问题，模型状态良好！")
    else:
        cmds.text(label=f"共检测到 {len(issues)} 个问题：", align='left')
        cmds.separator(height=5, style='none')
        
        for i, issue in enumerate(issues):
            cmds.text(label=f"  {i+1}. {issue['desc']}", align='left')
            cmds.text(label=f"     → 修复方案: {issue['fix']}", align='left', font='smallPlainLabelFont')
    
    cmds.separator(height=10, style='in')
    
    # 整体统计
    cmds.text(label=f"当前总面数: {total_faces}", font="boldLabelFont")
    
    cmds.separator(height=10, style='in')
    
    # 按钮行
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

# 弹出确认窗口
show_confirm_dialog(issues, total_faces)
