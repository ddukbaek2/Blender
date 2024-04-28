import bpy
import os
import json
import sys
import shutil
from PIL import Image
from datetime import datetime


def find_models(folder_src_path):
    model_info = {}
    for root, dirs, files in os.walk(folder_src_path):
        for file in files:
            file_lower = file.lower()
            print(file_lower)
            if file_lower.endswith('.fbx'):
                file_path = os.path.join(root, file)
                file_path = file_path.replace("\\", "/")
                file_name = os.path.basename(file_path)

                contained_vw_data = next((vw_data for vw_data in vw_datas if vw_data in file_name), None)
                if contained_vw_data is not None:
                    model_info[contained_vw_data] = file_path
    
    return model_info

### 컨버전 템플릿 생성에서는 사용하지 않는 함수 - FBX 임배딩 돼 있음
def find_textures(folder_src_path):
    textures_info = {
        'diffuse': None,
        'normal': None,
        'metallic': None,
        'roughness': None
    }
    for root, dirs, files in os.walk(folder_src_path):
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
    
    return textures_info


def find_idmaps(folder_src_path):
    found_files = []
    idmaps_info = {}
    
    for root, dirs, files in os.walk(folder_src_path):
        for file in files:
            file_lower = file.lower()
            if file_lower.endswith('.png') and 'id' in file_lower:
                file_path = os.path.join(root, file).replace("\\", "/")
                blender_common.reduce_colors_with_pillow(file_path, file_path)
                found_files.append(file_path)
    
    found_files.sort()
    
    for count, file_path in enumerate(found_files):
        idmaps_info[count] = file_path
    
    return idmaps_info


# 추출 병합
for id, model_name in model_dict.items():
    model_name_low = model_name.lower()
    model_dir = os.path.join(model_path, model_name_low)
    preset_dir = os.path.join(process_path, model_name_low)
    collect_dir = os.path.join(extract_to_path, model_name_low)
    blender_common.clear_directory(collect_dir)
    
    print(model_name_low)

    model_info = find_models(model_dir)
    print(f'model_info:')
    print(json.dumps(model_info, indent=4))
    
    process_info = find_models(preset_dir)
    print(f'process_info:')
    print(json.dumps(process_info, indent=4))

    isfirst = False    
    virtual_world = {}
    # 모델 폴더에서 모델링 옮기기. 텍스쳐, glb 처리
    for model, path in model_info.items():
        extract_files = []
        
        if blender_common.load_fbx(path):
            total_faces = sum([len(obj.data.polygons) for obj in bpy.data.objects if obj.type == 'MESH'])
            print(total_faces)
            if total_faces == 0:
                break

            textures, save_path = blender_common.save_texture(path)

            diffuse_path = textures['diffuse']
            normal_path = textures['normal']
            metallic_path = textures['metallic']
            roughness_path = textures['roughness']
            blender_common.setting_material(diffuse_path, normal_path, metallic_path, roughness_path)

            
            if idmap_export and isfirst == False:
                for obj in bpy.context.selected_objects:
                    if obj.type == 'MESH':
                        idmap_names = blender_common.export_idmap(collect_dir, obj)
                        isfirst = True
                        break

            extract_files.append(f"{model}.fbx")
            bpy.ops.export_scene.fbx(filepath=os.path.join(collect_dir, f"{model}.fbx"), path_mode='COPY', embed_textures=True, mesh_smooth_type='EDGE', bake_anim=False)
            
            blender_common.setting_export_glb()
            
            extract_files.append(f"{model}.glb")
            bpy.ops.export_scene.gltf(filepath=os.path.join(collect_dir, f"{model}.glb"), export_format='GLB', export_image_format='AUTO', export_apply=True)
            
            # extract_files.append(f"{model}_thumbnail.png")
            # blender_common.save_thumbnail(os.path.join(collect_dir, f"{model}_thumbnail.png"))

            if silhouettes_export:
                diffuse_path = '' # textures['diffuse']
            else:
                diffuse_path = textures['diffuse']
            normal_path = textures['normal']
            metallic_path = textures['metallic']
            roughness_path = textures['roughness']
            blender_common.setting_material(diffuse_path, normal_path, metallic_path, roughness_path)
            extract_files.append(f"{model}_thumbnail.png")
            blender_common.save_thumbnail(os.path.join(collect_dir, f"{model}_thumbnail.png"))
            
            virtual_world[model] = extract_files

            blender_common.clear_blender()
            if os.path.exists(save_path):
                shutil.rmtree(save_path, ignore_errors=True)
                
    for model, path in process_info.items():
        extract_files = []
        
        if blender_common.load_fbx(path):
            total_faces = sum([len(obj.data.polygons) for obj in bpy.data.objects if obj.type == 'MESH'])
            print(total_faces)
            if total_faces == 0:
                break

            textures, save_path = blender_common.save_texture(path)

            diffuse_path = textures['diffuse']
            normal_path = textures['normal']
            metallic_path = textures['metallic']
            roughness_path = textures['roughness']
            blender_common.setting_material(diffuse_path, normal_path, metallic_path, roughness_path)

            
            if idmap_export and isfirst == False:
                for obj in bpy.context.selected_objects:
                    if obj.type == 'MESH':
                        idmap_names = blender_common.export_idmap(collect_dir, obj)
                        isfirst = True
                        break

            extract_files.append(f"{model}.fbx")
            bpy.ops.export_scene.fbx(filepath=os.path.join(collect_dir, f"{model}.fbx"), path_mode='COPY', embed_textures=True, mesh_smooth_type='EDGE', bake_anim=False)
            
            blender_common.setting_export_glb()
            
            extract_files.append(f"{model}.glb")
            bpy.ops.export_scene.gltf(filepath=os.path.join(collect_dir, f"{model}.glb"), export_format='GLB', export_image_format='AUTO')
            
            extract_files.append(f"{model}_thumbnail.png")
            blender_common.save_thumbnail(os.path.join(collect_dir, f"{model}_thumbnail.png"))

            # if silhouettes_export:
            #     diffuse_path = '' # textures['diffuse']
            #     normal_path = textures['normal']
            #     metallic_path = textures['metallic']
            #     roughness_path = textures['roughness']
            #     blender_common.setting_material(diffuse_path, normal_path, metallic_path, roughness_path)
            #     blender_common.save_thumbnail(os.path.join(collect_dir, f"{model}_silhouettes.png"))
            
            virtual_world[model] = extract_files

            blender_common.clear_blender()
            if os.path.exists(save_path):
                shutil.rmtree(save_path, ignore_errors=True)
    
    
    report = {}
    report["idCount"] = len(idmap_names)
    for map_name in idmap_names:
        if "_all" in map_name:
            report["idCount"] = len(idmap_names) - 1
            break
    report["idName"] = idmap_names
    for model, data in virtual_world.items():
        report[model] = data
    
    print(json.dumps(report, indent=4))
    with open(os.path.join(collect_dir, 'data.json'), 'w', encoding='utf-8') as json_file:
        json.dump(report, json_file, ensure_ascii=False, indent=4)
    print()



def main(args : list):
    # 현재 스크립트의 디렉토리를 가져옴
    script_dir = os.path.dirname(os.path.abspath(__file__))
    # 스크립트 디렉토리를 Python의 검색 경로에 추가
    if script_dir not in sys.path:
        sys.path.append(script_dir)
    import blender_common

    # 현재 날짜와 시간을 얻어옴
    now = datetime.now()
    # 'YY_MM_DD' 형식으로 포매팅
    formatted_date = now.strftime("%y_%m_%d")

    # 실행 파일이 실제로 실행된 경로를 얻음
    if getattr(sys, 'frozen', False):
        # PyInstaller로 패키징된 경우
        application_dir = os.path.dirname(sys.executable)
    else:
        # 스크립트가 직접 Python 인터프리터로 실행된 경우
        application_dir = f"{script_dir}/Extract"

    application_dir = application_dir.replace("\\", "/")  # 윈도우 파일 경로 수정

    #application_dir = 'Z:\ACTS29_ART\ALTAVA\Conversion'

    # 실행 파일 폴더 검색 / 없다면 생성.
    if not os.path.exists(application_dir):
        print(f'not found extract folder. {application_dir}')
        os.makedirs(application_dir, exist_ok=True)
        sys.exit()  # 종료

    # path data 파일 검색 / 없다면 샘플 생성.
    loaded_json_data = {}  # 이 부분을 딕셔너리로 초기화
    json_file_path = os.path.join(application_dir, "info.json")
    json_file_path = json_file_path.replace("\\", "/")  # 윈도우 파일 경로 수정
    if not os.path.exists(json_file_path):
        print(f'not found json data file. {json_file_path}')
        
        loaded_json_data["model_path"] = 'Download/'
        loaded_json_data["process_path"] = 'Process/'
        loaded_json_data["extract_path"] = 'Complete/'
        loaded_json_data["vw_data"] = 'altava,roblox,snapchat,zepeto'
        loaded_json_data["idmap_export"] = '1'
        loaded_json_data["silhouettes_export"] = '1'
        
        blender_common.clear_directory(f'{application_dir}/Download/')

        with open(json_file_path, 'w', encoding='utf-8') as json_file:
            json.dump(loaded_json_data, json_file, ensure_ascii=False, indent=4)
        sys.exit()  # 종료


    # path data load.
    with open(json_file_path, "r") as json_file:
        loaded_json_data = json.load(json_file)



    model_path = f'{application_dir}/{loaded_json_data["model_path"]}'
    process_path = f'{application_dir}/{loaded_json_data["process_path"]}'
    vw_datas = loaded_json_data["vw_data"].split(',')
    idmap_export = False if loaded_json_data["idmap_export"] == '0' else True
    silhouettes_export = False if loaded_json_data["silhouettes_export"] == '0' else True
    extract_to_path = f'{application_dir}/{loaded_json_data["extract_path"]}'

    blender_common.clear_directory(extract_to_path)

    print(f'model_path:\t\t{model_path}')
    print(f'model_path:\t\t{process_path}')
    print(f'extract_to_path:\t{extract_to_path}')
    print(f'vw_datas:\t{vw_datas}')
    print(f'idmap_export:\t{idmap_export}')
    print(f'silhouettes_export:\t{silhouettes_export}')
    print('')

    model_dict = {}
    for root, dirs, files in os.walk(model_path):
        for model_folder_name in dirs:
            model_root = os.path.join(model_path, model_folder_name)
            if os.path.exists(model_root):
                model_dict[model_folder_name] = model_folder_name
        break

    print(f'model_dict:\n{model_dict}')
    print('')
