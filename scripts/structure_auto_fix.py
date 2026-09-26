"""
结构问题自动修复
检测到面片问题后，自动替换成实体
带确认窗口
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


def get_bbox(mesh):
    bb = cmds.exactWorldBoundingBox(mesh)
    center = [(bb[0]+bb[3])/2, (bb[1]+bb[4])/2, (bb[2]+bb[5])/2]
    size = [bb[3]-bb[0], bb[4]-bb[1], bb[5]-bb[2]]
    return {'center': center, 'size': size}


def detect_thin_parts():
    """检测所有面片问题"""
    meshes = get_selected_meshes()
    issues = []
    
    for mesh in meshes:
        transforms = cmds.listRelatives(mesh, parent=True, fullPath=True)[0]
        name = transforms.split('|')[-1]
        
        bbox = get_bbox(mesh)
        dims = sorted(bbox['size'])
        
        # 太薄就是面片
        if dims[0] < 0.2 * dims[1] and dims[1] > 0.3:
            issues.append({
                'mesh': mesh,
                'name': name,
                'bbox': bbox,
                'desc': f'{name} 是面片（太薄）',
                'fix': f'把{name}替换成实体立方体'
            })
    
    return issues


def fix_thin_to_solid(issue):
    """把面片替换成实体"""
    mesh = issue['mesh']
    bbox = issue['bbox']
    name = issue['name']
    
    # 记录位置和大小
    center = bbox['center']
    size = bbox['size']
    
    # 删除原来的面片
    transforms = cmds.listRelatives(mesh, parent=True, fullPath=True)[0]
    cmds.delete(transforms)
    
    # 创建新的立方体实体，大小和原来差不多
    # 让厚度至少和宽度一样
    new_width = max(size[0], 0.4)
    new_height = size[1]
    new_depth = max(size[2], 0.4)
    
    new_cube = cmds.polyCube(
        name=name,
        width=new_width,
        height=new_height,
        depth=new_depth
    )
    cmds.move(center[0], center[1], center[2], new_cube)
    
    return True


def run_fixes(issues, dialog_name):
    """执行所有修复"""
    cmds.deleteUI(dialog_name, window=True)
    
    print("\n" + "=" * 50)
    print("🔧 开始结构修复...")
    print("=" * 50)
    
    success = 0
    for issue in issues:
        print(f"\n修复: {issue['fix']}")
        try:
            fix_thin_to_solid(issue)
            print(f"   ✅ 成功：面片已替换为实体")
            success += 1
        except Exception as e:
            print(f"   ❌ 失败: {e}")
    
    print("\n" + "=" * 50)
    print(f"✅ 修复完成！成功 {success}/{len(issues)} 项")
    print("=" * 50)
    
    # 重新检测
    print("\n🔍 修复后重新检测...")
    new_issues = detect_thin_parts()
    if len(new_issues) == 0:
        print("   🎉 所有面片问题已修复！")
    else:
        print(f"   剩余问题: {len(new_issues)} 个")


def show_confirm_dialog(issues):
    """显示确认窗口"""
    window_name = "StructureFixDialog"
    
    if cmds.window(window_name, exists=True):
        cmds.deleteUI(window_name, window=True)
    
    cmds.window(window_name, title="结构问题修复方案", widthHeight=(500, 300), sizeable=True)
    cmds.columnLayout(adjustableColumn=True, rowSpacing=10)
    
    cmds.text(label="🔍 检测到以下结构问题", font="boldLabelFont")
    cmds.separator(height=10, style='in')
    
    for i, issue in enumerate(issues):
        cmds.text(label=f"  {i+1}. {issue['desc']}", align='left')
        cmds.text(label=f"     → 修复: {issue['fix']}", align='left', font='smallPlainLabelFont')
    
    cmds.separator(height=10, style='in')
    cmds.text(label="修复后会把面片替换成等大的实体立方体", font="smallPlainLabelFont")
    cmds.separator(height=10, style='in')
    
    cmds.rowLayout(numberOfColumns=2, columnWidth2=(200, 200), adjustableColumn=1)
    cmds.button(label="✅ 确认修复", backgroundColor=[0.3, 0.7, 0.3],
                command=lambda x: run_fixes(issues, window_name))
    cmds.button(label="❌ 取消", backgroundColor=[0.7, 0.3, 0.3],
                command=lambda x: cmds.deleteUI(window_name, window=True))
    
    cmds.showWindow(window_name)


# 主流程
print("🔍 检测结构问题...")
issues = detect_thin_parts()
print(f"发现 {len(issues)} 个面片问题")

if len(issues) > 0:
    show_confirm_dialog(issues)
else:
    print("✅ 没有检测到结构问题")
