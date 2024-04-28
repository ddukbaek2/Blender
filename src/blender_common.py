import bpy
import os
import shutil
import zipfile
import requests
from PIL import Image, ImageDraw, ImageOps
from shapely.geometry import Polygon, mapping
from shapely.ops import transform
from collections import Counter
from mathutils import Vector, Euler
from math import radians



def clear_directory(path, subfix=""):
    if os.path.exists(path):
        shutil.rmtree(path, ignore_errors=True)
    os.makedirs(f"{path}{subfix}", exist_ok=True)

def path_join_file(main_path, file_name):
    return os.path.join(os.path.dirname(main_path), file_name)

# ZIP 파일 압축 해제
def unzip(path, unzip_path):
    with zipfile.ZipFile(path, 'r') as zip_ref:
        zip_ref.extractall(unzip_path)

# ZIP 파일 생성 및 압축 실행
def create_zip(path, file_name):
    with zipfile.ZipFile(file_name, 'w', zipfile.ZIP_DEFLATED) as zipf:
        len_dir_path = len(os.path.abspath(path))
        for root, dirs, files in os.walk(path):
            for file in files:
                file_path = os.path.join(root, file)
                # path 내부의 상대 경로를 압축 파일 내 경로로 사용
                zipf.write(file_path, file_path[len_dir_path:])
                

# 디자인랩 툴에서 보낸 파일 압축 해제
def unzip_tool(path, unzip_path):
    # ZIP 파일 압축 해제
    unzip(path, unzip_path)
    
    # 모델 확인
    modelURL = ''
    modelType = ''
    modelName = ''
    for root, dirs, files in os.walk(unzip_path):
        for file in files:
            # 텍스트 파일인지 확인
            if file.endswith('.txt'):
                file_path = os.path.join(root, file)
                # 파일 열기 및 내용 읽기
                with open(file_path, 'r') as f:
                    lines = f.readlines()
                    modelURL = lines[0].strip()
                    typeSTR = lines[1].strip().lower()
                    # lines[2].strip()
                    modelName = typeSTR

                    if typeSTR == "altava":
                        modelType = 0
                    elif typeSTR == "roblox":
                        modelType = 1
                    else:
                        modelType = 0
                        # modelName = "unknown"

    return modelURL, modelType, modelName
                

def download_model(url, file_path):
    # URL로부터 파일 다운로드
    response = requests.get(url)

    # HTTP 요청이 성공했는지 확인 (200 OK)
    if response.status_code == 200:
        # 바이너리 쓰기 모드로 파일을 열고 내용을 쓴다
        with open(file_path, 'wb') as file:
            file.write(response.content)
        print("File downloaded successfully.")
    else:
        print(f"Failed to download the file. Status code: {response.status_code}")


# FBX 파일 로드
def load_fbx(file_path):
    if not os.path.exists(file_path):
        print("FBX 파일이 존재하지 않습니다.")
        return False
    
    clear_blender()
    bpy.ops.import_scene.fbx(filepath=file_path, use_image_search=False)
    return True

    
def clear_blender():
    # 안전하게 이미지 삭제
    for img in bpy.data.images:
        if img.users == 0:
            bpy.data.images.remove(img)

    # 기타 데이터 삭제
    for mesh in bpy.data.meshes:
        bpy.data.meshes.remove(mesh)
    for material in bpy.data.materials:
        bpy.data.materials.remove(material)
    for texture in bpy.data.textures:
        bpy.data.textures.remove(texture)
    for obj in bpy.data.objects:
        bpy.data.objects.remove(obj)

    # 모든 오브젝트 삭제
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete()
    

# 오브젝트의 메테리얼 텍스쳐 정보를 검사
def analyze_materials():
    texture_type_mapping = {
        'Base Color': 'Diffuse',
        'NORMAL_MAP': 'Normal',
        'Specular IOR Level': 'Specular',
        # 기타 텍스쳐 타입도 필요하다면 여기에 추가
    }

    material_info = []

    # 모든 오브젝트를 순회
    for obj in bpy.data.objects:
        if obj.type == 'MESH' and obj.material_slots:
            # 각 메테리얼 슬롯을 검사
            for slot in obj.material_slots:
                mat = slot.material
                if mat and mat.use_nodes:
                    seen_textures = set()  # 이미 처리된 텍스쳐 이름을 저장하는 세트
                    texture_info = []
                    # 노드 기반의 재질에서 텍스쳐 노드 검사
                    for node in mat.node_tree.nodes:
                        if node.type == 'TEX_IMAGE' and node.image:
                            image_name = node.image.name
                            if image_name not in seen_textures:  # 중복 체크
                                # print(image_name)
                                seen_textures.add(image_name)
                                # 이미지 텍스쳐 노드가 연결된 노드를 검사
                                for output in node.outputs:
                                    for link in output.links:
                                        linked_node = link.to_node
                                        linked_input = link.to_socket.name
                                        if linked_input == 'Alpha':
                                            continue
                                        # print(f"{linked_node.type}: {linked_input}")
                                        # 연결된 노드가 어떤 유형인지 검사하여 텍스쳐 타입 결정
                                        if linked_node.type == 'BSDF_PRINCIPLED' and any(linked_input.startswith(x) for x in ['Specular', 'Metallic', 'Roughness', 'Base Color']):
                                            tex_type = linked_input
                                        else:
                                            tex_type = linked_node.type

                                        tex_type = texture_type_mapping.get(tex_type, tex_type)
                                        
                                        #tex_type = tex_type.lower()
                                        
                                        texture_info.append({
                                            'type': tex_type, 
                                            'texture': node.image
                                            # 'texture': node.image.name if node.image else 'No image loaded'
                                        })

                    material_info = {
                        'material': mat.name, 
                        'textures': texture_info
                    }
            break
    
    return material_info


def clean_texture_name(texture_name):
    # 파일 이름을 점(.)을 기준으로 전체 파트로 나눔
    parts = texture_name.split('.')
    # 확장자 후보군 설정
    valid_extensions = ['png', 'jpg', 'jpeg', 'tga']
    # 파일명은 항상 첫 번째 부분
    base_name = parts[0]
    # 확장자 찾기
    extension = next((part for part in parts[1:] if part in valid_extensions), None)
    # 확장자가 발견되면 새로운 파일 이름 생성
    if extension:
        return f"{base_name}.{extension}"
    else:
        return texture_name


def save_texture(fbx_path):
    textures_info = {
        'diffuse': None,
        'normal': None,
        'metallic': None,
        'roughness': None
    }
    
    fbx_name, file_extension = os.path.splitext(os.path.basename(fbx_path))
    save_path = os.path.join(os.path.dirname(fbx_path), f'{fbx_name}_textures')
    clear_directory(save_path)

    for image in bpy.data.images:
        if image.type == 'IMAGE' and image:
            file_name = os.path.basename(image.filepath)
            file_name = clean_texture_name(file_name)
            # 이미지 저장 시도 및 실패 처리에 따른 에러 문구 표시 -- 툴 멈추는 에러 발생방지
            try:
                image.save_render(os.path.join(save_path, file_name))
            except RuntimeError as e:
                print(f"Failed to save {file_name}: {e}")


    for root, dirs, files in os.walk(save_path):
        for file in files:
            file_lower = file.lower()
            root_lower = root.lower()
            if not root_lower.endswith('.fbx') and not root_lower.endswith('.fbm'):
                file_path = os.path.join(root, file)
                file_path = file_path.replace("\\", "/")
                file_name = os.path.basename(file_path)
                
                if 'diffuse' in file_lower or file_lower.endswith('_dif.png') or file_lower.endswith('_d.png') or file_lower.endswith('diffuse.png'):
                    textures_info['diffuse'] = file_path
                elif 'normal' in file_lower or file_lower.endswith('_nor.png') or file_lower.endswith('_n.png') or file_lower.endswith('normal.png'):
                    textures_info['normal'] = file_path
                elif 'metallic' in file_lower or file_lower.endswith('_met.png') or file_lower.endswith('_m.png') or file_lower.endswith('metallic.png') or file_lower.endswith('_met.tga') or file_lower.endswith('_m.tga') or file_lower.endswith('metallic.tga'):
                    textures_info['metallic'] = file_path
                elif 'roughness' in file_lower or file_lower.endswith('_rgh.png') or file_lower.endswith('_r.png') or file_lower.endswith('roughness.png'):
                    textures_info['roughness'] = file_path
    
    if textures_info['metallic'] == None:
        # 임시 메탈릭 이미지 생성
        width, height = 1024, 1024  # 이미지의 너비와 높이
        image = Image.new("RGBA", (width, height))
        pixels = [(0, 0, 0, 0)] * (width * height)
        image.putdata(pixels)
        temp_path = f"{save_path}/metallic.png"
        temp_path = temp_path.replace("\\", "/")
        image.filepath = temp_path
        image.save(temp_path)
        textures_info['metallic'] = temp_path
        
    return textures_info, save_path


def setting_material(diffuse_path, normal_path, metallic_path, roughness_path):

    # 새 재질 생성
    material = bpy.data.materials.new(name='PBR_Material')
    material.use_nodes = True
    nodes = material.node_tree.nodes
    links = material.node_tree.links        
    # 모든 노드 제거
    while nodes:
        nodes.remove(nodes[0])
        
    # Principled BSDF 쉐이더 노드 생성
    principled_bsdf = nodes.new(type='ShaderNodeBsdfPrincipled')
    principled_bsdf.location = (0, 0)
    # 출력 노드 찾기
    output_node = nodes.new(type='ShaderNodeOutputMaterial')
    output_node.location = (400, 0)    
    # Principled BSDF와 출력 노드 연결
    links.new(principled_bsdf.outputs['BSDF'], output_node.inputs['Surface'])

    # 알파 클리핑 설정
    material.blend_method = 'CLIP'  # 알파 클리핑 활성화
    material.alpha_threshold = 0.5  # 알파 클리핑 임계값 설정
    
    # 메탈릭 텍스처에서 러프니스 정보 추출 및 저장
    try:
        # 메탈릭 텍스처 로드 및 알파 채널 확인
        if metallic_path:
            metallic_img = Image.open(metallic_path)
            if 'A' in metallic_img.getbands():  # 알파 채널이 존재하는지 확인
                alpha_channel = metallic_img.getchannel('A')
                inverted_alpha_channel = ImageOps.invert(alpha_channel)
                
                # roughness_path가 유효하지 않으면 metallic_path 기반으로 새 경로 생성
                if not roughness_path or not os.path.isdir(os.path.dirname(roughness_path)):
                    roughness_dir = os.path.dirname(metallic_path)
                    roughness_filename = "roughness.png"
                    roughness_path = os.path.join(roughness_dir, roughness_filename)
                
                inverted_alpha_channel.save(roughness_path)
            else:
                print("No alpha channel in metallic texture for roughness information.")
            if metallic_path.lower().endswith(('.tga')):
                metallic_path = metallic_path[:-4] + '.png'
                metallic_img.save(metallic_path)

    except Exception as e:
        print(f"Error processing metallic texture for roughness: {e}")

    print(f"Diffuse: {diffuse_path}")
    print(f"Normal: {normal_path}")
    print(f"Metallic: {metallic_path}")
    print(f"Roughness: {roughness_path}")

    # 텍스처 노드 생성 및 설정
    # 디퓨즈 텍스처
    if diffuse_path:
        diffuse_texture = nodes.new(type='ShaderNodeTexImage')
        diffuse_texture.image = bpy.data.images.load(diffuse_path)
        links.new(principled_bsdf.inputs['Base Color'], diffuse_texture.outputs['Color'])
        links.new(diffuse_texture.outputs['Alpha'], principled_bsdf.inputs['Alpha'])

    # 노멀 맵
    if normal_path:
        normal_map = nodes.new(type='ShaderNodeNormalMap')
        normal_texture = nodes.new(type='ShaderNodeTexImage')
        normal_texture.image = bpy.data.images.load(normal_path)
        normal_texture.image.colorspace_settings.name = 'Non-Color'
        links.new(normal_map.inputs['Color'], normal_texture.outputs['Color'])
        links.new(principled_bsdf.inputs['Normal'], normal_map.outputs['Normal'])

    # 메탈릭 및 러프니스
    if metallic_path:
        metallic_texture = nodes.new(type='ShaderNodeTexImage')
        metallic_texture.image = bpy.data.images.load(metallic_path)
        metallic_texture.image.colorspace_settings.name = 'Non-Color'
        links.new(principled_bsdf.inputs['Metallic'], metallic_texture.outputs['Color'])

    # 러프니스 텍스쳐 로드 및 설정
    if roughness_path:
        roughness_texture = nodes.new(type='ShaderNodeTexImage')
        roughness_texture.image = bpy.data.images.load(roughness_path)
        roughness_texture.image.colorspace_settings.name = 'Non-Color'
        links.new(principled_bsdf.inputs['Roughness'], roughness_texture.outputs['Color'])

    # 오큘루전
    #occlusion_texture = nodes.new(type='ShaderNodeTexImage')
    #occlusion_texture.image = bpy.data.images.load(occlusion_path)
    #occlusion_texture.image.colorspace_settings.name = 'Non-Color'
    #links.new(principled_bsdf.inputs['Occlusion'], occlusion_texture.outputs['Color'])
    
    # 모든 오브젝트를 순회하면서 메시 이름이 파일명과 같은 경우에만 재질 할당
    for obj in bpy.context.scene.objects:
        if obj.type == 'MESH':
            obj.data.name = obj.name
            if not 'cage' in obj.name.lower():
                # 기존에 할당된 재질이 있다면 제거
                obj.data.materials.clear()
                # 새 재질 할당
                obj.data.materials.append(material)

    return material


def setting_export_glb():
    for obj in bpy.context.scene.objects:
        # obj.location = (0, 0, 0)
        obj.scale = (0.01, 0.01, 0.01)
        # 'cage'를 이름에 포함하는 메시 객체를 찾음
        if obj.type == 'MESH' and 'cage' in obj.name.lower():
            bpy.data.objects.remove(obj, do_unlink=True)
        elif obj.type != 'MESH':
            bpy.data.objects.remove(obj, do_unlink=True)
        else:
            bpy.context.view_layer.objects.active = obj
            obj.select_set(True)
            bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='BOUNDS')
            obj.location.y = 0
            obj.location.z = 0
            if obj.dimensions.z < 0.1:
                obj.scale = obj.scale * 30


# 섬에 속한 폴리곤들의 UV 좌표를 기반으로 고유 식별자를 생성합니다.
def serialize_island(uv_layer, island):
    uv_coords_list = []
    for poly in island:
        for li in poly.loop_indices:
            uv_coords = uv_layer[li].uv[:]
            uv_coords_list.append(tuple(uv_coords))
    # UV 좌표를 정렬하여 문자열로 변환합니다.
    uv_coords_list = sorted(uv_coords_list)
    return str(uv_coords_list)

# 중복된 섬을 제거하고 고유한 섬들만 반환합니다.
def remove_duplicate_islands(obj, islands):
    mesh = obj.data
    uv_layer = mesh.uv_layers.active.data
    
    # 각 섬의 고유 식별자를 생성합니다.
    serialized_islands = [serialize_island(uv_layer, island) for island in islands]
    
    # 중복 제거
    unique_island_ids = set(serialized_islands)
    
    # 고유한 섬들만 필터링합니다.
    unique_islands = []
    seen = set()
    for island, serialized in zip(islands, serialized_islands):
        if serialized in unique_island_ids and serialized not in seen:
            unique_islands.append(island)
            seen.add(serialized)
    
    return unique_islands

# 아일랜드 찾기
def find_islands(obj):
    mesh = obj.data
    if not mesh.uv_layers:
        print(f"{obj.name} has no UV maps.")
        return []

    uv_layer = mesh.uv_layers.active.data
    polygons = mesh.polygons  # Mesh polygons (faces)
    vertex_indices = [list(p.vertices) for p in polygons]  # Convert vertex indices for each polygon to list

    visited = [False] * len(polygons)
    islands = []

    for i, poly in enumerate(polygons):
        if visited[i]:
            continue

        island = []
        to_visit = [i]
        while to_visit:
            current = to_visit.pop()
            if visited[current]:
                continue

            visited[current] = True
            current_poly = polygons[current]
            island.append(current_poly)
            for j, poly in enumerate(polygons):
                if visited[j] or j == current:
                    continue

                shared_vertices = set(vertex_indices[current]) & set(vertex_indices[j])
                if shared_vertices:
                    shared_uvs = False
                    for sv in shared_vertices:
                        uv1 = uv_layer[current_poly.loop_start + vertex_indices[current].index(sv)].uv
                        uv2 = uv_layer[poly.loop_start + vertex_indices[j].index(sv)].uv
                        if uv1 == uv2:
                            shared_uvs = True
                            break

                    if shared_uvs:
                        to_visit.append(j)

        islands.append(island)
        
    unique_islands = remove_duplicate_islands(obj, islands)
    return sorted(unique_islands, key=lambda unique_islands: len(unique_islands), reverse=True)
    


def save_thumbnail(export_file_path, size = 512, samples = 32):
    obj_height = 1
    obj_width = 1
    # 기존 카메라 및 조명 삭제
    bpy.ops.object.select_all(action='DESELECT')
    for obj in bpy.data.objects:
        if obj.type == 'CAMERA' or obj.type == 'LIGHT':
            bpy.data.objects.remove(obj, do_unlink=True)
        else:
            bpy.context.view_layer.objects.active = obj
            obj.select_set(True)
            bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='BOUNDS')
            obj.location.y = 0
            obj.location.z = 0
            if obj.dimensions.z < 0.1:
                # DEK : 애니메이션 데이터의 액션을 삭제
                # 애니메이션 데이터 때문에 썸네일 랜더를 찍는 시점에서 객체에 할당된 애니메이션 데이터 삭제
                if obj.animation_data:
                    obj.animation_data_clear()
                #################################################
                obj.scale = obj.scale * 30
                bpy.ops.object.transform_apply(scale=True)
            obj_height = obj.dimensions.z
            obj_width = max(obj.dimensions.x, obj.dimensions.y)
            
    # 새 카메라 추가 및 설정
    cam_data = bpy.data.cameras.new(name='ThumbnailCam')
    cam_obj = bpy.data.objects.new('ThumbnailCam', cam_data)
    bpy.context.scene.collection.objects.link(cam_obj)
    bpy.context.scene.camera = cam_obj
    
    cam_data.clip_start = 0.001
    cam_data.clip_end = 100.0

    # if model_type == 0: # altava or origin
    #     cam_obj.location = (0.7, -2.58, 1.41)
    # elif model_type == 1: # Roblox
    #     cam_obj.location = (0.019555, -0.072313, 0.01257)
    # else:
    #     cam_obj.location = (0.7, -2.58, 1.41)        
        
    #cam_obj.rotation_euler = (1.361357, 0, 0.261799) # 78, 0, 15
    # 카메라 회전값 설정 (라디안 단위로 변환) (각도로: X축 약 78°, Y축 0°, Z축 약 15°)
    cam_obj.rotation_euler = Euler((1.361357, 0, 0.261799), 'XYZ')

    # 카메라 방향 벡터 계산
    # 카메라가 바라보는 방향으로의 단위 벡터
    direction_vector = Vector((0, 0, -1))  # 초기 방향 (블렌더에서 카메라의 기본 방향)
    direction_vector.rotate(cam_obj.rotation_euler)
    # 오브젝트의 크기를 기반으로 적절한 거리 계산
    max_dimension = max(max(obj_height, obj_width), 0.7)
    distance = max_dimension * 1.6  # 이 값은 실험을 통해 조정될 수 있음

    # 카메라 위치 조정
    # 오브젝트의 중심을 바라보도록 카메라 위치 설정
    cam_obj.location = Vector((0, 0, 0)) - direction_vector * distance

        
    # # 새 조명 추가 및 설정
    # light_data = bpy.data.lights.new(name='ThumbnailLight', type='SUN')
    # light_data.energy = 10
    # light_obj = bpy.data.objects.new(name='ThumbnailLight', object_data=light_data)
    # bpy.context.scene.collection.objects.link(light_obj)
    # # 조명 위치 설정 (모델에 따라 조정 필요)
    # light_obj.location = (0, -3, 5)
    # # light_obj.rotation_euler = (1.047198, -0.261799, 0) #60, -15, 0
    # light_obj.rotation_euler = (1.047198, -0.261799, 0) #60, -15, 0
    lights_data = [
        # {'name': 'CustomAreaLight', 'type': 'AREA', 'location': (1.2083696126937866, -2.7185118198394775, 3.0593149662017822), 'rotation_euler': (0.7463805079460144, -0.2348528802394867, 0.6711027026176453), 'energy': 50.0, 'color': (1.0, 0.7963117957115173, 0.6689997911453247)},
        # {'name': '스폿', 'type': 'SPOT', 'location': (-1.366156816482544, 1.1623139381408691, 0.3955937922000885), 'rotation_euler': (1.2164150476455688, -0.85017991065979, -2.0067708492279053), 'energy': 1000.0, 'color': (0.504607617855072, 0.6922617554664612, 1.0)},
        # {'name': '스폿.001', 'type': 'SPOT', 'location': (1.0009199380874634, -0.669060230255127, 0.5638577342033386), 'rotation_euler': (0.7976665496826172, 0.8984875679016113, 0.3149455189704895), 'energy': 200.0, 'color': (1.0, 0.9201820492744446, 0.8236137628555298)},
        # {'name': '태양', 'type': 'SUN', 'location': (0.0, -4.019999980926514, 2.1000001430511475), 'rotation_euler': (0.8726646900177002, 1.2217304706573486, 0.0), 'energy': 5.0, 'color': (1.0, 1.0, 1.0), 'angle': 0.009180432185530663}
        {'name': 'light_back', 'type': 'AREA', 'location': (-3.7646849155426025, 3.7481722831726074, 2.898800849914551), 'rotation_euler': (1.1693706512451172, -0.0, -2.33821702003479), 'energy': 1000.0, 'color': (0.42225509881973267, 0.6411089897155762, 1.0)},
        {'name': 'light_back.001', 'type': 'AREA', 'location': (-1.8545600175857544, 4.611219882965088, 2.569610118865967), 'rotation_euler': (1.1993082761764526, -0.15578128397464752, -2.7172157764434814), 'energy': 500.0, 'color': (0.5473594665527344, 0.8090500831604004, 1.0)},
        {'name': 'light_fill', 'type': 'AREA', 'location': (-2.85036039352417, -1.5933434963226318, 1.4312896728515625), 'rotation_euler': (1.3962634801864624, -0.0, -1.0375155210494995), 'energy': 50.0, 'color': (1.0, 1.0, 1.0)},
        {'name': 'light_fill.001', 'type': 'AREA', 'location': (-6.132923126220703, -3.082439422607422, 2.0668649673461914), 'rotation_euler': (1.3962634801864624, -0.0, -1.1449209451675415), 'energy': 100.0, 'color': (1.0, 1.0, 1.0)},
        {'name': 'light_key', 'type': 'AREA', 'location': (2.724699020385742, -1.350525140762329, 1.4312896728515625), 'rotation_euler': (1.3962634801864624, -0.0, 1.108622670173645), 'energy': 300.0, 'color': (1.0, 0.9411072134971619, 0.8647058606147766)},
        {'name': 'light_key.001', 'type': 'AREA', 'location': (4.795300006866455, -2.382009983062744, 1.8391900062561035), 'rotation_euler': (1.3962633609771729, 0.0, 1.108622670173645), 'energy': 300.0, 'color': (1.0, 1.0, 1.0)}
    ]
    # 로드된 조명 데이터를 바탕으로 조명을 씬에 추가합니다.
    for light_info in lights_data:
        # 조명 타입에 따라 다르게 처리합니다.
        if light_info['type'] == 'AREA':
            bpy.ops.object.light_add(type='AREA', location=light_info['location'])
            light = bpy.context.object
            light.data.size = light_info.get('size', 5)  # 'size' 값이 없는 경우 기본값으로 1을 사용합니다.
        elif light_info['type'] == 'SUN':
            bpy.ops.object.light_add(type='SUN', location=light_info['location'])
            light = bpy.context.object
            light.data.angle = light_info['angle']
        elif light_info['type'] == 'SPOT':
            bpy.ops.object.light_add(type='SPOT', location=light_info['location'])
            light = bpy.context.object
            light.data.spot_size = light_info.get('spot_size', 1.0472)  # 기본값은 라디안으로 약 60도
            light.data.spot_blend = light_info.get('spot_blend', 1)  # 빛의 가장자리 부드러움 정도
            
        else:
            continue  # 다른 타입의 조명은 여기에서 처리하지 않습니다.

        # 공통 조명 속성 설정
        light.name = light_info['name']
        light.data.energy = light_info['energy']
        light.data.color = light_info['color']
        light.rotation_euler = light_info['rotation_euler']


    # 렌더 설정
    bpy.context.scene.render.engine = 'CYCLES'  # 렌더 엔진을 CYCLES, BLENDER_EEVEE
    bpy.context.scene.render.resolution_x = size  # 이미지 가로 해상도
    bpy.context.scene.render.resolution_y = size  # 이미지 세로 해상도
    bpy.context.scene.render.image_settings.file_format = 'PNG'  # 출력 이미지 포맷
    bpy.context.scene.render.film_transparent = True  # 배경을 투명하게 설정
    bpy.context.scene.cycles.samples = samples

    # 이미지 렌더링 및 저장
    #bpy.context.scene.render.filepath = f"{export_path}/thumbnail.png"
    bpy.context.scene.render.filepath = export_file_path
    bpy.ops.render.render(write_still=True)  # 렌더링 및 이미지 파일로 저장


def save_uv_layout(image_path, obj):
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    
    # UV 맵 가시화
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')  # 모든 메쉬 선택
    bpy.ops.uv.reveal()  # 모든 UV 언랩
    
    # UV 레이아웃을 이미지로 저장
    bpy.ops.uv.export_layout(filepath=image_path, 
                             check_existing=True, 
                             export_all=False, 
                             modified=False, 
                             mode='SVG', 
                             size=(1024, 1024), 
                             opacity=0.5)
    
    bpy.ops.object.mode_set(mode='OBJECT')


def visualize_and_save_uv_map(path):
    for obj in bpy.context.scene.objects:
        if obj.type == 'MESH':
            image_path = os.path.join(os.path.dirname(path), obj.name + "_UV_Layout.svg")
            save_uv_layout(image_path, obj)
            print(f"UV 레이아웃 저장됨: {image_path}")
            # 한 오브젝트에 대해서만 실행하므로 루프 빠져나감
            break


def expand_polygon(points, expand_by=2):
    polygon = Polygon(points)
    expanded_polygon = polygon.buffer(expand_by)
    x, y = expanded_polygon.exterior.coords.xy
    return list(zip(x, y))


# 이미지 생성 및 저장
def export_idmap(path, obj, texture_size=(1024, 1024), expand_by=3):
    islands = find_islands(obj)  # 아일랜드 찾기
    mesh = obj.data
    uv_layer = mesh.uv_layers.active.data

    img_all = Image.new("RGBA", texture_size, color=(255, 255, 255, 0))
    draw_all = ImageDraw.Draw(img_all)

    # 아일랜드별 색상 지정을 위한 기본 색상
    base_colors = ["#FF5050", "#20E14B", "#2033E1", "#FF0DAD", "#FFCA0D", "#8F00FF", "#26F2FF", "#FF7A00", "#929292", "#D3FF00", "#FF5050", "#4FAC96", "#B78CD1", "#FF9B9B", "#A31659", "#007722", "#E2E2E2", "#C10000", "#1D97DB", "#FFFAA4"]
    color_index = 0

    save_textures = []

    for island in islands:
        # 텍스처 이미지 생성
        img = Image.new("RGBA", texture_size, color=(255, 255, 255, 0))
        draw = ImageDraw.Draw(img)
        
        if len(base_colors) > color_index:
            color = base_colors[color_index % len(base_colors)]  # 현재 아일랜드에 적용할 색상
        else:
            color = "#000000"
            break

        for poly in island:
            # 폴리곤의 UV 좌표를 기반으로 텍스처 이미지에 색상 적용
            uv_coords = [uv_layer[li].uv for li in poly.loop_indices]
            pixel_coords = [(int(uv[0] * (texture_size[0] - 1)), int((1 - uv[1]) * (texture_size[1] - 1))) for uv in uv_coords]
        
            expanded_coords = expand_polygon(pixel_coords, expand_by)
            # 폴리곤의 경계선만 그리는 대신 색을 채우는 로직을 추가해야 함
            draw.polygon(expanded_coords, fill=color)
            draw_all.polygon(expanded_coords, fill=color)

        # 텍스처 이미지 저장
        save_textures.append(f'idmap_{(color_index+1):02}.png')
        output_path = os.path.join(path, f'idmap_{color_index+1:02}.png')
        img.save(output_path)

        color_index += 1
    
    # 텍스처 이미지 저장
    #save_textures.append(f'idmap_all.png')
    output_path = os.path.join(path, f'idmap_all.png')
    img_all.save(output_path)
    return save_textures


def reduce_colors_with_pillow(input_path, output_path, num_colors = 256):
    with Image.open(input_path) as img:
        # 이미지를 P-모드로 변환하여 색상 수를 줄임
        img = img.convert('P', palette=Image.ADAPTIVE, colors=num_colors)
        
        # PNG 형식으로 저장
        img.save(output_path, format='PNG')