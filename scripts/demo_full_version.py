"""
完整演示脚本：创建测试模型 + 运行质量检测
直接在Maya脚本编辑器里粘贴运行即可
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


def check_poly_count(mesh):
    transforms = cmds.listRelatives(mesh, parent=True, fullPath=True)[0]
    short_name = transforms.split('|')[-1]
    vertices = cmds.polyEvaluate(mesh, vertex=True)
    edges = cmds.polyEvaluate(mesh, edge=True)
    faces = cmds.polyEvaluate(mesh, face=True)
    triangles = cmds.polyEvaluate(mesh, triangle=True)
    return {'name': short_name, 'vertices': vertices, 'edges': edges, 'faces': faces, 'triangles': triangles}


def check_ngons(mesh):
    """检测N-gon面（大于4边的面）"""
    try:
        cmds.polySelect(mesh, ngon=True)
        selection = cmds.ls(selection=True, long=True)
        count = len([s for s in selection if mesh in s])
        cmds.select(mesh)
        return count
    except:
        return 0


def check_lamina_faces(mesh):
    """检测重叠面"""
    try:
        cmds.polySelect(mesh, lamina=True)
        selection = cmds.ls(selection=True, long=True)
        count = len([s for s in selection if mesh in s])
        cmds.select(mesh)
        return count
    except:
        return 0


def check_nonmanifold_edges(mesh):
    """检测非流形边"""
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
    if stats['faces'] > 10000:
        suggestions.append(f"⚠️ 面数较高（{stats['faces']}面），游戏模型建议优化")
    if ngons > 0:
        suggestions.append(f"⚠️ 发现 {ngons} 个N-gon面（大于4边），建议三角化")
    if lamina > 0:
        suggestions.append(f"⚠️ 发现 {lamina} 个重叠面，建议删除")
    if nonmanifold > 0:
        suggestions.append(f"⚠️ 发现 {nonmanifold} 条非流形边，检查拓扑")
    if floating > 0:
        suggestions.append(f"⚠️ 发现 {floating} 个游离顶点，建议清理")
    if not suggestions:
        suggestions.append("✅ 基础拓扑检查通过，状态良好！")
    return suggestions


def run_quality_check():
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


# ========== 创建演示模型 ==========

def create_demo_model():
    print("🔨 正在创建演示模型...")
    cmds.file(new=True, force=True)

    sphere = cmds.polySphere(name='Demo_Sphere', radius=2, subdivisionsAxis=20, subdivisionsHeight=15)
    print(f"   ✅ 创建标准球体: {sphere[0]}")

    cube = cmds.polyCube(name='Demo_Cube', width=3, height=3, depth=3)
    print(f"   ✅ 创建立方体: {cube[0]}")

    plane = cmds.polyPlane(name='Demo_ProblemPlane', width=5, height=5, subdivisionsX=1, subdivisionsY=1)
    print(f"   ⚠️ 创建有问题的平面（单段，N-gon面）: {plane[0]}")

    cmds.move(-4, 0, 0, sphere)
    cmds.move(4, 0, 0, cube)
    cmds.move(0, 0, 4, plane)

    cmds.select([sphere[0], cube[0], plane[0]])
    print("\n📦 演示模型创建完成！")


# ========== 运行 ==========

create_demo_model()
print("\n" + "=" * 50)
run_quality_check()
