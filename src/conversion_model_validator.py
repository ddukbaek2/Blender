import bpy
import os
import math
import json
import shutil
import blender_common


# 1. 텍스처 포함 여부 확인
def check_textures(fbx_path):
    required_textures = {
        'BaseColor': ['dif', '_d', 'diffuse'],
        'Normal': ['nor', '_n', 'normal'],
        'Metallic': ['met', '_m', 'metallic'],
        'Roughness': ['rgh', '_r', 'roughness']
    }

    texture_presence = {key: {'image_name': None, 'exists': False, 'correct_naming': False} for key in required_textures.keys()}

    textures, save_path = blender_common.save_texture(fbx_path)
    
    print(textures)
    for texture_type, texture_path in textures.items():
        # DEK : texutre_path가 None 일때 해당 함수에서 에러발생 후 뒤에 코드 진행 불가
        if texture_path is None:
            continue
        #
        tex_file_name = os.path.basename(texture_path)
        tex_name_lower = tex_file_name.lower()
        for type, identifiers in required_textures.items():
            for identifier in identifiers:
                if identifier in tex_name_lower:
                    # 네이밍 규칙에 맞는지 체크
                    texture_presence[type]['image_name'] = tex_name_lower
                    texture_presence[type]['exists'] = True
                    break

    if os.path.exists(save_path):
        shutil.rmtree(save_path, ignore_errors=True)
        
    return texture_presence


# 2. 텍스처 네이밍 여부 확인
def check_textures_naming(checked_textures):
    naming_issues = False
    # DEK : 베이스 맵은 무조건 있어야하고 네이밍 규칙 체크까지 완료 한 확인
    if not checked_textures["BaseColor"]["exists"]:
            naming_issues = True

    # DEK : 그 외 나머지 텍스처들은 존재하면 네이밍 규칙을 검사하기 때문에 일단 있는지 확인이 먼저 필요하다.
    if checked_textures["Normal"]['image_name'] and checked_textures["Normal"]["exists"] is False:
            naming_issues = True

    if checked_textures["Metallic"]['image_name'] and checked_textures["Metallic"]["exists"] is False:
            naming_issues = True

    if checked_textures["Roughness"]['image_name'] and checked_textures["Roughness"]["exists"] is False:
            naming_issues = True
    #
    return naming_issues

# 3. Unity setup의 1unit 기준이 centimeters로 되어있는지 확인 (FBX import 시에 설정에 따라 다름, 블렌더는 기본적으로 미터를 사용)
# 이 항목은 FBX 파일을 임포트할 때 설정되며, 스크립트로 직접 확인하기 어려움

# 4. 피복 위치가 (0, 0, 0)으로 되어있는지 확인
def check_object_location():
    for obj in bpy.data.objects:
        if obj.type == 'MESH':
            print(f"object location: {obj.location}")
            if not all(math.isclose(obj.location[i], 0.0, abs_tol=1e-6) for i in range(3)):
                return False
    return True

# 4. 피복 크기가 맥스 센치미터 기준으로 (100%, 100%, 100%)으로 되어있는지 확인
def check_object_scale():
    for obj in bpy.data.objects:
        if obj.type == 'MESH':
            print(f"object scale: {obj.scale}")
            if not all(math.isclose(obj.scale[i], 100.0, abs_tol=1e-6) for i in range(3)):
                return False
    return True

# 4. 피복 회전가 (0, 0, 0)으로 되어있는지 확인
def check_object_rotation():
    for obj in bpy.data.objects:
        if obj.type == 'MESH':
            print(f"object rotation: {obj.rotation_euler}")
            if not all(math.isclose(obj.rotation_euler[i], 0.0, abs_tol=1e-6) for i in range(3)):
                return False
    return True

# 5. 폴리곤 수 20,000개 이하 체크
def check_polygon_count():
    total_faces = sum([len(obj.data.polygons) for obj in bpy.data.objects if obj.type == 'MESH'])
    return total_faces

# 6. 5각 이상 폴리곤 존재 체크
def check_ngons():
    for obj in bpy.data.objects:
        if obj.type == 'MESH':
            for poly in obj.data.polygons:
                if len(poly.vertices) > 4:
                    return True
    return False

# 7. 연결되어 있지 않는 vertex 존재 체크
def check_loose_verts():
    for obj in bpy.data.objects:
        if obj.type == 'MESH':
            # 모든 버텍스에 대해 연결된 엣지의 수를 기록하는 딕셔너리 초기화
            vert_edges = {v: 0 for v in range(len(obj.data.vertices))}
            
            # 각 엣지가 연결하는 버텍스에 대해 카운트 증가
            for edge in obj.data.edges:
                vert_edges[edge.vertices[0]] += 1
                vert_edges[edge.vertices[1]] += 1
            
            # 연결된 엣지가 없는 버텍스 확인
            loose_verts = [v for v, count in vert_edges.items() if count == 0]
            
            if loose_verts:
                return True
    return False

# 8. Watertight 체크는 앞서 제공한 함수를 사용
def is_watertight(mesh):
    edges_shared_by_faces = {}
    for polygon in mesh.polygons:
        for key in polygon.edge_keys:
            edges_shared_by_faces[key] = edges_shared_by_faces.get(key, 0) + 1
    for count in edges_shared_by_faces.values():
        if count != 2:
            print(f" is_watertight return Count : {count}")
            return False
    return True

def check_all_meshes_watertight():
    watertight_results = []
    for obj in bpy.data.objects:
        if obj.type == 'MESH':
            result = {
                "name": obj.name,
                "state": is_watertight(obj.data)
            }
            watertight_results.append(result)
    return watertight_results

def print_watertight_results(watertight_results):
    for obj_name, is_wt in watertight_results.items():
        print(f"\'{obj_name}\' is watertight: {is_wt}")


# 9. uv island 체크
def check_islands():
    results = []
    for obj in bpy.context.selected_objects:
        if obj.type == 'MESH':
            result = {
                "name": obj.name,
                "count": len(blender_common.find_islands(obj))
            }
            results.append(result)

    return results


# 10. animation 체크
def check_animation():
    for obj in bpy.data.objects:
        if obj.animation_data:
            return True
    return False


# 11. 폴리곤 메쉬 flip의 수
def check_flipped():
    counter_clockwise_count = 0
    for obj in bpy.data.objects:
        if obj.type == 'MESH':
            obj.data.calc_normals_split()  # 노멀 재계산
            for polygon in obj.data.polygons:
                verts = [obj.data.vertices[v] for v in polygon.vertices]
                # 와인딩 오더를 계산하여 방향성 체크
                if (verts[1].co - verts[0].co).cross(verts[2].co - verts[1].co).dot(polygon.normal) < 0:
                    counter_clockwise_count += 1
    return counter_clockwise_count


# 12.그룹(컬렉션)의 이름 목록
def check_group_collections():
    group_names = [collection.name for collection in bpy.data.collections]
    return group_names

# 12. 그룹 ( 단일 메쉬 체크 및 그룹 오브젝트 체크 )
def check_group_mesh():
    # 모든 Mesh 타입 오브젝트 카운트
    mesh_count = sum(1 for obj in bpy.data.objects if obj.type == 'MESH')
    
    # 하위 객체를 가진 부모 오브젝트 카운트
    parent_objects = set()
    for obj in bpy.data.objects:
        if obj.parent:
            parent_objects.add(obj.parent)

    parent_object_count = len(parent_objects)

    return {
        'total_mesh_count': mesh_count,
        'parent_object_count': parent_object_count
    }

# result Text Print
def decode_issues(result):
    issues = []
    issues_index = []
    issue_descriptions = {
        0: "At least one of the Diffuse map or Basemap must be included.",
        1: "The name format is incorrect.",
        # 2: "The unit setup is incorrect.",
        3: "The position axis is not at (0,0,0).",
        # 4: "The object's central axis is not at (0,0,0).",  # 보류된 체크
        # 5: "Object rotation check failed",  # 보류된 체크
        # 8: "Inverted mesh(s) exist.",
        9: "Grouped meshe(s) exist.",
        10: "The maximum number of polygons has been exceeded (maximum of 20,000).",
        11: "Polygons other than triangles or quadrilaterals are included.",
        12: "There are disconnected vertices.",
        # 13: "",
        # 14: "",
        15: "There are holes in the mesh.",
        16: "It contains animation data.",
        17: "The number of ID maps has exceeded the limit (maximum of 20).",
        18: "The file format is incorrect."
    }

    # 각 문제에 대해 result 값을 비트 마스크와 AND 연산하여 체크
    for bit_position, description in issue_descriptions.items():
        if result & (1 << bit_position):
            issues_index.append(bit_position+1)
            issues.append(description)

    return issues_index, issues


# json 저장
def create_inspection_report(fbx_path):

    result = 0
    report = {}
    # 1 = texture check
    checked_textures = check_textures(fbx_path)
    report["Texture"] = checked_textures
    if checked_textures["BaseColor"]["exists"] == False:
        result |= 1 << 0

    #2 = texture name check
    if check_textures_naming(checked_textures):
        result |= 1 << 1

    # 4 = pivot location check
    checked_object_location = check_object_location()
    report["Location"] = checked_object_location
    if checked_object_location == False:
        result |= 1 << 3

    # 5 = pivot scale check (보류)
    checked_object_scale = check_object_scale()
    report["Scale"] = checked_object_scale
    # if checked_object_scale == False:
    #     result |= 1 << 4

    # 6 = pivot rotation check (보류)
    checked_object_rotation = check_object_rotation()
    report["Rotation"] = checked_object_rotation
    # if checked_object_rotation == False:
    #     result |= 1 << 5

    # 9 = flipped normal check
    checked_flipped = check_flipped()
    report["FlippedCount"] = checked_flipped
    # 경고처리 필요
    #if checked_flipped > 0:
    #    result |= 1 << 8

    # 10 = groupping check
    checked_group_collections = check_group_collections()
    checked_group_mesh =check_group_mesh()
    report["GroupCollections"] = checked_group_collections
    report["GroupMeshCheck"] = checked_group_mesh
    if len(checked_group_collections) > 1:
        result |= 1 << 9
    elif checked_group_mesh["total_mesh_count"] > 1 or checked_group_mesh["parent_object_count"] > 0:
        result |= 1 << 9

    # 11 = polygon count check
    checked_polygon_count = check_polygon_count()
    report["PolygonCount"] = checked_polygon_count
    if checked_polygon_count > 20000:
        result |= 1 << 10

    # 12 = polygon ngons check
    checked_ngons = check_ngons()
    report["Ngons"] = checked_ngons
    # 경고처리 필요
    #if checked_ngons == True:
    #    result |= 1 << 11

    # 13 = loose verts check
    checked_loose_verts = check_loose_verts()
    report["LooseVertices"] = checked_loose_verts
    # 경고처리 필요
    #if checked_loose_verts == True:
    #    result |= 1 << 12

    # 16 = watertight check
    checked_meshes_watertight = check_all_meshes_watertight()
    report["Watertight"] = checked_meshes_watertight
    # 방수 기능 체크는 에러가 아닌 경고이므로 임시로 결과값에 반영되지 않게 처리.
    #for watertight in checked_meshes_watertight:
    #    if watertight["state"] == False:
    #        result |= 1 << 15
    #        break

    # 17 = animation check
    checked_animation = check_animation()
    report["Animations"] = checked_animation
    if checked_animation == True:
        result |= 1 << 16

    # 18 = islands count check
    checked_islands = check_islands()
    report["Islands"] = checked_islands
    for islands in checked_islands:
        if islands["count"] > 20:
            result |= 1 << 17
            break

    # result    
    report["result"] = result
    binary_result = bin(result)[2:]  # '0b' 접두어 제거
    print(f"result: {result} ({binary_result.zfill(18)})")
    report["result_array"] = []
    report["result_array"] , report["result_desc"] = decode_issues(result)
    return report

def set_units_to_centimeters():

    # 현재 씬의 단위 설정을 가져옴
    unit_settings = bpy.context.scene.unit_settings
    # 단위 시스템을 메트릭으로 설정
    unit_settings.system = 'METRIC'
    # 길이 단위를 센티미터로 설정
    unit_settings.length_unit = 'CENTIMETERS'



def main(args : list):
    # '--' 인수 뒤에 오는 파일 경로를 가져옵니다.
    if len(args) > 0:        
        file_path = args[0]
        file_name, file_extension = os.path.splitext(file_path)  # 확장자 제거
        if file_extension.lower() == ".fbx":
            if os.path.isfile(f"{script_dir}/{file_name}_report.json"):
                os.remove(f"{script_dir}/{file_name}_report.json")
            
            fileOpen = False

            try:
                fileOpen = blender_common.load_fbx(file_path)
            except Exception as e:
                fileOpen = False
                print("예외가 발생했습니다:", e) 

            if fileOpen:
                report = create_inspection_report(file_path)
            else:
                result = {}
                result_code = 0
                result_code |= 1 << 18
                result["result"] = result_code
                binary_result = bin(result_code)[2:]  # '0b' 접두어 제거
                print(f"result: {result_code} ({binary_result.zfill(18)})")
                result["result_array"] = []
                result["result_array"] , result["result_desc"] = decode_issues(result_code)
                report = result

            print(json.dumps(report, indent=4))
            with open(f'{file_name}_report.json', 'w', encoding='utf-8') as json_file:
                json.dump(report, json_file, ensure_ascii=False, indent=4)
        else:
            print("Error: FBX file path not provided.")
    else:
        print("Error: '--' argument separator not found.")

    return 0

# # # # 테스트 코드
# file_path = 'sample_resources/model.fbx'
# if blender_common.load_fbx(file_path):
#     # set_units_to_centimeters()
#     report = create_inspection_report(file_path)
#     # JSON 형식으로 결과 출력
#     print(json.dumps(report, indent=4))
#     with open('inspection_report.json', 'w', encoding='utf-8') as json_file:
#         json.dump(report, json_file, ensure_ascii=False, indent=4)