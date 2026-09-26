"""
带瑕疵的Q版游戏角色演示脚本
自动创建一个有各种建模问题的角色，然后检测并给出修改意见
直接在Maya脚本编辑器里运行即可
"""

import maya.cmds as cmds


# ========== 检测函数 ==========

def check_poly_count(mesh):
    transforms = cmds.listRelatives(mesh, parent=True, fullPath=True)[0]
    short_name = transforms.split('|')[-1]
    vertices = cmds.polyEvaluate(mesh, vertex=True)
    edges = cmds.polyEvaluate(mesh, edge=True)
    faces = cmds.polyEvaluate(mesh, face=True)
    triangles = cmds.polyEvaluate(mesh, triangle=True)
    return {'name': short_name, 'vertices': vertices, 'edges': edges, 'faces': faces, 'triangles': triangles}


def check_ngons(mesh):
    try:
        cmds.polySelect(mesh, ngon=True)
        selection = cmds.ls(selection=True, long=True)
        count = len([s for s in selection if mesh in s])
        cmds.select(mesh)
        return count
    except:
        return 0


def check_lamina_faces(mesh):
    try:
        cmds.polySelect(mesh, lamina=True)
        selection = cmds.ls(selection=True, long=True)
        count = len([s for s in selection if mesh in s])
        cmds.select(mesh)
        return count
    except:
        return 0


def check_nonmanifold_edges(mesh):
    try:
        cmds.polySelect(mesh, nonManifoldEdges=True)
        selection = cmds.ls(selection=True, long=True)
        count = len([s for s in selection if mesh in s])
        cmds.select(mesh)
        return count
    except:
        return 0


def check_floating_vertices(mesh):
    vertices = cmds.ls(mesh + '.vtx[*]', flatten=True)
    floating = 0
    for vtx in vertices:
        edges = cmds.polyListComponentConversion(vtx, toEdge=True)
        if not edges or len(cmds.ls(edges, flatten=True)) == 0:
            floating += 1
    return floating


def calculate_tri_ratio(faces, triangles):
    if faces == 0:
        return 0
    return round(triangles / faces * 100, 1)


def generate_suggestions(stats, ngons, lamina, nonmanifold, floating):
    suggestions = []
    
    # 面数建议
    if stats['faces'] > 5000:
        suggestions.append(f"🔴 面数过高（{stats['faces']}面），游戏角色建议控制在2000面以内")
    elif stats['faces'] > 2000:
        suggestions.append(f"🟡 面数偏多（{stats['faces']}面），可根据项目需求优化")
    
    # N-gon建议
    if ngons > 0:
        suggestions.append(f"🔴 发现 {ngons} 个N-gon面，游戏引擎不支持，必须三角化或合理加线")
    
    # 重叠面建议
    if lamina > 0:
        suggestions.append(f"🔴 发现 {lamina} 个重叠面，会导致渲染闪烁，必须删除")
    
    # 非流形边建议
    if nonmanifold > 0:
        suggestions.append(f"🟡 发现 {nonmanifold} 条非流形边，会导致平滑错误，建议修复")
    
    # 游离顶点建议
    if floating > 0:
        suggestions.append(f"🟡 发现 {floating} 个游离顶点，建议清理删除")
    
    if not suggestions:
        suggestions.append("✅ 模型拓扑检查通过，状态良好！")
    
    return suggestions


# ========== 创建带瑕疵的角色 ==========

def create_buggy_character():
    """创建一个带各种瑕疵的Q版角色"""
    
    print("🎮 正在创建Q版游戏角色（故意带瑕疵）...")
    cmds.file(new=True, force=True)
    
    # 头部 - 正常球体
    head = cmds.polySphere(name='Character_Head', radius=1.2, subdivisionsAxis=20, subdivisionsHeight=15)
    cmds.move(0, 3, 0, head)
    print("   ✅ 头部：正常球体")
    
    # 身体 - 正常立方体
    body = cmds.polyCube(name='Character_Body', width=1.5, height=1.8, depth=1)
    cmds.move(0, 1.2, 0, body)
    print("   ✅ 身体：正常立方体")
    
    # 左臂 - 正常圆柱体
    arm_l = cmds.polyCylinder(name='Character_ArmL', radius=0.3, height=1.2, subdivisionsAxis=12)
    cmds.move(-1.2, 1.5, 0, arm_l)
    print("   ✅ 左臂：正常圆柱体")
    
    # 右臂 - 面数过高（故意做多细分）
    arm_r = cmds.polyCylinder(name='Character_ArmR', radius=0.3, height=1.2, subdivisionsAxis=32, subdivisionsHeight=20)
    cmds.move(1.2, 1.5, 0, arm_r)
    print("   🔴 右臂：面数过高（32x20细分）")
    
    # 左腿 - 正常
    leg_l = cmds.polyCube(name='Character_LegL', width=0.4, height=1.2, depth=0.4)
    cmds.move(-0.4, -0.3, 0, leg_l)
    print("   ✅ 左腿：正常立方体")
    
    # 右腿 - 1x1分段的平面（N-gon瑕疵）
    leg_r = cmds.polyPlane(name='Character_LegR', width=0.4, height=1.2, subdivisionsX=1, subdivisionsY=1)
    cmds.move(0.4, -0.3, 0, leg_r)
    cmds.rotate(90, 0, 0, leg_r)
    print("   🔴 右腿：单段平面（N-gon面瑕疵）")
    
    # 故意添加一个重叠面（在身体上复制一个面）
    cmds.select(body[0] + '.f[2]')
    cmds.duplicate(returnPaths=True, inputConnections=3)
    print("   🔴 身体上有重叠面瑕疵")
    
    # 故意添加游离顶点
    cmds.select(clear=True)
    floating_vtx = cmds.polyCreateFacet(point=[(5, 5, 0), (5.1, 5, 0), (5, 5.1, 0)])
    cmds.select(floating_vtx[0] + '.f[0]')
    cmds.delete()
    print("   🟡 场景中有游离顶点瑕疵")
    
    # 选中所有角色部件
    all_parts = [head[0], body[0], arm_l[0], arm_r[0], leg_l[0], leg_r[0]]
    cmds.select(all_parts)
    
    print("\n📦 角色创建完成！")
    print("   包含6个部件，故意埋了以下问题：")
    print("   - 右臂面数过高")
    print("   - 右腿是N-gon单段平面")
    print("   - 身体上有重叠面")
    print("   - 场景中有游离顶点")
    
    return all_parts


# ========== 运行检测 ==========

print("=" * 60)
print("🎮 Q版游戏角色建模质量检测")
print("=" * 60)

# 创建带瑕疵的角色
create_buggy_character()

print("\n" + "=" * 60)
print("🔍 开始检测...")
print("=" * 60)

# 获取所有选中的mesh
selection = cmds.ls(selection=True, long=True)
meshes = []
for node in selection:
    shapes = cmds.listRelatives(node, shapes=True, type='mesh', fullPath=True)
    if shapes:
        meshes.extend(shapes)

all_suggestions = []
total_faces = 0

for mesh in meshes:
    stats = check_poly_count(mesh)
    ngons = check_ngons(mesh)
    lamina = check_lamina_faces(mesh)
    nonmanifold = check_nonmanifold_edges(mesh)
    floating = check_floating_vertices(mesh)
    tri_ratio = calculate_tri_ratio(stats['faces'], stats['triangles'])
    
    total_faces += stats['faces']
    
    print(f"\n🔹 {stats['name']}")
    print(f"   顶点: {stats['vertices']}  |  面数: {stats['faces']}  |  三角面占比: {tri_ratio}%")
    print(f"   N-gon: {ngons}  |  重叠面: {lamina}  |  非流形边: {nonmanifold}  |  游离顶点: {floating}")
    
    suggestions = generate_suggestions(stats, ngons, lamina, nonmanifold, floating)
    for s in suggestions:
        print(f"      {s}")
    all_suggestions.extend([(stats['name'], s) for s in suggestions])

# 整体总结
print("\n" + "=" * 60)
print("📊 整体评估")
print("=" * 60)
print(f"   总面数: {total_faces}")
if total_faces > 2000:
    print(f"   🔴 总面数超标！游戏角色建议控制在2000面以内")
else:
    print(f"   ✅ 总面数符合游戏模型要求")

print("\n" + "=" * 60)
print("💡 整体修改建议")
print("=" * 60)
print("   1. 【右臂】面数过高，32x20细分可以降到12x8，节省约80%面数")
print("   2. 【右腿】单段平面是N-gon，需要加线做成合理的腿部拓扑")
print("   3. 【身体】删除重叠面，避免渲染闪烁")
print("   4. 【场景】清理多余的游离顶点")
print("   5. 【整体】UV需要展开并布局到0-1棋盘格内")
print("\n   修复后预计面数可控制在500面以内，符合手游角色标准")
print("=" * 60)
